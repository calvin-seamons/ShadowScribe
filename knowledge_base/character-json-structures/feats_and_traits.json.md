// 2. feats_and_traits.json - All features, traits, and feats
{
  "features_and_traits": {
    "class_features": {
      // Dynamic object for any number of classes
      "class_name": {
        "level": 0,
        "subclass": "",
        "features": [
          {
            "name": "",
            "source": "",
            "level_gained": 0,
            "description": "",
            "action_type": "", // "action", "bonus_action", "reaction", "no_action", "passive"
            "uses": {
              "current": 0,
              "maximum": 0,
              "reset": "" // "short_rest", "long_rest", "dawn", etc.
            },
            "range": "",
            "duration": "",
            "effect": "",
            "save": {
              "type": "",
              "dc": 0
            },
            "damage": {},
            "special": [],
            "tags": []
          }
        ]
      }
    },
    "species_traits": {
      "species": "",
      "subspecies": "",
      "traits": [
        {
          "name": "",
          "source": "",
          "description": "",
          "effect": "",
          "passive": false,
          "tags": []
        }
      ]
    },
    "feats": [
      {
        "name": "",
        "source": "",
        "prerequisite": "",
        "description": "",
        "ability_increase": {
          "ability": "",
          "amount": 0
        },
        "effects": [],
        "spells": [],
        "tags": []
      }
    ],
    "custom_features": [
      // For homebrew or special features
      {
        "name": "",
        "type": "",
        "description": "",
        "effects": []
      }
    ]
  },
  "metadata": {
    "version": "",
    "last_updated": "",
    "notes": []
  }
}