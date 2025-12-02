"""Configuration for 574 NLP Assignment - Transformer Training

This config uses relative paths for portability with VS Code Colab extension.
"""
from pathlib import Path

# Project paths (relative to this file's location)
PROJECT_ROOT = Path(__file__).parent.resolve()
DATA_PATH = PROJECT_ROOT / "data" / "generated"
TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates"
MODEL_PATH = PROJECT_ROOT / "models" / "joint_deberta"
RESULTS_PATH = PROJECT_ROOT / "results"

# Ensure directories exist
DATA_PATH.mkdir(parents=True, exist_ok=True)
MODEL_PATH.mkdir(parents=True, exist_ok=True)
RESULTS_PATH.mkdir(parents=True, exist_ok=True)

# Model configuration
MODEL_CONFIG = {
    'model_name': 'microsoft/deberta-v3-base',
    'batch_size': 32,
    'learning_rate': 2e-5,
    'num_epochs': 10,
    'warmup_ratio': 0.1,
    'weight_decay': 0.01,
    'max_length': 128,
    'gradient_accumulation_steps': 1,
    'tool_loss_weight': 1.0,
    'intent_loss_weight': 1.0,
    'ner_loss_weight': 1.0,
    'patience': 3,
    'classifier_dropout': 0.1,
}

# Dataset configuration
DATASET_CONFIG = {
    # K-expansion: generate K samples per template with different entity fills
    # Templates WITH slots generate K variations; templates WITHOUT slots generate 1
    'expansions_per_template': 10,  # Each template generates up to K variations
    
    # Augmentations: typos, case changes, contractions per sample
    'augmentations_per_sample': 3,  # Generate N augmented versions per sample
    
    # Train/val/test splits
    'train_split': 0.80,
    'val_split': 0.10,
    'test_split': 0.10,
    
    'random_seed': 42,
    
    # Deduplication: skip samples that are identical to existing ones
    'deduplicate': True,
}

# Tools and their intents
TOOLS = ['character_data', 'session_notes', 'rulebook']

CHARACTER_INTENTS = [
    'ability_scores', 'combat_info', 'skills_proficiencies', 'class_features',
    'spell_slots', 'inventory', 'background', 'race_traits', 'level_info', 'full_character'
]

SESSION_INTENTS = [
    'recent_events', 'npc_interactions', 'location_info', 'quest_status',
    'party_decisions', 'combat_history', 'treasure_loot', 'plot_threads',
    'character_development', 'time_tracking', 'relationship_status', 'faction_standing',
    'unresolved_mysteries', 'player_notes', 'dm_notes', 'session_summary',
    'next_session_hooks', 'world_lore', 'house_rules', 'campaign_timeline'
]

RULEBOOK_INTENTS = [
    'spell_details', 'spell_list_query', 'class_info', 'subclass_info',
    'race_info', 'feat_info', 'condition_rules', 'combat_rules',
    'skill_rules', 'ability_check_rules', 'saving_throw_rules', 'death_rules',
    'rest_rules', 'movement_rules', 'cover_rules', 'action_rules',
    'reaction_rules', 'equipment_info', 'weapon_info', 'armor_info',
    'magic_item_info', 'monster_info', 'multiclassing_rules', 'spellcasting_rules',
    'concentration_rules', 'ritual_rules', 'component_rules', 'aoe_rules',
    'range_rules', 'duration_rules', 'damage_type_rules'
]

# NER tags (BIO scheme)
NER_TAGS = [
    'O',
    'B-SPELL', 'I-SPELL',
    'B-CLASS', 'I-CLASS',
    'B-RACE', 'I-RACE',
    'B-CREATURE', 'I-CREATURE',
    'B-ITEM', 'I-ITEM',
    'B-LOCATION', 'I-LOCATION',
    'B-ABILITY', 'I-ABILITY',
    'B-SKILL', 'I-SKILL',
    'B-CONDITION', 'I-CONDITION',
    'B-DAMAGE_TYPE', 'I-DAMAGE_TYPE',
    'B-FEAT', 'I-FEAT',
    'B-BACKGROUND', 'I-BACKGROUND'
]
