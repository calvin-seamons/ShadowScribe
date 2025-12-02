#!/usr/bin/env python3
"""
Character Builder

This module orchestrates all parsing scripts to create a complete Character object
from D&D Beyond JSON data.

Usage:
    from src.character_creation import CharacterBuilder
    
    builder = CharacterBuilder(dndbeyond_json_path)
    character = builder.build()
    
    # Or use the convenience function
    character = CharacterBuilder.from_json_file(dndbeyond_json_path)
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.rag.character.character_types import Character
from src.character_creation.parsing.parse_core_character import DNDBeyondCoreParser
from src.character_creation.parsing.parse_background_personality import DNDBeyondBackgroundParser
from src.character_creation.parsing.parse_features_traits import DNDBeyondFeaturesParser
from src.character_creation.parsing.parse_inventory import DNDBeyondInventoryParser
from src.character_creation.parsing.parse_actions import DNDBeyondActionsParser
from src.character_creation.parsing.parse_spelllist import DNDBeyondSpellParser


class CharacterBuilder:
    """
    Orchestrates all parsing to build a complete Character object.
    
    This class coordinates the specialized parsers to extract all character data
    from a D&D Beyond JSON export and assemble it into a unified Character object.
    """
    
    def __init__(self, json_data: Dict[str, Any]):
        """
        Initialize the character builder with D&D Beyond JSON data.
        
        Args:
            json_data: Complete D&D Beyond character export as dictionary
        """
        self.json_data = json_data
        self.data = json_data.get("data", {})
        
    @classmethod
    def from_json_file(cls, file_path: str) -> Character:
        """
        Convenience method to build a character directly from a JSON file.
        
        Args:
            file_path: Path to D&D Beyond JSON export file
            
        Returns:
            Complete Character object
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file isn't valid JSON
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        builder = cls(json_data)
        return builder.build()
    
    def build(self) -> Character:
        """
        Build the complete Character object by running all parsers in parallel.
        
        Returns:
            Complete Character object with all data populated
        """
        print("Building character from D&D Beyond data...")
        print("=" * 60)
        print("\nInitializing parsers...")
        
        # Initialize all parsers
        core_parser = DNDBeyondCoreParser(self.json_data)
        background_parser = DNDBeyondBackgroundParser(self.json_data)
        features_parser = DNDBeyondFeaturesParser(self.json_data)
        inventory_parser = DNDBeyondInventoryParser(self.json_data)
        actions_parser = DNDBeyondActionsParser(self.json_data)
        spell_parser = DNDBeyondSpellParser(self.json_data)
        
        print("Parsing all data in parallel...")
        
        # Run all parsers in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=6) as executor:
            # Submit all parsing tasks
            futures = {
                executor.submit(core_parser.parse_all_core_data): "core",
                executor.submit(background_parser.parse_all_background_data): "background",
                executor.submit(features_parser.parse_all_features): "features",
                executor.submit(inventory_parser.parse_inventory): "inventory",
                executor.submit(actions_parser.parse_all_actions): "actions",
                executor.submit(spell_parser.parse_all_spells): "spells"
            }
            
            # Collect results as they complete
            results = {}
            completed_count = 0
            total = len(futures)
            
            for future in as_completed(futures):
                parser_name = futures[future]
                completed_count += 1
                try:
                    results[parser_name] = future.result()
                    print(f"  ✓ [{completed_count}/{total}] {parser_name.capitalize()} parsing complete")
                except Exception as e:
                    print(f"  ✗ [{completed_count}/{total}] {parser_name.capitalize()} parsing failed: {e}")
                    import traceback
                    traceback.print_exc()
                    raise
        
        # Extract parsed data
        core_data = results["core"]
        background_data = results["background"]
        features_and_traits = results["features"]
        inventory = results["inventory"]
        actions = results["actions"]
        spell_list = results["spells"]
        
        # Build the complete character
        print("\n" + "=" * 60)
        print("Assembling complete character object...")
        
        from src.rag.character.character_types import (
            ActionEconomy,
            ObjectivesAndContracts
        )
        
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
        
        print("✓ Character build complete!")
        self._print_character_summary(character)
        
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
    
    def _print_character_summary(self, character: Character):
        """Print a summary of the built character."""
        print("\n" + "=" * 60)
        print("CHARACTER SUMMARY")
        print("=" * 60)
        print(f"Name: {character.character_base.name}")
        print(f"Race: {character.character_base.race}")
        print(f"Class: {character.character_base.character_class}")
        print(f"Level: {character.character_base.total_level}")
        print(f"Background: {character.character_base.background}")
        print(f"Alignment: {character.character_base.alignment}")
        
        if character.character_base.multiclass_levels:
            print("\nMulticlass Levels:")
            for cls, level in character.character_base.multiclass_levels.items():
                print(f"  • {cls}: {level}")
        
        print(f"\nHP: {character.combat_stats.max_hp}")
        print(f"AC: {character.combat_stats.armor_class}")
        print(f"Speed: {character.combat_stats.speed} ft")
        
        print("\nAbility Scores:")
        print(f"  STR: {character.ability_scores.strength}")
        print(f"  DEX: {character.ability_scores.dexterity}")
        print(f"  CON: {character.ability_scores.constitution}")
        print(f"  INT: {character.ability_scores.intelligence}")
        print(f"  WIS: {character.ability_scores.wisdom}")
        print(f"  CHA: {character.ability_scores.charisma}")
        
        if character.features_and_traits:
            print(f"\nRacial Traits: {len(character.features_and_traits.racial_traits)}")
            print(f"Feats: {len(character.features_and_traits.feats)}")
            
            total_class_features = sum(
                len(features)
                for levels in character.features_and_traits.class_features.values()
                for features in levels.values()
            )
            print(f"Class Features: {total_class_features}")
        
        if character.action_economy:
            print(f"\nTotal Actions: {len(character.action_economy.actions)}")
            print(f"Attacks per Action: {character.action_economy.attacks_per_action}")
        
        if character.inventory:
            equipped_count = sum(
                len(items) for items in character.inventory.equipped_items.values()
            )
            backpack_count = len(character.inventory.backpack)
            print(f"\nInventory Items: {equipped_count + backpack_count}")
            print(f"  Equipped: {equipped_count}")
            print(f"  Backpack: {backpack_count}")
            print(f"  Total Weight: {character.inventory.total_weight} {character.inventory.weight_unit}")
        
        if character.spell_list:
            total_spells = sum(
                len(spells)
                for class_spells in character.spell_list.spells.values()
                for spells in class_spells.values()
            )
            print(f"\nSpells Known: {total_spells}")
            print(f"Spellcasting Classes: {len(character.spell_list.spellcasting)}")
        
        print("=" * 60)


def main():
    """Main function for standalone script usage."""
    if len(sys.argv) != 2:
        print("Usage: python character_builder.py <path_to_dndbeyond_json>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    try:
        character = CharacterBuilder.from_json_file(json_file)
        
        # Optionally save the character
        output_file = json_file.replace('.json', '_character.pkl')
        
        from src.rag.character.character_manager import CharacterManager
        manager = CharacterManager()
        saved_path = manager.save_character(character)
        
        print(f"\n✓ Character saved to: {saved_path}")
        
    except FileNotFoundError:
        print(f"Error: File '{json_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{json_file}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
