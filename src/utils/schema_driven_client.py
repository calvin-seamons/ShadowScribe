"""
Schema-Driven LLM Client

This module provides a generic, schema-driven approach to targeting and validating
character data without hardcoded character-specific logic.
"""

import json
import os
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
        
        # Initialize the schema loader
        self.schema_loader = JSONSchemaLoader()
        
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
        if (self.model.startswith("gpt-5") or 
            self.model.startswith("o1") or 
            self.model.startswith("o3")):
            return {"max_completion_tokens": max_tokens}
        else:
            return {"max_tokens": max_tokens}
    
    def _get_temperature_params(self, desired_temperature: float = 0.1) -> Dict[str, float]:
        """Get the appropriate temperature parameter based on model support."""
        if (self.model.startswith("gpt-5") or
            self.model.startswith("o1") or
            self.model.startswith("o3")):
            return {}
        return {"temperature": desired_temperature}
    
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
                
                # Generate description based on template structure
                description = f"{filename} - "
                
                if isinstance(template, dict):
                    top_level_keys = list(template.keys())[:5]  # First 5 keys
                    description += f"Contains: {', '.join(top_level_keys)}"
                    if len(template) > 5:
                        description += f" and {len(template) - 5} more sections"
                else:
                    description += "Character data file"
                
                descriptions.append(description)
                
            except Exception as e:
                descriptions.append(f"{filename} - Character data file")
        
        return "\n".join(descriptions)
    
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
- Complex queries may need multiple sources

Return ONLY a JSON object with this exact format:
{{
  "sources_needed": ["character_data", "dnd_rulebook"],
  "reasoning": "Character data for stats, rulebook for spell mechanics"
}}

RESPOND WITH ONLY VALID JSON, NO OTHER TEXT."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                **self._get_temperature_params(0.1),
                **self._get_token_params(600)
            )
            
            content = response.choices[0].message.content.strip()
            
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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                **self._get_temperature_params(0.1),
                **self._get_token_params(800)
            )
            
            content = response.choices[0].message.content.strip()
            
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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                **self._get_temperature_params(0.1),
                **self._get_token_params(200)
            )
            
            content = response.choices[0].message.content.strip()
            
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
    
    async def generate_natural_response(self, prompt: str, temperature: float = 0.7, max_tokens: int = 3000) -> str:
        """Generate a natural language response."""
        await self._call_debug_callback(
            "NATURAL_RESPONSE_START", 
            "Generating natural language response",
            {"prompt_length": len(prompt), "temperature": temperature, "max_tokens": max_tokens}
        )
        
        try:
            token_params = self._get_token_params(max_tokens)
            temp_params = self._get_temperature_params(temperature)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **temp_params,
                **token_params
            )
            
            content = response.choices[0].message.content.strip()
            
            await self._call_debug_callback(
                "NATURAL_RESPONSE_SUCCESS", 
                "Successfully generated natural response",
                {"response_length": len(content)}
            )
            
            return content
            
        except Exception as e:
            await self._call_debug_callback(
                "NATURAL_RESPONSE_ERROR", 
                f"Natural response generation failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
            
            return f"I apologize, but I encountered an error while generating a response: {str(e)}"