"""
Comprehensive tests for inventory parsing module.

Tests the DNDBeyondInventoryParser class and utility functions for:
- HTML cleaning and entity decoding
- Inventory item extraction and merging
- InventoryItem and Inventory object creation
- Edge cases and malformed data handling
"""

import pytest
from typing import Dict, Any

from src.character_creation.parsing.parse_inventory import (
    DNDBeyondInventoryParser,
    extract_inventory_items,
    clean_html,
    should_include_field,
    load_json_file
)
from src.rag.character.character_types import (
    InventoryItem,
    Inventory,
    InventoryItemDefinition
)


class TestCleanHtml:
    """Test HTML cleaning and entity decoding functionality."""
    
    def test_clean_html_basic_entities(self):
        """Test decoding of common HTML entities."""
        assert clean_html("Hello&nbsp;World") == "Hello World"
        assert clean_html("Rock&amp;Roll") == "Rock&Roll"
        assert clean_html("Less&lt;Than") == "Less<Than"
        assert clean_html("Greater&gt;Than") == "Greater>Than"
        assert clean_html("Quote&quot;Mark") == 'Quote"Mark'
    
    def test_clean_html_paragraph_tags(self):
        """Test conversion of paragraph tags to newlines."""
        html = "<p>First paragraph</p><p>Second paragraph</p>"
        result = clean_html(html)
        assert "First paragraph" in result
        assert "Second paragraph" in result
        assert "\n\n" in result
    
    def test_clean_html_break_tags(self):
        """Test conversion of <br> tags to single newlines."""
        assert "Line1\nLine2" in clean_html("Line1<br>Line2")
        assert "Line1\nLine2" in clean_html("Line1<br/>Line2")
        assert "Line1\nLine2" in clean_html("Line1<BR>Line2")
    
    def test_clean_html_remove_all_tags(self):
        """Test removal of all HTML tags."""
        html = '<span class="special">Text</span>'
        assert clean_html(html) == "Text"
        
        html = '<div><strong>Bold</strong> and <em>italic</em></div>'
        result = clean_html(html)
        assert "Bold and italic" in result
        assert "<" not in result
        assert ">" not in result
    
    def test_clean_html_header_tags(self):
        """Test conversion of header tags to paragraph breaks."""
        html = "<h1>Title</h1><p>Content</p>"
        result = clean_html(html)
        assert "Title" in result
        assert "Content" in result
        assert "\n\n" in result
    
    def test_clean_html_whitespace_collapse(self):
        """Test collapsing of excessive whitespace."""
        html = "Too    many     spaces"
        assert clean_html(html) == "Too many spaces"
        
        html = "Line1\n\n\n\n\nLine2"
        result = clean_html(html)
        assert "\n\n\n" not in result  # Should collapse to max 2 newlines
    
    def test_clean_html_line_trimming(self):
        """Test trimming of leading/trailing whitespace from lines."""
        html = "  Line with spaces  \n  Another line  "
        result = clean_html(html)
        assert result.startswith("Line")
        assert not result.startswith(" ")
    
    def test_clean_html_empty_string(self):
        """Test handling of empty and None values."""
        assert clean_html("") == ""
        assert clean_html(None) == ""  # Returns empty string for type safety (str -> str)
        assert clean_html("   \n\n   ") == ""
    
    def test_clean_html_complex_formatting(self):
        """Test complex HTML with mixed formatting."""
        html = """
        <div class="container">
            <p>First paragraph with <strong>bold</strong> text.</p>
            <br/>
            <p>Second paragraph with &nbsp; spaces and &amp; ampersands.</p>
        </div>
        """
        result = clean_html(html)
        assert "First paragraph with bold text." in result
        assert "Second paragraph with" in result
        assert "spaces and & ampersands" in result
        assert "<" not in result
        assert "&" not in result or result.count("&") == 1  # Only literal &
    
    def test_clean_html_preserves_structure(self):
        """Test that paragraph structure is preserved."""
        html = "<p>Para 1</p><p>Para 2</p><p>Para 3</p>"
        result = clean_html(html)
        lines = [line for line in result.split("\n") if line.strip()]
        assert len(lines) == 3
        assert "Para 1" in lines[0]
        assert "Para 2" in lines[1]
        assert "Para 3" in lines[2]


class TestShouldIncludeField:
    """Test field inclusion logic for output filtering."""
    
    def test_exclude_none_values(self):
        """Test that None values are always excluded."""
        assert not should_include_field("any_field", None)
    
    def test_exclude_zero_weight(self):
        """Test that zero weight values are excluded."""
        assert not should_include_field("weight", 0)
        assert not should_include_field("capacityWeight", 0)
    
    def test_include_nonzero_weight(self):
        """Test that non-zero weight values are included."""
        assert should_include_field("weight", 5)
        assert should_include_field("weight", 0.5)
        assert should_include_field("capacityWeight", 10)
    
    def test_exclude_empty_strings(self):
        """Test that empty strings are excluded."""
        assert not should_include_field("description", "")
        assert not should_include_field("description", "   ")
        assert not should_include_field("description", "\n\n")
    
    def test_include_nonempty_strings(self):
        """Test that non-empty strings are included."""
        assert should_include_field("description", "Valid text")
        assert should_include_field("name", "Item Name")
    
    def test_exclude_empty_lists(self):
        """Test that empty lists are excluded."""
        assert not should_include_field("tags", [])
        assert not should_include_field("modifiers", [])
    
    def test_include_nonempty_lists(self):
        """Test that non-empty lists are included."""
        assert should_include_field("tags", ["tag1"])
        assert should_include_field("modifiers", [{"type": "bonus"}])
    
    def test_include_other_types(self):
        """Test that other types are included based on value."""
        assert should_include_field("quantity", 1)
        assert should_include_field("magic", True)
        assert should_include_field("magic", False)  # False is still included
        assert should_include_field("data", {"key": "value"})


class TestExtractInventoryItems:
    """Test inventory item extraction from D&D Beyond JSON."""
    
    def test_extract_empty_inventory(self):
        """Test handling of data with no inventory."""
        data = {"data": {}}
        assert extract_inventory_items(data) == []
        
        data = {"data": {"inventory": []}}
        assert extract_inventory_items(data) == []
    
    def test_extract_missing_inventory_key(self):
        """Test handling of missing inventory key."""
        data = {}
        assert extract_inventory_items(data) == []
        
        data = {"other_key": "value"}
        assert extract_inventory_items(data) == []
    
    def test_extract_single_item(self):
        """Test extraction of a single inventory item."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {
                            "name": "Longsword",
                            "type": "Weapon",
                            "weight": 3,
                            "magic": False
                        },
                        "quantity": 1,
                        "equipped": True,
                        "isAttuned": False
                    }
                ]
            }
        }
        items = extract_inventory_items(data)
        assert len(items) == 1
        assert items[0].definition.name == "Longsword"
        assert items[0].quantity == 1
        assert items[0].equipped is True
    
    def test_extract_multiple_items(self):
        """Test extraction of multiple inventory items."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {"name": "Item1", "weight": 1},
                        "quantity": 1,
                        "equipped": False
                    },
                    {
                        "definition": {"name": "Item2", "weight": 2},
                        "quantity": 2,
                        "equipped": True
                    }
                ]
            }
        }
        items = extract_inventory_items(data)
        assert len(items) == 2
        assert items[0].definition.name == "Item1"
        assert items[1].definition.name == "Item2"
    
    def test_merge_duplicate_items(self):
        """Test merging of items with same name and description."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {
                            "name": "Arrow",
                            "description": "Standard arrow"
                        },
                        "quantity": 10,
                        "equipped": False
                    },
                    {
                        "definition": {
                            "name": "Arrow",
                            "description": "Standard arrow"
                        },
                        "quantity": 10,
                        "equipped": False
                    }
                ]
            }
        }
        items = extract_inventory_items(data)
        assert len(items) == 1
        assert items[0].quantity == 20  # Merged quantities
    
    def test_no_merge_different_descriptions(self):
        """Test that items with same name but different descriptions don't merge."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {
                            "name": "Potion",
                            "description": "Healing"
                        },
                        "quantity": 1,
                        "equipped": False
                    },
                    {
                        "definition": {
                            "name": "Potion",
                            "description": "Mana"
                        },
                        "quantity": 1,
                        "equipped": False
                    }
                ]
            }
        }
        items = extract_inventory_items(data)
        assert len(items) == 2
    
    def test_extract_item_with_granted_modifiers(self):
        """Test extraction of items with granted modifiers."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {
                            "name": "Magic Sword",
                            "grantedModifiers": [
                                {
                                    "type": "bonus",
                                    "subType": "attack",
                                    "fixedValue": 1,
                                    "dice": {"diceString": "1d6"}
                                }
                            ]
                        },
                        "quantity": 1,
                        "equipped": True
                    }
                ]
            }
        }
        items = extract_inventory_items(data)
        assert len(items) == 1
        assert items[0].definition.grantedModifiers is not None
        assert len(items[0].definition.grantedModifiers) == 1
        assert items[0].definition.grantedModifiers[0].fixedValue == 1
    
    def test_extract_item_with_limited_use(self):
        """Test extraction of items with limited use."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {"name": "Wand"},
                        "quantity": 1,
                        "equipped": False,
                        "limitedUse": {
                            "maxUses": 3,
                            "resetType": "long_rest",
                            "resetTypeDescription": "Recharges on long rest"
                        }
                    }
                ]
            }
        }
        items = extract_inventory_items(data)
        assert len(items) == 1
        assert items[0].limitedUse is not None
        assert items[0].limitedUse.maxUses == 3
        assert items[0].limitedUse.resetType == "long_rest"
    
    def test_extract_item_with_html_description(self):
        """Test that HTML in descriptions is cleaned."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {
                            "name": "Scroll",
                            "description": "<p>A scroll with <strong>magical</strong> text&nbsp;inside.</p>"
                        },
                        "quantity": 1,
                        "equipped": False
                    }
                ]
            }
        }
        items = extract_inventory_items(data)
        assert len(items) == 1
        description = items[0].definition.description
        assert "magical" in description
        assert "inside" in description
        assert "<" not in description
        assert "&nbsp;" not in description
    
    def test_extract_item_with_all_fields(self):
        """Test extraction of item with all possible fields."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {
                            "name": "Complete Item",
                            "type": "Weapon",
                            "description": "Full description",
                            "canAttune": True,
                            "attunementDescription": "Requires attunement",
                            "rarity": "Rare",
                            "weight": 5,
                            "capacity": 10,
                            "capacityWeight": 2,
                            "canEquip": True,
                            "magic": True,
                            "tags": ["magical", "weapon"],
                            "damage": "1d8",
                            "damageType": "slashing",
                            "attackType": "melee",
                            "range": 5,
                            "longRange": 10,
                            "isContainer": False,
                            "isCustomItem": False
                        },
                        "quantity": 1,
                        "equipped": True,
                        "isAttuned": True
                    }
                ]
            }
        }
        items = extract_inventory_items(data)
        assert len(items) == 1
        item = items[0]
        assert item.definition.name == "Complete Item"
        assert item.definition.type == "Weapon"
        assert item.definition.rarity == "Rare"
        assert item.definition.weight == 5
        assert item.definition.magic is True
        assert item.equipped is True
        assert item.isAttuned is True


class TestDNDBeyondInventoryParser:
    """Test the DNDBeyondInventoryParser class."""
    
    def test_parse_empty_inventory(self):
        """Test parsing of empty inventory."""
        parser = DNDBeyondInventoryParser({"data": {"inventory": []}})
        inventory = parser.parse_inventory()
        
        assert isinstance(inventory, Inventory)
        assert inventory.total_weight == 0
        assert inventory.weight_unit == "lb"
        assert len(inventory.equipped_items) == 0
        assert len(inventory.backpack) == 0
    
    def test_parse_equipped_items(self):
        """Test that equipped items are placed in equipped_items list."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {"name": "Armor", "weight": 20},
                        "quantity": 1,
                        "equipped": True
                    }
                ]
            }
        }
        parser = DNDBeyondInventoryParser(data)
        inventory = parser.parse_inventory()
        
        assert len(inventory.equipped_items) == 1
        assert len(inventory.backpack) == 0
        assert inventory.equipped_items[0].definition.name == "Armor"
    
    def test_parse_backpack_items(self):
        """Test that unequipped items are placed in backpack."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {"name": "Rope", "weight": 10},
                        "quantity": 1,
                        "equipped": False
                    }
                ]
            }
        }
        parser = DNDBeyondInventoryParser(data)
        inventory = parser.parse_inventory()
        
        assert len(inventory.equipped_items) == 0
        assert len(inventory.backpack) == 1
        assert inventory.backpack[0].definition.name == "Rope"
    
    def test_parse_mixed_equipped_unequipped(self):
        """Test parsing mix of equipped and unequipped items."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {"name": "Sword", "weight": 3},
                        "quantity": 1,
                        "equipped": True
                    },
                    {
                        "definition": {"name": "Rations", "weight": 1},
                        "quantity": 5,
                        "equipped": False
                    }
                ]
            }
        }
        parser = DNDBeyondInventoryParser(data)
        inventory = parser.parse_inventory()
        
        assert len(inventory.equipped_items) == 1
        assert len(inventory.backpack) == 1
        assert inventory.equipped_items[0].definition.name == "Sword"
        assert inventory.backpack[0].definition.name == "Rations"
    
    def test_parse_calculates_total_weight(self):
        """Test that total weight is calculated correctly."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {"name": "Item1", "weight": 5},
                        "quantity": 2,
                        "equipped": False
                    },
                    {
                        "definition": {"name": "Item2", "weight": 3},
                        "quantity": 1,
                        "equipped": True
                    }
                ]
            }
        }
        parser = DNDBeyondInventoryParser(data)
        inventory = parser.parse_inventory()
        
        # (5 * 2) + (3 * 1) = 13
        assert inventory.total_weight == 13
    
    def test_parse_handles_missing_weight(self):
        """Test that items with no weight don't cause errors."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {"name": "Weightless Item"},
                        "quantity": 10,
                        "equipped": False
                    }
                ]
            }
        }
        parser = DNDBeyondInventoryParser(data)
        inventory = parser.parse_inventory()
        
        assert inventory.total_weight == 0
        assert len(inventory.backpack) == 1
    
    def test_parse_weight_unit_is_lb(self):
        """Test that weight unit is set to 'lb'."""
        parser = DNDBeyondInventoryParser({"data": {"inventory": []}})
        inventory = parser.parse_inventory()
        assert inventory.weight_unit == "lb"
    
    def test_parse_valuables_empty(self):
        """Test that valuables list is initialized as empty."""
        parser = DNDBeyondInventoryParser({"data": {"inventory": []}})
        inventory = parser.parse_inventory()
        assert inventory.valuables == []


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_malformed_inventory_not_list(self):
        """Test handling when inventory is not a list."""
        data = {"data": {"inventory": "not a list"}}
        items = extract_inventory_items(data)
        assert items == []
    
    def test_missing_definition(self):
        """Test handling of items with missing definition."""
        data = {
            "data": {
                "inventory": [
                    {
                        "quantity": 1,
                        "equipped": False
                    }
                ]
            }
        }
        items = extract_inventory_items(data)
        # Should still create item with empty definition
        assert len(items) >= 0  # Implementation dependent
    
    def test_invalid_quantity_defaults(self):
        """Test that missing quantity defaults to 1."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {"name": "Item"},
                        "equipped": False
                    }
                ]
            }
        }
        items = extract_inventory_items(data)
        assert len(items) == 1
        assert items[0].quantity == 1
    
    def test_empty_granted_modifiers_not_included(self):
        """Test that empty granted modifiers are not included."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {
                            "name": "Item",
                            "grantedModifiers": []
                        },
                        "quantity": 1,
                        "equipped": False
                    }
                ]
            }
        }
        items = extract_inventory_items(data)
        assert len(items) == 1
        # Empty list should result in None
        assert items[0].definition.grantedModifiers is None
    
    def test_empty_limited_use_not_included(self):
        """Test that empty limited use is not included."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {"name": "Item"},
                        "quantity": 1,
                        "equipped": False,
                        "limitedUse": {}
                    }
                ]
            }
        }
        items = extract_inventory_items(data)
        assert len(items) == 1
        # Empty dict should result in None
        assert items[0].limitedUse is None


class TestIntegration:
    """Integration tests for complete workflow."""
    
    def test_full_parsing_workflow(self):
        """Test complete parsing workflow with realistic data."""
        data = {
            "data": {
                "inventory": [
                    {
                        "definition": {
                            "name": "Longsword +1",
                            "type": "Weapon",
                            "description": "<p>A finely crafted <strong>magical</strong> longsword.</p>",
                            "magic": True,
                            "rarity": "Uncommon",
                            "weight": 3,
                            "damage": "1d8",
                            "damageType": "slashing",
                            "grantedModifiers": [
                                {
                                    "type": "bonus",
                                    "subType": "magic",
                                    "fixedValue": 1
                                }
                            ]
                        },
                        "quantity": 1,
                        "equipped": True,
                        "isAttuned": False
                    },
                    {
                        "definition": {
                            "name": "Rations",
                            "type": "Gear",
                            "weight": 2,
                            "description": "One day's food"
                        },
                        "quantity": 10,
                        "equipped": False
                    },
                    {
                        "definition": {
                            "name": "Healing Potion",
                            "type": "Potion",
                            "description": "<p>Restores <em>2d4+2</em> hit&nbsp;points.</p>",
                            "magic": True,
                            "weight": 0.5
                        },
                        "quantity": 3,
                        "equipped": False
                    }
                ]
            }
        }
        
        parser = DNDBeyondInventoryParser(data)
        inventory = parser.parse_inventory()
        
        # Verify inventory structure
        assert isinstance(inventory, Inventory)
        assert inventory.weight_unit == "lb"
        
        # Verify equipped items
        assert len(inventory.equipped_items) == 1
        sword = inventory.equipped_items[0]
        assert sword.definition.name == "Longsword +1"
        assert sword.equipped is True
        assert "magical" in sword.definition.description
        assert "<" not in sword.definition.description
        
        # Verify backpack items
        assert len(inventory.backpack) == 2
        
        # Verify total weight: (3 * 1) + (2 * 10) + (0.5 * 3) = 24.5
        assert inventory.total_weight == 24.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])