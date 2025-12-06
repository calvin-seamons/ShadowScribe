#!/usr/bin/env python3
"""
Async Character Builder

Async wrapper for CharacterBuilder that provides real-time progress updates
via callbacks during the parsing process. All parsers run in parallel using
asyncio.TaskGroup for maximum performance.

This module is designed for use in the character creation wizard to provide
real-time feedback to users as their character is being parsed.

Usage:
    from src.character_creation.async_character_builder import AsyncCharacterBuilder
    
    async def progress_handler(event):
        print(f"{event['type']}: {event['parser']}")
    
    builder = AsyncCharacterBuilder(dndbeyond_json_data)
    character = await builder.build_async(progress_callback=progress_handler)
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime
from dataclasses import asdict

from src.rag.character.character_types import Character, ActionEconomy, ObjectivesAndContracts
from src.character_creation.parsing.parse_core_character import DNDBeyondCoreParser
from src.character_creation.parsing.parse_background_personality import DNDBeyondBackgroundParser
from src.character_creation.parsing.parse_features_traits import DNDBeyondFeaturesParser
from src.character_creation.parsing.parse_inventory import DNDBeyondInventoryParser
from src.character_creation.parsing.parse_actions import DNDBeyondActionsParser
from src.character_creation.parsing.parse_spelllist import DNDBeyondSpellParser


# Type alias for progress callback
ProgressCallback = Callable[[Dict[str, Any]], Awaitable[None]]


class AsyncCharacterBuilder:
    """
    Async wrapper for character building with progress callbacks.
    
    This class coordinates all parsers to run in parallel and provides
    real-time progress updates through callback functions.
    """
    
    def __init__(self, json_data: Dict[str, Any]):
        """
        Initialize the async character builder.
        
        Args:
            json_data: Complete D&D Beyond character export as dictionary
        """
        self.json_data = json_data
        self.data = json_data.get("data", {})
        
    async def build_async(
        self, 
        progress_callback: Optional[ProgressCallback] = None
    ) -> Character:
        """
        Build character asynchronously with progress updates.
        
        All 6 parsers run in parallel with no dependencies between them.
        Progress events are emitted for each parser as they start and complete.
        
        Args:
            progress_callback: Optional async callback for progress events.
                              Receives dict with keys: type, parser, completed, total, 
                              execution_time_ms (optional), message (optional)
        
        Returns:
            Complete Character object
            
        Progress Event Types:
            - parser_started: Parser has begun execution
            - parser_progress: Parser reports progress (for LLM-based parsers)
            - parser_complete: Parser has finished with timing data
            - assembly_started: Character object assembly has begun
            - creation_complete: Character creation finished
        """
        total_start = time.time()
        timing = {}
        
        # Parser definitions with names
        parsers = [
            ('core', DNDBeyondCoreParser, 'parse_all_core_data'),
            ('inventory', DNDBeyondInventoryParser, 'parse_inventory'),
            ('spells', DNDBeyondSpellParser, 'parse_all_spells'),
            ('features', DNDBeyondFeaturesParser, 'parse_all_features'),
            ('background', DNDBeyondBackgroundParser, 'parse_all_async'),  # Native async
            ('actions', DNDBeyondActionsParser, 'parse_all_actions'),
        ]
        
        total = len(parsers)
        completed = 0
        results = {}
        
        # Helper to emit progress events
        async def emit_progress(event: Dict[str, Any]):
            if progress_callback:
                await progress_callback(event)
        
        # Create tasks for all parsers
        async def run_parser(parser_name: str, parser_class, method_name: str):
            """Run a single parser with timing and progress tracking."""
            nonlocal completed
            
            parser_start = time.time()
            
            # Emit started event
            await emit_progress({
                'type': 'parser_started',
                'parser': parser_name,
                'completed': completed,
                'total': total
            })
            
            try:
                # Initialize parser
                parser = parser_class(self.json_data)
                parse_method = getattr(parser, method_name)
                
                # Run parser (use asyncio.to_thread for sync methods)
                if method_name == 'parse_all_async':
                    # Background parser is already async
                    result = await parse_method()
                else:
                    # Other parsers are sync, run in thread pool
                    result = await asyncio.to_thread(parse_method)
                
                parser_time = (time.time() - parser_start) * 1000  # Convert to ms
                timing[parser_name] = parser_time
                
                # Emit completed event
                completed += 1
                await emit_progress({
                    'type': 'parser_complete',
                    'parser': parser_name,
                    'completed': completed,
                    'total': total,
                    'execution_time_ms': round(parser_time, 2)
                })
                
                return parser_name, result
                
            except Exception as e:
                # Emit error but let it propagate
                await emit_progress({
                    'type': 'parser_error',
                    'parser': parser_name,
                    'completed': completed,
                    'total': total,
                    'error': str(e)
                })
                raise
        
        # Run all parsers in parallel using TaskGroup
        async with asyncio.TaskGroup() as group:
            tasks = [
                group.create_task(run_parser(name, parser_cls, method))
                for name, parser_cls, method in parsers
            ]
        
        # Collect results from completed tasks
        for task in tasks:
            parser_name, result = task.result()
            results[parser_name] = result
        
        # Emit assembly started
        await emit_progress({
            'type': 'assembly_started',
            'completed': total,
            'total': total
        })
        
        # Assemble the complete character
        character = self._assemble_character(results)
        
        # Calculate total time
        total_time = (time.time() - total_start) * 1000
        
        # Emit completion with performance metrics
        await emit_progress({
            'type': 'creation_complete',
            'character_name': character.character_base.name,
            'total_time_ms': round(total_time, 2),
            'parser_times': {k: round(v, 2) for k, v in timing.items()}
        })
        
        return character
    
    def _assemble_character(self, results: Dict[str, Any]) -> Character:
        """
        Assemble Character object from parser results.
        
        Args:
            results: Dictionary mapping parser names to their results
            
        Returns:
            Complete Character object
        """
        # Extract parsed data
        core_data = results["core"]
        background_data = results["background"]
        features_and_traits = results["features"]
        inventory = results["inventory"]
        actions = results["actions"]
        spell_list = results["spells"]
        
        # Create action economy from parsed actions
        action_economy = ActionEconomy(
            attacks_per_action=self._calculate_attacks_per_action(features_and_traits),
            actions=actions
        )
        
        # Create empty objectives (not available in D&D Beyond exports)
        objectives_and_contracts = ObjectivesAndContracts()
        
        # Assemble the complete character
        character = Character(
            # Required core fields
            character_base=core_data.character_base,
            characteristics=core_data.characteristics,
            ability_scores=core_data.ability_scores,
            combat_stats=core_data.combat_stats,
            background_info=background_data["background_info"],
            personality=background_data["personality_traits"],
            backstory=background_data["backstory"],
            
            # Optional fields
            organizations=background_data["organizations"],
            allies=background_data["allies"],
            enemies=background_data["enemies"],
            proficiencies=core_data.proficiencies,
            damage_modifiers=core_data.damage_modifiers,
            passive_scores=core_data.passive_scores,
            senses=core_data.senses,
            action_economy=action_economy,
            features_and_traits=features_and_traits,
            inventory=inventory,
            spell_list=spell_list,
            objectives_and_contracts=objectives_and_contracts,
            
            # Metadata
            notes={},
            created_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        return character
    
    def _calculate_attacks_per_action(self, features_and_traits) -> int:
        """
        Calculate attacks per action from class features.
        
        Looks for "Extra Attack" features to determine attack count.
        
        Args:
            features_and_traits: FeaturesAndTraits object
            
        Returns:
            Number of attacks per action (default 1)
        """
        attacks = 1
        
        for class_name, levels in features_and_traits.class_features.items():
            for level, features in levels.items():
                for feature in features:
                    if "extra attack" in feature.name.lower():
                        attacks = 2  # Standard extra attack gives 2 attacks
                        
                        # Fighters get more at higher levels
                        if class_name.lower() == "fighter" and level >= 11:
                            attacks = 3
                        if class_name.lower() == "fighter" and level >= 20:
                            attacks = 4
        
        return attacks


async def test_async_builder():
    """Test function to demonstrate async builder usage."""
    import json
    import sys
    from pathlib import Path
    
    if len(sys.argv) < 2:
        print("Usage: python async_character_builder.py <path_to_dndbeyond_json>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Progress callback
    async def progress_handler(event: Dict[str, Any]):
        event_type = event['type']
        
        if event_type == 'parser_started':
            print(f"  ⏳ [{event['completed']}/{event['total']}] Starting {event['parser']}...")
        
        elif event_type == 'parser_complete':
            time_ms = event.get('execution_time_ms', 0)
            print(f"  ✓ [{event['completed']}/{event['total']}] {event['parser'].capitalize()} complete ({time_ms:.0f}ms)")
        
        elif event_type == 'parser_error':
            print(f"  ✗ {event['parser'].capitalize()} failed: {event['error']}")
        
        elif event_type == 'assembly_started':
            print(f"\n  🔧 Assembling character object...")
        
        elif event_type == 'creation_complete':
            print(f"\n  ✓ Character creation complete!")
            print(f"     Character: {event['character_name']}")
            print(f"     Total time: {event['total_time_ms']:.0f}ms")
            print(f"\n  Parser execution times:")
            for parser, time_ms in sorted(event['parser_times'].items(), key=lambda x: x[1], reverse=True):
                print(f"     {parser}: {time_ms:.0f}ms")
    
    # Build character
    print("\n" + "="*80)
    print("ASYNC CHARACTER BUILDER - TEST")
    print("="*80)
    print(f"Input: {json_file}\n")
    
    builder = AsyncCharacterBuilder(json_data)
    character = await builder.build_async(progress_callback=progress_handler)
    
    # Print summary
    print("\n" + "="*80)
    print("CHARACTER SUMMARY")
    print("="*80)
    print(f"Name: {character.character_base.name}")
    print(f"Race: {character.character_base.race}")
    print(f"Class: {character.character_base.character_class}")
    print(f"Level: {character.character_base.total_level}")
    print(f"HP: {character.combat_stats.max_hp}")
    print(f"AC: {character.combat_stats.armor_class}")
    
    if character.spell_list:
        total_spells = sum(
            len(spells)
            for class_spells in character.spell_list.spells.values()
            for spells in class_spells.values()
        )
        print(f"Spells: {total_spells}")
    
    if character.inventory:
        total_items = (
            len(character.inventory.equipped_items) +
            len(character.inventory.backpack)
        )
        print(f"Items: {total_items}")
    
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_async_builder())
