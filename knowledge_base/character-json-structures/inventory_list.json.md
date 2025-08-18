// 4. inventory_list.json - All equipment and items
{
  "inventory": {
    "total_weight": 0,
    "weight_unit": "lb",
    "currency": {
      "cp": 0,
      "sp": 0,
      "ep": 0,
      "gp": 0,
      "pp": 0
    },
    "equipped_items": {
      "weapons": [
        {
          "name": "",
          "type": "",
          "rarity": "",
          "requires_attunement": false,
          "attuned": false,
          "equipped": false,
          "proficient": false,
          "attack_type": "", // "melee", "ranged"
          "attack_bonus": 0,
          "damage": "",
          "damage_type": "",
          "range": "",
          "properties": [],
          "weight": 0,
          "cost": "",
          "magical_properties": {},
          "charges": {
            "current": 0,
            "maximum": 0,
            "recharge": ""
          },
          "description": "",
          "tags": []
        }
      ],
      "armor": [
        {
          "name": "",
          "type": "",
          "rarity": "",
          "equipped": false,
          "armor_class": 0,
          "armor_class_bonus": 0,
          "stealth_disadvantage": false,
          "strength_requirement": 0,
          "weight": 0,
          "cost": "",
          "magical_properties": {},
          "description": "",
          "tags": []
        }
      ],
      "wondrous_items": [
        {
          "name": "",
          "type": "wondrous item",
          "rarity": "",
          "requires_attunement": false,
          "attuned": false,
          "equipped": false,
          "weight": 0,
          "cost": "",
          "magical_properties": {},
          "charges": {
            "current": 0,
            "maximum": 0,
            "recharge": ""
          },
          "description": "",
          "tags": []
        }
      ],
      "consumables": [
        // Can be either a string for simple items or an object for complex items
        "Rations (1 day)",
        {
          "name": "Potion of Healing",
          "type": "consumable",
          "rarity": "common",
          "quantity": 1,
          "weight": 0.5,
          "cost": "50 gp",
          "uses": {
            "current": 1,
            "maximum": 1
          },
          "description": "Heals 2d4+2 hit points when consumed",
          "tags": ["consumable", "potion", "magic"]
        }
      ],
      "tools": [
        // Can be either a string for simple tools or an object for complex tools
        "Thieves' Tools",
        {
          "name": "Alchemist's Supplies",
          "type": "tool",
          "proficient": true,
          "weight": 8,
          "cost": "50 gp",
          "description": "Used to craft potions, alchemical items, and perform related checks",
          "tags": ["tool", "artisan"]
        }
      ],
      "containers": [
        // Can be either a string for simple containers or an object for magical containers
        "Backpack",
        {
          "name": "Bag of Holding",
          "type": "container",
          "rarity": "uncommon",
          "capacity": "500 lbs, 64 cubic feet",
          "weight": 15,
          "cost": "4000 gp",
          "magical_properties": {
            "description": "This bag can hold up to 500 lbs. not exceeding a volume of 64 cubic feet"
          },
          "description": "A magical bag that can hold much more than its outside dimensions suggest",
          "tags": ["container", "magic", "wondrous"]
        }
      ]
    },
    "unequipped_items": [
      // Can be either strings for simple items or objects for complex items
      "Bedroll",
      "Torch (5)",
      {
        "name": "Studded Leather +1",
        "type": "light armor",
        "rarity": "rare",
        "armor_class": 12,
        "armor_class_bonus": 1,
        "weight": 13,
        "cost": "1450 gp",
        "description": "Light armor with magical enhancement (+1 AC)",
        "tags": ["armor", "light", "magic"]
      }
    ],
    "stored_items": {} // For items in specific containers
  }
}