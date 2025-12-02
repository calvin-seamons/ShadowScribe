"""
Multi-Tool Query Templates

Templates for generating synthetic training data that requires 2-3 tools.
These represent compound questions that users commonly ask.

Target: 70% of dataset should be multi-tool queries
- 50% 2-tool queries (5,000 samples)
- 20% 3-tool queries (2,000 samples)

Tool combinations:
- character_data + rulebook (most common - questions about character + rules)
- character_data + session_notes (character info + what happened)
- session_notes + rulebook (what happened + rules clarification)
- character_data + session_notes + rulebook (all three)
"""

# =============================================================================
# CHARACTER_DATA + RULEBOOK (2-tool)
# Most common: "What's my X and how does Y work?"
# =============================================================================

CHARACTER_RULEBOOK_TEMPLATES = [
    # Combat stats + spell/rule mechanics
    {
        "template": "What's my AC and how does {spell} affect it?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "spell_details"},
        "slots": {"spell": "spell"}
    },
    {
        "template": "What's my attack bonus and how do critical hits work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What's my HP and how does {spell} heal?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "spell_details"},
        "slots": {"spell": "spell"}
    },
    {
        "template": "What's my initiative and how does surprise work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What's my {ability} save and what triggers it?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "saving_throws"},
        "slots": {"ability": "ability"}
    },

    # Full character + rules
    {
        "template": "Give me my complete character sheet and explain how {feature} works",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "full_character", "rulebook": "describe_entity"},
        "slots": {"feature": "feature"}
    },
    {
        "template": "Show me everything about my character and how my class abilities function",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "full_character", "rulebook": "describe_entity"},
        "slots": {}
    },
    {
        "template": "What's my full character breakdown and what are the rules for my race?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "full_character", "rulebook": "describe_entity"},
        "slots": {}
    },
    {
        "template": "Display my entire character and explain multiclassing rules",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "full_character", "rulebook": "multiclass_rules"},
        "slots": {}
    },
    {
        "template": "I need my complete character info and the rules for character creation",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "full_character", "rulebook": "character_creation"},
        "slots": {}
    },

    # Character creation rules
    {
        "template": "What race am I and what are the rules for creating a {race} character?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "character_creation"},
        "slots": {"race": "race"}
    },
    {
        "template": "What class am I and how do I build a {class_name} from scratch?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "character_creation"},
        "slots": {"class_name": "class"}
    },
    {
        "template": "What's my background and what are the character creation options for it?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "character_creation"},
        "slots": {}
    },
    {
        "template": "What ability scores do I have and how does point buy work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "character_creation"},
        "slots": {}
    },
    {
        "template": "What level am I and what's the starting equipment for my class?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "character_creation"},
        "slots": {}
    },

    # Class spell access
    {
        "template": "What class am I and what spells can {class_name}s learn?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "class_spell_access"},
        "slots": {"class_name": "class"}
    },
    {
        "template": "What spells do I have and what's the full {class_name} spell list?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "class_spell_access"},
        "slots": {"class_name": "class"}
    },
    {
        "template": "What cantrips do I know and what other cantrips can my class learn?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "class_spell_access"},
        "slots": {}
    },
    {
        "template": "What's my spell save DC and which spells are available to my subclass?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "class_spell_access"},
        "slots": {}
    },
    {
        "template": "What level spells can I cast and what {level} level spells are on my class list?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "class_spell_access"},
        "slots": {"level": "level"}
    },

    # Compare entities
    {
        "template": "What class am I and how does it compare to {class_name}?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "compare_entities"},
        "slots": {"class_name": "class"}
    },
    {
        "template": "What race am I and what's the difference between my race and {race}?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "compare_entities"},
        "slots": {"race": "race"}
    },
    {
        "template": "What weapons do I have and how does {weapon} compare to other options?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "inventory_info", "rulebook": "compare_entities"},
        "slots": {"weapon": "weapon"}
    },
    {
        "template": "What spells do I have prepared and how does {spell} compare to similar spells?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "compare_entities"},
        "slots": {"spell": "spell"}
    },
    {
        "template": "What's my subclass and how does it differ from other {class_name} subclasses?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "compare_entities"},
        "slots": {"class_name": "class"}
    },

    # Find by criteria
    {
        "template": "What spells do I have and what spells deal {damage_type} damage?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "find_by_criteria"},
        "slots": {"damage_type": "damage_type"}
    },
    {
        "template": "What's my class and what feats require {ability} 13 or higher?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "find_by_criteria"},
        "slots": {"ability": "ability"}
    },
    {
        "template": "What level am I and what monsters are appropriate for my level?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "find_by_criteria"},
        "slots": {}
    },
    {
        "template": "What spell slots do I have and what spells can be cast as rituals?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "find_by_criteria"},
        "slots": {}
    },
    {
        "template": "How much gold do I have and what magic items can I afford?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "inventory_info", "rulebook": "find_by_criteria"},
        "slots": {}
    },

    # Interaction rules
    {
        "template": "What spells do I have and can I combine {spell} with {spell}?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "interaction_rules"},
        "slots": {"spell": "spell"}
    },
    {
        "template": "What class features do I have and how do they interact with each other?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "interaction_rules"},
        "slots": {}
    },
    {
        "template": "What concentration spells am I running and can I use other abilities while concentrating?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "interaction_rules"},
        "slots": {}
    },
    {
        "template": "What's my rage ability and how does it interact with spellcasting?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "interaction_rules"},
        "slots": {}
    },
    {
        "template": "What reactions do I have and how do they stack with other effects?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "interaction_rules"},
        "slots": {}
    },

    # Tactical usage
    {
        "template": "What abilities do I have and how should I use them tactically?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "tactical_usage"},
        "slots": {}
    },
    {
        "template": "What spells do I have prepared and what's the best way to use {spell}?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "tactical_usage"},
        "slots": {"spell": "spell"}
    },
    {
        "template": "What's my combat role and how can I be most effective in battle?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "tactical_usage"},
        "slots": {}
    },
    {
        "template": "What class features do I have and when is the best time to use them?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "tactical_usage"},
        "slots": {}
    },
    {
        "template": "What weapons do I have and what's the optimal fighting style for them?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "inventory_info", "rulebook": "tactical_usage"},
        "slots": {}
    },

    # Creature abilities
    {
        "template": "What's my attack bonus and what special abilities do {creature}s have?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "creature_abilities"},
        "slots": {"creature": "creature"}
    },
    {
        "template": "What resistances do I have and what abilities can bypass them?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "creature_abilities"},
        "slots": {}
    },
    {
        "template": "What's my AC and how do {creature} abilities affect it?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "creature_abilities"},
        "slots": {"creature": "creature"}
    },
    {
        "template": "What saves do I have and what creature abilities target them?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "creature_abilities"},
        "slots": {}
    },
    {
        "template": "What immunities do I have and what creatures can affect me anyway?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "creature_abilities"},
        "slots": {}
    },

    # Subclass features
    {
        "template": "What's my subclass and what features do I get from it?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "subclass_features"},
        "slots": {}
    },
    {
        "template": "What level am I and what subclass abilities do I unlock next?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "subclass_features"},
        "slots": {}
    },
    {
        "template": "What subclass abilities do I have and how do they scale?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "subclass_features"},
        "slots": {}
    },
    {
        "template": "What's my archetype and what unique features does it provide?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "subclass_features"},
        "slots": {}
    },
    {
        "template": "What domain/oath/school am I and what special abilities come with it?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "subclass_features"},
        "slots": {}
    },

    # Downtime activities
    {
        "template": "How much gold do I have and what downtime activities can I afford?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "inventory_info", "rulebook": "downtime_activities"},
        "slots": {}
    },
    {
        "template": "What skills am I proficient in and what downtime uses them?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "downtime_activities"},
        "slots": {}
    },
    {
        "template": "What's my background and what downtime activities fit it?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "downtime_activities"},
        "slots": {}
    },
    {
        "template": "What tools am I proficient with and can I use them during downtime?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "downtime_activities"},
        "slots": {}
    },
    {
        "template": "What's my spellcasting ability and can I craft magic items during downtime?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "downtime_activities"},
        "slots": {}
    },

    # Prerequisite check
    {
        "template": "What are my ability scores and do I meet the prerequisites for {feat}?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "prerequisite_check"},
        "slots": {"feat": "feat"}
    },
    {
        "template": "What class am I and can I take levels in {class_name}?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "prerequisite_check"},
        "slots": {"class_name": "class"}
    },
    {
        "template": "What level am I and do I meet the requirements for {feat}?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "prerequisite_check"},
        "slots": {"feat": "feat"}
    },
    {
        "template": "What's my spellcasting ability and can I take the Ritual Caster feat?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "prerequisite_check"},
        "slots": {}
    },
    {
        "template": "What proficiencies do I have and what are the prerequisites for {class_name}?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "prerequisite_check"},
        "slots": {"class_name": "class"}
    },

    # Environmental rules
    {
        "template": "Do I have darkvision and how does magical darkness work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "environmental_rules"},
        "slots": {}
    },
    {
        "template": "What's my Constitution and how does extreme cold affect me?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "environmental_rules"},
        "slots": {}
    },
    {
        "template": "What movement speed do I have and how does difficult terrain affect it?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "environmental_rules"},
        "slots": {}
    },
    {
        "template": "What senses do I have and how does heavy obscurement work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "environmental_rules"},
        "slots": {}
    },
    {
        "template": "Can I breathe underwater and what are the rules for underwater combat?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "environmental_rules"},
        "slots": {}
    },

    # Damage types
    {
        "template": "What resistances do I have and what deals {damage_type} damage?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "damage_types"},
        "slots": {"damage_type": "damage_type"}
    },
    {
        "template": "What weapons do I have and what damage types do they deal?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "inventory_info", "rulebook": "damage_types"},
        "slots": {}
    },
    {
        "template": "What spells do I have and which ones deal {damage_type} damage?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "damage_types"},
        "slots": {"damage_type": "damage_type"}
    },
    {
        "template": "What immunities do I have and how do damage immunities work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "damage_types"},
        "slots": {}
    },
    {
        "template": "What vulnerabilities do I have and how does vulnerability work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "damage_types"},
        "slots": {}
    },

    # Legendary mechanics
    {
        "template": "What's my CR equivalent and how do legendary actions work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "legendary_mechanics"},
        "slots": {}
    },
    {
        "template": "What level am I and how do lair actions affect combat?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "legendary_mechanics"},
        "slots": {}
    },
    {
        "template": "What saves do I have and how do legendary resistances work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "legendary_mechanics"},
        "slots": {}
    },
    {
        "template": "What attacks can I make and how do I fight creatures with legendary actions?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "legendary_mechanics"},
        "slots": {}
    },
    {
        "template": "What's my initiative and when do legendary actions occur in combat?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "legendary_mechanics"},
        "slots": {}
    },

    # Abilities + rule explanations
    {
        "template": "What's my {skill} bonus and when do I use it?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "skill_usage"},
        "slots": {"skill": "skill"}
    },
    {
        "template": "Am I proficient in {skill} and what can I do with it?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "skill_usage"},
        "slots": {"skill": "skill"}
    },
    {
        "template": "What languages do I know and how does language work in D&D?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "Do I have darkvision and how does it work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What's my passive perception and how is it calculated?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "calculate_values"},
        "slots": {}
    },

    # Magic + spell rules
    {
        "template": "Can I cast {spell} and what does it do?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "spell_details"},
        "slots": {"spell": "spell"}
    },
    {
        "template": "What's my spell save DC and how is it calculated?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "calculate_values"},
        "slots": {}
    },
    {
        "template": "How many spell slots do I have and how do they recover?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "rest_mechanics"},
        "slots": {}
    },
    {
        "template": "What cantrips do I know and how does {spell} scale?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "spell_details"},
        "slots": {"spell": "spell"}
    },
    {
        "template": "Do I have {spell} prepared and what are its components?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "spell_details"},
        "slots": {"spell": "spell"}
    },

    # Inventory + equipment rules
    {
        "template": "What weapons do I have and what's the damage for {weapon}?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "inventory_info", "rulebook": "equipment_properties"},
        "slots": {"weapon": "weapon"}
    },
    {
        "template": "What armor am I wearing and how does AC calculation work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "inventory_info", "rulebook": "calculate_values"},
        "slots": {}
    },
    {
        "template": "Do I have a {item} and how does it work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "inventory_info", "rulebook": "magic_item_usage"},
        "slots": {"item": "magic_item"}
    },
    {
        "template": "What magic items do I have and how does attunement work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "inventory_info", "rulebook": "magic_item_usage"},
        "slots": {}
    },
    {
        "template": "How much gold do I have and what can I buy with it?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "inventory_info", "rulebook": "cost_lookup"},
        "slots": {}
    },

    # Character basics + class features
    {
        "template": "What class am I and what features do I get at level {level}?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "level_progression"},
        "slots": {"level": "level"}
    },
    {
        "template": "What level am I and when do I get Extra Attack?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "level_progression"},
        "slots": {}
    },
    {
        "template": "What race am I and what racial traits do I get?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "describe_entity"},
        "slots": {}
    },
    {
        "template": "What's my subclass and what features does it give?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "subclass_features"},
        "slots": {}
    },
    {
        "template": "What's my background and what feature does it provide?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "describe_entity"},
        "slots": {}
    },

    # Class features + how they work
    {
        "template": "Do I have {feature} and how does it work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "describe_entity"},
        "slots": {"feature": "feature"}
    },
    {
        "template": "What class features do I have and how does {feature} work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "describe_entity"},
        "slots": {"feature": "feature"}
    },
    {
        "template": "What feats do I have and what are the prerequisites for {feat}?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "prerequisite_check"},
        "slots": {"feat": "feat"}
    },

    # Character + monster comparison
    {
        "template": "What's my AC compared to a {creature}'s attack bonus?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "monster_stats"},
        "slots": {"creature": "creature"}
    },
    {
        "template": "Can I hit a {creature} with my attack bonus?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "monster_stats"},
        "slots": {"creature": "creature"}
    },
    {
        "template": "Am I resistant to {damage_type} and what creatures deal that damage?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "damage_types"},
        "slots": {"damage_type": "damage_type"}
    },

    # Character + condition effects
    {
        "template": "What actions can I take and what happens if I'm {condition}?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "condition_effects"},
        "slots": {"condition": "condition"}
    },
    {
        "template": "Can I still cast spells while {condition}?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "magic_info", "rulebook": "condition_effects"},
        "slots": {"condition": "condition"}
    },

    # Multiclass questions
    {
        "template": "What class am I and can I multiclass into {class_name}?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "multiclass_rules"},
        "slots": {"class_name": "class"}
    },
    {
        "template": "What are my ability scores and do I meet multiclass requirements?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "multiclass_rules"},
        "slots": {}
    },

    # Optimization questions
    {
        "template": "What's my class and what feats would be good for me?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "optimization_advice"},
        "slots": {}
    },
    {
        "template": "What's my build and how can I optimize my damage?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_summary", "rulebook": "optimization_advice"},
        "slots": {}
    },

    # Progress + leveling
    {
        "template": "How much XP do I have and when do I level up?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "progress_info", "rulebook": "level_progression"},
        "slots": {}
    },
    {
        "template": "What are my current goals and what rewards are typical?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "progress_info", "rulebook": "cost_lookup"},
        "slots": {}
    },

    # Story + planar
    {
        "template": "Where did my character come from and what's the {plane} like?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "story_info", "rulebook": "planar_properties"},
        "slots": {"plane": "plane"}
    },

    # Action economy questions
    {
        "template": "What bonus actions do I have and can I cast {spell} as a bonus action?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "action_options"},
        "slots": {"spell": "spell"}
    },
    {
        "template": "How many attacks can I make and how does two-weapon fighting work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "action_options"},
        "slots": {}
    },

    # Rest and recovery
    {
        "template": "What abilities do I recover on a short rest and how do hit dice work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "rest_mechanics"},
        "slots": {}
    },
    {
        "template": "How many hit dice do I have and how do I spend them?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "rest_mechanics"},
        "slots": {}
    },

    # Additional saving throws coverage
    {
        "template": "What's my Wisdom save and what spells require Wisdom saves?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "saving_throws"},
        "slots": {}
    },
    {
        "template": "What are all my saving throw bonuses and when do I roll each type?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "saving_throws"},
        "slots": {}
    },
    {
        "template": "Am I proficient in {ability} saves and how do save proficiencies work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "saving_throws"},
        "slots": {"ability": "ability"}
    },

    # Additional planar properties coverage
    {
        "template": "What's my backstory and what are the rules for the {plane}?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "story_info", "rulebook": "planar_properties"},
        "slots": {"plane": "plane"}
    },
    {
        "template": "What deity do I worship and what's their home plane like?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "story_info", "rulebook": "planar_properties"},
        "slots": {}
    },
    {
        "template": "What race am I and what plane do my ancestors come from?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "character_basics", "rulebook": "planar_properties"},
        "slots": {}
    },

    # Additional equipment properties coverage
    {
        "template": "What armor am I wearing and what are its properties?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "inventory_info", "rulebook": "equipment_properties"},
        "slots": {}
    },
    {
        "template": "What weapons am I proficient with and what properties do they have?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "abilities_info", "rulebook": "equipment_properties"},
        "slots": {}
    },
    {
        "template": "What tools do I have and what are their equipment rules?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "inventory_info", "rulebook": "equipment_properties"},
        "slots": {}
    },
]

# =============================================================================
# CHARACTER_DATA + SESSION_NOTES (2-tool)
# "What's my X and what happened with it?"
# =============================================================================

CHARACTER_SESSION_TEMPLATES = [
    # Items + session history
    {
        "template": "What magic items do I have and how did I get them?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "inventory_info", "session_notes": "item_tracking"},
        "slots": {}
    },
    {
        "template": "What's in my inventory and what loot did we find last session?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "inventory_info", "session_notes": "loot_rewards"},
        "slots": {}
    },
    {
        "template": "What weapons do I have and when did I get my current weapon?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "inventory_info", "session_notes": "item_tracking"},
        "slots": {}
    },
    {
        "template": "How much gold do I have and what was our last big treasure haul?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "inventory_info", "session_notes": "loot_rewards"},
        "slots": {}
    },
    {
        "template": "What armor am I wearing and where did I find it?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "inventory_info", "session_notes": "item_tracking"},
        "slots": {}
    },

    # Character stats + combat history
    {
        "template": "What's my current HP and what happened in our last fight?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "combat_info", "session_notes": "combat_recap"},
        "slots": {}
    },
    {
        "template": "What's my AC and how did that help in recent combat?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "combat_info", "session_notes": "combat_recap"},
        "slots": {}
    },
    {
        "template": "What attacks can I make and what did I fight last session?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "combat_info", "session_notes": "combat_recap"},
        "slots": {}
    },

    # Spells + usage history
    {
        "template": "What spells do I have and which ones did I cast last session?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "magic_info", "session_notes": "spell_ability_usage"},
        "slots": {}
    },
    {
        "template": "How many spell slots do I have and how many did I use?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "magic_info", "session_notes": "spell_ability_usage"},
        "slots": {}
    },
    {
        "template": "What cantrips do I know and when did I use them effectively?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "magic_info", "session_notes": "spell_ability_usage"},
        "slots": {}
    },

    # Abilities + usage
    {
        "template": "What class features do I have and when did I use them?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "abilities_info", "session_notes": "spell_ability_usage"},
        "slots": {}
    },
    {
        "template": "What's my {skill} bonus and when did I roll it?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "abilities_info", "session_notes": "rules_mechanics"},
        "slots": {"skill": "skill"}
    },

    # Character identity + story
    {
        "template": "What's my backstory and how has it come up in the campaign?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "character_decisions"},
        "slots": {}
    },
    {
        "template": "What are my character's goals and what progress have I made?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "quest_tracking"},
        "slots": {}
    },
    {
        "template": "What motivates my character and what choices have I made?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "character_decisions"},
        "slots": {}
    },

    # Social + NPC interactions
    {
        "template": "Who are my allies and who did we meet last session?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "social_info", "session_notes": "npc_info"},
        "slots": {}
    },
    {
        "template": "What factions am I part of and how is my standing with them?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "social_info", "session_notes": "npc_info"},
        "slots": {}
    },
    {
        "template": "Who are my contacts and what did they tell me?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "social_info", "session_notes": "npc_info"},
        "slots": {}
    },

    # Progress + quests
    {
        "template": "What are my current objectives and what quests have I completed?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "progress_info", "session_notes": "quest_tracking"},
        "slots": {}
    },
    {
        "template": "What quests am I on and what's the status of each?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "progress_info", "session_notes": "quest_tracking"},
        "slots": {}
    },
    {
        "template": "What long-term goals do I have and what mysteries remain unsolved?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "progress_info", "session_notes": "unresolved_mysteries"},
        "slots": {}
    },

    # Character status
    {
        "template": "What's my character's current status and condition?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "character_summary", "session_notes": "character_status"},
        "slots": {}
    },
    {
        "template": "Give me an overview of my character and recent events",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "character_summary", "session_notes": "event_sequence"},
        "slots": {}
    },

    # Death and revival
    {
        "template": "What's my HP and have I ever been knocked unconscious?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "combat_info", "session_notes": "death_revival"},
        "slots": {}
    },
    {
        "template": "What healing do I have access to and when have I needed it?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "magic_info", "session_notes": "death_revival"},
        "slots": {}
    },

    # Party dynamics
    {
        "template": "Who are my companions and how do we work together?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "social_info", "session_notes": "party_dynamics"},
        "slots": {}
    },
    {
        "template": "What role do I play in the party and how has that evolved?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "character_summary", "session_notes": "party_dynamics"},
        "slots": {}
    },

    # Location and exploration
    {
        "template": "What senses do I have and what locations have we explored?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "abilities_info", "session_notes": "location_details"},
        "slots": {}
    },

    # Divine/religious
    {
        "template": "What's my alignment and what divine encounters have we had?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "character_basics", "session_notes": "divine_religious"},
        "slots": {}
    },

    # Humor and moments
    {
        "template": "What's my personality and what funny moments have I had?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "humor_moments"},
        "slots": {}
    },

    # Future implications
    {
        "template": "What are my goals and what consequences might come from recent actions?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "progress_info", "session_notes": "future_implications"},
        "slots": {}
    },

    # Memory/vision (NEW - was missing entirely)
    {
        "template": "What's my backstory and have I had any visions or flashbacks?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "memory_vision"},
        "slots": {}
    },
    {
        "template": "What's my character's history and what memories have surfaced in play?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "memory_vision"},
        "slots": {}
    },
    {
        "template": "Do I have any prophetic abilities and what visions have I experienced?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "abilities_info", "session_notes": "memory_vision"},
        "slots": {}
    },
    {
        "template": "What's my connection to the past and what revelations have occurred?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "memory_vision"},
        "slots": {}
    },
    {
        "template": "What dreams or visions has my character had and do they relate to my backstory?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "memory_vision"},
        "slots": {}
    },

    # Cross-session (was at 1)
    {
        "template": "What progress have I made and what carried over from previous sessions?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "progress_info", "session_notes": "cross_session"},
        "slots": {}
    },
    {
        "template": "What's my XP and how has my character evolved across sessions?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "progress_info", "session_notes": "cross_session"},
        "slots": {}
    },
    {
        "template": "What level am I and what major events happened during my level-ups?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "character_basics", "session_notes": "cross_session"},
        "slots": {}
    },
    {
        "template": "What new abilities have I gained and when did I get them?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "abilities_info", "session_notes": "cross_session"},
        "slots": {}
    },
    {
        "template": "What's my character arc and how has it developed over time?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "cross_session"},
        "slots": {}
    },

    # Humor moments (was at 1)
    {
        "template": "What's my Charisma and what funny things have I said?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "character_basics", "session_notes": "humor_moments"},
        "slots": {}
    },
    {
        "template": "What's my character like and what embarrassing moments have we had?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "character_summary", "session_notes": "humor_moments"},
        "slots": {}
    },
    {
        "template": "What are my character flaws and when have they led to comedy?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "humor_moments"},
        "slots": {}
    },
    {
        "template": "What's my personality and what running jokes involve my character?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "humor_moments"},
        "slots": {}
    },

    # Future implications (was at 1)
    {
        "template": "What choices have I made and what might happen because of them?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "character_summary", "session_notes": "future_implications"},
        "slots": {}
    },
    {
        "template": "What enemies have I made and what revenge might they seek?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "social_info", "session_notes": "future_implications"},
        "slots": {}
    },
    {
        "template": "What promises have I made and what obligations do I have?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "future_implications"},
        "slots": {}
    },
    {
        "template": "What seeds have been planted that might grow into future plot?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "progress_info", "session_notes": "future_implications"},
        "slots": {}
    },

    # Character decisions (was at 2)
    {
        "template": "What's my alignment and what moral choices have I made?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "character_basics", "session_notes": "character_decisions"},
        "slots": {}
    },
    {
        "template": "What ideals does my character hold and when have I acted on them?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "character_decisions"},
        "slots": {}
    },
    {
        "template": "What bonds do I have and how have they influenced my decisions?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "character_decisions"},
        "slots": {}
    },

    # Party dynamics (was at 3)
    {
        "template": "What class am I and how does my role complement the party?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "character_basics", "session_notes": "party_dynamics"},
        "slots": {}
    },
    {
        "template": "What abilities do I bring and how have they helped the group?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "abilities_info", "session_notes": "party_dynamics"},
        "slots": {}
    },

    # Divine religious (was at 3)
    {
        "template": "What deity do I worship and what religious events have occurred?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "divine_religious"},
        "slots": {}
    },
    {
        "template": "What's my oath or domain and how has my faith been tested?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "character_basics", "session_notes": "divine_religious"},
        "slots": {}
    },

    # Event sequence (was at 2)
    {
        "template": "What level am I and what major events led to my current level?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "character_basics", "session_notes": "event_sequence"},
        "slots": {}
    },
    {
        "template": "What's my story so far and what events have shaped my character?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "event_sequence"},
        "slots": {}
    },
    {
        "template": "What happened in our last session and how did it affect me?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "character_summary", "session_notes": "event_sequence"},
        "slots": {}
    },

    # Unresolved mysteries (was at 2)
    {
        "template": "What questions does my character have and what mysteries are we pursuing?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "unresolved_mysteries"},
        "slots": {}
    },
    {
        "template": "What's my backstory and are there any unresolved elements from it?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "story_info", "session_notes": "unresolved_mysteries"},
        "slots": {}
    },
    {
        "template": "What clues have I found and what mysteries remain unsolved?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "progress_info", "session_notes": "unresolved_mysteries"},
        "slots": {}
    },

    # Puzzle solutions (was at 2)
    {
        "template": "What's my Intelligence and what puzzles have I helped solve?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "character_basics", "session_notes": "puzzle_solutions"},
        "slots": {}
    },
    {
        "template": "What skills do I have and what riddles have we encountered?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "abilities_info", "session_notes": "puzzle_solutions"},
        "slots": {}
    },
    {
        "template": "What tools am I proficient with and how did I use them to solve puzzles?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "abilities_info", "session_notes": "puzzle_solutions"},
        "slots": {}
    },

    # Item tracking (was at 4)
    {
        "template": "What consumables do I have and when did I acquire them?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "inventory_info", "session_notes": "item_tracking"},
        "slots": {}
    },

    # Full character + session
    {
        "template": "Give me my full character sheet and summarize recent sessions",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "full_character", "session_notes": "event_sequence"},
        "slots": {}
    },
    {
        "template": "Show me everything about my character and our campaign progress",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "full_character", "session_notes": "quest_tracking"},
        "slots": {}
    },
    {
        "template": "What's my complete character breakdown and current campaign status?",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "full_character", "session_notes": "character_status"},
        "slots": {}
    },
    {
        "template": "Display my entire character info and what happened recently",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "full_character", "session_notes": "event_sequence"},
        "slots": {}
    },
    {
        "template": "I need my complete character details and a session recap",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "full_character", "session_notes": "combat_recap"},
        "slots": {}
    },
]

# =============================================================================
# SESSION_NOTES + RULEBOOK (2-tool)
# "What happened and how does that rule work?"
# =============================================================================

SESSION_RULEBOOK_TEMPLATES = [
    # Combat events + rules
    {
        "template": "What happened in our last fight and how does {mechanic} work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "rule_mechanics"},
        "slots": {"mechanic": "mechanic"}
    },
    {
        "template": "Who did we fight and what's a {creature}'s stat block?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "monster_stats"},
        "slots": {"creature": "creature"}
    },
    {
        "template": "What enemies did we face and what resistances do {creature}s have?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "monster_stats"},
        "slots": {"creature": "creature"}
    },

    # Spells used + spell details
    {
        "template": "What spells were cast and how does {spell} work exactly?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "spell_ability_usage", "rulebook": "spell_details"},
        "slots": {"spell": "spell"}
    },
    {
        "template": "When did we use {spell} and what are its full details?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "spell_ability_usage", "rulebook": "spell_details"},
        "slots": {"spell": "spell"}
    },

    # Items found + item rules
    {
        "template": "What magic items did we find and how does {magic_item} work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "item_tracking", "rulebook": "magic_item_usage"},
        "slots": {"magic_item": "magic_item"}
    },
    {
        "template": "What loot did we get and what's the value of {item}?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "loot_rewards", "rulebook": "cost_lookup"},
        "slots": {"item": "item"}
    },
    {
        "template": "What weapons did we find and what are the properties of {weapon}?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "loot_rewards", "rulebook": "equipment_properties"},
        "slots": {"weapon": "weapon"}
    },

    # Conditions encountered + condition rules
    {
        "template": "What conditions affected us and how does {condition} work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "condition_effects"},
        "slots": {"condition": "condition"}
    },
    {
        "template": "Who got {condition} and what are the effects?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "character_status", "rulebook": "condition_effects"},
        "slots": {"condition": "condition"}
    },

    # Locations + planar rules
    {
        "template": "Where did we go and what are the rules for the {plane}?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "location_details", "rulebook": "planar_properties"},
        "slots": {"plane": "plane"}
    },
    {
        "template": "What location did we explore and how does {mechanic} work there?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "location_details", "rulebook": "environmental_rules"},
        "slots": {"mechanic": "mechanic"}
    },

    # NPCs + creature abilities
    {
        "template": "Who did we meet and what abilities do {creature}s have?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "npc_info", "rulebook": "creature_abilities"},
        "slots": {"creature": "creature"}
    },
    {
        "template": "What monster did we encounter and what's its challenge rating?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "monster_stats"},
        "slots": {}
    },

    # Rules clarifications from play
    {
        "template": "What rule question came up and how does {mechanic} actually work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "rules_mechanics", "rulebook": "rule_mechanics"},
        "slots": {"mechanic": "mechanic"}
    },
    {
        "template": "What happened when we tried {mechanic} and is that how it works?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "rules_mechanics", "rulebook": "rule_mechanics"},
        "slots": {"mechanic": "mechanic"}
    },

    # Puzzles + skill checks
    {
        "template": "What puzzle did we solve and how do {skill} checks work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "puzzle_solutions", "rulebook": "skill_usage"},
        "slots": {"skill": "skill"}
    },

    # Death/revival + rules
    {
        "template": "Who went down in combat and how do death saves work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "death_revival", "rulebook": "saving_throws"},
        "slots": {}
    },
    {
        "template": "What resurrection happened and what are the rules for it?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "death_revival", "rulebook": "spell_details"},
        "slots": {}
    },

    # Divine encounters + rules
    {
        "template": "What divine event occurred and how do divine interventions work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "divine_religious", "rulebook": "rule_mechanics"},
        "slots": {}
    },

    # Quest rewards + values
    {
        "template": "What quest rewards did we get and how much are they worth?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "loot_rewards", "rulebook": "cost_lookup"},
        "slots": {}
    },

    # Downtime between sessions
    {
        "template": "What downtime did we have and what activities are available?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "cross_session", "rulebook": "downtime_activities"},
        "slots": {}
    },

    # Legendary creatures
    {
        "template": "What boss did we fight and how do legendary actions work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "legendary_mechanics"},
        "slots": {}
    },
    {
        "template": "What legendary creature did we encounter and what can it do?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "legendary_mechanics"},
        "slots": {}
    },

    # Character creation (missing)
    {
        "template": "What new characters joined our party and how does character creation work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "party_dynamics", "rulebook": "character_creation"},
        "slots": {}
    },
    {
        "template": "Who died and needs a new character, and what are the creation rules?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "death_revival", "rulebook": "character_creation"},
        "slots": {}
    },
    {
        "template": "What backup characters have been discussed and how do I make one?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "character_decisions", "rulebook": "character_creation"},
        "slots": {}
    },
    {
        "template": "What new player joined and what are the starting equipment rules?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "party_dynamics", "rulebook": "character_creation"},
        "slots": {}
    },
    {
        "template": "What character died and what are the rules for creating a replacement?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "death_revival", "rulebook": "character_creation"},
        "slots": {}
    },

    # Class spell access (missing)
    {
        "template": "What spells were cast and what class has access to {spell}?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "spell_ability_usage", "rulebook": "class_spell_access"},
        "slots": {"spell": "spell"}
    },
    {
        "template": "What magic happened and which classes can learn those spells?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "spell_ability_usage", "rulebook": "class_spell_access"},
        "slots": {}
    },
    {
        "template": "What divine magic did we see and what's on the cleric spell list?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "divine_religious", "rulebook": "class_spell_access"},
        "slots": {}
    },
    {
        "template": "What arcane spells were used and what's on the wizard spell list?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "spell_ability_usage", "rulebook": "class_spell_access"},
        "slots": {}
    },
    {
        "template": "What cantrips came up and which classes have access to them?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "spell_ability_usage", "rulebook": "class_spell_access"},
        "slots": {}
    },

    # Compare entities (missing)
    {
        "template": "What monsters did we fight and how do they compare to each other?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "compare_entities"},
        "slots": {}
    },
    {
        "template": "What weapons did we find and how do they compare to standard weapons?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "loot_rewards", "rulebook": "compare_entities"},
        "slots": {}
    },
    {
        "template": "What spells were used and how does {spell} compare to {spell}?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "spell_ability_usage", "rulebook": "compare_entities"},
        "slots": {"spell": "spell"}
    },
    {
        "template": "What items did we get and how do they compare to similar items?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "item_tracking", "rulebook": "compare_entities"},
        "slots": {}
    },
    {
        "template": "What different creature types did we encounter and how do they differ?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "compare_entities"},
        "slots": {}
    },

    # Find by criteria (missing)
    {
        "template": "What damage types did we encounter and what deals {damage_type} damage?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "find_by_criteria"},
        "slots": {"damage_type": "damage_type"}
    },
    {
        "template": "What level are we and what spells become available at this level?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "character_status", "rulebook": "find_by_criteria"},
        "slots": {}
    },
    {
        "template": "What loot is in the treasure hoard and what items have magical properties?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "loot_rewards", "rulebook": "find_by_criteria"},
        "slots": {}
    },
    {
        "template": "What creatures did we fight and what monsters have similar abilities?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "find_by_criteria"},
        "slots": {}
    },
    {
        "template": "What conditions came up and what spells can cure them?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "character_status", "rulebook": "find_by_criteria"},
        "slots": {}
    },

    # Interaction rules (missing)
    {
        "template": "What spell combos were used and how do those spells interact?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "spell_ability_usage", "rulebook": "interaction_rules"},
        "slots": {}
    },
    {
        "template": "What abilities stacked in combat and how does stacking work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "interaction_rules"},
        "slots": {}
    },
    {
        "template": "What concentration spells were running and can they overlap?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "spell_ability_usage", "rulebook": "interaction_rules"},
        "slots": {}
    },
    {
        "template": "What effects were active and how do they interact with each other?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "interaction_rules"},
        "slots": {}
    },
    {
        "template": "What magic items were used together and do they conflict?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "item_tracking", "rulebook": "interaction_rules"},
        "slots": {}
    },

    # Tactical usage (low coverage)
    {
        "template": "What tactics did we use and what's the best way to handle {creature}?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "tactical_usage"},
        "slots": {"creature": "creature"}
    },
    {
        "template": "What combat strategies worked and what tactics should we use?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "tactical_usage"},
        "slots": {}
    },
    {
        "template": "What positioning helped in the fight and how does tactical movement work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "tactical_usage"},
        "slots": {}
    },
    {
        "template": "What could we have done better and what's the optimal strategy?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "tactical_usage"},
        "slots": {}
    },
    {
        "template": "What abilities did we combo and how can we improve our tactics?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "spell_ability_usage", "rulebook": "tactical_usage"},
        "slots": {}
    },

    # Creature abilities (low coverage)
    {
        "template": "What special attacks hit us and what abilities do those creatures have?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "creature_abilities"},
        "slots": {}
    },
    {
        "template": "What monster abilities surprised us and how do they work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "creature_abilities"},
        "slots": {}
    },
    {
        "template": "What creature did we run from and what dangerous abilities does it have?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "creature_abilities"},
        "slots": {}
    },
    {
        "template": "What NPC abilities did we see and are those standard creature powers?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "npc_info", "rulebook": "creature_abilities"},
        "slots": {}
    },

    # Subclass features (low coverage)
    {
        "template": "What subclass abilities were used and how do they work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "spell_ability_usage", "rulebook": "subclass_features"},
        "slots": {}
    },
    {
        "template": "What archetype features came up and what are their full effects?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "spell_ability_usage", "rulebook": "subclass_features"},
        "slots": {}
    },
    {
        "template": "What domain/oath abilities did we see and how do they scale?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "spell_ability_usage", "rulebook": "subclass_features"},
        "slots": {}
    },
    {
        "template": "What specialty features were key to victory and what do they do?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "subclass_features"},
        "slots": {}
    },

    # Downtime activities (low coverage)
    {
        "template": "What happened between sessions and what downtime activities exist?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "cross_session", "rulebook": "downtime_activities"},
        "slots": {}
    },
    {
        "template": "What crafting did we do and how does crafting work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "item_tracking", "rulebook": "downtime_activities"},
        "slots": {}
    },
    {
        "template": "What research happened and what are the rules for researching?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "puzzle_solutions", "rulebook": "downtime_activities"},
        "slots": {}
    },
    {
        "template": "What training occurred and how does training in a new skill work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "cross_session", "rulebook": "downtime_activities"},
        "slots": {}
    },

    # Prerequisite check (low coverage)
    {
        "template": "What feats were discussed and what are their prerequisites?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "character_decisions", "rulebook": "prerequisite_check"},
        "slots": {}
    },
    {
        "template": "What multiclass was considered and what are the requirements?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "character_decisions", "rulebook": "prerequisite_check"},
        "slots": {}
    },
    {
        "template": "What magic items require attunement and what are those prerequisites?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "item_tracking", "rulebook": "prerequisite_check"},
        "slots": {}
    },
    {
        "template": "What level-up choices were made and what prerequisites did they require?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "character_decisions", "rulebook": "prerequisite_check"},
        "slots": {}
    },

    # Additional coverage for low intents
    # Multiclass rules
    {
        "template": "What multiclass characters are in the party and how does multiclassing work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "party_dynamics", "rulebook": "multiclass_rules"},
        "slots": {}
    },
    {
        "template": "Who multiclassed recently and what are the multiclass spell rules?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "character_decisions", "rulebook": "multiclass_rules"},
        "slots": {}
    },
    {
        "template": "What class combo did someone take and how do proficiencies work for multiclass?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "character_decisions", "rulebook": "multiclass_rules"},
        "slots": {}
    },

    # Damage types
    {
        "template": "What damage types hurt us and what resistances exist for them?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "damage_types"},
        "slots": {}
    },
    {
        "template": "What element was the dragon and how do breath weapon damage types work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "damage_types"},
        "slots": {}
    },
    {
        "template": "What magical damage did we encounter and what's the difference between types?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "damage_types"},
        "slots": {}
    },

    # Calculate values
    {
        "template": "What damage was rolled and how is average damage calculated?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "calculate_values"},
        "slots": {}
    },
    {
        "template": "What XP did we get and how is encounter XP calculated?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "loot_rewards", "rulebook": "calculate_values"},
        "slots": {}
    },
    {
        "template": "What carrying happened and how is carrying capacity calculated?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "item_tracking", "rulebook": "calculate_values"},
        "slots": {}
    },

    # Action options
    {
        "template": "What actions were taken in combat and what options exist?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "action_options"},
        "slots": {}
    },
    {
        "template": "What bonus actions were used and what can I do with a bonus action?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "spell_ability_usage", "rulebook": "action_options"},
        "slots": {}
    },
    {
        "template": "What reactions happened and what triggers reactions?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "action_options"},
        "slots": {}
    },

    # Optimization advice
    {
        "template": "What worked well in combat and how can we optimize our builds?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "optimization_advice"},
        "slots": {}
    },
    {
        "template": "What strategies failed and what would be more optimal?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "optimization_advice"},
        "slots": {}
    },
    {
        "template": "What party composition issues came up and how can we improve?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "party_dynamics", "rulebook": "optimization_advice"},
        "slots": {}
    },

    # Level progression
    {
        "template": "Who leveled up and what do they get at that level?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "character_status", "rulebook": "level_progression"},
        "slots": {}
    },
    {
        "template": "What XP milestone did we hit and what features come at this level?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "quest_tracking", "rulebook": "level_progression"},
        "slots": {}
    },

    # Memory/vision coverage for session+rulebook
    {
        "template": "What prophetic vision occurred and how does divination magic work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "memory_vision", "rulebook": "spell_details"},
        "slots": {}
    },
    {
        "template": "What dream sequence happened and what spells affect dreams?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "memory_vision", "rulebook": "spell_details"},
        "slots": {}
    },
    {
        "template": "What flashback revealed information and how do memory spells work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "memory_vision", "rulebook": "spell_details"},
        "slots": {}
    },
    {
        "template": "What scrying happened and what are the rules for scrying?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "memory_vision", "rulebook": "spell_details"},
        "slots": {}
    },
    {
        "template": "What omens did we receive and how do augury spells work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "memory_vision", "rulebook": "spell_details"},
        "slots": {}
    },

    # Humor moments coverage
    {
        "template": "What funny thing happened and does that actually work by the rules?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "humor_moments", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What ridiculous plan worked and how did the rules allow it?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "humor_moments", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What critical fail happened and how do critical failures work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "humor_moments", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What nat 20 shenanigans occurred and what are the rules for natural 20s?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "humor_moments", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What absurd skill check succeeded and what are the rules for impossible DCs?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "humor_moments", "rulebook": "skill_usage"},
        "slots": {}
    },

    # Future implications coverage
    {
        "template": "What consequences are coming and what rules govern those situations?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "future_implications", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What enemy escaped and what abilities might they return with?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "future_implications", "rulebook": "creature_abilities"},
        "slots": {}
    },
    {
        "template": "What curse was placed on us and how do curses work in the long term?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "future_implications", "rulebook": "condition_effects"},
        "slots": {}
    },
    {
        "template": "What oath was broken and what are the paladin oathbreaker rules?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "future_implications", "rulebook": "subclass_features"},
        "slots": {}
    },
    {
        "template": "What seeds were planted and how might those affect future sessions?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "future_implications", "rulebook": "rule_mechanics"},
        "slots": {}
    },

    # Additional saving throws coverage
    {
        "template": "What save was rolled in combat and how do saving throw DCs work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "saving_throws"},
        "slots": {}
    },
    {
        "template": "Who failed a save against {spell} and what determines spell save DC?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "spell_ability_usage", "rulebook": "saving_throws"},
        "slots": {"spell": "spell"}
    },
    {
        "template": "What conditions required saves and how do ability check saves work?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "character_status", "rulebook": "saving_throws"},
        "slots": {}
    },

    # Additional planar properties coverage
    {
        "template": "What plane did we visit and what environmental effects apply there?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "location_details", "rulebook": "planar_properties"},
        "slots": {}
    },
    {
        "template": "What extraplanar creature did we meet and what's its home plane like?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "npc_info", "rulebook": "planar_properties"},
        "slots": {}
    },
    {
        "template": "What divine realm was referenced and what are the rules for that plane?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "divine_religious", "rulebook": "planar_properties"},
        "slots": {}
    },

    # Additional equipment properties coverage
    {
        "template": "What weapons were used in combat and what properties do they have?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "combat_recap", "rulebook": "equipment_properties"},
        "slots": {}
    },
    {
        "template": "What armor was discussed and what are the stealth/strength requirements?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "item_tracking", "rulebook": "equipment_properties"},
        "slots": {}
    },
    {
        "template": "What equipment did we buy and what are the special properties of each?",
        "tools": ["session_notes", "rulebook"],
        "intents": {"session_notes": "item_tracking", "rulebook": "equipment_properties"},
        "slots": {}
    },
]

# =============================================================================
# ALL THREE TOOLS (3-tool)
# Complex compound questions
# =============================================================================

THREE_TOOL_TEMPLATES = [
    # Character + session + spell rules
    {
        "template": "What spells do I know, when did I cast {spell}, and what are its full rules?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "magic_info", "session_notes": "spell_ability_usage", "rulebook": "spell_details"},
        "slots": {"spell": "spell"}
    },
    {
        "template": "What's my spell save DC, what spells did I cast last session, and how does upcasting work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "magic_info", "session_notes": "spell_ability_usage", "rulebook": "spell_details"},
        "slots": {}
    },

    # Character + session + combat rules
    {
        "template": "What's my AC, what did we fight, and how does cover affect AC?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "combat_info", "session_notes": "combat_recap", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What attacks can I make, what combat happened, and how do opportunity attacks work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "combat_info", "session_notes": "combat_recap", "rulebook": "action_options"},
        "slots": {}
    },
    {
        "template": "What's my HP, what damage did I take last session, and how does resistance work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "combat_info", "session_notes": "combat_recap", "rulebook": "damage_types"},
        "slots": {}
    },

    # Character + session + item rules
    {
        "template": "What magic items do I have, when did I get them, and how does {magic_item} work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "inventory_info", "session_notes": "item_tracking", "rulebook": "magic_item_usage"},
        "slots": {"magic_item": "magic_item"}
    },
    {
        "template": "What's in my inventory, what did we loot, and what are these items worth?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "inventory_info", "session_notes": "loot_rewards", "rulebook": "cost_lookup"},
        "slots": {}
    },
    {
        "template": "What weapons do I have, what fights used them, and what's the damage for {weapon}?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "inventory_info", "session_notes": "combat_recap", "rulebook": "equipment_properties"},
        "slots": {"weapon": "weapon"}
    },

    # Character + session + creature rules
    {
        "template": "What's my attack bonus, what monsters did we fight, and what's a {creature}'s AC?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "combat_info", "session_notes": "combat_recap", "rulebook": "monster_stats"},
        "slots": {"creature": "creature"}
    },
    {
        "template": "What resistances do I have, what hit us, and what damage types do {creature}s deal?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "combat_info", "session_notes": "combat_recap", "rulebook": "monster_stats"},
        "slots": {"creature": "creature"}
    },

    # Character + session + condition rules
    {
        "template": "What's my current status, what conditions affected us, and how does {condition} work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_summary", "session_notes": "character_status", "rulebook": "condition_effects"},
        "slots": {"condition": "condition"}
    },
    {
        "template": "What saves do I have, what saves did I roll, and how do saving throws work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "combat_info", "session_notes": "rules_mechanics", "rulebook": "saving_throws"},
        "slots": {}
    },

    # Character + session + skill rules
    {
        "template": "What's my {skill} bonus, when did I use it, and what are typical DCs?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "abilities_info", "session_notes": "rules_mechanics", "rulebook": "skill_usage"},
        "slots": {"skill": "skill"}
    },
    {
        "template": "What skills am I proficient in, what checks did I make, and how does advantage work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "abilities_info", "session_notes": "rules_mechanics", "rulebook": "rule_mechanics"},
        "slots": {}
    },

    # Character + session + class progression
    {
        "template": "What level am I, what progress have I made, and when do I get my next feature?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "quest_tracking", "rulebook": "level_progression"},
        "slots": {}
    },
    {
        "template": "What class features do I have, when did I use them, and how does {feature} work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "abilities_info", "session_notes": "spell_ability_usage", "rulebook": "describe_entity"},
        "slots": {"feature": "feature"}
    },

    # Character + session + NPC/social rules
    {
        "template": "Who are my allies, who did we meet, and how do social encounters work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "social_info", "session_notes": "npc_info", "rulebook": "skill_usage"},
        "slots": {}
    },

    # Character + session + location rules
    {
        "template": "What senses do I have, where did we explore, and how does darkness affect perception?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "abilities_info", "session_notes": "location_details", "rulebook": "environmental_rules"},
        "slots": {}
    },

    # Character + session + rest rules
    {
        "template": "How many hit dice do I have, what rest did we take, and what recovers on a short rest?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "combat_info", "session_notes": "character_status", "rulebook": "rest_mechanics"},
        "slots": {}
    },
    {
        "template": "What spell slots do I have left, how many did I use, and how do they recover?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "magic_info", "session_notes": "spell_ability_usage", "rulebook": "rest_mechanics"},
        "slots": {}
    },

    # Character + session + death rules
    {
        "template": "What's my max HP, have I gone down before, and how do death saves work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "combat_info", "session_notes": "death_revival", "rulebook": "saving_throws"},
        "slots": {}
    },

    # Character + session + divine rules
    {
        "template": "What's my alignment, what divine encounters have we had, and how does divine magic work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "divine_religious", "rulebook": "rule_mechanics"},
        "slots": {}
    },

    # Character + session + planar rules
    {
        "template": "What's my backstory, what planes have we visited, and what are the rules for the {plane}?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "story_info", "session_notes": "location_details", "rulebook": "planar_properties"},
        "slots": {"plane": "plane"}
    },

    # Quest + progress + rules
    {
        "template": "What are my goals, what quests have we done, and what are typical quest rewards?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "progress_info", "session_notes": "quest_tracking", "rulebook": "cost_lookup"},
        "slots": {}
    },

    # Character + puzzle + skill rules
    {
        "template": "What's my Intelligence, what puzzles have we solved, and how do Investigation checks work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "puzzle_solutions", "rulebook": "skill_usage"},
        "slots": {}
    },

    # Full character breakdown
    {
        "template": "Give me my character summary, recent events, and rules for my key abilities",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_summary", "session_notes": "event_sequence", "rulebook": "describe_entity"},
        "slots": {}
    },
    {
        "template": "What's my full character sheet, what happened recently, and how do my abilities work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "full_character", "session_notes": "character_status", "rulebook": "describe_entity"},
        "slots": {}
    },

    # Future planning
    {
        "template": "What are my long-term goals, what mysteries remain, and what's the best way to advance?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "progress_info", "session_notes": "unresolved_mysteries", "rulebook": "optimization_advice"},
        "slots": {}
    },

    # Party coordination
    {
        "template": "What role do I play, how does our party work, and how can we optimize our tactics?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_summary", "session_notes": "party_dynamics", "rulebook": "tactical_usage"},
        "slots": {}
    },

    # Memory/vision coverage in 3-tool
    {
        "template": "What's my backstory, what visions have I had, and how does divination magic work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "story_info", "session_notes": "memory_vision", "rulebook": "spell_details"},
        "slots": {}
    },
    {
        "template": "What prophetic abilities do I have, what dreams occurred, and how do those spells function?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "abilities_info", "session_notes": "memory_vision", "rulebook": "spell_details"},
        "slots": {}
    },
    {
        "template": "What's my connection to the divine, what omens have we received, and how does commune work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "story_info", "session_notes": "memory_vision", "rulebook": "spell_details"},
        "slots": {}
    },
    {
        "template": "What deity do I worship, what visions came from them, and how does divine revelation work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "story_info", "session_notes": "memory_vision", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What's my character history, what flashbacks have I experienced, and how does memory magic work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "story_info", "session_notes": "memory_vision", "rulebook": "spell_details"},
        "slots": {}
    },

    # Humor moments in 3-tool
    {
        "template": "What's my Charisma, what funny moments have I caused, and do those antics work by RAW?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "humor_moments", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What class am I, what ridiculous things have I done, and could I actually do that?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "humor_moments", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What personality traits do I have, what comedy ensued, and what are the rules for that situation?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "story_info", "session_notes": "humor_moments", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What's my character like, what embarrassing failures occurred, and how do critical fails work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_summary", "session_notes": "humor_moments", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What flaws do I have, what running jokes developed, and can those actions actually happen in 5e?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "story_info", "session_notes": "humor_moments", "rulebook": "rule_mechanics"},
        "slots": {}
    },

    # Future implications in 3-tool
    {
        "template": "What enemies have I made, what revenge might they seek, and what abilities do those foes have?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "social_info", "session_notes": "future_implications", "rulebook": "creature_abilities"},
        "slots": {}
    },
    {
        "template": "What choices did I make, what consequences are coming, and what rules govern those situations?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "story_info", "session_notes": "future_implications", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What pacts have I made, what might the patron demand, and how do warlock pacts work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "future_implications", "rulebook": "describe_entity"},
        "slots": {}
    },
    {
        "template": "What oaths have I sworn, what consequences for breaking them, and what are the oathbreaker rules?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "future_implications", "rulebook": "subclass_features"},
        "slots": {}
    },
    {
        "template": "What seeds were planted, what plot might grow from them, and how do those mechanics work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "progress_info", "session_notes": "future_implications", "rulebook": "rule_mechanics"},
        "slots": {}
    },

    # Cross-session in 3-tool
    {
        "template": "What level am I now, how have I progressed across sessions, and what features did I gain?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "cross_session", "rulebook": "level_progression"},
        "slots": {}
    },
    {
        "template": "What's my character arc, what happened over the campaign, and how do character development rules work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "story_info", "session_notes": "cross_session", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "What new abilities do I have, when did I get them, and how do those features function?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "abilities_info", "session_notes": "cross_session", "rulebook": "describe_entity"},
        "slots": {}
    },
    {
        "template": "What magic items have I accumulated, how did I find each, and what are their properties?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "inventory_info", "session_notes": "cross_session", "rulebook": "magic_item_usage"},
        "slots": {}
    },
    {
        "template": "What's my current power level, how did I get here, and what comes next on my progression?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_summary", "session_notes": "cross_session", "rulebook": "level_progression"},
        "slots": {}
    },

    # Character creation in 3-tool
    {
        "template": "What race am I, what racial events occurred, and what are the racial trait rules?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "character_decisions", "rulebook": "character_creation"},
        "slots": {}
    },
    {
        "template": "What class am I, what defined my character growth, and how does class building work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "cross_session", "rulebook": "character_creation"},
        "slots": {}
    },
    {
        "template": "What background do I have, how did it affect the story, and what are background options?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "character_decisions", "rulebook": "character_creation"},
        "slots": {}
    },
    {
        "template": "What ability scores do I have, how did they help in play, and how is point buy calculated?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "rules_mechanics", "rulebook": "character_creation"},
        "slots": {}
    },
    {
        "template": "What starting equipment do I have, how did I get additional gear, and what are starting rules?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "inventory_info", "session_notes": "item_tracking", "rulebook": "character_creation"},
        "slots": {}
    },

    # Class spell access in 3-tool
    {
        "template": "What spells do I know, which did I cast recently, and what's my full class spell list?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "magic_info", "session_notes": "spell_ability_usage", "rulebook": "class_spell_access"},
        "slots": {}
    },
    {
        "template": "What cantrips do I have, when did I use them, and what other cantrips can I learn?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "magic_info", "session_notes": "spell_ability_usage", "rulebook": "class_spell_access"},
        "slots": {}
    },
    {
        "template": "What's my spellcasting class, what magic happened in session, and what spells can I add?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "spell_ability_usage", "rulebook": "class_spell_access"},
        "slots": {}
    },
    {
        "template": "What domain spells do I get, when did I use them, and what's the cleric spell list?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "magic_info", "session_notes": "spell_ability_usage", "rulebook": "class_spell_access"},
        "slots": {}
    },
    {
        "template": "What patron spells do I have, how did they help, and what's the warlock expanded list?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "magic_info", "session_notes": "spell_ability_usage", "rulebook": "class_spell_access"},
        "slots": {}
    },

    # Compare entities in 3-tool
    {
        "template": "What class am I, what other classes did we see, and how do they compare?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "party_dynamics", "rulebook": "compare_entities"},
        "slots": {}
    },
    {
        "template": "What weapons do I use, what weapons did we find, and how do they compare?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "inventory_info", "session_notes": "loot_rewards", "rulebook": "compare_entities"},
        "slots": {}
    },
    {
        "template": "What spells do I have, what spells were cast against us, and how do they compare?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "magic_info", "session_notes": "combat_recap", "rulebook": "compare_entities"},
        "slots": {}
    },
    {
        "template": "What race am I, what other races are in the party, and what are the differences?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "party_dynamics", "rulebook": "compare_entities"},
        "slots": {}
    },
    {
        "template": "What subclass am I, what archetypes have we encountered, and how do they differ?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "npc_info", "rulebook": "compare_entities"},
        "slots": {}
    },

    # Find by criteria in 3-tool
    {
        "template": "What spells do I have, what damage did we need, and what spells deal that damage type?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "magic_info", "session_notes": "combat_recap", "rulebook": "find_by_criteria"},
        "slots": {}
    },
    {
        "template": "What level am I, what challenges did we face, and what monsters fit our level?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "combat_recap", "rulebook": "find_by_criteria"},
        "slots": {}
    },
    {
        "template": "What class am I, what abilities helped, and what feats enhance those abilities?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "spell_ability_usage", "rulebook": "find_by_criteria"},
        "slots": {}
    },
    {
        "template": "How much gold do I have, what did we spend money on, and what items can I afford?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "inventory_info", "session_notes": "loot_rewards", "rulebook": "find_by_criteria"},
        "slots": {}
    },
    {
        "template": "What conditions affected me, what cured them, and what spells remove those conditions?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_summary", "session_notes": "character_status", "rulebook": "find_by_criteria"},
        "slots": {}
    },

    # Interaction rules in 3-tool
    {
        "template": "What spells do I concentrate on, what else was I doing, and can those effects stack?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "magic_info", "session_notes": "spell_ability_usage", "rulebook": "interaction_rules"},
        "slots": {}
    },
    {
        "template": "What class features do I have, what combos happened, and how do those features interact?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "abilities_info", "session_notes": "combat_recap", "rulebook": "interaction_rules"},
        "slots": {}
    },
    {
        "template": "What rage ability do I have, did I cast spells while raging, and can rage and spells mix?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "abilities_info", "session_notes": "spell_ability_usage", "rulebook": "interaction_rules"},
        "slots": {}
    },
    {
        "template": "What reactions do I have, when did I use them, and how do reactions stack with other effects?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "combat_info", "session_notes": "combat_recap", "rulebook": "interaction_rules"},
        "slots": {}
    },
    {
        "template": "What multiclass am I, what abilities combined, and how do multiclass features interact?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "character_basics", "session_notes": "spell_ability_usage", "rulebook": "interaction_rules"},
        "slots": {}
    },

    # Additional full_character 3-tool coverage
    {
        "template": "Show me my complete character, what major events shaped them, and how do my abilities work?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "full_character", "session_notes": "event_sequence", "rulebook": "describe_entity"},
        "slots": {}
    },
    {
        "template": "Give me everything about my character, our campaign recap, and rules for my key features",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "full_character", "session_notes": "quest_tracking", "rulebook": "describe_entity"},
        "slots": {}
    },
    {
        "template": "What's my full character breakdown, what happened to me, and what are my class rules?",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "full_character", "session_notes": "character_status", "rulebook": "describe_entity"},
        "slots": {}
    },
    {
        "template": "Display my entire character sheet, recent combat history, and applicable rules",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "full_character", "session_notes": "combat_recap", "rulebook": "rule_mechanics"},
        "slots": {}
    },
    {
        "template": "I need my complete character info, session summary, and clarification on my abilities",
        "tools": ["character_data", "session_notes", "rulebook"],
        "intents": {"character_data": "full_character", "session_notes": "event_sequence", "rulebook": "describe_entity"},
        "slots": {}
    },
]

# =============================================================================
# CONSOLIDATED TEMPLATES
# =============================================================================

MULTI_TOOL_TEMPLATES = {
    "character_rulebook": CHARACTER_RULEBOOK_TEMPLATES,
    "character_session": CHARACTER_SESSION_TEMPLATES,
    "session_rulebook": SESSION_RULEBOOK_TEMPLATES,
    "three_tool": THREE_TOOL_TEMPLATES,
}

# Template counts for dataset generation
TEMPLATE_COUNTS = {
    "character_rulebook": len(CHARACTER_RULEBOOK_TEMPLATES),
    "character_session": len(CHARACTER_SESSION_TEMPLATES),
    "session_rulebook": len(SESSION_RULEBOOK_TEMPLATES),
    "three_tool": len(THREE_TOOL_TEMPLATES),
}


def get_all_multi_tool_templates():
    """Return all multi-tool templates as a flat list."""
    all_templates = []
    for category, templates in MULTI_TOOL_TEMPLATES.items():
        for template in templates:
            all_templates.append({
                **template,
                "category": category,
            })
    return all_templates


def get_two_tool_templates():
    """Get all 2-tool templates."""
    templates = []
    templates.extend(CHARACTER_RULEBOOK_TEMPLATES)
    templates.extend(CHARACTER_SESSION_TEMPLATES)
    templates.extend(SESSION_RULEBOOK_TEMPLATES)
    return templates


def get_three_tool_templates():
    """Get all 3-tool templates."""
    return THREE_TOOL_TEMPLATES.copy()


def get_templates_by_tools(tools: list):
    """Get templates that use exactly the specified tools."""
    all_templates = get_all_multi_tool_templates()
    return [t for t in all_templates if set(t["tools"]) == set(tools)]
