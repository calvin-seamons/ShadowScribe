// 3. spell_list.json - All spells organized by class
{
  "spellcasting": {
    // Dynamic object for any spellcasting class
    "class_name": {
      "ability": "",
      "spell_save_dc": 0,
      "spell_attack_bonus": 0,
      "focus": "",
      "ritual_casting": false,
      "spellcasting_type": "", // "prepared", "known", "pact", etc.
      "spells_known": 0,
      "spells_prepared": 0,
      "spell_slots": {
        "1st": { "current": 0, "maximum": 0 },
        "2nd": { "current": 0, "maximum": 0 },
        "3rd": { "current": 0, "maximum": 0 },
        "4th": { "current": 0, "maximum": 0 },
        "5th": { "current": 0, "maximum": 0 },
        "6th": { "current": 0, "maximum": 0 },
        "7th": { "current": 0, "maximum": 0 },
        "8th": { "current": 0, "maximum": 0 },
        "9th": { "current": 0, "maximum": 0 },
        "pact": { "level": 0, "current": 0, "maximum": 0 }
      },
      "spells": {
        "cantrips": [
          {
            "name": "",
            "prepared": false,
            "school": "",
            "casting_time": "",
            "range": "",
            "components": {
              "verbal": false,
              "somatic": false,
              "material": ""
            },
            "duration": "",
            "concentration": false,
            "ritual": false,
            "description": "",
            "source": "",
            "tags": []
          }
        ],
        "1st_level": [],
        "2nd_level": [],
        "3rd_level": [],
        "4th_level": [],
        "5th_level": [],
        "6th_level": [],
        "7th_level": [],
        "8th_level": [],
        "9th_level": []
      }
    }
  },
  "innate_spellcasting": {
    // For racial or feat-based spells
    "source": "",
    "ability": "",
    "spell_save_dc": 0,
    "spells": []
  },
  "metadata": {
    "version": "",
    "last_updated": "",
    "notes": []
  }
}