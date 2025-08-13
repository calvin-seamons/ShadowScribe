"""
Intelligent Character Data Mapper

This module provides intelligent mapping and validation of character data
extracted from PDFs, ensuring proper categorization and mechanical accuracy.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from pathlib import Path
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of data validation with confidence and suggestions."""
    is_valid: bool
    confidence: float
    suggestions: List[str]
    errors: List[str]
    corrected_value: Any = None


@dataclass
class MappingResult:
    """Result of intelligent data mapping."""
    mapped_data: Dict[str, Any]
    validation_results: Dict[str, ValidationResult]
    uncertain_fields: List[str]
    overall_confidence: float


class IntelligentDataMapper:
    """
    Intelligent mapper for character data extracted from PDFs.
    Handles spell validation, feature categorization, equipment classification,
    and mechanical accuracy validation.
    """
    
    def __init__(self, srd_data_path: str, schema_loader):
        """
        Initialize the intelligent data mapper.
        
        Args:
            srd_data_path: Path to D&D 5e SRD data file
            schema_loader: JSONSchemaLoader instance for validation
        """
        self.schema_loader = schema_loader
        self.srd_data = self._load_srd_data(srd_data_path)
        self.spell_names = self._extract_spell_names()
        self.equipment_types = self._load_equipment_types()
        self.ability_categories = self._load_ability_categories()
        
    def _load_srd_data(self, srd_path: str) -> Dict[str, Any]:
        """Load D&D 5e SRD data for validation."""
        try:
            with open(srd_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load SRD data: {e}")
            return {}
    
    def _extract_spell_names(self) -> Set[str]:
        """Extract all spell names from SRD data."""
        spell_names = set()
        
        # Extract from SRD sections
        if 'sections' in self.srd_data:
            for section in self._find_spell_sections(self.srd_data['sections']):
                spells = self._extract_spells_from_section(section)
                spell_names.update(spells)
        
        # Add common spell variations and abbreviations
        spell_names.update(self._get_common_spell_variations())
        
        return spell_names
    
    def _find_spell_sections(self, sections: List[Dict]) -> List[Dict]:
        """Find sections containing spell information."""
        spell_sections = []
        for section in sections:
            if self._is_spell_section(section):
                spell_sections.append(section)
            if 'subsections' in section:
                spell_sections.extend(self._find_spell_sections(section['subsections']))
        return spell_sections
    
    def _is_spell_section(self, section: Dict) -> bool:
        """Check if a section contains spell information."""
        title = section.get('title', '').lower()
        content = section.get('content', '').lower()
        keywords = ['spell', 'cantrip', 'magic', 'spellcasting']
        return any(keyword in title or keyword in content for keyword in keywords)
    
    def _extract_spells_from_section(self, section: Dict) -> Set[str]:
        """Extract spell names from a section."""
        spells = set()
        content = section.get('content', '')
        
        # Look for spell patterns in content
        spell_patterns = [
            r'\*\*([A-Z][a-z\s]+)\*\*',  # Bold spell names
            r'_([A-Z][a-z\s]+)_',        # Italic spell names
            r'([A-Z][a-z\s]+) \(cantrip\)',  # Cantrip pattern
            r'([A-Z][a-z\s]+) \(\d+[a-z]+ level\)',  # Level pattern
        ]
        
        for pattern in spell_patterns:
            matches = re.findall(pattern, content)
            spells.update(match.strip() for match in matches if len(match.strip()) > 2)
        
        return spells
    
    def _get_common_spell_variations(self) -> Set[str]:
        """Get common spell name variations and abbreviations."""
        return {
            # Common cantrips
            'Eldritch Blast', 'Fire Bolt', 'Sacred Flame', 'Vicious Mockery',
            'Minor Illusion', 'Prestidigitation', 'Thaumaturgy', 'Druidcraft',
            'Mage Hand', 'Light', 'Dancing Lights', 'Guidance',
            
            # Common 1st level spells
            'Magic Missile', 'Cure Wounds', 'Healing Word', 'Shield',
            'Detect Magic', 'Identify', 'Sleep', 'Charm Person',
            'Thunderwave', 'Burning Hands', 'Magic Weapon',
            
            # Common higher level spells
            'Fireball', 'Lightning Bolt', 'Counterspell', 'Dispel Magic',
            'Fly', 'Haste', 'Slow', 'Polymorph', 'Greater Invisibility',
            'Dimension Door', 'Wall of Fire', 'Cone of Cold',
            
            # Healing spells
            'Cure Light Wounds', 'Cure Moderate Wounds', 'Cure Serious Wounds',
            'Mass Cure Wounds', 'Heal', 'Regenerate',
        }
    
    def _load_equipment_types(self) -> Dict[str, List[str]]:
        """Load equipment type classifications."""
        return {
            'weapons': {
                'melee': ['sword', 'axe', 'mace', 'hammer', 'dagger', 'spear', 'staff', 'club'],
                'ranged': ['bow', 'crossbow', 'dart', 'javelin', 'sling', 'blowgun'],
                'simple': ['club', 'dagger', 'dart', 'javelin', 'light hammer', 'mace', 'staff', 'crossbow light', 'shortbow', 'sling'],
                'martial': ['battleaxe', 'flail', 'glaive', 'greataxe', 'greatsword', 'halberd', 'lance', 'longsword', 'maul', 'morningstar', 'pike', 'rapier', 'scimitar', 'shortsword', 'trident', 'war pick', 'warhammer', 'whip', 'blowgun', 'crossbow hand', 'crossbow heavy', 'longbow', 'net']
            },
            'armor': {
                'light': ['padded', 'leather', 'studded leather'],
                'medium': ['hide', 'chain shirt', 'scale mail', 'breastplate', 'half plate'],
                'heavy': ['ring mail', 'chain mail', 'splint', 'plate'],
                'shield': ['shield']
            },
            'tools': ['thieves tools', 'artisan tools', 'gaming set', 'musical instrument', 'navigator tools', 'poisoner kit'],
            'consumables': ['potion', 'scroll', 'ammunition', 'food', 'drink'],
            'containers': ['backpack', 'bag', 'chest', 'pouch', 'quiver', 'case'],
            'adventuring_gear': ['rope', 'torch', 'lantern', 'bedroll', 'blanket', 'tent', 'rations']
        }
    
    def _load_ability_categories(self) -> Dict[str, List[str]]:
        """Load ability and feature categorization rules."""
        return {
            'class_features': [
                'rage', 'unarmored defense', 'reckless attack', 'danger sense',
                'extra attack', 'fast movement', 'feral instinct', 'brutal critical',
                'relentless rage', 'persistent rage', 'indomitable might', 'primal champion',
                'spellcasting', 'divine domain', 'channel divinity', 'destroy undead',
                'divine intervention', 'action surge', 'second wind', 'fighting style',
                'superiority dice', 'maneuvers', 'know your enemy', 'improved critical',
                'remarkable athlete', 'additional fighting style', 'indomitable',
                'wild shape', 'druidic', 'natural recovery', 'circle spells',
                'land stride', 'nature ward', 'natures sanctuary', 'timeless body',
                'beast spells', 'archdruid', 'ki', 'unarmored movement', 'martial arts',
                'deflect missiles', 'slow fall', 'stunning strike', 'ki empowered strikes',
                'evasion', 'stillness of mind', 'purity of body', 'tongue of sun and moon',
                'diamond soul', 'timeless body', 'empty body', 'perfect self',
                'divine sense', 'lay on hands', 'divine smite', 'divine health',
                'sacred oath', 'aura of protection', 'aura of courage', 'improved divine smite',
                'cleansing touch', 'aura improvements', 'favored enemy', 'natural explorer',
                'hunter mark', 'primeval awareness', 'lands stride', 'hide in plain sight',
                'vanish', 'feral senses', 'foe slayer', 'expertise', 'sneak attack',
                'thieves cant', 'cunning action', 'uncanny dodge', 'reliable talent',
                'blindsense', 'slippery mind', 'elusive', 'stroke of luck',
                'sorcerous origin', 'font of magic', 'sorcery points', 'metamagic',
                'sorcerous restoration', 'otherworldly patron', 'pact magic', 'eldritch invocations',
                'pact boon', 'mystic arcanum', 'eldritch master', 'arcane recovery',
                'ritual casting', 'arcane tradition', 'spell mastery', 'signature spells'
            ],
            'racial_traits': [
                'darkvision', 'keen senses', 'fey ancestry', 'trance', 'elf weapon training',
                'cantrip', 'extra language', 'draconic ancestry', 'breath weapon',
                'damage resistance', 'lucky', 'brave', 'halfling nimbleness',
                'naturally stealthy', 'dwarven resilience', 'dwarven combat training',
                'stonecunning', 'dwarven toughness', 'dwarven armor training',
                'menacing', 'relentless endurance', 'savage attacks', 'gnome cunning',
                'speak with small beasts', 'artificers lore', 'tinker', 'natural illusionist',
                'speak with animals', 'amphibious', 'swim speed', 'call to the wave',
                'guardian of the depths', 'emissary of the sea', 'control air and water',
                'mingle with the wind', 'draconic ancestry', 'breath weapon', 'damage resistance',
                'draconic ancestry', 'breath weapon', 'damage resistance'
            ],
            'feats': [
                'alert', 'athlete', 'actor', 'charger', 'crossbow expert', 'defensive duelist',
                'dual wielder', 'dungeon delver', 'durable', 'elemental adept', 'fey touched',
                'great weapon master', 'healer', 'heavily armored', 'heavy armor master',
                'inspiring leader', 'keen mind', 'lightly armored', 'linguist', 'lucky',
                'mage slayer', 'magic initiate', 'martial adept', 'medium armor master',
                'mobile', 'moderately armored', 'mounted combatant', 'observant', 'polearm master',
                'resilient', 'ritual caster', 'savage attacker', 'sentinel', 'sharpshooter',
                'shield master', 'skilled', 'skulker', 'spell sniper', 'tavern brawler',
                'tough', 'war caster', 'weapon master'
            ],
            'background_features': [
                'feature', 'shelter of the faithful', 'by popular demand', 'false identity',
                'criminal contact', 'folk hero', 'rustic hospitality', 'guild membership',
                'position of privilege', 'researcher', 'ship passage', 'wanderer'
            ]
        }

    def map_character_data(self, parsed_data: Dict[str, Any]) -> MappingResult:
        """
        Intelligently map parsed character data to proper JSON structures.
        
        Args:
            parsed_data: Raw parsed data from LLM
            
        Returns:
            MappingResult with mapped data and validation results
        """
        mapped_data = {}
        validation_results = {}
        uncertain_fields = []
        
        # Map each file type
        for file_type in ['character', 'spell_list', 'feats_and_traits', 'inventory_list', 'character_background']:
            if file_type in parsed_data:
                result = self._map_file_data(file_type, parsed_data[file_type])
                mapped_data[file_type] = result['data']
                validation_results[file_type] = result['validation']
                uncertain_fields.extend(result['uncertain_fields'])
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(validation_results)
        
        return MappingResult(
            mapped_data=mapped_data,
            validation_results=validation_results,
            uncertain_fields=uncertain_fields,
            overall_confidence=overall_confidence
        )
    
    def _map_file_data(self, file_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map data for a specific file type."""
        if file_type == 'spell_list':
            return self._map_spell_data(data)
        elif file_type == 'feats_and_traits':
            return self._map_features_data(data)
        elif file_type == 'inventory_list':
            return self._map_inventory_data(data)
        elif file_type == 'character_background':
            return self._map_background_data(data)
        elif file_type == 'character':
            return self._map_character_data(data)
        else:
            return {'data': data, 'validation': {}, 'uncertain_fields': []}
    
    def _map_spell_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map and validate spell data."""
        if not isinstance(data, dict):
            return {'data': {}, 'validation': {}, 'uncertain_fields': []}
        
        mapped_data = data.copy()
        validation_results = {}
        uncertain_fields = []
        
        # Validate spells in spellcasting classes
        if 'spellcasting' in data:
            for class_name, class_data in data['spellcasting'].items():
                if 'spells' in class_data:
                    for level, spells in class_data['spells'].items():
                        for i, spell in enumerate(spells):
                            if isinstance(spell, dict) and 'name' in spell:
                                validation = self.validate_spell_name(spell['name'])
                                field_path = f"spellcasting.{class_name}.spells.{level}[{i}].name"
                                validation_results[field_path] = validation
                                
                                if validation.corrected_value:
                                    mapped_data['spellcasting'][class_name]['spells'][level][i]['name'] = validation.corrected_value
                                
                                if validation.confidence < 0.8:
                                    uncertain_fields.append(field_path)
        
        return {
            'data': mapped_data,
            'validation': validation_results,
            'uncertain_fields': uncertain_fields
        }
    
    def validate_spell_name(self, spell_name: str) -> ValidationResult:
        """
        Validate a spell name against D&D 5e SRD data.
        
        Args:
            spell_name: The spell name to validate
            
        Returns:
            ValidationResult with validation status and suggestions
        """
        if not spell_name or not isinstance(spell_name, str):
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                suggestions=[],
                errors=["Empty or invalid spell name"]
            )
        
        # Clean the spell name
        clean_name = self._clean_spell_name(spell_name)
        
        # Exact match
        if clean_name in self.spell_names:
            return ValidationResult(
                is_valid=True,
                confidence=1.0,
                suggestions=[],
                errors=[]
            )
        
        # Fuzzy matching for close matches
        best_matches = self._find_best_spell_matches(clean_name)
        
        if best_matches:
            best_match, similarity = best_matches[0]
            if similarity > 0.8:
                return ValidationResult(
                    is_valid=True,
                    confidence=similarity,
                    suggestions=[match[0] for match in best_matches[:3]],
                    errors=[],
                    corrected_value=best_match
                )
            elif similarity > 0.6:
                return ValidationResult(
                    is_valid=False,
                    confidence=similarity,
                    suggestions=[match[0] for match in best_matches[:5]],
                    errors=[f"Spell name '{spell_name}' not found in SRD"]
                )
        
        return ValidationResult(
            is_valid=False,
            confidence=0.0,
            suggestions=[],
            errors=[f"Spell name '{spell_name}' not recognized"]
        )
    
    def _clean_spell_name(self, name: str) -> str:
        """Clean and normalize spell name for comparison."""
        # Remove extra whitespace and normalize case
        clean = re.sub(r'\s+', ' ', name.strip())
        
        # Handle common abbreviations
        abbreviations = {
            'MM': 'Magic Missile',
            'EB': 'Eldritch Blast',
            'FB': 'Fire Bolt',
            'CW': 'Cure Wounds',
            'HW': 'Healing Word'
        }
        
        if clean.upper() in abbreviations:
            return abbreviations[clean.upper()]
        
        return clean
    
    def _find_best_spell_matches(self, spell_name: str) -> List[Tuple[str, float]]:
        """Find best matching spell names using fuzzy matching."""
        matches = []
        
        for known_spell in self.spell_names:
            similarity = SequenceMatcher(None, spell_name.lower(), known_spell.lower()).ratio()
            if similarity > 0.5:  # Only consider reasonably similar matches
                matches.append((known_spell, similarity))
        
        # Sort by similarity descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:10]  # Return top 10 matches
    
    def _map_features_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map and categorize features and abilities."""
        if not isinstance(data, dict):
            return {'data': {}, 'validation': {}, 'uncertain_fields': []}
        
        mapped_data = data.copy()
        validation_results = {}
        uncertain_fields = []
        
        # Process features and categorize them properly
        if 'features_and_traits' in data:
            features_data = data['features_and_traits']
            
            # Categorize class features
            if 'class_features' in features_data:
                for class_name, class_data in features_data['class_features'].items():
                    if 'features' in class_data:
                        for i, feature in enumerate(class_data['features']):
                            if isinstance(feature, dict) and 'name' in feature:
                                validation = self.categorize_ability(feature['name'], 'class_feature')
                                field_path = f"features_and_traits.class_features.{class_name}.features[{i}]"
                                validation_results[field_path] = validation
                                
                                if validation.confidence < 0.7:
                                    uncertain_fields.append(field_path)
            
            # Categorize racial traits
            if 'species_traits' in features_data and 'traits' in features_data['species_traits']:
                for i, trait in enumerate(features_data['species_traits']['traits']):
                    if isinstance(trait, dict) and 'name' in trait:
                        validation = self.categorize_ability(trait['name'], 'racial_trait')
                        field_path = f"features_and_traits.species_traits.traits[{i}]"
                        validation_results[field_path] = validation
                        
                        if validation.confidence < 0.7:
                            uncertain_fields.append(field_path)
            
            # Validate feats
            if 'feats' in features_data:
                for i, feat in enumerate(features_data['feats']):
                    if isinstance(feat, dict) and 'name' in feat:
                        validation = self.categorize_ability(feat['name'], 'feat')
                        field_path = f"features_and_traits.feats[{i}]"
                        validation_results[field_path] = validation
                        
                        if validation.confidence < 0.7:
                            uncertain_fields.append(field_path)
        
        return {
            'data': mapped_data,
            'validation': validation_results,
            'uncertain_fields': uncertain_fields
        }
    
    def categorize_ability(self, ability_name: str, expected_type: str) -> ValidationResult:
        """
        Categorize an ability or feature and validate its placement.
        
        Args:
            ability_name: Name of the ability/feature
            expected_type: Expected category ('class_feature', 'racial_trait', 'feat', etc.)
            
        Returns:
            ValidationResult with categorization confidence
        """
        if not ability_name or not isinstance(ability_name, str):
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                suggestions=[],
                errors=["Empty or invalid ability name"]
            )
        
        clean_name = ability_name.lower().strip()
        
        # Check if ability matches expected category
        category_matches = {
            'class_feature': self._matches_class_features(clean_name),
            'racial_trait': self._matches_racial_traits(clean_name),
            'feat': self._matches_feats(clean_name),
            'background_feature': self._matches_background_features(clean_name)
        }
        
        expected_match = category_matches.get(expected_type, 0.0)
        best_category = max(category_matches.items(), key=lambda x: x[1])
        
        if expected_match > 0.7:
            return ValidationResult(
                is_valid=True,
                confidence=expected_match,
                suggestions=[],
                errors=[]
            )
        elif best_category[1] > 0.7 and best_category[0] != expected_type:
            return ValidationResult(
                is_valid=False,
                confidence=best_category[1],
                suggestions=[f"Consider moving to {best_category[0]} category"],
                errors=[f"Ability '{ability_name}' seems to belong in {best_category[0]} category"]
            )
        else:
            return ValidationResult(
                is_valid=True,
                confidence=0.5,  # Neutral confidence for unknown abilities
                suggestions=[],
                errors=[],
                corrected_value=ability_name
            )
    
    def _matches_class_features(self, ability_name: str) -> float:
        """Check how well an ability matches class features."""
        class_features = self.ability_categories['class_features']
        return self._calculate_name_similarity(ability_name, class_features)
    
    def _matches_racial_traits(self, ability_name: str) -> float:
        """Check how well an ability matches racial traits."""
        racial_traits = self.ability_categories['racial_traits']
        return self._calculate_name_similarity(ability_name, racial_traits)
    
    def _matches_feats(self, ability_name: str) -> float:
        """Check how well an ability matches known feats."""
        feats = self.ability_categories['feats']
        return self._calculate_name_similarity(ability_name, feats)
    
    def _matches_background_features(self, ability_name: str) -> float:
        """Check how well an ability matches background features."""
        bg_features = self.ability_categories['background_features']
        return self._calculate_name_similarity(ability_name, bg_features)
    
    def _calculate_name_similarity(self, name: str, known_names: List[str]) -> float:
        """Calculate similarity between a name and a list of known names."""
        best_similarity = 0.0
        
        for known_name in known_names:
            # Exact match
            if name == known_name.lower():
                return 1.0
            
            # Partial match
            if name in known_name.lower() or known_name.lower() in name:
                similarity = max(len(name) / len(known_name), len(known_name) / len(name))
                best_similarity = max(best_similarity, similarity * 0.9)
            
            # Fuzzy match
            similarity = SequenceMatcher(None, name, known_name.lower()).ratio()
            best_similarity = max(best_similarity, similarity)
        
        return best_similarity
    
    def _map_inventory_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map and classify equipment and inventory items."""
        if not isinstance(data, dict):
            return {'data': {}, 'validation': {}, 'uncertain_fields': []}
        
        mapped_data = data.copy()
        validation_results = {}
        uncertain_fields = []
        
        if 'inventory' in data and 'equipped_items' in data['inventory']:
            equipped = data['inventory']['equipped_items']
            
            # Classify weapons
            if 'weapons' in equipped:
                for i, weapon in enumerate(equipped['weapons']):
                    if isinstance(weapon, dict) and 'name' in weapon:
                        validation = self.classify_equipment(weapon['name'], 'weapon')
                        field_path = f"inventory.equipped_items.weapons[{i}]"
                        validation_results[field_path] = validation
                        
                        # Apply classification results
                        if validation.corrected_value and isinstance(validation.corrected_value, dict):
                            mapped_data['inventory']['equipped_items']['weapons'][i].update(validation.corrected_value)
                        
                        if validation.confidence < 0.7:
                            uncertain_fields.append(field_path)
            
            # Classify armor
            if 'armor' in equipped:
                for i, armor in enumerate(equipped['armor']):
                    if isinstance(armor, dict) and 'name' in armor:
                        validation = self.classify_equipment(armor['name'], 'armor')
                        field_path = f"inventory.equipped_items.armor[{i}]"
                        validation_results[field_path] = validation
                        
                        # Apply classification results
                        if validation.corrected_value and isinstance(validation.corrected_value, dict):
                            mapped_data['inventory']['equipped_items']['armor'][i].update(validation.corrected_value)
                        
                        if validation.confidence < 0.7:
                            uncertain_fields.append(field_path)
        
        return {
            'data': mapped_data,
            'validation': validation_results,
            'uncertain_fields': uncertain_fields
        }
    
    def classify_equipment(self, item_name: str, expected_type: str) -> ValidationResult:
        """
        Classify equipment and determine its properties.
        
        Args:
            item_name: Name of the equipment item
            expected_type: Expected equipment type ('weapon', 'armor', 'tool', etc.)
            
        Returns:
            ValidationResult with classification and properties
        """
        if not item_name or not isinstance(item_name, str):
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                suggestions=[],
                errors=["Empty or invalid item name"]
            )
        
        clean_name = item_name.lower().strip()
        
        if expected_type == 'weapon':
            return self._classify_weapon(clean_name, item_name)
        elif expected_type == 'armor':
            return self._classify_armor(clean_name, item_name)
        else:
            return self._classify_general_equipment(clean_name, item_name)
    
    def _classify_weapon(self, clean_name: str, original_name: str) -> ValidationResult:
        """Classify a weapon and determine its properties."""
        weapon_data = {}
        confidence = 0.5
        suggestions = []
        errors = []
        
        # Determine weapon type and properties
        if any(weapon in clean_name for weapon in self.equipment_types['weapons']['melee']):
            weapon_data['attack_type'] = 'melee'
            confidence += 0.2
        elif any(weapon in clean_name for weapon in self.equipment_types['weapons']['ranged']):
            weapon_data['attack_type'] = 'ranged'
            confidence += 0.2
        
        # Determine proficiency category
        if any(weapon in clean_name for weapon in self.equipment_types['weapons']['simple']):
            weapon_data['proficiency_category'] = 'simple'
            confidence += 0.2
        elif any(weapon in clean_name for weapon in self.equipment_types['weapons']['martial']):
            weapon_data['proficiency_category'] = 'martial'
            confidence += 0.2
        
        # Set weapon properties based on common weapons
        weapon_properties = self._get_weapon_properties(clean_name)
        if weapon_properties:
            weapon_data.update(weapon_properties)
            confidence += 0.1
        
        return ValidationResult(
            is_valid=True,
            confidence=min(confidence, 1.0),
            suggestions=suggestions,
            errors=errors,
            corrected_value=weapon_data if weapon_data else None
        )
    
    def _classify_armor(self, clean_name: str, original_name: str) -> ValidationResult:
        """Classify armor and determine its properties."""
        armor_data = {}
        confidence = 0.5
        suggestions = []
        errors = []
        
        # Determine armor type
        for armor_type, armors in self.equipment_types['armor'].items():
            if any(armor in clean_name for armor in armors):
                armor_data['type'] = armor_type
                confidence += 0.3
                break
        
        # Set armor properties based on type
        armor_properties = self._get_armor_properties(clean_name)
        if armor_properties:
            armor_data.update(armor_properties)
            confidence += 0.2
        
        return ValidationResult(
            is_valid=True,
            confidence=min(confidence, 1.0),
            suggestions=suggestions,
            errors=errors,
            corrected_value=armor_data if armor_data else None
        )
    
    def _classify_general_equipment(self, clean_name: str, original_name: str) -> ValidationResult:
        """Classify general equipment items."""
        item_data = {}
        confidence = 0.5
        
        # Determine item category
        for category, items in self.equipment_types.items():
            if category in ['weapons', 'armor']:
                continue
            
            if isinstance(items, list):
                if any(item in clean_name for item in items):
                    item_data['category'] = category
                    confidence += 0.3
                    break
        
        return ValidationResult(
            is_valid=True,
            confidence=confidence,
            suggestions=[],
            errors=[],
            corrected_value=item_data if item_data else None
        )
    
    def _get_weapon_properties(self, weapon_name: str) -> Dict[str, Any]:
        """Get standard properties for common weapons."""
        weapon_stats = {
            'dagger': {'damage': '1d4', 'damage_type': 'piercing', 'properties': ['finesse', 'light', 'thrown']},
            'shortsword': {'damage': '1d6', 'damage_type': 'piercing', 'properties': ['finesse', 'light']},
            'longsword': {'damage': '1d8', 'damage_type': 'slashing', 'properties': ['versatile']},
            'greatsword': {'damage': '2d6', 'damage_type': 'slashing', 'properties': ['heavy', 'two-handed']},
            'shortbow': {'damage': '1d6', 'damage_type': 'piercing', 'range': '80/320', 'properties': ['ammunition', 'two-handed']},
            'longbow': {'damage': '1d8', 'damage_type': 'piercing', 'range': '150/600', 'properties': ['ammunition', 'heavy', 'two-handed']},
            'crossbow': {'damage': '1d8', 'damage_type': 'piercing', 'range': '100/400', 'properties': ['ammunition', 'loading', 'two-handed']},
        }
        
        for weapon, stats in weapon_stats.items():
            if weapon in weapon_name:
                return stats
        
        return {}
    
    def _get_armor_properties(self, armor_name: str) -> Dict[str, Any]:
        """Get standard properties for common armor."""
        armor_stats = {
            'leather': {'armor_class': 11, 'stealth_disadvantage': False},
            'studded leather': {'armor_class': 12, 'stealth_disadvantage': False},
            'chain shirt': {'armor_class': 13, 'stealth_disadvantage': False},
            'scale mail': {'armor_class': 14, 'stealth_disadvantage': True},
            'chain mail': {'armor_class': 16, 'stealth_disadvantage': True, 'strength_requirement': 13},
            'plate': {'armor_class': 18, 'stealth_disadvantage': True, 'strength_requirement': 15},
            'shield': {'armor_class_bonus': 2, 'stealth_disadvantage': False},
        }
        
        for armor, stats in armor_stats.items():
            if armor in armor_name:
                return stats
        
        return {}
    
    def _map_background_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map and organize character background elements."""
        if not isinstance(data, dict):
            return {'data': {}, 'validation': {}, 'uncertain_fields': []}
        
        mapped_data = data.copy()
        validation_results = {}
        uncertain_fields = []
        
        # Validate background elements
        if 'background' in data and 'name' in data['background']:
            validation = self.validate_background(data['background']['name'])
            validation_results['background.name'] = validation
            
            if validation.confidence < 0.7:
                uncertain_fields.append('background.name')
        
        # Organize personality traits, ideals, bonds, flaws
        if 'characteristics' in data:
            char_data = data['characteristics']
            for trait_type in ['personality_traits', 'ideals', 'bonds', 'flaws']:
                if trait_type in char_data:
                    validation = self.validate_character_traits(char_data[trait_type], trait_type)
                    validation_results[f'characteristics.{trait_type}'] = validation
                    
                    if validation.confidence < 0.7:
                        uncertain_fields.append(f'characteristics.{trait_type}')
        
        return {
            'data': mapped_data,
            'validation': validation_results,
            'uncertain_fields': uncertain_fields
        }
    
    def validate_background(self, background_name: str) -> ValidationResult:
        """Validate a character background name."""
        if not background_name or not isinstance(background_name, str):
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                suggestions=[],
                errors=["Empty or invalid background name"]
            )
        
        # Common D&D 5e backgrounds
        known_backgrounds = [
            'acolyte', 'criminal', 'folk hero', 'noble', 'sage', 'soldier',
            'charlatan', 'entertainer', 'guild artisan', 'hermit', 'outlander', 'sailor'
        ]
        
        clean_name = background_name.lower().strip()
        
        # Exact match
        if clean_name in known_backgrounds:
            return ValidationResult(
                is_valid=True,
                confidence=1.0,
                suggestions=[],
                errors=[]
            )
        
        # Fuzzy matching
        best_matches = []
        for bg in known_backgrounds:
            similarity = SequenceMatcher(None, clean_name, bg).ratio()
            if similarity > 0.6:
                best_matches.append((bg, similarity))
        
        best_matches.sort(key=lambda x: x[1], reverse=True)
        
        if best_matches and best_matches[0][1] > 0.8:
            return ValidationResult(
                is_valid=True,
                confidence=best_matches[0][1],
                suggestions=[match[0] for match in best_matches[:3]],
                errors=[],
                corrected_value=best_matches[0][0]
            )
        
        return ValidationResult(
            is_valid=True,
            confidence=0.5,  # Accept custom backgrounds
            suggestions=[match[0] for match in best_matches[:3]] if best_matches else [],
            errors=[]
        )
    
    def validate_character_traits(self, traits: List[str], trait_type: str) -> ValidationResult:
        """Validate character personality traits, ideals, bonds, or flaws."""
        if not isinstance(traits, list):
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                suggestions=[],
                errors=[f"Invalid {trait_type} format - should be a list"]
            )
        
        # Basic validation - traits should be non-empty strings
        valid_traits = []
        for trait in traits:
            if isinstance(trait, str) and trait.strip():
                valid_traits.append(trait.strip())
        
        confidence = len(valid_traits) / max(len(traits), 1) if traits else 0.0
        
        return ValidationResult(
            is_valid=len(valid_traits) > 0,
            confidence=confidence,
            suggestions=[],
            errors=[] if valid_traits else [f"No valid {trait_type} found"]
        )
    
    def _map_character_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map and validate core character data."""
        if not isinstance(data, dict):
            return {'data': {}, 'validation': {}, 'uncertain_fields': []}
        
        mapped_data = data.copy()
        validation_results = {}
        uncertain_fields = []
        
        # Validate ability scores
        if 'ability_scores' in data:
            validation = self.validate_ability_scores(data['ability_scores'])
            validation_results['ability_scores'] = validation
            
            if validation.confidence < 0.8:
                uncertain_fields.append('ability_scores')
        
        # Validate combat stats
        if 'combat_stats' in data:
            validation = self.validate_combat_stats(data['combat_stats'], data.get('ability_scores', {}))
            validation_results['combat_stats'] = validation
            
            if validation.confidence < 0.8:
                uncertain_fields.append('combat_stats')
        
        return {
            'data': mapped_data,
            'validation': validation_results,
            'uncertain_fields': uncertain_fields
        }
    
    def validate_ability_scores(self, ability_scores: Dict[str, int]) -> ValidationResult:
        """Validate character ability scores for mechanical accuracy."""
        if not isinstance(ability_scores, dict):
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                suggestions=[],
                errors=["Ability scores must be a dictionary"]
            )
        
        required_abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        errors = []
        suggestions = []
        
        # Check all required abilities are present
        missing_abilities = [ability for ability in required_abilities if ability not in ability_scores]
        if missing_abilities:
            errors.append(f"Missing ability scores: {', '.join(missing_abilities)}")
        
        # Validate score ranges
        for ability, score in ability_scores.items():
            if not isinstance(score, int):
                errors.append(f"{ability} score must be an integer")
                continue
            
            if score < 1 or score > 30:
                errors.append(f"{ability} score {score} is outside valid range (1-30)")
            elif score < 8 or score > 18:
                suggestions.append(f"{ability} score {score} is unusual for starting characters (typically 8-18)")
        
        # Calculate confidence based on validation results
        confidence = 1.0
        if errors:
            confidence -= 0.5
        if suggestions:
            confidence -= 0.2
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            confidence=max(confidence, 0.0),
            suggestions=suggestions,
            errors=errors
        )
    
    def validate_combat_stats(self, combat_stats: Dict[str, Any], ability_scores: Dict[str, int]) -> ValidationResult:
        """Validate combat statistics for mechanical accuracy."""
        if not isinstance(combat_stats, dict):
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                suggestions=[],
                errors=["Combat stats must be a dictionary"]
            )
        
        errors = []
        suggestions = []
        
        # Validate HP
        if 'max_hp' in combat_stats:
            hp = combat_stats['max_hp']
            if not isinstance(hp, int) or hp < 1:
                errors.append("Max HP must be a positive integer")
        
        # Validate AC
        if 'armor_class' in combat_stats:
            ac = combat_stats['armor_class']
            if not isinstance(ac, int) or ac < 10 or ac > 30:
                errors.append("Armor Class should typically be between 10-30")
        
        # Validate initiative bonus against Dex modifier
        if 'initiative_bonus' in combat_stats and 'dexterity' in ability_scores:
            init_bonus = combat_stats['initiative_bonus']
            dex_modifier = (ability_scores['dexterity'] - 10) // 2
            
            if abs(init_bonus - dex_modifier) > 5:  # Allow for some flexibility
                suggestions.append(f"Initiative bonus {init_bonus} seems inconsistent with Dex modifier {dex_modifier}")
        
        # Calculate confidence
        confidence = 1.0
        if errors:
            confidence -= 0.5
        if suggestions:
            confidence -= 0.2
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            confidence=max(confidence, 0.0),
            suggestions=suggestions,
            errors=errors
        )
    
    def _calculate_overall_confidence(self, validation_results: Dict[str, Dict]) -> float:
        """Calculate overall confidence score from all validation results."""
        if not validation_results:
            return 0.5
        
        total_confidence = 0.0
        total_validations = 0
        
        for file_type, file_validations in validation_results.items():
            for field, validation in file_validations.items():
                if hasattr(validation, 'confidence'):
                    total_confidence += validation.confidence
                    total_validations += 1
        
        return total_confidence / max(total_validations, 1)