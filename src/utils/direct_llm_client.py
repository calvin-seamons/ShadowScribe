"""
Direct LLM client that bypasses function calling for more reliable responses.
"""

import json
import os
from typing import Dict, List, Optional, Callable, Any
from openai import AsyncOpenAI
from .response_models import DirectCharacterTargeting


class DirectLLMClient:
    """LLM client that uses direct JSON parsing instead of function calling."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.debug_callback: Optional[Callable] = None
    
    def set_debug_callback(self, callback: Callable):
        """Set debug callback for progress tracking."""
        self.debug_callback = callback
    
    async def _call_debug_callback(self, stage: str, message: str, data: Dict[str, Any] = None):
        """Call debug callback if set."""
        if self.debug_callback:
            try:
                # Check if callback is a coroutine function
                import inspect
                if inspect.iscoroutinefunction(self.debug_callback):
                    await self.debug_callback(stage, message, data or {})
                else:
                    # Handle sync callbacks
                    self.debug_callback(stage, message, data or {})
            except Exception as e:
                # Don't let debug callback errors break the main flow
                print(f"Debug callback error: {e}")
    
    async def select_sources(self, query: str) -> Dict[str, Any]:
        """
        Select knowledge sources using direct JSON parsing.
        Returns dict with 'sources_needed' list and 'reasoning' string.
        """
        
        await self._call_debug_callback(
            "SOURCE_SELECTION", 
            "Analyzing query for knowledge source needs",
            {"query": query}
        )
        
        prompt = f"""Given this D&D query: "{query}"

Determine which knowledge sources are needed to answer this query.

Available sources:
1. dnd_rulebook - D&D 5e rules, spells, classes, mechanics
2. character_data - Character stats, equipment, backstory for Duskryn Nightwarden
3. session_notes - Campaign events, NPCs, story progression

Selection guidelines:
- For rule questions (spells, combat, mechanics) → include "dnd_rulebook"
- For character questions (stats, backstory, equipment) → include "character_data"  
- For story/campaign questions (NPCs, events, party) → include "session_notes"
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
                temperature=0.1,
                max_tokens=300
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
            
            # Smart fallback based on keywords
            return self._create_source_fallback(query)
    
    def _create_source_fallback(self, query: str) -> Dict[str, Any]:
        """Create smart fallback for source selection."""
        query_lower = query.lower()
        sources = ["character_data"]  # Always include character data as base
        
        # Add rulebook for rule-related queries
        if any(word in query_lower for word in 
               ["rule", "spell", "how does", "can i", "what is", "mechanic", "damage", "attack", "save"]):
            sources.append("dnd_rulebook")
        
        # Add session notes for story queries
        if any(word in query_lower for word in 
               ["session", "story", "npc", "quest", "party", "campaign", "last time", "what happened"]):
            sources.append("session_notes")
        
        return {
            "sources_needed": sources,
            "reasoning": f"Keyword-based fallback selected {len(sources)} sources"
        }

    async def target_character_files(self, query: str) -> Dict[str, List[str]]:
        """
        Target character files using a two-step process:
        1. Select which files are needed
        2. For each file, select specific fields based on actual structure
        """
        
        await self._call_debug_callback(
            "CHARACTER_TARGETING", 
            "Starting two-step character file targeting",
            {"query": query}
        )
        
        # Step 1: Select which files are needed
        selected_files = await self._select_character_files(query)
        
        await self._call_debug_callback(
            "FILES_SELECTED", 
            f"Selected {len(selected_files)} files for detailed targeting",
            {"files": selected_files}
        )
        
        # Step 2: For each selected file, determine specific fields needed
        result = {}
        for filename in selected_files:
            try:
                fields = await self._select_fields_for_file(query, filename)
                if fields:
                    result[filename] = fields
                    
                await self._call_debug_callback(
                    "FIELDS_SELECTED", 
                    f"Selected {len(fields)} fields from {filename}",
                    {"file": filename, "fields": fields}
                )
                    
            except Exception as e:
                await self._call_debug_callback(
                    "FIELD_SELECTION_ERROR", 
                    f"Failed to select fields for {filename}: {str(e)}",
                    {"file": filename, "error": str(e)}
                )
                # Use fallback - include the whole file
                result[filename] = ["*"]
        
        if not result:
            # Fallback to keyword-based selection
            result = DirectCharacterTargeting.create_keyword_fallback(query)
            
        await self._call_debug_callback(
            "CHARACTER_TARGETING_COMPLETE", 
            f"Character targeting complete: {len(result)} files with specific fields",
            {"final_result": {k: len(v) for k, v in result.items()}}
        )
        
        return result
    
    async def _select_character_files(self, query: str) -> List[str]:
        """
        Step 1: Select which character files are needed for the query.
        """
        prompt = f"""Given this D&D character query: "{query}"

Which character data files are needed for Duskryn Nightwarden?

Available files:
1. character.json - Basic stats, abilities, combat stats, proficiencies, class/race info
2. character_background.json - Backstory, family history, personality, allies, enemies  
3. inventory_list.json - All equipment, weapons, armor, items
4. spell_list.json - All known spells organized by class and level
5. action_list.json - Combat actions, attacks, special abilities
6. feats_and_traits.json - Class features, racial traits, feats
7. objectives_and_contracts.json - Active quests, contracts, divine covenants

SELECTION RULES:
- For spell queries → spell_list.json
- For equipment/inventory queries → inventory_list.json  
- For backstory/family queries → character_background.json
- For combat/stats queries → character.json + action_list.json
- For abilities/features queries → feats_and_traits.json
- For quest/objective queries → objectives_and_contracts.json

Return ONLY a JSON array of filenames:
["spell_list.json", "character.json"]

RESPOND WITH ONLY VALID JSON ARRAY, NO OTHER TEXT."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Output only a JSON array of filenames."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean and parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            files = json.loads(content)
            
            # Validate it's a list of strings
            if not isinstance(files, list):
                raise ValueError("Expected a list of filenames")
            
            # Filter to valid filenames
            valid_files = [
                "character.json", "character_background.json", "inventory_list.json", 
                "spell_list.json", "action_list.json", "feats_and_traits.json", 
                "objectives_and_contracts.json"
            ]
            
            selected = [f for f in files if f in valid_files]
            
            if not selected:
                # Fallback based on keywords
                query_lower = query.lower()
                if any(word in query_lower for word in ["spell", "magic", "cast"]):
                    selected = ["spell_list.json"]
                elif any(word in query_lower for word in ["backstory", "family", "background"]):
                    selected = ["character_background.json"]
                else:
                    selected = ["character.json"]
            
            return selected
            
        except Exception as e:
            # Keyword-based fallback
            query_lower = query.lower()
            if any(word in query_lower for word in ["spell", "magic", "cast"]):
                return ["spell_list.json"]
            elif any(word in query_lower for word in ["backstory", "family", "background"]):
                return ["character_background.json"]
            elif any(word in query_lower for word in ["inventory", "equipment", "weapon"]):
                return ["inventory_list.json"]
            else:
                return ["character.json"]
    
    async def _select_fields_for_file(self, query: str, filename: str) -> List[str]:
        """
        Step 2: For a specific file, determine which fields are needed based on actual file structure.
        """
        # Get the actual file structure
        file_structure = await self._get_file_structure(filename)
        
        if not file_structure:
            return ["*"]  # Fallback to whole file
        
        prompt = f"""Given this D&D query: "{query}"

Here is the actual structure of {filename}:
{json.dumps(file_structure, indent=2)}

Which specific fields from this file are needed to answer the query?

IMPORTANT RULES:
- Choose specific field paths, NOT wildcards like "*"
- Use dot notation for nested fields: "spellcasting.paladin.spells"
- Only select fields that directly answer the query
- For spell queries, focus on spell-related fields
- For character info, focus on relevant character fields

Examples:
- For spell queries from spell_list.json: ["spellcasting.paladin.spells", "spellcasting.warlock.spells"]
- For character stats: ["character_base", "ability_scores", "combat_stats"]
- For backstory: ["backstory.family_backstory.parents"]

Return ONLY a JSON array of specific field paths:
["spellcasting.paladin.spells", "spellcasting.warlock.spells"]

RESPOND WITH ONLY VALID JSON ARRAY, NO OTHER TEXT."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Output only a JSON array of field paths."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean and parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            fields = json.loads(content)
            
            # Validate it's a list
            if not isinstance(fields, list):
                return ["*"]
            
            return fields if fields else ["*"]
            
        except Exception as e:
            await self._call_debug_callback(
                "FIELD_SELECTION_FALLBACK", 
                f"Field selection failed for {filename}, using smart fallback",
                {"error": str(e)}
            )
            
            # Smart fallback based on filename and query
            return self._get_fallback_fields(filename, query)
    
    async def _get_file_structure(self, filename: str) -> Dict[str, Any]:
        """Get the actual structure of a character file."""
        try:
            # Import the character handler to get file structure
            from ..knowledge.character_handler import CharacterHandler
            
            # Create a temporary handler instance
            handler = CharacterHandler("/Users/calvinseamons/ShadowScribe/knowledge_base")
            
            # Load and initialize the handler
            handler.load_data()
            
            # Get the data from the loaded files
            if filename in handler.data:
                data = handler.data[filename]
            else:
                return {}
            
            if not data:
                return {}
            
            # Return the structure (keys and nested structure, not values)
            return self._extract_structure(data)
            
        except Exception as e:
            await self._call_debug_callback(
                "STRUCTURE_ERROR", 
                f"Failed to get structure for {filename}: {str(e)}",
                {"file": filename, "error": str(e)}
            )
            return {}
    
    def _extract_structure(self, data: Any, max_depth: int = 3, current_depth: int = 0) -> Any:
        """Extract the structure of nested data, showing keys but not values."""
        if current_depth >= max_depth:
            return "..."
        
        if isinstance(data, dict):
            structure = {}
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    structure[key] = self._extract_structure(value, max_depth, current_depth + 1)
                else:
                    structure[key] = f"<{type(value).__name__}>"
            return structure
        elif isinstance(data, list) and data:
            # Show structure of first item in list
            return [self._extract_structure(data[0], max_depth, current_depth + 1)]
        else:
            return f"<{type(data).__name__}>"
    
    def _get_fallback_fields(self, filename: str, query: str) -> List[str]:
        """Get smart fallback fields based on filename and query keywords."""
        query_lower = query.lower()
        
        if filename == "spell_list.json":
            return ["spellcasting.paladin.spells", "spellcasting.warlock.spells"]
        elif filename == "character_background.json":
            if any(word in query_lower for word in ["family", "parent", "thaldrin", "brenna"]):
                return ["backstory.family_backstory", "backstory.family_backstory.parents"]
            else:
                return ["backstory", "personality", "characteristics"]
        elif filename == "inventory_list.json":
            return ["inventory"]
        elif filename == "action_list.json":
            return ["character_actions"]
        elif filename == "feats_and_traits.json":
            return ["features_and_traits"]
        elif filename == "objectives_and_contracts.json":
            return ["objectives_and_contracts"]
        else:  # character.json
            return ["character_base", "combat_stats"]
    
    async def target_rulebook_content(self, query: str) -> Dict[str, List[str]]:
        """
        Target D&D rulebook content using direct JSON parsing.
        Returns dict with 'section_ids' and 'keywords' lists.
        """
        
        await self._call_debug_callback(
            "RULEBOOK_TARGETING", 
            "Analyzing query for rulebook content needs",
            {"query": query}
        )
        
        prompt = f"""Given this D&D query: "{query}"

Determine what D&D 5e rulebook content is needed.

Return ONLY a JSON object with this exact format:
{{
  "section_ids": ["combat", "spellcasting"],
  "keywords": ["attack roll", "spell slot"]
}}

Choose relevant section_ids from: combat, spellcasting, classes, races, equipment, conditions, exploration, social
Choose specific keywords that would appear in relevant rules.

RESPOND WITH ONLY VALID JSON, NO OTHER TEXT."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
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
            if "section_ids" not in result:
                result["section_ids"] = []
            if "keywords" not in result:
                result["keywords"] = []
            
            await self._call_debug_callback(
                "RULEBOOK_SUCCESS", 
                "Successfully parsed rulebook targeting",
                {"sections": len(result.get("section_ids", [])), "keywords": len(result.get("keywords", []))}
            )
            
            return result
            
        except Exception as e:
            await self._call_debug_callback(
                "RULEBOOK_ERROR", 
                f"Rulebook targeting failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
            
            # Basic fallback
            return {
                "section_ids": ["combat", "spellcasting"],
                "keywords": ["rule", "mechanic"]
            }
    
    async def target_session_notes(self, query: str) -> Dict[str, List[str]]:
        """
        Target session notes using direct JSON parsing.
        Returns dict with 'session_dates' and 'keywords' lists.
        """
        
        await self._call_debug_callback(
            "SESSION_TARGETING", 
            "Analyzing query for session note needs",
            {"query": query}
        )
        
        prompt = f"""Given this D&D session query: "{query}"

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
                temperature=0.1,
                max_tokens=200
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
    
    async def generate_natural_response(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1500) -> str:
        """
        Generate a natural language response using the direct client.
        This method is for final response generation, not structured parsing.
        """
        await self._call_debug_callback(
            "NATURAL_RESPONSE_START", 
            "Generating natural language response",
            {"prompt_length": len(prompt), "temperature": temperature, "max_tokens": max_tokens}
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
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
            
            # Return a basic error response
            return f"I apologize, but I encountered an error while generating a response: {str(e)}"
