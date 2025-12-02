"""
Character Inspector Utility

A comprehensive debugging and inspection tool for character objects.
Supports multiple output formats, filtering, and detailed analysis
for character development and debugging purposes.
"""

import argparse
import inspect
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import get_type_hints, get_origin, get_args, Any, Dict, List, Optional

# Always use package imports - script should be run as a module
from src.rag.character.character_manager import CharacterManager
from src.rag.character.character_types import Character


class CharacterInspector:
    """A utility class for inspecting and debugging character objects."""
    
    def __init__(self, output_format: str = "text", max_depth: int = 10, 
                 show_types: bool = True, show_none_values: bool = False):
        """
        Initialize the character inspector.
        
        Args:
            output_format: Output format ('text', 'json', 'summary')
            max_depth: Maximum recursion depth for nested objects
            show_types: Whether to show type information
            show_none_values: Whether to include None/empty values
        """
        self.output_format = output_format.lower()
        self.max_depth = max_depth
        self.show_types = show_types
        self.show_none_values = show_none_values
        self.current_depth = 0
    
    def get_type_name(self, obj: Any) -> str:
        """Get a readable type name for an object."""
        obj_type = type(obj)
        
        # Handle basic types
        if obj_type in (str, int, float, bool, type(None)):
            return obj_type.__name__
        
        # Handle lists
        if obj_type == list:
            if obj:
                element_type = self.get_type_name(obj[0])
                return f"List[{element_type}]"
            return "List"
        
        # Handle dicts
        if obj_type == dict:
            if obj:
                # Try to get a sample key-value type
                sample_key, sample_value = next(iter(obj.items()))
                key_type = self.get_type_name(sample_key)
                value_type = self.get_type_name(sample_value)
                return f"Dict[{key_type}, {value_type}]"
            return "Dict"
        
        # Handle dataclass instances
        if hasattr(obj_type, '__dataclass_fields__'):
            return obj_type.__name__
        
        # Handle datetime
        if obj_type == datetime:
            return "datetime"
        
        # Default
        return obj_type.__name__


    def format_value(self, value: Any, indent_level: int = 0, max_items: int = 3) -> str:
        """Format a value for display with proper indentation."""
        indent = "  " * indent_level
        
        if value is None:
            return "None" if self.show_none_values else ""
        elif isinstance(value, (str, int, float, bool)):
            return repr(value)
        elif isinstance(value, datetime):
            return f"datetime({value.strftime('%Y-%m-%d %H:%M:%S')})"
        elif isinstance(value, list):
            if not value:
                return "[]" if self.show_none_values else ""
            elif len(value) == 1:
                return f"[{self.format_value(value[0], 0)}]"
            else:
                items = []
                for i, item in enumerate(value[:max_items]):
                    items.append(f"{indent}  {self.format_value(item, indent_level + 1)}")
                if len(value) > max_items:
                    items.append(f"{indent}  ... and {len(value) - max_items} more items")
                return "[\n" + ",\n".join(items) + f"\n{indent}]"
        elif isinstance(value, dict):
            if not value:
                return "{}" if self.show_none_values else ""
            items = []
            for i, (k, v) in enumerate(list(value.items())[:max_items]):
                items.append(f"{indent}  {repr(k)}: {self.format_value(v, indent_level + 1)}")
            if len(value) > max_items:
                items.append(f"{indent}  ... and {len(value) - max_items} more items")
            return "{\n" + ",\n".join(items) + f"\n{indent}}}"
        elif hasattr(type(value), '__dataclass_fields__'):
            return f"{type(value).__name__}(...)"
        else:
            return f"{type(value).__name__}(...)"
    
    def should_include_field(self, field_name: str, value: Any, filters: Optional[List[str]] = None) -> bool:
        """Determine if a field should be included based on filters and settings."""
        # Skip None values if not showing them
        if not self.show_none_values and value is None:
            return False
        
        # Skip empty containers if not showing none values
        if not self.show_none_values and (
            (isinstance(value, (list, dict)) and not value)
        ):
            return False
        
        # Apply field filters
        if filters:
            return any(filter_term.lower() in field_name.lower() for filter_term in filters)
        
        return True


    def inspect_dataclass(self, obj: Any, output_lines: List[str], indent_level: int = 0, 
                         prefix: str = "", filters: Optional[List[str]] = None) -> None:
        """Recursively inspect a dataclass and add to output lines."""
        if self.current_depth >= self.max_depth:
            output_lines.append(f"{'  ' * indent_level}... (max depth reached)")
            return
        
        indent = "  " * indent_level
        class_name = type(obj).__name__
        
        if prefix:
            output_lines.append(f"{indent}{prefix} ({class_name}):")
        else:
            output_lines.append(f"{indent}{class_name}:")
        
        if hasattr(type(obj), '__dataclass_fields__'):
            fields = type(obj).__dataclass_fields__
            
            self.current_depth += 1
            for field_name, field_info in fields.items():
                if hasattr(obj, field_name):
                    value = getattr(obj, field_name)
                    
                    if not self.should_include_field(field_name, value, filters):
                        continue
                    
                    type_name = self.get_type_name(value) if self.show_types else ""
                    
                    # Format the field header
                    if self.show_types:
                        field_header = f"{indent}  {field_name}: {type_name}"
                    else:
                        field_header = f"{indent}  {field_name}"
                    
                    if value is None:
                        if self.show_none_values:
                            output_lines.append(f"{field_header} = None")
                    elif isinstance(value, (str, int, float, bool)):
                        output_lines.append(f"{field_header} = {repr(value)}")
                    elif isinstance(value, datetime):
                        output_lines.append(f"{field_header} = {value.strftime('%Y-%m-%d %H:%M:%S')}")
                    elif isinstance(value, list):
                        output_lines.append(f"{field_header} = List with {len(value)} items")
                        if value and hasattr(type(value[0]), '__dataclass_fields__'):
                            # Show first item in detail if it's a dataclass
                            output_lines.append(f"{indent}    [0]:")
                            self.inspect_dataclass(value[0], output_lines, indent_level + 2, filters=filters)
                            if len(value) > 1:
                                output_lines.append(f"{indent}    ... and {len(value) - 1} more items")
                        elif value:
                            # Show first few items if they're simple types
                            for i, item in enumerate(value[:3]):
                                output_lines.append(f"{indent}    [{i}]: {self.format_value(item)}")
                            if len(value) > 3:
                                output_lines.append(f"{indent}    ... and {len(value) - 3} more items")
                    elif isinstance(value, dict):
                        output_lines.append(f"{field_header} = Dict with {len(value)} items")
                        for i, (k, v) in enumerate(list(value.items())[:2]):  # Show first 2 items
                            if hasattr(type(v), '__dataclass_fields__'):
                                output_lines.append(f"{indent}    {repr(k)}:")
                                self.inspect_dataclass(v, output_lines, indent_level + 2, filters=filters)
                            elif isinstance(v, list) and v and hasattr(type(v[0]), '__dataclass_fields__'):
                                # Special handling for lists of dataclass objects (like spells)
                                output_lines.append(f"{indent}    {repr(k)}: List with {len(v)} items")
                                if v:  # Show first spell in detail
                                    output_lines.append(f"{indent}      [0]:")
                                    self.inspect_dataclass(v[0], output_lines, indent_level + 3, filters=filters)
                                    if len(v) > 1:
                                        output_lines.append(f"{indent}      ... and {len(v) - 1} more items")
                            else:
                                output_lines.append(f"{indent}    {repr(k)}: {self.format_value(v)}")
                        if len(value) > 2:
                            output_lines.append(f"{indent}    ... and {len(value) - 2} more items")
                    elif hasattr(type(value), '__dataclass_fields__'):
                        output_lines.append(f"{field_header}")
                        self.inspect_dataclass(value, output_lines, indent_level + 1, filters=filters)
                    else:
                        output_lines.append(f"{field_header} = {self.format_value(value)}")
                    
                    output_lines.append("")  # Empty line for readability
            
            self.current_depth -= 1


    def generate_summary(self, character: Character) -> Dict[str, Any]:
        """Generate a concise summary of the character."""
        summary = {
            "name": character.character_base.name,
            "race": character.character_base.race,
            "character_class": character.character_base.character_class,
            "level": character.character_base.total_level,
            "max_hp": character.combat_stats.max_hp,
            "armor_class": character.combat_stats.armor_class,
            "ability_scores": {
                "strength": character.ability_scores.strength,
                "dexterity": character.ability_scores.dexterity,
                "constitution": character.ability_scores.constitution,
                "intelligence": character.ability_scores.intelligence,
                "wisdom": character.ability_scores.wisdom,
                "charisma": character.ability_scores.charisma,
            },
            "spell_count": len(character.spell_list.spells) if character.spell_list else 0,
            "inventory_count": (
                len(character.inventory.backpack) + 
                sum(len(items) for items in character.inventory.equipped_items.values())
            ) if character.inventory else 0,
            "last_updated": character.last_updated.isoformat() if character.last_updated else None
        }
        return summary
    
    def to_json_dict(self, obj: Any, max_depth: int = None) -> Any:
        """Convert a character object to a JSON-serializable dictionary."""
        if max_depth is None:
            max_depth = self.max_depth
        
        if max_depth <= 0:
            return f"<{type(obj).__name__}> (max depth reached)"
        
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, list):
            return [self.to_json_dict(item, max_depth - 1) for item in obj]
        elif isinstance(obj, dict):
            return {k: self.to_json_dict(v, max_depth - 1) for k, v in obj.items()}
        elif hasattr(type(obj), '__dataclass_fields__'):
            result = {}
            for field_name, field_info in type(obj).__dataclass_fields__.items():
                if hasattr(obj, field_name):
                    value = getattr(obj, field_name)
                    if self.should_include_field(field_name, value):
                        result[field_name] = self.to_json_dict(value, max_depth - 1)
            return result
        else:
            return str(obj)
    
    def inspect_character(self, character: Character, filters: Optional[List[str]] = None) -> str:
        """
        Inspect a character and return formatted output.
        
        Args:
            character: The Character object to inspect
            filters: Optional list of field name filters
            
        Returns:
            Formatted string output
        """
        self.current_depth = 0
        
        if self.output_format == "json":
            data = self.to_json_dict(character)
            return json.dumps(data, indent=2, ensure_ascii=False)
        
        elif self.output_format == "summary":
            summary = self.generate_summary(character)
            output_lines = [
                f"Character Summary: {summary['name']}",
                f"Race: {summary['race']}, Class: {summary['character_class']}, Level: {summary['level']}",
                f"HP: {summary['max_hp']}, AC: {summary['armor_class']}",
                f"Abilities: STR {summary['ability_scores']['strength']}, "
                f"DEX {summary['ability_scores']['dexterity']}, "
                f"CON {summary['ability_scores']['constitution']}, "
                f"INT {summary['ability_scores']['intelligence']}, "
                f"WIS {summary['ability_scores']['wisdom']}, "
                f"CHA {summary['ability_scores']['charisma']}",
                f"Spells: {summary['spell_count']}, Inventory Items: {summary['inventory_count']}",
                f"Last Updated: {summary['last_updated'] or 'Never'}"
            ]
            return '\n'.join(output_lines)
        
        else:  # text format
            output_lines = []
            
            # Header
            output_lines.append("=" * 80)
            output_lines.append(f"CHARACTER INSPECTION REPORT")
            output_lines.append(f"Character: {character.character_base.name}")
            output_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            output_lines.append(f"Format: {self.output_format}, Max Depth: {self.max_depth}")
            if filters:
                output_lines.append(f"Filters: {', '.join(filters)}")
            output_lines.append("=" * 80)
            output_lines.append("")
            
            # Inspect the character
            self.inspect_dataclass(character, output_lines, filters=filters)
            
            return '\n'.join(output_lines)


def inspect_character(character_name: str, output_filename: str = None, 
                     output_format: str = "text", max_depth: int = 10,
                     show_types: bool = True, show_none_values: bool = False,
                     filters: Optional[List[str]] = None):
    """
    Load and inspect a character, writing all information to a file or stdout.
    
    Args:
        character_name: Name of the character file to load
        output_filename: Output filename (optional, defaults to stdout if None)
        output_format: Output format ('text', 'json', 'summary')
        max_depth: Maximum recursion depth for nested objects
        show_types: Whether to show type information
        show_none_values: Whether to include None/empty values
        filters: Optional list of field name filters
    """
    # Load the character
    manager = CharacterManager()
    try:
        character = manager.load_character(character_name)
    except FileNotFoundError:
        print(f"Character '{character_name}' not found!")
        print("Available characters:", manager.list_saved_characters())
        return
    
    # Create inspector
    inspector = CharacterInspector(
        output_format=output_format,
        max_depth=max_depth,
        show_types=show_types,
        show_none_values=show_none_values
    )
    
    # Generate output
    output = inspector.inspect_character(character, filters=filters)
    
    # Write to file or stdout
    if output_filename:
        # Determine file extension based on format
        if not Path(output_filename).suffix:
            ext = ".json" if output_format == "json" else ".txt"
            output_filename += ext
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(output)
        
        print(f"Character inspection written to: {output_filename}")
        print(f"Format: {output_format}, Lines: {len(output.splitlines())}")
    else:
        print(output)


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description="Character Inspector - Debug and analyze RPG character objects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python character_inspector.py                           # Interactive mode
  python character_inspector.py Duskryn                   # Inspect specific character
  python character_inspector.py Duskryn -f json          # JSON output
  python character_inspector.py Duskryn -f summary       # Summary only
  python character_inspector.py Duskryn -o report.txt    # Save to file
  python character_inspector.py Duskryn --filter spell   # Filter fields containing 'spell'
  python character_inspector.py Duskryn --no-types       # Hide type information
  python character_inspector.py Duskryn --show-empty     # Include empty values
        """
    )
    
    parser.add_argument("character", nargs="?", help="Character name to inspect")
    parser.add_argument("-o", "--output", help="Output filename (default: stdout)")
    parser.add_argument("-f", "--format", choices=["text", "json", "summary"], 
                       default="text", help="Output format (default: text)")
    parser.add_argument("-d", "--max-depth", type=int, default=10,
                       help="Maximum recursion depth (default: 10)")
    parser.add_argument("--no-types", action="store_true",
                       help="Hide type information")
    parser.add_argument("--show-empty", action="store_true",
                       help="Include None/empty values")
    parser.add_argument("--filter", action="append", dest="filters",
                       help="Filter fields containing this text (can be used multiple times)")
    parser.add_argument("-l", "--list", action="store_true",
                       help="List available characters and exit")
    
    args = parser.parse_args()
    
    # List characters if requested
    if args.list:
        manager = CharacterManager()
        available_chars = manager.list_saved_characters()
        if available_chars:
            print("Available characters:")
            for i, char_name in enumerate(available_chars, 1):
                print(f"  {i}. {char_name}")
        else:
            print("No saved characters found!")
        return
    
    # Interactive mode if no character specified
    if not args.character:
        print("=== Character Inspector ===")
        
        # List available characters
        manager = CharacterManager()
        available_chars = manager.list_saved_characters()
        
        if not available_chars:
            print("No saved characters found!")
            print("Run character_manager.py first to save a character.")
            return
        
        print("Available characters:")
        for i, char_name in enumerate(available_chars, 1):
            print(f"  {i}. {char_name}")
        
        try:
            choice = input("\nEnter character number or name: ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(available_chars):
                    args.character = available_chars[idx]
                else:
                    print("Invalid choice!")
                    return
            else:
                args.character = choice
        except KeyboardInterrupt:
            print("\nExiting...")
            return
    
    # Inspect the character
    inspect_character(
        character_name=args.character,
        output_filename=args.output,
        output_format=args.format,
        max_depth=args.max_depth,
        show_types=not args.no_types,
        show_none_values=args.show_empty,
        filters=args.filters
    )


def quick_compare_characters(char1_name: str, char2_name: str, field_filter: str = None):
    """Quick comparison between two characters."""
    manager = CharacterManager()
    
    try:
        char1 = manager.load_character(char1_name)
        char2 = manager.load_character(char2_name)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    
    inspector = CharacterInspector(output_format="summary")
    
    print(f"=== Character Comparison ===")
    print(f"Character 1: {char1_name}")
    print(inspector.inspect_character(char1))
    print(f"\nCharacter 2: {char2_name}")
    print(inspector.inspect_character(char2))


def debug_character_field(character_name: str, field_path: str):
    """Debug a specific field in a character (e.g., 'spell_list.spells')."""
    manager = CharacterManager()
    
    try:
        character = manager.load_character(character_name)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    
    # Navigate to the field
    obj = character
    path_parts = field_path.split('.')
    
    try:
        for part in path_parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict) and part in obj:
                obj = obj[part]
            elif isinstance(obj, list) and part.isdigit():
                obj = obj[int(part)]
            else:
                print(f"Field '{part}' not found in path '{field_path}'")
                return
    except (IndexError, KeyError, AttributeError) as e:
        print(f"Error navigating to field '{field_path}': {e}")
        return
    
    inspector = CharacterInspector(output_format="text", show_types=True)
    
    print(f"=== Field Debug: {character_name}.{field_path} ===")
    print(f"Type: {inspector.get_type_name(obj)}")
    print(f"Value: {inspector.format_value(obj)}")


def validate_character_structure(character_name: str):
    """Validate that a character has all expected fields."""
    manager = CharacterManager()
    
    try:
        character = manager.load_character(character_name)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    
    print(f"=== Character Structure Validation: {character_name} ===")
    
    # Expected top-level fields
    expected_fields = [
        'character_base', 'ability_scores', 'combat_stats', 'background',
        'feats_and_traits', 'actions', 'inventory_list', 'spell_list',
        'objectives_and_contracts', 'last_updated'
    ]
    
    missing_fields = []
    empty_fields = []
    
    for field in expected_fields:
        if not hasattr(character, field):
            missing_fields.append(field)
        else:
            value = getattr(character, field)
            if value is None or (isinstance(value, (list, dict)) and not value):
                empty_fields.append(field)
    
    if missing_fields:
        print(f"❌ Missing fields: {', '.join(missing_fields)}")
    else:
        print("✅ All expected fields present")
    
    if empty_fields:
        print(f"⚠️  Empty fields: {', '.join(empty_fields)}")
    else:
        print("✅ No empty fields")
    
    print(f"\nCharacter summary:")
    inspector = CharacterInspector(output_format="summary")
    print(inspector.inspect_character(character))


if __name__ == "__main__":
    main()
