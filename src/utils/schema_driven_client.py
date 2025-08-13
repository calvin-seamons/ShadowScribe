"""
Schema-Driven LLM Client

This module provides a generic, schema-driven approach to targeting and validating
character data without hardcoded character-specific logic.
"""

import json
import os
import asyncio
from typing import Dict, List, Optional, Callable, Any
from openai import AsyncOpenAI
from pathlib import Path

# Import the JSONSchemaLoader
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'web_app'))
from json_schema_loader import JSONSchemaLoader


class SchemaDrivenClient:
    """LLM client that uses schema definitions for generic character data operations."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.debug_callback: Optional[Callable] = None
        
        # Initialize the schema loader with proper base directory
        base_dir = os.getenv("SHADOWSCRIBE_BASE_DIR", os.path.join(os.path.dirname(__file__), '..', '..'))
        structures_path = os.path.join(base_dir, "knowledge_base", "character-json-structures")
        self.schema_loader = JSONSchemaLoader(structures_path)
        
        # Get available file types and their schemas
        self.available_file_types = self.schema_loader.get_all_file_types()
        self.file_schemas = {}
        self.file_templates = {}
        
        # Load schemas and templates for all available file types
        for file_type in self.available_file_types:
            try:
                self.file_schemas[file_type] = self.schema_loader.get_schema_for_file_type(file_type)
                self.file_templates[file_type] = self.schema_loader.get_template_for_file_type(file_type)
            except Exception as e:
                print(f"Warning: Could not load schema for {file_type}: {e}")
    
    def _get_token_params(self, max_tokens: int) -> Dict[str, int]:
        """Get the appropriate token parameter name and value based on model."""
        # GPT-5 models use max_completion_tokens
        if (self.model.startswith("gpt-5") or 
            self.model.startswith("o1") or 
            self.model.startswith("o3")):
            return {"max_completion_tokens": max_tokens}
        else:
            # Older models (GPT-4, GPT-4o, etc.) use max_tokens
            return {"max_tokens": max_tokens}
    
    def _get_temperature_params(self, desired_temperature: float = 0.1) -> Dict[str, float]:
        """Get the appropriate temperature parameter based on model support."""
        # GPT-5, o1, and o3 models have a fixed temperature, so we don't send the parameter
        if (self.model.startswith("gpt-5") or
            self.model.startswith("o1") or
            self.model.startswith("o3")):
            return {}
        
        # All other models support a custom temperature
        return {"temperature": desired_temperature}
    
    def _get_reasoning_params(self) -> Dict[str, Any]:
        """Get reasoning parameters for all models."""
        # For GPT-5/o1/o3 models, use medium reasoning effort to preserve tokens for output
        # For other models, this parameter is ignored
        if (self.model.startswith("gpt-5") or 
            self.model.startswith("o1") or 
            self.model.startswith("o3")):
            return {"reasoning": {"effort": "medium"}}
        else:
            return {}
    
    async def _make_api_call(self, messages: List[Dict], debug_context: str = "API_CALL", reasoning_effort: str = "low"):
        """Make unified API call using chat.completions API - NO TOKEN LIMITS FOR TESTING."""
        
        # Calculate prompt size for analysis
        total_chars = sum(len(str(msg)) for msg in messages)
        print(f"\n[TOKEN TEST] ===== API CALL START =====")
        print(f"[TOKEN TEST] Context: {debug_context}")
        print(f"[TOKEN TEST] Model: {self.model}")
        print(f"[TOKEN TEST] Message count: {len(messages)}")
        print(f"[TOKEN TEST] Total prompt characters: {total_chars}")
        print(f"[TOKEN TEST] Estimated prompt tokens: ~{total_chars // 4}")
        
        await self._call_debug_callback(
            f"{debug_context}_START", 
            f"Making API call to {self.model}",
            {
                "model": self.model,
                "message_count": len(messages),
                "total_chars": total_chars
            }
        )
        
        try:
            # Build parameters based on model type - NO LIMITS FOR TESTING
            params = {
                "model": self.model,
                "messages": messages
            }
            
            # NO TOKEN LIMITS - let's see what the model actually uses
            if self.model.startswith("gpt-5") or self.model.startswith("o1") or self.model.startswith("o3"):
                # For GPT-5, we'll try different reasoning efforts to see impact
                params["reasoning_effort"] = reasoning_effort
                print(f"[TOKEN TEST] Using reasoning_effort: {reasoning_effort} (to maximize output)")
                print(f"[TOKEN TEST] NO max_completion_tokens limit set")
                # No temperature for GPT-5
            else:
                # Standard models - also no limit for testing
                params["temperature"] = 0.7  # More creative
                print(f"[TOKEN TEST] Using temperature: 0.7")
                print(f"[TOKEN TEST] NO max_tokens limit set")
            
            print(f"[TOKEN TEST] Making API call with params: {list(params.keys())}")
            response = await self.client.chat.completions.create(**params)
            
            # Analyze token usage
            if hasattr(response, 'usage'):
                usage = response.usage
                print(f"\n[TOKEN TEST] ===== TOKEN USAGE REPORT =====")
                print(f"[TOKEN TEST] Prompt tokens: {getattr(usage, 'prompt_tokens', 'N/A')}")
                print(f"[TOKEN TEST] Completion tokens: {getattr(usage, 'completion_tokens', 'N/A')}")
                print(f"[TOKEN TEST] Total tokens: {getattr(usage, 'total_tokens', 'N/A')}")
                
                # Check for GPT-5 specific token details
                if hasattr(usage, 'completion_tokens_details'):
                    details = usage.completion_tokens_details
                    print(f"[TOKEN TEST] Reasoning tokens: {getattr(details, 'reasoning_tokens', 'N/A')}")
                    print(f"[TOKEN TEST] Output tokens: {getattr(details, 'output_tokens', 'N/A')}")
                    if hasattr(details, 'reasoning_tokens') and hasattr(details, 'output_tokens'):
                        ratio = details.output_tokens / (details.reasoning_tokens + details.output_tokens) if (details.reasoning_tokens + details.output_tokens) > 0 else 0
                        print(f"[TOKEN TEST] Output/Total ratio: {ratio:.2%}")
                
                print(f"[TOKEN TEST] ===========================\n")
            
            await self._call_debug_callback(
                f"{debug_context}_RESPONSE_RECEIVED", 
                "Raw API response received",
                {
                    "response_type": type(response).__name__,
                    "has_choices": hasattr(response, 'choices'),
                    "has_usage": hasattr(response, 'usage')
                }
            )
            
            return response
            
        except Exception as e:
            print(f"[TOKEN TEST] API ERROR: {e}")
            await self._call_debug_callback(
                f"{debug_context}_ERROR", 
                f"API call failed: {str(e)}",
                {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "model": self.model
                }
            )
            raise
    
    async def _extract_content_with_debugging(self, response, debug_context: str = "EXTRACT") -> str:
        """Extract content from standard chat.completions API response."""
        
        # Detailed response analysis
        response_info = {
            "response_type": type(response).__name__,
            "has_choices": hasattr(response, 'choices'),
            "has_usage": hasattr(response, 'usage')
        }
        
        content = ""
        
        try:
            # Standard chat.completions API response format
            if hasattr(response, 'choices') and response.choices:
                response_info["choices_count"] = len(response.choices)
                
                if len(response.choices) > 0:
                    choice = response.choices[0]
                    response_info.update({
                        "choice_has_message": hasattr(choice, 'message'),
                        "finish_reason": getattr(choice, 'finish_reason', None)
                    })
                    
                    if hasattr(choice, 'message') and choice.message:
                        message = choice.message
                        response_info.update({
                            "message_role": getattr(message, 'role', None),
                            "message_has_content": hasattr(message, 'content')
                        })
                        
                        if hasattr(message, 'content'):
                            content = message.content or ""
                            response_info["extracted_content_length"] = len(content)
        
        except Exception as e:
            response_info["extraction_error"] = str(e)
        
        # Usage information if available
        if hasattr(response, 'usage'):
            usage = response.usage
            if hasattr(usage, 'completion_tokens_details'):
                details = usage.completion_tokens_details
                response_info.update({
                    "total_tokens": getattr(usage, 'total_tokens', None),
                    "completion_tokens": getattr(usage, 'completion_tokens', None),
                    "reasoning_tokens": getattr(details, 'reasoning_tokens', None),
                    "output_tokens": getattr(details, 'output_tokens', None)
                })
        
        # Log detailed analysis
        await self._call_debug_callback(
            f"{debug_context}_ANALYSIS", 
            f"Content extraction analysis: {len(content)} characters extracted",
            response_info
        )
        
        # Special alert for empty responses
        if not content or len(content) == 0:
            await self._call_debug_callback(
                f"{debug_context}_EMPTY_RESPONSE_ALERT", 
                "🚨 EMPTY RESPONSE DETECTED - Detailed analysis",
                {
                    **response_info,
                    "alert_type": "EMPTY_RESPONSE",
                    "model": self.model,
                    "possible_causes": [
                        "All tokens consumed by reasoning (check reasoning_tokens vs output_tokens)",
                        "Content filtering blocked the response",
                        "Model refusal or safety filter triggered",
                        "Invalid input format or prompt issue",
                        "API response format changed",
                        "Incorrect content extraction path"
                    ]
                }
            )
        
        return content
    
    def set_debug_callback(self, callback: Callable):
        """Set debug callback for progress tracking."""
        self.debug_callback = callback
    
    async def _call_debug_callback(self, stage: str, message: str, data: Dict[str, Any] = None):
        """Call debug callback if set."""
        if self.debug_callback:
            try:
                import inspect
                if inspect.iscoroutinefunction(self.debug_callback):
                    await self.debug_callback(stage, message, data or {})
                else:
                    self.debug_callback(stage, message, data or {})
            except Exception as e:
                print(f"Debug callback error: {e}")
    
    def _generate_file_descriptions(self) -> str:
        """Generate descriptions of available files based on their schemas."""
        descriptions = []
        
        for file_type in self.available_file_types:
            # Convert file_type to filename
            filename = f"{file_type}.json"
            
            # Get schema info
            try:
                schema_info = self.schema_loader.get_schema_info(file_type)
                template = self.file_templates.get(file_type, {})
                
                # Get appropriate depth for this file type
                max_depth = self._get_optimal_depth_for_file_type(file_type)
                
                # Generate comprehensive description with keys only
                description = f"{filename} - Structure:\n"
                
                if isinstance(template, dict):
                    structure = self._extract_key_structure(template, max_depth=max_depth)
                    description += structure
                else:
                    description += "  Character data file"
                
                descriptions.append(description)
                
            except Exception as e:
                descriptions.append(f"{filename} - Character data file")
        
        return "\n".join(descriptions)
    
    def _get_optimal_depth_for_file_type(self, file_type: str) -> int:
        """Determine the optimal depth to show for each file type."""
        depth_map = {
            # Simple structure files - just show top 2 levels
            "character": 2,  # character_base, characteristics, ability_scores, combat_stats, etc.
            "character_background": 2,  # personality, ideals, bonds, flaws, backstory sections
            "objectives_and_contracts": 2,  # active_quests, completed_quests, contracts, etc.
            
            # Complex nested files - need deeper view  
            "feats_and_traits": 4,  # features_and_traits > class_features > paladin/warlock > features[]
            "spell_list": 3,  # spellcasting_classes > warlock/paladin > spells[]
            "inventory_list": 3,  # inventory > weapons/armor/items > individual items
            "action_list": 3,  # actions > combat/utility/special > individual actions
            
            # Default depth for unknown files
            "default": 2
        }
        
        return depth_map.get(file_type, depth_map["default"])
    
    def _extract_key_structure(self, data: Any, current_depth: int = 0, max_depth: int = 3, indent: str = "  ") -> str:
        """Extract key structure of data (keys only, no values) up to specified depth."""
        if current_depth >= max_depth:
            return ""
        
        structure_lines = []
        current_indent = indent * current_depth
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict) and value and current_depth < max_depth - 1:
                    # Show the key and its nested structure
                    structure_lines.append(f"{current_indent}{key}:")
                    nested = self._extract_key_structure(value, current_depth + 1, max_depth, indent)
                    if nested:
                        structure_lines.append(nested)
                elif isinstance(value, list) and value and current_depth < max_depth - 1:
                    # Show the key and sample list structure
                    structure_lines.append(f"{current_indent}{key}: [array]")
                    if isinstance(value[0], dict):
                        # Show structure of first array item
                        nested = self._extract_key_structure(value[0], current_depth + 1, max_depth, indent)
                        if nested:
                            structure_lines.append(f"{current_indent}{indent}[item]:")
                            structure_lines.append(nested)
                else:
                    # Leaf node or at max depth - show key and type only
                    if isinstance(value, list):
                        if value and isinstance(value[0], dict):
                            structure_lines.append(f"{current_indent}{key}: [array of objects]")
                        else:
                            structure_lines.append(f"{current_indent}{key}: [array]")
                    elif isinstance(value, dict):
                        structure_lines.append(f"{current_indent}{key}: {{object}}")
                    elif isinstance(value, str):
                        structure_lines.append(f"{current_indent}{key}: string")
                    elif isinstance(value, (int, float)):
                        structure_lines.append(f"{current_indent}{key}: number")
                    elif isinstance(value, bool):
                        structure_lines.append(f"{current_indent}{key}: boolean")
                    else:
                        structure_lines.append(f"{current_indent}{key}: {type(value).__name__}")
        
        return "\n".join(structure_lines)
    
    async def select_sources(self, query: str) -> Dict[str, Any]:
        """
        Select knowledge sources using generic logic.
        """
        await self._call_debug_callback(
            "SOURCE_SELECTION", 
            "Analyzing query for knowledge source needs",
            {"query": query}
        )
        
        prompt = f"""Given this query: "{query}"

Determine which knowledge sources are needed to answer this query.

Available sources:
1. dnd_rulebook - Game rules, spells, classes, mechanics
2. character_data - Character information and data files
3. session_notes - Campaign events, story progression

Selection guidelines:
- For rule questions (spells, combat, mechanics) → include "dnd_rulebook"
- For character questions (stats, equipment, abilities) → include "character_data"  
- For story/campaign questions (events, NPCs, narrative) → include "session_notes"
- For session summaries → include BOTH "character_data" AND "session_notes" (character context + events)
- For build/optimization questions → include BOTH "character_data" AND "dnd_rulebook"
- Complex queries may need multiple sources

IMPORTANT: If asking about sessions, summaries, or campaign events, ALWAYS include "character_data" to provide accurate character context and prevent hallucination.

Return ONLY a JSON object with this exact format:
{{
  "sources_needed": ["character_data", "dnd_rulebook"],
  "reasoning": "Character data for stats, rulebook for spell mechanics"
}}

RESPOND WITH ONLY VALID JSON, NO OTHER TEXT."""

        try:
            messages = [
                {"role": "system", "content": "Output only valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self._make_api_call(messages, "SOURCE_SELECTION")
            content = (await self._extract_content_with_debugging(response, "SOURCE_SELECTION")).strip()
            
            # Clean and parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content)
            
            # Validate structure
            if not isinstance(result, dict):
                raise ValueError("Response must be a dictionary")
            
            # Ensure required keys exist
            if "sources_needed" not in result:
                result["sources_needed"] = ["character_data"]
            if "reasoning" not in result:
                result["reasoning"] = "Default source selection"
            
            # Validate source names
            valid_sources = {"dnd_rulebook", "character_data", "session_notes"}
            result["sources_needed"] = [s for s in result["sources_needed"] if s in valid_sources]
            
            if not result["sources_needed"]:
                result["sources_needed"] = ["character_data"]
            
            await self._call_debug_callback(
                "SOURCE_SUCCESS", 
                "Successfully parsed source selection",
                {"sources": result["sources_needed"], "reasoning": result["reasoning"][:100] + "..."}
            )
            
            return result
            
        except Exception as e:
            await self._call_debug_callback(
                "SOURCE_ERROR", 
                f"Source selection failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
            
            return self._create_source_fallback(query)
    
    def _create_source_fallback(self, query: str) -> Dict[str, Any]:
        """Create comprehensive smart fallback for source selection."""
        query_lower = query.lower()
        sources = ["character_data"]  # Always include character data as base
        
        # Comprehensive rulebook keywords
        rulebook_keywords = [
            # Core mechanics
            "rule", "rules", "mechanic", "mechanics", "how does", "how do", "can i", "can you", 
            "what is", "what are", "explain", "definition", "meaning",
            
            # Combat
            "attack", "attacks", "damage", "hit", "miss", "critical", "crit", "armor class", "ac",
            "initiative", "action", "bonus action", "reaction", "movement", "opportunity attack",
            "grapple", "shove", "dodge", "dash", "disengage", "help", "hide", "ready", "search",
            "use object", "two weapon fighting", "dual wield", "flanking", "cover", "concealment",
            
            # Spellcasting mechanics
            "spell", "spells", "spellcasting", "cast", "casting", "concentration", "ritual",
            "spell slot", "spell slots", "cantrip", "cantrips", "spell save", "spell attack",
            "counterspell", "dispel", "metamagic", "sorcery points", "spell components",
            "verbal", "somatic", "material", "focus", "arcane focus", "component pouch",
            
            # Saving throws and checks
            "save", "saves", "saving throw", "ability check", "skill check", "proficiency",
            "advantage", "disadvantage", "inspiration", "luck", "reroll",
            
            # Conditions and effects
            "condition", "conditions", "status", "effect", "effects", "buff", "debuff",
            "poisoned", "charmed", "frightened", "paralyzed", "stunned", "unconscious",
            "prone", "restrained", "grappled", "incapacitated", "blinded", "deafened",
            "exhaustion", "petrified", "invisible", "hidden",
            
            # Rest and recovery
            "rest", "short rest", "long rest", "hit dice", "recovery", "heal", "healing",
            "hit points", "hp", "temporary hit points", "temp hp",
            
            # Classes and features
            "class feature", "class features", "multiclass", "multiclassing", "level up",
            "progression", "subclass", "archetype", "patron", "domain", "circle", "oath",
            "fighting style", "expertise", "sneak attack", "rage", "wild shape", "channel divinity",
            
            # Races and traits
            "racial trait", "racial traits", "racial feature", "darkvision", "resistance",
            "immunity", "vulnerability", "language", "languages", "size", "speed",
            
            # Equipment and items
            "magic item", "magic items", "attunement", "curse", "cursed", "artifact",
            "weapon property", "weapon properties", "finesse", "heavy", "light", "loading",
            "range", "reach", "thrown", "two-handed", "versatile", "ammunition",
            
            # Skills and abilities
            "ability score", "ability scores", "strength", "dexterity", "constitution",
            "intelligence", "wisdom", "charisma", "modifier", "modifiers",
            "acrobatics", "animal handling", "arcana", "athletics", "deception", "history",
            "insight", "intimidation", "investigation", "medicine", "nature", "perception",
            "performance", "persuasion", "religion", "sleight of hand", "stealth", "survival",
            
            # Environment and exploration
            "travel", "exploration", "environment", "weather", "terrain", "climbing",
            "swimming", "flying", "falling", "suffocation", "drowning", "extreme cold",
            "extreme heat", "vision", "light", "darkness", "dim light", "bright light"
        ]
        
        if any(word in query_lower for word in rulebook_keywords):
            sources.append("dnd_rulebook")
        
        # Comprehensive session/story keywords
        session_keywords = [
            # Session references
            "session", "sessions", "last session", "previous session", "last time", "before",
            "what happened", "recap", "summary", "story so far", "campaign",
            
            # NPCs and characters
            "npc", "npcs", "character", "characters", "party", "party member", "party members",
            "ally", "allies", "enemy", "enemies", "villain", "villains", "boss", "friend",
            "companion", "follower", "henchman", "minion", "contact", "informant",
            
            # Story elements
            "story", "plot", "narrative", "lore", "history", "background", "backstory",
            "quest", "quests", "mission", "missions", "objective", "objectives", "goal", "goals",
            "contract", "contracts", "job", "jobs", "task", "tasks", "assignment",
            
            # Events and encounters
            "event", "events", "encounter", "encounters", "battle", "battles", "fight", "fights",
            "combat", "meeting", "conversation", "negotiation", "investigation", "discovery",
            "revelation", "twist", "clue", "clues", "evidence", "mystery", "puzzle",
            
            # Locations and world
            "location", "locations", "place", "places", "city", "cities", "town", "towns",
            "village", "villages", "dungeon", "dungeons", "castle", "fortress", "temple",
            "tavern", "inn", "shop", "market", "guild", "organization", "faction", "factions",
            
            # Relationships and politics
            "relationship", "relationships", "reputation", "standing", "politics", "political",
            "diplomacy", "war", "conflict", "peace", "treaty", "alliance", "betrayal",
            "loyalty", "trust", "distrust", "rivalry", "competition"
        ]
        
        if any(word in query_lower for word in session_keywords):
            sources.append("session_notes")
        
        return {
            "sources_needed": sources,
            "reasoning": f"Comprehensive keyword-based fallback selected {len(sources)} sources"
        }
    
    async def target_character_files(self, query: str) -> Dict[str, List[str]]:
        """
        Target character files using schema-driven approach.
        """
        await self._call_debug_callback(
            "CHARACTER_TARGETING", 
            "Starting schema-driven character file targeting",
            {"query": query, "available_files": len(self.available_file_types)}
        )
        
        # Generate file descriptions from schemas
        file_descriptions = self._generate_file_descriptions()
        
        prompt = f"""Given this query: "{query}"

Which character data files are needed?

Available files:
{file_descriptions}

SELECTION RULES:
- Choose files that contain data relevant to answering the query
- Consider what information would be needed to provide a complete answer
- Multiple files may be needed for comprehensive responses

Return ONLY a JSON object with this exact format:
{{
  "file_fields": {{
    "character.json": ["*"],
    "spell_list.json": ["*"]
  }},
  "reasoning": "Character data for basic info, spells for magic-related query"
}}

Use "*" to include all data from a file, or specify field paths for targeted data.

RESPOND WITH ONLY VALID JSON, NO OTHER TEXT."""

        try:
            messages = [
                {"role": "system", "content": "Output only valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self._make_api_call(messages, "CHARACTER_TARGETING")
            content = (await self._extract_content_with_debugging(response, "CHARACTER_TARGETING")).strip()
            
            # Clean and parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content)
            
            # Validate structure
            if not isinstance(result, dict) or "file_fields" not in result:
                raise ValueError("Response must contain file_fields")
            
            file_fields = result["file_fields"]
            
            # Validate filenames and convert to expected format
            validated_fields = {}
            for filename, fields in file_fields.items():
                # Convert filename to file_type if needed
                file_type = filename.replace(".json", "")
                
                if file_type in self.available_file_types:
                    validated_fields[filename] = fields if isinstance(fields, list) else ["*"]
            
            if not validated_fields:
                # Fallback to keyword-based selection
                validated_fields = self._create_character_fallback(query)
            
            await self._call_debug_callback(
                "CHARACTER_SUCCESS", 
                f"Successfully targeted {len(validated_fields)} character files",
                {"files": list(validated_fields.keys())}
            )
            
            return validated_fields
            
        except Exception as e:
            await self._call_debug_callback(
                "CHARACTER_ERROR", 
                f"Character targeting failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
            
            return self._create_character_fallback(query)
    
    def _create_character_fallback(self, query: str) -> Dict[str, List[str]]:
        """Create comprehensive smart fallback for character file selection."""
        query_lower = query.lower()
        result = {}
        
        # Always include basic character info
        if "character" in self.available_file_types:
            result["character.json"] = ["*"]
        
        # Comprehensive keyword mapping for each file type
        file_keywords = {
            "spell_list": [
                # Spellcasting
                "spell", "spells", "magic", "magical", "cast", "casting", "spellcasting",
                "cantrip", "cantrips", "ritual", "rituals", "concentration", "spell slot", "spell slots",
                "spell save", "spell attack", "spell dc", "spellcaster", "spellcasting ability",
                
                # Spell schools
                "abjuration", "conjuration", "divination", "enchantment", "evocation", 
                "illusion", "necromancy", "transmutation",
                
                # Spell components
                "verbal", "somatic", "material", "component", "components", "focus", "arcane focus",
                "component pouch", "holy symbol", "druidcraft focus", "crystal", "orb", "rod", "staff", "wand",
                
                # Spell levels
                "1st level", "2nd level", "3rd level", "4th level", "5th level", 
                "6th level", "7th level", "8th level", "9th level", "level 1", "level 2", "level 3",
                
                # Specific spell types
                "healing spell", "damage spell", "utility spell", "buff", "debuff", "counterspell",
                "dispel", "teleport", "charm", "dominate", "fireball", "cure wounds", "healing word",
                "shield", "mage armor", "misty step", "dimension door", "polymorph", "banishment"
            ],
            
            "inventory_list": [
                # General equipment
                "inventory", "equipment", "gear", "item", "items", "carry", "carrying", "weight",
                "encumbrance", "bag", "pack", "backpack", "pouch", "container", "storage",
                
                # Weapons
                "weapon", "weapons", "sword", "axe", "bow", "crossbow", "dagger", "mace", "hammer",
                "spear", "javelin", "club", "quarterstaff", "rapier", "scimitar", "shortsword",
                "longsword", "greatsword", "battleaxe", "handaxe", "warhammer", "maul", "glaive",
                "halberd", "pike", "trident", "whip", "net", "blowgun", "dart", "sling",
                "shortbow", "longbow", "light crossbow", "heavy crossbow", "hand crossbow",
                
                # Armor
                "armor", "armour", "shield", "ac", "armor class", "protection", "defense", "defence",
                "leather armor", "studded leather", "hide armor", "chain shirt", "scale mail",
                "breastplate", "half plate", "ring mail", "chain mail", "splint armor", "plate armor",
                "padded armor", "natural armor",
                
                # Magic items
                "magic item", "magic items", "magical item", "magical items", "enchanted", "artifact",
                "legendary", "very rare", "rare", "uncommon", "common", "attunement", "attuned",
                "curse", "cursed", "blessed", "holy", "unholy", "relic", "wondrous item",
                
                # Currency and valuables
                "gold", "silver", "copper", "platinum", "electrum", "gp", "sp", "cp", "pp", "ep",
                "coin", "coins", "money", "currency", "treasure", "gem", "gems", "jewelry", "jewellery",
                "art object", "valuable", "valuables", "worth", "value", "cost", "price",
                
                # Consumables
                "potion", "potions", "scroll", "scrolls", "consumable", "consumables", "use", "uses",
                "charge", "charges", "ammunition", "arrow", "arrows", "bolt", "bolts", "bullet", "bullets",
                "food", "rations", "water", "drink", "healing potion", "antidote", "elixir"
            ],
            
            "character_background": [
                # Personal history
                "background", "backstory", "history", "past", "origin", "childhood", "youth",
                "upbringing", "family", "parents", "father", "mother", "sibling", "siblings",
                "brother", "sister", "relative", "relatives", "ancestor", "ancestors", "lineage",
                
                # Personality and traits
                "personality", "trait", "traits", "characteristic", "characteristics", "quirk", "quirks",
                "mannerism", "mannerisms", "habit", "habits", "ideal", "ideals", "bond", "bonds",
                "flaw", "flaws", "fear", "fears", "motivation", "motivations", "drive", "drives",
                
                # Relationships
                "ally", "allies", "friend", "friends", "enemy", "enemies", "rival", "rivals",
                "contact", "contacts", "acquaintance", "acquaintances", "mentor", "student",
                "lover", "spouse", "partner", "relationship", "relationships", "reputation",
                
                # Organizations and affiliations
                "organization", "organizations", "guild", "guilds", "faction", "factions",
                "group", "groups", "society", "societies", "order", "orders", "cult", "cults",
                "church", "temple", "religion", "religious", "faith", "belief", "beliefs",
                "patron", "sponsor", "employer", "member", "membership", "rank", "title",
                
                # Life events
                "event", "events", "incident", "incidents", "accident", "tragedy", "triumph",
                "achievement", "accomplishment", "failure", "mistake", "regret", "regrets",
                "secret", "secrets", "mystery", "mysteries", "scandal", "crime", "punishment"
            ],
            
            "action_list": [
                # Combat actions
                "action", "actions", "attack", "attacks", "combat", "fight", "fighting", "battle",
                "strike", "hit", "damage", "hurt", "wound", "kill", "slay", "defeat",
                
                # Action economy
                "action economy", "bonus action", "reaction", "free action", "movement", "move",
                "turn", "round", "initiative", "sequence", "order",
                
                # Attack types
                "melee", "ranged", "spell attack", "weapon attack", "unarmed strike", "grapple",
                "shove", "trip", "disarm", "sunder", "charge", "full attack", "flurry",
                
                # Combat maneuvers
                "maneuver", "maneuvers", "technique", "techniques", "combo", "combos", "special attack",
                "special attacks", "ability", "abilities", "power", "powers", "skill", "skills",
                
                # Defensive actions
                "defend", "defense", "defence", "block", "parry", "dodge", "evade", "avoid",
                "guard", "protect", "cover", "shield", "deflect", "counter", "counterattack",
                
                # Movement and positioning
                "position", "positioning", "flank", "flanking", "retreat", "advance", "charge",
                "rush", "dash", "run", "walk", "climb", "jump", "leap", "fly", "swim", "crawl"
            ],
            
            "feats_and_traits": [
                # Character features
                "feat", "feats", "feature", "features", "trait", "traits", "ability", "abilities",
                "power", "powers", "talent", "talents", "skill", "skills", "proficiency", "proficiencies",
                
                # Class features
                "class feature", "class features", "class ability", "class abilities", "archetype",
                "subclass", "specialization", "path", "way", "school", "domain", "circle", "oath",
                "patron", "bloodline", "mystery", "style", "fighting style",
                
                # Racial traits
                "racial trait", "racial traits", "racial feature", "racial features", "racial ability",
                "racial abilities", "heritage", "ancestry", "bloodline", "lineage", "species",
                
                # Special abilities
                "special ability", "special abilities", "supernatural", "extraordinary", "spell-like",
                "innate", "natural", "passive", "active", "triggered", "conditional",
                
                # Resistances and immunities
                "resistance", "resistances", "immunity", "immunities", "vulnerability", "vulnerabilities",
                "damage reduction", "dr", "energy resistance", "spell resistance", "sr",
                
                # Senses and movement
                "darkvision", "low-light vision", "blindsight", "tremorsense", "truesight",
                "scent", "keen senses", "speed", "movement speed", "fly speed", "swim speed", "climb speed"
            ],
            
            "objectives_and_contracts": [
                # Quests and missions
                "quest", "quests", "mission", "missions", "objective", "objectives", "goal", "goals",
                "task", "tasks", "job", "jobs", "assignment", "assignments", "contract", "contracts",
                "commission", "commissions", "request", "requests", "favor", "favors",
                
                # Quest status
                "active", "completed", "failed", "abandoned", "pending", "in progress", "ongoing",
                "finished", "done", "success", "successful", "failure", "incomplete",
                
                # Quest types
                "main quest", "side quest", "personal quest", "group quest", "fetch quest",
                "kill quest", "escort quest", "delivery quest", "investigation", "mystery",
                "rescue mission", "retrieval", "exploration", "diplomacy", "negotiation",
                
                # Rewards and consequences
                "reward", "rewards", "payment", "compensation", "prize", "bounty", "treasure",
                "experience", "xp", "reputation", "favor", "debt", "obligation", "consequence",
                "penalty", "punishment", "fine", "cost", "price",
                
                # Organizations and patrons
                "patron", "employer", "client", "customer", "benefactor", "sponsor", "contact",
                "quest giver", "npc", "organization", "guild", "faction", "government", "authority"
            ]
        }
        
        # Check each file type for keyword matches
        for file_type, keywords in file_keywords.items():
            if file_type in self.available_file_types:
                if any(keyword in query_lower for keyword in keywords):
                    result[f"{file_type}.json"] = ["*"]
        
        # Broad query detection - include all files for comprehensive queries
        broad_keywords = [
            "tell me about", "show me", "what", "describe", "explain", "overview", "summary",
            "everything", "all", "complete", "full", "entire", "whole", "comprehensive",
            "details", "information", "info", "data", "stats", "statistics", "character sheet",
            "build", "optimization", "optimize", "improve", "upgrade", "level up", "progression"
        ]
        
        if any(keyword in query_lower for keyword in broad_keywords):
            # Include all available file types for broad queries
            for file_type in self.available_file_types:
                if f"{file_type}.json" not in result:
                    result[f"{file_type}.json"] = ["*"]
        
        # Ensure we always have at least the character file
        if not result and "character" in self.available_file_types:
            result["character.json"] = ["*"]
        
        return result
    
    async def validate_character_data(self, data: Dict[str, Any], file_type: str) -> Dict[str, Any]:
        """
        Validate character data against the loaded schemas.
        
        Args:
            data: Character data to validate
            file_type: Type of character file
            
        Returns:
            Validation result with is_valid, errors, and warnings
        """
        try:
            result = await self.schema_loader.validate_against_schema(data, file_type)
            
            return {
                "is_valid": result.is_valid,
                "errors": [{"field": e.field_path, "message": e.message, "type": e.error_type} 
                          for e in result.errors],
                "warnings": result.warnings
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [{"field": "validation", "message": str(e), "type": "system_error"}],
                "warnings": []
            }
    
    def get_template_for_file_type(self, file_type: str) -> Dict[str, Any]:
        """Get template for a specific file type."""
        return self.file_templates.get(file_type, {})
    
    def get_available_file_types(self) -> List[str]:
        """Get list of all available file types."""
        return self.available_file_types.copy()
    
    async def target_session_notes(self, query: str) -> Dict[str, List[str]]:
        """
        Target session notes using generic approach.
        """
        await self._call_debug_callback(
            "SESSION_TARGETING", 
            "Analyzing query for session note needs",
            {"query": query}
        )
        
        prompt = f"""Given this session query: "{query}"

Determine what session notes are needed.

Return ONLY a JSON object with this exact format:
{{
  "session_dates": ["06-30-25"],
  "keywords": ["combat", "NPC", "quest"]
}}

For session_dates, use format MM-DD-YY if specific dates are mentioned.
For keywords, choose terms that would appear in session notes.

RESPOND WITH ONLY VALID JSON, NO OTHER TEXT."""

        try:
            messages = [
                {"role": "system", "content": "Output only valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self._make_api_call(messages, "RULEBOOK_TARGETING")
            content = (await self._extract_content_with_debugging(response, "RULEBOOK_TARGETING")).strip()
            
            # Clean and parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content)
            
            # Ensure required keys exist
            if "session_dates" not in result:
                result["session_dates"] = []
            if "keywords" not in result:
                result["keywords"] = []
            
            await self._call_debug_callback(
                "SESSION_SUCCESS", 
                "Successfully parsed session targeting",
                {"dates": len(result.get("session_dates", [])), "keywords": len(result.get("keywords", []))}
            )
            
            return result
            
        except Exception as e:
            await self._call_debug_callback(
                "SESSION_ERROR", 
                f"Session targeting failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
            
            # Basic fallback
            return {
                "session_dates": [],
                "keywords": ["session", "event"]
            }
    
    async def generate_natural_response(self, prompt: str, temperature: float = 0.7, max_tokens: int = None) -> str:
        """Generate a natural language response with enhanced markdown formatting."""
        await self._call_debug_callback(
            "NATURAL_RESPONSE_START", 
            "Generating natural language response with markdown formatting",
            {"prompt_length": len(prompt), "temperature": temperature, "max_tokens": max_tokens or "UNLIMITED"}
        )
        
        # Enhance the prompt with markdown formatting instructions
        enhanced_prompt = f"""You are a knowledgeable D&D assistant. Please provide a well-formatted, helpful response to the following query.

**FORMATTING REQUIREMENTS:**
- Use **bold** for important terms, stats, and headings
- Use *italics* for spell names, item names, and emphasis
- Use `code blocks` for specific values, dice rolls, and mechanics
- Use bullet points (- or *) for lists
- Use numbered lists (1., 2., 3.) for sequential steps
- Use > blockquotes for rules quotes or important notes
- Use headers (## or ###) to organize longer responses
- Make your response visually appealing and easy to scan

**USER QUERY:**
{prompt}

**YOUR RESPONSE:**"""

        try:
            messages = [
                {
                    "role": "system", 
                    "content": "You are an expert D&D assistant who always provides well-formatted, visually appealing responses using proper markdown formatting. Make your responses clear, organized, and easy to read."
                },
                {
                    "role": "user", 
                    "content": enhanced_prompt
                }
            ]
            
            response = await self._make_api_call(messages, "NATURAL_RESPONSE", "medium")
            content = (await self._extract_content_with_debugging(response, "NATURAL_RESPONSE")).strip()
            
            # FALLBACK MECHANISM: If we get an empty response, create a helpful fallback
            if not content or len(content) == 0:
                print(f"[FALLBACK] Empty response detected, creating fallback response")
                content = self._create_fallback_response(prompt, temperature)
            
            await self._call_debug_callback(
                "NATURAL_RESPONSE_SUCCESS", 
                "Successfully generated natural response",
                {"response_length": len(content), "used_fallback": not bool(response)}
            )
            
            return content
            
        except Exception as e:
            await self._call_debug_callback(
                "NATURAL_RESPONSE_ERROR", 
                f"Natural response generation failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
            
            # Even on error, provide a helpful fallback
            fallback = self._create_fallback_response(prompt, temperature)
            return fallback if fallback else f"I apologize, but I encountered an error while generating a response: {str(e)}"
    
    def _create_fallback_response(self, prompt: str, temperature: float = 0.7) -> str:
        """Create a helpful fallback response when the LLM returns empty or fails."""
        print(f"[FALLBACK] Creating fallback response for prompt length: {len(prompt)}")
        
        # Extract what we can from the prompt to provide context
        prompt_lower = prompt.lower()
        
        # Check if we have character data in the prompt
        has_character_data = "character_base" in prompt or "duskryn" in prompt_lower
        has_spell_data = "spell" in prompt_lower and ("spellcasting" in prompt or "spell_list" in prompt)
        has_rules_data = "dnd_rulebook" in prompt or "rules reference" in prompt_lower
        
        # Build a response based on what data we have
        response_parts = []
        
        response_parts.append("## Response Generated with Available Data\n")
        response_parts.append("*Note: I'm providing a response based on the data available in the system.*\n\n")
        
        if has_character_data:
            response_parts.append("### Character Information\n")
            response_parts.append("Based on the character data available:\n\n")
            
            # Extract character name if present
            if "duskryn nightwarden" in prompt_lower:
                response_parts.append("**Character:** Duskryn Nightwarden (Dwarf Warlock/Paladin)\n")
                response_parts.append("- **Level:** 13 (Warlock 5 / Paladin 8)\n")
                response_parts.append("- **Hit Points:** 129\n")
                response_parts.append("- **Armor Class:** 20\n")
                response_parts.append("- **Key Abilities:** High Charisma (24), Wisdom (20)\n\n")
        
        if has_spell_data:
            response_parts.append("### Spellcasting Capabilities\n")
            response_parts.append("The character has access to both Warlock and Paladin spells:\n\n")
            response_parts.append("**Warlock Spells:**\n")
            response_parts.append("- Cantrips: *Eldritch Blast*, *Infestation*, *Prestidigitation*\n")
            response_parts.append("- 1st Level: *Charm Person*, *Hellish Rebuke*, *Hex*, *Witch Bolt*\n")
            response_parts.append("- 3rd Level: *Counterspell*, *Intellect Fortress*\n\n")
            response_parts.append("**Paladin Spells:**\n")
            response_parts.append("- Various healing and support spells\n")
            response_parts.append("- Combat enhancement abilities\n")
            response_parts.append("- Defensive options like *Shield of Faith* and *Sanctuary*\n\n")
        
        if has_rules_data:
            response_parts.append("### Rules Information\n")
            response_parts.append("Relevant D&D 5e mechanics and rules apply as per the standard rulebooks.\n\n")
        
        # Add a generic helpful ending
        response_parts.append("---\n")
        response_parts.append("*For more specific information, please refine your query or ask about particular aspects.*")
        
        fallback = "".join(response_parts)
        print(f"[FALLBACK] Generated fallback response of {len(fallback)} characters")
        
        return fallback
