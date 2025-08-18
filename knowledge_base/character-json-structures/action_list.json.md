// 5. action_list.json - Combat actions and abilities
{
  "character_actions": {
    "attacks_per_action": 0,
    "proficiency_bonus": 0,
    "action_economy": {
      "actions": [
        {
          "name": "",
          "type": "", // "attack", "spell", "ability", "item"
          "description": "",
          "uses_per_turn": 0,
          "uses": {
            "current": 0,
            "maximum": 0,
            "reset": ""
          },
          "range": "",
          "attack_bonus": 0,
          "damage": "",
          "damage_type": "",
          "save": {
            "type": "",
            "dc": 0
          },
          "effect": "",
          "requirements": "",
          "tags": []
        }
      ],
      "bonus_actions": [],
      "reactions": [],
      "movement": {
        "speed": 0,
        "climb": 0,
        "swim": 0,
        "fly": 0,
        "special_movement": []
      },
      "other_actions": [], // Free actions, special actions
      "legendary_actions": {
        "available": false,
        "points": 0,
        "actions": []
      },
      "lair_actions": []
    },
    "combat_modifiers": {
      "attack_bonuses": {},
      "damage_bonuses": {},
      "critical_range": 20,
      "special_conditions": []
    }
  }
}