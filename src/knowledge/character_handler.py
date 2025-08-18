"""
Character Handler - Manages character data access and processing.
"""

from typing import Dict, Any, List, Optional
import json
import os


class CharacterHandler:
    """
    Handles access to character data files:
    - character.json (basic stats and info)
    - inventory_list.json (equipment and items)
    - feats_and_traits.json (abilities and features)
    - spell_list.json (available spells)
    - action_list.json (combat actions)
    - character_background.json (backstory and roleplay)
    - objectives_and_contracts.json (quests, goals, and divine covenants)
    """
    
    def __init__(self, knowledge_base_path: str):
        """Initialize character handler with file paths."""
        self.base_path = knowledge_base_path
        self.characters_path = os.path.join(knowledge_base_path, "characters")
        self.current_character = None
        self.character_files = {
            "character.json": "character.json",
            "inventory_list.json": "inventory_list.json", 
            "feats_and_traits.json": "feats_and_traits.json",
            "spell_list.json": "spell_list.json",
            "action_list.json": "action_list.json",
            "character_background.json": "character_background.json",
            "objectives_and_contracts.json": "objectives_and_contracts.json"
        }
        
        # Field alias mapping - maps common field requests to actual field paths
        self.field_aliases = {
            # Character basic info aliases
            "level": ["character_base.total_level", "total_level"],
            "lvl": ["character_base.total_level", "total_level"],
            "character_level": ["character_base.total_level", "total_level"],
            "name": ["character_base.name"],
            "character_name": ["character_base.name"],
            "class": ["character_base.class"],
            "character_class": ["character_base.class"],
            "race": ["character_base.race"],
            "subrace": ["character_base.subrace"],
            "alignment": ["character_base.alignment", "characteristics.alignment"],
            "experience": ["character_base.experience_points"],
            "exp": ["character_base.experience_points"],
            "xp": ["character_base.experience_points"],
            "background": ["character_base.background"],
            "lifestyle": ["character_base.lifestyle"],
            
            # Multi-class specific aliases
            "warlock_level": ["character_base.warlock_level"],
            "paladin_level": ["character_base.paladin_level"],
            "hit_dice": ["character_base.hit_dice"],
            
            # Ability scores aliases
            "str": ["ability_scores.strength"],
            "dex": ["ability_scores.dexterity"],
            "con": ["ability_scores.constitution"],
            "int": ["ability_scores.intelligence"],
            "wis": ["ability_scores.wisdom"],
            "cha": ["ability_scores.charisma"],
            "strength": ["ability_scores.strength"],
            "dexterity": ["ability_scores.dexterity"],
            "constitution": ["ability_scores.constitution"],
            "intelligence": ["ability_scores.intelligence"],
            "wisdom": ["ability_scores.wisdom"],
            "charisma": ["ability_scores.charisma"],
            
            # Combat stats aliases
            "hp": ["combat_stats.max_hp"],
            "health": ["combat_stats.max_hp"],
            "hit_points": ["combat_stats.max_hp"],
            "max_hp": ["combat_stats.max_hp"],
            "ac": ["combat_stats.armor_class"],
            "armor_class": ["combat_stats.armor_class"],
            "speed": ["combat_stats.speed"],
            "initiative": ["combat_stats.initiative_bonus"],
            "temporary_hp": ["combat_stats.temp_hp"],
            "inspiration": ["combat_stats.inspiration"],
            
            # Spell-related aliases
            "spells": ["spellcasting"],
            "character_spells": ["spellcasting"],
            "spell_list": ["spellcasting"],
            "magic": ["spellcasting"],
            "spellcasting": ["spellcasting"],
            "cantrips": ["spellcasting.paladin.spells.cantrips", "spellcasting.warlock.spells.cantrips"],
            "paladin_spells": ["spellcasting.paladin"],
            "warlock_spells": ["spellcasting.warlock"],
            
            # Equipment aliases
            "equipment": ["inventory"],
            "gear": ["inventory"],
            "items": ["inventory"],
            "inventory": ["inventory"],
            "weapons": ["inventory.equipped_items.weapons"],
            "armor": ["inventory.equipped_items.armor"],
            "equipped": ["inventory.equipped_items"],
            "equipped_items": ["inventory.equipped_items"],
            "weight": ["inventory.total_weight"],
            "total_weight": ["inventory.total_weight"],
            
            # Actions and combat aliases
            "actions": ["character_actions"],
            "combat_actions": ["character_actions"],
            "attacks": ["character_actions.action_economy.actions"],
            "attack": ["character_actions.action_economy.actions"],
            "attacks_per_action": ["character_actions.attacks_per_action"],
            "action_economy": ["character_actions.action_economy"],
            
            # Features and traits aliases
            "features": ["features_and_traits"],
            "traits": ["features_and_traits"],
            "abilities": ["features_and_traits"],
            "class_features": ["features_and_traits.class_features"],
            "racial_traits": ["features_and_traits.racial_traits"],
            "feats": ["features_and_traits.feats"],
            "paladin_features": ["features_and_traits.class_features.paladin"],
            "warlock_features": ["features_and_traits.class_features.warlock"],
            
            # Background and personality aliases
            "personality": ["characteristics"],
            "ideals": ["characteristics.ideals"],
            "bonds": ["characteristics.bonds"],
            "flaws": ["characteristics.flaws"],
            "personality_traits": ["characteristics.personality_traits"],
            "faith": ["characteristics.faith"],
            
            # Backstory and family aliases
            "backstory": ["backstory"],
            "family_backstory": ["backstory.family_backstory"],
            "parents": ["backstory.family_backstory.parents"],
            "family": ["backstory.family_backstory"],
            "family_history": ["backstory.family_backstory"],
            "father": ["backstory.family_backstory.parents"],
            "mother": ["backstory.family_backstory.parents"],
            "thaldrin": ["backstory.family_backstory.parents"],
            "brenna": ["backstory.family_backstory.parents"],
            "organizations": ["organizations"],
            "allies": ["allies"],
            "enemies": ["enemies"],
            "character_background": ["background", "backstory", "characteristics"],
            
            # Physical characteristics aliases
            "age": ["characteristics.age"],
            "height": ["characteristics.height"],
            "size": ["characteristics.size"],
            "eyes": ["characteristics.eyes"],
            "hair": ["characteristics.hair"],
            "skin": ["characteristics.skin"],
            "gender": ["characteristics.gender"],
            
            # Objectives and contracts aliases
            "objectives": ["objectives_and_contracts"],
            "contracts": ["objectives_and_contracts"],
            "quests": ["objectives_and_contracts"],
            "active_objectives": ["objectives_and_contracts.active_contracts", "objectives_and_contracts.current_objectives"],
            "completed_objectives": ["objectives_and_contracts.completed_objectives"],
            "covenant": ["objectives_and_contracts.completed_objectives"],
            "active_contracts": ["objectives_and_contracts.active_contracts"],
            "current_objectives": ["objectives_and_contracts.current_objectives"],
        }
        
        self.data: Dict[str, Any] = {}
        self._loaded = False
    
    def _get_default_character(self) -> str:
        """Get the default character to load."""
        if not os.path.exists(self.characters_path):
            return None
            
        # Get all character directories
        characters = []
        for item in os.listdir(self.characters_path):
            char_path = os.path.join(self.characters_path, item)
            if os.path.isdir(char_path):
                characters.append(item)
        
        # Return the first character found, or None if no characters exist
        return characters[0] if characters else None
    
    def load_data(self):
        """Load all character data files."""
        self.data = {}
        loaded_files = 0
        
        # If no current character is set, try to find a default one
        if not self.current_character:
            self.current_character = self._get_default_character()
        
        if not self.current_character:
            print("Warning: No character found in characters directory")
            self._loaded = False
            return
        
        # Load files from the character's directory
        character_dir = os.path.join(self.characters_path, self.current_character)
        
        for file_key, filename in self.character_files.items():
            file_path = os.path.join(character_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.data[file_key] = json.load(f)
                loaded_files += 1
            except Exception as e:
                print(f"Warning: Could not load {filename} for character {self.current_character}: {str(e)}")
                self.data[file_key] = {}
        
        self._loaded = loaded_files > 0
    
    def is_loaded(self) -> bool:
        """Check if character data is loaded."""
        return self._loaded and len(self.data) > 0
    
    def get_available_files(self) -> List[str]:
        """Get list of available character data files."""
        return list(self.character_files.keys())
    
    def get_character_name(self) -> str:
        """Get the character's name."""
        if not self.is_loaded():
            return "Unknown"
        
        character_data = self.data.get("character.json", {})
        return character_data.get("character_base", {}).get("name", "Unknown Character")
    
    def get_current_character_folder(self) -> str:
        """Get the current character folder name."""
        return self.current_character or "Unknown"
    
    def _find_field_in_nested_dict(self, data: Dict[str, Any], field_name: str, current_path: str = "") -> List[tuple]:
        """
        Recursively search for a field name in nested dictionaries.
        
        Args:
            data: Dictionary to search in
            field_name: Name of the field to find
            current_path: Current path in the nested structure
            
        Returns:
            List of tuples containing (full_path, value) for each match
        """
        matches = []
        
        if not isinstance(data, dict):
            return matches
            
        for key, value in data.items():
            current_key_path = f"{current_path}.{key}" if current_path else key
            
            # Check if this key matches what we're looking for
            if key.lower() == field_name.lower():
                matches.append((current_key_path, value))
            
            # Recursively search in nested dictionaries
            if isinstance(value, dict):
                nested_matches = self._find_field_in_nested_dict(value, field_name, current_key_path)
                matches.extend(nested_matches)
        
        return matches

    def _resolve_field_alias(self, field_name: str) -> List[str]:
        """
        Resolve field aliases to actual field paths.
        
        Args:
            field_name: The field name to resolve
            
        Returns:
            List of potential field paths to try
        """
        field_lower = field_name.lower()
        if field_lower in self.field_aliases:
            return self.field_aliases[field_lower]
        return [field_name]  # Return original if no alias found

    def get_file_data(self, filename: str, fields: List[str] = None) -> Dict[str, Any]:
        """
        Get data from a specific character file.
        
        Args:
            filename: Name of the file to retrieve data from
            fields: Specific fields to retrieve (None for all, supports dot notation for nested fields)
            
        Returns:
            Dictionary containing the requested data
        """
        if not self.is_loaded() or filename not in self.data:
            return {}
        
        file_data = self.data[filename]
        
        if fields is None or "all" in fields or "*" in fields:
            return file_data
        
        # Extract specific fields
        result = {}
        for field in fields:
            if field in file_data:
                # Direct field access
                result[field] = file_data[field]
            elif '.' in field:
                # Try nested field access (e.g., "character_base.name" or "objectives_and_contracts.active_contracts")
                current = file_data
                field_parts = field.split('.')
                try:
                    for part in field_parts:
                        current = current[part]
                    # Store with the full path as key for clarity
                    result[field] = current
                except (KeyError, TypeError):
                    # Field not found, try to be helpful and log what's available
                    if len(field_parts) > 1:
                        # For nested paths, check if the parent exists
                        try:
                            parent = file_data
                            for part in field_parts[:-1]:
                                parent = parent[part]
                            if isinstance(parent, dict):
                                available_keys = list(parent.keys())
                                print(f"Debug: Field '{field}' not found in {filename}. Available keys in '{'.'.join(field_parts[:-1])}': {available_keys}")
                        except (KeyError, TypeError):
                            print(f"Debug: Parent path '{'.'.join(field_parts[:-1])}' not found in {filename}")
                    else:
                        if isinstance(file_data, dict):
                            available_keys = list(file_data.keys())
                            print(f"Debug: Field '{field}' not found in {filename}. Available root keys: {available_keys}")
                    continue
            else:
                # Search for the field at any level in the nested structure
                matches = self._find_field_in_nested_dict(file_data, field)
                
                if matches:
                    # If we found multiple matches, include all of them
                    if len(matches) == 1:
                        # Single match - use the field name as key for backwards compatibility
                        result[field] = matches[0][1]
                        print(f"Debug: Found '{field}' at path '{matches[0][0]}' in {filename}")
                    else:
                        # Multiple matches - include all with their paths
                        for path, value in matches:
                            result[path] = value
                        print(f"Debug: Found multiple matches for '{field}' in {filename}: {[path for path, _ in matches]}")
                else:
                    # Field not found anywhere - try alias fallback
                    potential_paths = self._resolve_field_alias(field)
                    alias_found = False
                    
                    for alias_path in potential_paths:
                        if alias_path != field:  # Don't retry the same field name
                            if '.' in alias_path:
                                # Try nested field access for alias
                                current = file_data
                                field_parts = alias_path.split('.')
                                try:
                                    for part in field_parts:
                                        current = current[part]
                                    result[field] = current  # Use original field name as key
                                    print(f"Debug: Found '{field}' via alias '{alias_path}' in {filename}")
                                    alias_found = True
                                    break
                                except (KeyError, TypeError):
                                    continue
                            else:
                                # Try direct access for alias
                                if alias_path in file_data:
                                    result[field] = file_data[alias_path]
                                    print(f"Debug: Found '{field}' via alias '{alias_path}' in {filename}")
                                    alias_found = True
                                    break
                    
                    if not alias_found:
                        # Still not found anywhere - provide helpful debug info
                        if isinstance(file_data, dict):
                            available_keys = list(file_data.keys())
                            potential_aliases = self._resolve_field_alias(field)
                            if len(potential_aliases) > 1:
                                print(f"Debug: Field '{field}' not found anywhere in {filename}. Tried aliases: {potential_aliases}. Available root keys: {available_keys}")
                            else:
                                print(f"Debug: Field '{field}' not found anywhere in {filename}. Available root keys: {available_keys}")
                        continue
        
        return result
    
    def get_basic_info(self) -> Dict[str, Any]:
        """Get essential character information."""
        if not self.is_loaded():
            return {}
        
        character_data = self.data.get("character.json", {})
        character_base = character_data.get("character_base", {})
        characteristics = character_data.get("characteristics", {})
        ability_scores = character_data.get("ability_scores", {})
        combat_stats = character_data.get("combat_stats", {})
        
        return {
            "name": character_base.get("name", "Unknown"),
            "race": character_base.get("race", "Unknown"),
            "subrace": character_base.get("subrace", ""),
            "class": character_base.get("class", "Unknown"),
            "level": character_base.get("total_level", 1),
            "alignment": character_base.get("alignment", "Unknown"),
            "ability_scores": ability_scores,
            "max_hp": combat_stats.get("max_hp", 0),
            "current_hp": combat_stats.get("current_hp", 0),
            "armor_class": combat_stats.get("armor_class", 10),
            "speed": combat_stats.get("speed", 30)
        }
    
    def get_combat_info(self) -> Dict[str, Any]:
        """Get character's combat-related information."""
        if not self.is_loaded():
            return {}
        
        # Combine relevant combat data from multiple files
        character_data = self.data.get("character.json", {})
        action_data = self.data.get("action_list.json", {})
        inventory_data = self.data.get("inventory_list.json", {})
        
        combat_stats = character_data.get("combat_stats", {})
        character_actions = action_data.get("character_actions", {})
        equipped_items = inventory_data.get("inventory", {}).get("equipped_items", {})
        
        return {
            "combat_stats": combat_stats,
            "actions": character_actions.get("action_economy", {}),
            "equipped_weapons": equipped_items.get("weapons", []),
            "equipped_armor": equipped_items.get("armor", []),
            "attacks_per_action": character_actions.get("attacks_per_action", 1)
        }
    
    def get_spells(self, spell_class: str = None) -> Dict[str, Any]:
        """
        Get character's available spells.
        
        Args:
            spell_class: Specific class to get spells for (e.g., "paladin", "warlock")
            
        Returns:
            Dictionary of spells organized by class and level
        """
        if not self.is_loaded():
            return {}
        
        spell_data = self.data.get("spell_list.json", {})
        spellcasting = spell_data.get("spellcasting", {})
        
        if spell_class:
            return spellcasting.get(spell_class, {})
        
        return spellcasting
    
    def get_equipment(self, equipment_type: str = None) -> Dict[str, Any]:
        """
        Get character's equipment.
        
        Args:
            equipment_type: Specific type (e.g., "weapons", "armor", "consumables")
            
        Returns:
            Dictionary of equipment
        """
        if not self.is_loaded():
            return {}
        
        inventory_data = self.data.get("inventory_list.json", {})
        inventory = inventory_data.get("inventory", {})
        
        if equipment_type:
            if equipment_type == "equipped":
                return inventory.get("equipped_items", {})
            else:
                return inventory.get(equipment_type, {})
        
        return inventory
    
    def get_abilities_and_features(self) -> Dict[str, Any]:
        """Get character's racial traits, class features, and feats."""
        if not self.is_loaded():
            return {}
        
        return self.data.get("feats_and_traits.json", {})
    
    def get_background_info(self) -> Dict[str, Any]:
        """Get character's background, personality, and roleplay information."""
        if not self.is_loaded():
            return {}
        
        return self.data.get("character_background.json", {})
    
    def get_spell_save_dc(self, spell_class: str) -> int:
        """Get spell save DC for a specific class."""
        abilities_data = self.get_abilities_and_features()
        class_features = abilities_data.get("features_and_traits", {}).get("class_features", {})
        
        class_data = class_features.get(spell_class, {})
        for feature in class_data.get("features", []):
            if feature.get("name") == "Spellcasting":
                return feature.get("spell_save_dc", 10)
        
        return 10  # Default
    
    def get_spell_attack_bonus(self, spell_class: str) -> int:
        """Get spell attack bonus for a specific class."""
        abilities_data = self.get_abilities_and_features()
        class_features = abilities_data.get("features_and_traits", {}).get("class_features", {})
        
        class_data = class_features.get(spell_class, {})
        for feature in class_data.get("features", []):
            if feature.get("name") == "Spellcasting":
                return feature.get("spell_attack_bonus", 0)
        
        return 0  # Default
    
    def get_proficiency_bonus(self) -> int:
        """Get character's proficiency bonus based on level."""
        basic_info = self.get_basic_info()
        level = basic_info.get("level", 1)
        
        # D&D 5e proficiency bonus calculation
        return 2 + ((level - 1) // 4)
    
    def get_objectives_and_contracts(self) -> Dict[str, Any]:
        """Get character's objectives and contracts."""
        if not self.is_loaded():
            self.load_data()
        
        return self.data.get("objectives_and_contracts.json", {})
    
    def get_active_objectives(self) -> List[Dict[str, Any]]:
        """Get currently active objectives and contracts."""
        objectives_data = self.get_objectives_and_contracts()
        objectives_section = objectives_data.get("objectives_and_contracts", {})
        
        active = []
        active.extend(objectives_section.get("active_contracts", []))
        active.extend(objectives_section.get("current_objectives", []))
        
        return active
    
    def get_completed_objectives(self) -> List[Dict[str, Any]]:
        """Get completed objectives and contracts."""
        objectives_data = self.get_objectives_and_contracts()
        objectives_section = objectives_data.get("objectives_and_contracts", {})
        
        return objectives_section.get("completed_objectives", [])
    
    def get_covenant_details(self) -> Dict[str, Any]:
        """Get details about the covenant with Ghul'Vor."""
        completed = self.get_completed_objectives()
        
        for objective in completed:
            if objective.get("id") == "covenant_eternal_service":
                return objective
        
        return {}
    
    def validate(self) -> Dict[str, Any]:
        """Validate the integrity of character data."""
        validation_result = {
            "status": "success" if self.is_loaded() else "error",
            "files_loaded": {},
            "data_integrity": {}
        }
        
        # Check which files are loaded
        for file_key in self.character_files:
            validation_result["files_loaded"][file_key] = file_key in self.data and bool(self.data[file_key])
        
        if self.is_loaded():
            # Basic data integrity checks
            basic_info = self.get_basic_info()
            validation_result["data_integrity"] = {
                "has_character_name": bool(basic_info.get("name")) and basic_info.get("name") != "Unknown",
                "has_class_info": bool(basic_info.get("class")) and basic_info.get("class") != "Unknown",
                "has_ability_scores": bool(basic_info.get("ability_scores")),
                "has_combat_stats": bool(basic_info.get("max_hp", 0) > 0),
                "character_level": basic_info.get("level", 0)
            }
        
        return validation_result