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
        self.character_files = {
            "character.json": "character.json",
            "inventory_list.json": "inventory_list.json", 
            "feats_and_traits.json": "feats_and_traits.json",
            "spell_list.json": "spell_list.json",
            "action_list.json": "action_list.json",
            "character_background.json": "character_background.json",
            "objectives_and_contracts.json": "objectives_and_contracts.json"
        }
        
        self.data: Dict[str, Any] = {}
        self._loaded = False
    
    def load_data(self):
        """Load all character data files."""
        self.data = {}
        loaded_files = 0
        
        for file_key, filename in self.character_files.items():
            file_path = os.path.join(self.base_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.data[file_key] = json.load(f)
                loaded_files += 1
            except Exception as e:
                print(f"Warning: Could not load {filename}: {str(e)}")
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
        
        if fields is None or "all" in fields:
            return file_data
        
        # Extract specific fields
        result = {}
        for field in fields:
            if field in file_data:
                # Direct field access
                result[field] = file_data[field]
            else:
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