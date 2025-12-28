"""
Test serialization behavior of character types.

This test ensures that converting from dataclasses to Pydantic models
produces identical serialization output. Run this BEFORE and AFTER
the conversion to verify no breaking changes.
"""
import pytest
from dataclasses import asdict
from datetime import datetime

from src.rag.character.character_types import (
    # Core types
    AbilityScores,
    CombatStats,
    CharacterBase,
    PhysicalCharacteristics,
    Proficiency,
    DamageModifier,
    PassiveScores,
    Senses,
    # Background types
    BackgroundFeature,
    BackgroundInfo,
    PersonalityTraits,
    BackstorySection,
    FamilyBackstory,
    Backstory,
    Organization,
    Ally,
    Enemy,
    # Action types
    ActionActivation,
    ActionUsage,
    ActionRange,
    ActionDamage,
    ActionSave,
    CharacterAction,
    ActionEconomy,
    # Feature types
    FeatureActivation,
    FeatureRange,
    RacialTrait,
    ClassFeature,
    Feat,
    FeatureAction,
    FeatureModifier,
    FeaturesAndTraits,
    LimitedUse,
    # Inventory types
    ItemModifier,
    InventoryItemDefinition,
    InventoryItem,
    Inventory,
    # Spell types
    SpellComponents,
    SpellRite,
    Spell,
    SpellcastingInfo,
    SpellList,
    # Objective types
    BaseObjective,
    Quest,
    Contract,
    ContractTemplate,
    ObjectivesAndContracts,
    # Main character
    Character,
    create_empty_character,
)


def serialize(obj):
    """
    Convert a dataclass or Pydantic model instance into its dictionary representation.
    
    Parameters:
        obj (Any): A dataclass instance or a Pydantic model instance to serialize.
    
    Returns:
        dict: A dictionary containing the serialized fields of `obj`.
    """
    if hasattr(obj, 'model_dump'):
        # Pydantic model
        return obj.model_dump()
    else:
        # Dataclass
        return asdict(obj)


class TestCoreTypes:
    """Test core character type serialization."""

    def test_ability_scores(self):
        scores = AbilityScores(
            strength=16,
            dexterity=14,
            constitution=15,
            intelligence=10,
            wisdom=12,
            charisma=8
        )
        result = serialize(scores)

        assert result == {
            'strength': 16,
            'dexterity': 14,
            'constitution': 15,
            'intelligence': 10,
            'wisdom': 12,
            'charisma': 8
        }

    def test_combat_stats_minimal(self):
        stats = CombatStats(
            max_hp=45,
            armor_class=18,
            initiative_bonus=2,
            speed=30
        )
        result = serialize(stats)

        assert result['max_hp'] == 45
        assert result['armor_class'] == 18
        assert result['initiative_bonus'] == 2
        assert result['speed'] == 30
        assert result['hit_dice'] is None

    def test_combat_stats_with_hit_dice(self):
        stats = CombatStats(
            max_hp=45,
            armor_class=18,
            initiative_bonus=2,
            speed=30,
            hit_dice={'d10': '5d10', 'd8': '2d8'}
        )
        result = serialize(stats)

        assert result['hit_dice'] == {'d10': '5d10', 'd8': '2d8'}

    def test_character_base_minimal(self):
        base = CharacterBase(
            name="Thorn",
            race="Half-Elf",
            character_class="Ranger",
            total_level=5,
            alignment="Chaotic Good",
            background="Outlander"
        )
        result = serialize(base)

        assert result['name'] == "Thorn"
        assert result['race'] == "Half-Elf"
        assert result['character_class'] == "Ranger"
        assert result['total_level'] == 5
        assert result['subrace'] is None
        assert result['multiclass_levels'] is None

    def test_character_base_multiclass(self):
        base = CharacterBase(
            name="Thorn",
            race="Half-Elf",
            character_class="Ranger",
            total_level=7,
            alignment="Chaotic Good",
            background="Outlander",
            subrace="Wood Elf",
            multiclass_levels={'Ranger': 5, 'Rogue': 2},
            lifestyle="Modest"
        )
        result = serialize(base)

        assert result['multiclass_levels'] == {'Ranger': 5, 'Rogue': 2}
        assert result['subrace'] == "Wood Elf"
        assert result['lifestyle'] == "Modest"

    def test_proficiency(self):
        prof = Proficiency(type="skill", name="Stealth")
        result = serialize(prof)

        assert result == {'type': 'skill', 'name': 'Stealth'}

    def test_damage_modifier(self):
        mod = DamageModifier(damage_type="fire", modifier_type="resistance")
        result = serialize(mod)

        assert result == {'damage_type': 'fire', 'modifier_type': 'resistance'}

    def test_passive_scores(self):
        scores = PassiveScores(
            perception=15,
            investigation=12,
            insight=14,
            stealth=None
        )
        result = serialize(scores)

        assert result['perception'] == 15
        assert result['investigation'] == 12
        assert result['insight'] == 14
        assert result['stealth'] is None

    def test_senses_empty(self):
        senses = Senses()
        result = serialize(senses)

        assert result == {'senses': {}}

    def test_senses_with_values(self):
        senses = Senses(senses={'darkvision': 60, 'blindsight': 10})
        result = serialize(senses)

        assert result == {'senses': {'darkvision': 60, 'blindsight': 10}}


class TestBackgroundTypes:
    """Test background and personality type serialization."""

    def test_background_feature(self):
        feature = BackgroundFeature(
            name="Shelter of the Faithful",
            description="As an acolyte, you command the respect..."
        )
        result = serialize(feature)

        assert result == {
            'name': 'Shelter of the Faithful',
            'description': 'As an acolyte, you command the respect...'
        }

    def test_background_info(self):
        info = BackgroundInfo(
            name="Acolyte",
            feature=BackgroundFeature(name="Test", description="Desc"),
            skill_proficiencies=["Insight", "Religion"],
            tool_proficiencies=[],
            language_proficiencies=["Elvish", "Dwarvish"],
            equipment=["Holy symbol", "Prayer book"]
        )
        result = serialize(info)

        assert result['name'] == "Acolyte"
        assert result['skill_proficiencies'] == ["Insight", "Religion"]
        assert result['tool_proficiencies'] == []
        assert result['language_proficiencies'] == ["Elvish", "Dwarvish"]

    def test_personality_traits(self):
        traits = PersonalityTraits(
            personality_traits=["I am suspicious of strangers"],
            ideals=["Greater Good"],
            bonds=["I protect those who cannot protect themselves"],
            flaws=["I am too trusting"]
        )
        result = serialize(traits)

        assert len(result['personality_traits']) == 1
        assert len(result['ideals']) == 1
        assert len(result['bonds']) == 1
        assert len(result['flaws']) == 1

    def test_backstory_section(self):
        section = BackstorySection(
            heading="Early Life",
            content="Born in the mountains..."
        )
        result = serialize(section)

        assert result == {'heading': 'Early Life', 'content': 'Born in the mountains...'}

    def test_organization(self):
        org = Organization(
            name="The Order of the Gauntlet",
            role="Knight",
            description="A militant order..."
        )
        result = serialize(org)

        assert result['name'] == "The Order of the Gauntlet"
        assert result['role'] == "Knight"

    def test_ally(self):
        ally = Ally(
            name="Elara",
            description="A childhood friend",
            title="Priestess"
        )
        result = serialize(ally)

        assert result['title'] == "Priestess"

    def test_enemy(self):
        enemy = Enemy(name="Strahd", description="The vampire lord")
        result = serialize(enemy)

        assert result == {'name': 'Strahd', 'description': 'The vampire lord'}


class TestActionTypes:
    """Test action type serialization."""

    def test_action_activation(self):
        activation = ActionActivation(
            activationType="action",
            activationTime=1,
            activationCondition="When you take the Attack action"
        )
        result = serialize(activation)

        assert result['activationType'] == "action"
        assert result['activationTime'] == 1

    def test_action_usage(self):
        """
        Verify ActionUsage serializes to a dict preserving `maxUses` and `resetType`.
        
        Creates an ActionUsage with `maxUses=3`, `resetType='long_rest'`, and `usesPerActivation=1`, then asserts the serialized dictionary contains the expected `maxUses` and `resetType` values.
        """
        usage = ActionUsage(
            maxUses=3,
            resetType="long_rest",
            usesPerActivation=1
        )
        result = serialize(usage)

        assert result['maxUses'] == 3
        assert result['resetType'] == "long_rest"

    def test_action_range(self):
        range_info = ActionRange(
            range=30,
            longRange=120,
            aoeType="cone",
            aoeSize=15
        )
        result = serialize(range_info)

        assert result['range'] == 30
        assert result['longRange'] == 120
        assert result['aoeType'] == "cone"

    def test_action_damage(self):
        damage = ActionDamage(
            diceNotation="2d6+4",
            damageType="slashing",
            bonusDamage="1d6 fire"
        )
        result = serialize(damage)

        assert result['diceNotation'] == "2d6+4"
        assert result['damageType'] == "slashing"

    def test_action_save(self):
        save = ActionSave(
            saveDC=15,
            saveAbility="Dexterity",
            onSuccess="Half damage",
            onFailure="Full damage and prone"
        )
        result = serialize(save)

        assert result['saveDC'] == 15
        assert result['saveAbility'] == "Dexterity"

    def test_character_action_full(self):
        action = CharacterAction(
            name="Longsword Attack",
            description="A melee weapon attack",
            shortDescription="Melee attack",
            activation=ActionActivation(activationType="action"),
            damage=ActionDamage(diceNotation="1d8+3", damageType="slashing"),
            actionCategory="attack",
            source="item",
            attackBonus=7,
            isWeaponAttack=True
        )
        result = serialize(action)

        assert result['name'] == "Longsword Attack"
        assert result['activation']['activationType'] == "action"
        assert result['damage']['diceNotation'] == "1d8+3"
        assert result['isWeaponAttack'] is True

    def test_action_economy(self):
        economy = ActionEconomy(
            attacks_per_action=2,
            actions=[
                CharacterAction(name="Longsword", isWeaponAttack=True),
                CharacterAction(name="Second Wind", actionCategory="feature")
            ]
        )
        result = serialize(economy)

        assert result['attacks_per_action'] == 2
        assert len(result['actions']) == 2


class TestFeatureTypes:
    """Test feature type serialization."""

    def test_racial_trait(self):
        trait = RacialTrait(
            name="Darkvision",
            description="You can see in dim light within 60 feet...",
            featureType="trait"
        )
        result = serialize(trait)

        assert result['name'] == "Darkvision"
        assert result['featureType'] == "trait"

    def test_class_feature(self):
        feature = ClassFeature(
            name="Fighting Style",
            description="You adopt a particular style of fighting..."
        )
        result = serialize(feature)

        assert result == {
            'name': 'Fighting Style',
            'description': 'You adopt a particular style of fighting...'
        }

    def test_feat(self):
        feat = Feat(
            name="Great Weapon Master",
            description="You've learned to put the weight...",
            activation=FeatureActivation(activationType="bonus_action"),
            isRepeatable=False
        )
        result = serialize(feat)

        assert result['name'] == "Great Weapon Master"
        assert result['activation']['activationType'] == "bonus_action"
        assert result['isRepeatable'] is False

    def test_features_and_traits(self):
        features = FeaturesAndTraits(
            racial_traits=[RacialTrait(name="Darkvision", description="See in dark")],
            class_features={
                "Fighter": {
                    1: [ClassFeature(name="Fighting Style", description="Pick a style")],
                    2: [ClassFeature(name="Action Surge", description="Extra action")]
                }
            },
            feats=[Feat(name="Alert", description="Can't be surprised")],
            modifiers={}
        )
        result = serialize(features)

        assert len(result['racial_traits']) == 1
        assert "Fighter" in result['class_features']
        assert 1 in result['class_features']['Fighter']
        assert len(result['feats']) == 1


class TestInventoryTypes:
    """Test inventory type serialization."""

    def test_item_modifier(self):
        mod = ItemModifier(
            type="bonus",
            subType="armor-class",
            fixedValue=2,
            friendlyTypeName="Bonus",
            friendlySubtypeName="Armor Class"
        )
        result = serialize(mod)

        assert result['type'] == "bonus"
        assert result['fixedValue'] == 2

    def test_limited_use(self):
        limited = LimitedUse(
            maxUses=3,
            numberUsed=1,
            resetType="long_rest",
            resetTypeDescription="Regain all uses after a long rest"
        )
        result = serialize(limited)

        assert result['maxUses'] == 3
        assert result['numberUsed'] == 1

    def test_inventory_item_definition(self):
        definition = InventoryItemDefinition(
            name="Longsword",
            type="Weapon",
            description="A versatile martial weapon",
            rarity="Common",
            weight=3,
            canEquip=True,
            magic=False,
            damageType="Slashing",
            range=5
        )
        result = serialize(definition)

        assert result['name'] == "Longsword"
        assert result['weight'] == 3
        assert result['magic'] is False

    def test_inventory_item(self):
        item = InventoryItem(
            definition=InventoryItemDefinition(name="Potion of Healing", type="Potion"),
            quantity=3,
            isAttuned=False,
            equipped=False,
            limitedUse=LimitedUse(maxUses=1, resetType="consumable")
        )
        result = serialize(item)

        assert result['quantity'] == 3
        assert result['definition']['name'] == "Potion of Healing"
        assert result['limitedUse']['maxUses'] == 1

    def test_inventory(self):
        inventory = Inventory(
            total_weight=45.5,
            weight_unit="lb",
            equipped_items=[
                InventoryItem(
                    definition=InventoryItemDefinition(name="Chain Mail", type="Armor"),
                    quantity=1,
                    isAttuned=False,
                    equipped=True
                )
            ],
            backpack=[
                InventoryItem(
                    definition=InventoryItemDefinition(name="Rope", type="Adventuring Gear"),
                    quantity=1,
                    isAttuned=False,
                    equipped=False
                )
            ]
        )
        result = serialize(inventory)

        assert result['total_weight'] == 45.5
        assert len(result['equipped_items']) == 1
        assert len(result['backpack']) == 1


class TestSpellTypes:
    """Test spell type serialization."""

    def test_spell_components(self):
        components = SpellComponents(
            verbal=True,
            somatic=True,
            material="A pinch of sulfur"
        )
        result = serialize(components)

        assert result['verbal'] is True
        assert result['somatic'] is True
        assert result['material'] == "A pinch of sulfur"

    def test_spell_rite(self):
        rite = SpellRite(name="Rite of Flame", effect="Adds 1d6 fire damage")
        result = serialize(rite)

        assert result == {'name': 'Rite of Flame', 'effect': 'Adds 1d6 fire damage'}

    def test_spell(self):
        """
        Create a Spell instance and assert its serialized fields match expected values.
        
        Constructs a Spell named "Fireball" (level 3, school "Evocation") with verbal, somatic, and material components, serializes it, and asserts that the serialized dict contains the expected 'name', 'level', that components.verbal is True, and the 'area' value.
        """
        spell = Spell(
            name="Fireball",
            level=3,
            school="Evocation",
            casting_time="1 action",
            range="150 feet",
            components=SpellComponents(verbal=True, somatic=True, material="A tiny ball of bat guano"),
            duration="Instantaneous",
            description="A bright streak flashes...",
            concentration=False,
            ritual=False,
            tags=["damage", "fire"],
            area="20-foot radius sphere"
        )
        result = serialize(spell)

        assert result['name'] == "Fireball"
        assert result['level'] == 3
        assert result['components']['verbal'] is True
        assert result['area'] == "20-foot radius sphere"

    def test_spellcasting_info(self):
        info = SpellcastingInfo(
            ability="Intelligence",
            spell_save_dc=15,
            spell_attack_bonus=7,
            cantrips_known=["Fire Bolt", "Prestidigitation"],
            spells_known=["Magic Missile", "Shield", "Fireball"],
            spell_slots={1: 4, 2: 3, 3: 2}
        )
        result = serialize(info)

        assert result['ability'] == "Intelligence"
        assert result['spell_save_dc'] == 15
        assert len(result['cantrips_known']) == 2
        assert result['spell_slots'][1] == 4

    def test_spell_list(self):
        """
        Verify that a SpellList containing spellcasting info and spells for a class serializes with the expected keys and counts.
        
        Asserts that the "Wizard" entry appears in both `spellcasting` and `spells`, and that the Wizard's `cantrip` list contains exactly one spell.
        """
        spell_list = SpellList(
            spellcasting={
                "Wizard": SpellcastingInfo(
                    ability="Intelligence",
                    spell_save_dc=15,
                    spell_attack_bonus=7
                )
            },
            spells={
                "Wizard": {
                    "cantrip": [
                        Spell(
                            name="Fire Bolt",
                            level=0,
                            school="Evocation",
                            casting_time="1 action",
                            range="120 feet",
                            components=SpellComponents(verbal=True, somatic=True),
                            duration="Instantaneous",
                            description="Hurl a mote of fire"
                        )
                    ]
                }
            }
        )
        result = serialize(spell_list)

        assert "Wizard" in result['spellcasting']
        assert "Wizard" in result['spells']
        assert len(result['spells']['Wizard']['cantrip']) == 1


class TestObjectiveTypes:
    """Test objective type serialization."""

    def test_base_objective(self):
        """
        Verifies that a BaseObjective instance serializes to a dictionary containing the expected id, status, and two objectives.
        
        The test constructs a BaseObjective with id "quest-001", status "Active", and two objectives, then asserts those fields are present and correct in the serialized output.
        """
        obj = BaseObjective(
            id="quest-001",
            name="Rescue the Princess",
            type="main_quest",
            status="Active",
            description="The princess has been captured...",
            priority="High",
            objectives=["Find the tower", "Defeat the dragon"],
            rewards=["Gold", "Title"]
        )
        result = serialize(obj)

        assert result['id'] == "quest-001"
        assert result['status'] == "Active"
        assert len(result['objectives']) == 2

    def test_quest(self):
        """
        Validate that a Quest instance serializes with its `quest_giver` and `deity` fields preserved.
        
        Asserts that the serialized representation contains the expected `quest_giver` and `deity` values.
        """
        quest = Quest(
            id="quest-002",
            name="Divine Mission",
            type="divine_quest",
            status="In Progress",
            description="Your god has tasked you...",
            quest_giver="High Priest Aldric",
            location="Temple of Light",
            deity="Pelor",
            divine_favor="Blessed"
        )
        result = serialize(quest)

        assert result['quest_giver'] == "High Priest Aldric"
        assert result['deity'] == "Pelor"

    def test_contract(self):
        contract = Contract(
            id="contract-001",
            name="Bounty Hunt",
            type="bounty",
            status="Active",
            description="Hunt the criminal...",
            client="City Guard",
            payment="500 gold",
            penalties="Reputation loss"
        )
        result = serialize(contract)

        assert result['client'] == "City Guard"
        assert result['payment'] == "500 gold"

    def test_objectives_and_contracts(self):
        objectives = ObjectivesAndContracts(
            active_contracts=[
                Contract(
                    id="c1",
                    name="Escort Mission",
                    type="escort",
                    status="Active",
                    description="Escort the merchant"
                )
            ],
            current_objectives=[
                Quest(
                    id="q1",
                    name="Main Quest",
                    type="main",
                    status="Active",
                    description="Save the world"
                )
            ],
            metadata={"last_updated": "2024-01-01"}
        )
        result = serialize(objectives)

        assert len(result['active_contracts']) == 1
        assert len(result['current_objectives']) == 1
        assert result['metadata']['last_updated'] == "2024-01-01"


class TestFullCharacter:
    """Test full character serialization."""

    def test_create_empty_character(self):
        """Test the utility function creates a valid character."""
        char = create_empty_character("Test", "Human", "Fighter")
        result = serialize(char)

        assert result['character_base']['name'] == "Test"
        assert result['character_base']['race'] == "Human"
        assert result['character_base']['character_class'] == "Fighter"
        assert result['ability_scores']['strength'] == 10
        assert result['combat_stats']['max_hp'] == 10

    def test_full_character_serialization(self):
        """Test a complete character with all fields."""
        char = Character(
            character_base=CharacterBase(
                name="Duskryn",
                race="Dark Elf",
                character_class="Warlock",
                total_level=10,
                alignment="Chaotic Neutral",
                background="Acolyte",
                subrace="Drow",
                multiclass_levels={"Warlock": 8, "Cleric": 2}
            ),
            characteristics=PhysicalCharacteristics(
                alignment="Chaotic Neutral",
                gender="Male",
                eyes="Red",
                size="Medium",
                height="5'8\"",
                hair="White",
                skin="Dark Gray",
                age=150,
                weight="140 lb",
                faith="Lolth"
            ),
            ability_scores=AbilityScores(
                strength=10,
                dexterity=16,
                constitution=14,
                intelligence=12,
                wisdom=13,
                charisma=18
            ),
            combat_stats=CombatStats(
                max_hp=75,
                armor_class=15,
                initiative_bonus=3,
                speed=30,
                hit_dice={"d8": "10d8"}
            ),
            background_info=BackgroundInfo(
                name="Acolyte",
                feature=BackgroundFeature(
                    name="Shelter of the Faithful",
                    description="You can receive free healing..."
                ),
                skill_proficiencies=["Insight", "Religion"]
            ),
            personality=PersonalityTraits(
                personality_traits=["Mysterious"],
                ideals=["Power"],
                bonds=["My patron"],
                flaws=["Secretive"]
            ),
            backstory=Backstory(
                title="The Exile",
                family_backstory=FamilyBackstory(
                    parents="Unknown",
                    sections=[BackstorySection(heading="Origin", content="Born in the Underdark")]
                ),
                sections=[BackstorySection(heading="The Pact", content="Made a deal...")]
            ),
            organizations=[Organization(name="Cult of the Eye", role="Initiate", description="A secretive cult")],
            allies=[Ally(name="Shadow", description="A familiar", title=None)],
            enemies=[Enemy(name="The Hunter", description="A bounty hunter")],
            proficiencies=[
                Proficiency(type="skill", name="Deception"),
                Proficiency(type="weapon", name="Simple Weapons")
            ],
            damage_modifiers=[
                DamageModifier(damage_type="poison", modifier_type="resistance")
            ],
            passive_scores=PassiveScores(perception=13, investigation=11, insight=13),
            senses=Senses(senses={"darkvision": 120, "devil's sight": 120}),
            action_economy=ActionEconomy(
                attacks_per_action=1,
                actions=[CharacterAction(name="Eldritch Blast", actionCategory="spell")]
            ),
            features_and_traits=FeaturesAndTraits(
                racial_traits=[RacialTrait(name="Superior Darkvision", description="120 feet")],
                class_features={"Warlock": {1: [ClassFeature(name="Pact Magic", description="...")]}},
                feats=[],
                modifiers={}
            ),
            inventory=Inventory(
                total_weight=20.0,
                equipped_items=[],
                backpack=[]
            ),
            spell_list=SpellList(
                spellcasting={"Warlock": SpellcastingInfo(
                    ability="Charisma",
                    spell_save_dc=16,
                    spell_attack_bonus=8
                )},
                spells={}
            ),
            objectives_and_contracts=ObjectivesAndContracts(),
            notes={"dm_notes": "Interesting character"},
            created_date=datetime(2024, 1, 1, 12, 0, 0),
            last_updated=datetime(2024, 6, 15, 18, 30, 0)
        )

        result = serialize(char)

        # Verify structure is complete
        assert result['character_base']['name'] == "Duskryn"
        assert result['character_base']['multiclass_levels'] == {"Warlock": 8, "Cleric": 2}
        assert result['ability_scores']['charisma'] == 18
        assert result['combat_stats']['hit_dice'] == {"d8": "10d8"}
        assert len(result['organizations']) == 1
        assert len(result['proficiencies']) == 2
        assert result['senses']['senses']['darkvision'] == 120
        assert result['spell_list']['spellcasting']['Warlock']['spell_save_dc'] == 16
        assert result['notes'] == {"dm_notes": "Interesting character"}

        # Verify nested structures
        assert result['backstory']['family_backstory']['sections'][0]['heading'] == "Origin"
        assert result['features_and_traits']['racial_traits'][0]['name'] == "Superior Darkvision"


class TestSerializationConsistency:
    """Tests to verify serialization output is consistent."""

    def test_empty_lists_serialize_as_empty_lists(self):
        """Empty lists should serialize as [], not None."""
        traits = PersonalityTraits()
        result = serialize(traits)

        assert result['personality_traits'] == []
        assert result['ideals'] == []
        assert result['bonds'] == []
        assert result['flaws'] == []

    def test_empty_dicts_serialize_as_empty_dicts(self):
        """Empty dicts should serialize as {}, not None."""
        features = FeaturesAndTraits()
        result = serialize(features)

        assert result['class_features'] == {}
        assert result['modifiers'] == {}

    def test_none_values_serialize_as_none(self):
        """Optional fields with no value should serialize as None."""
        base = CharacterBase(
            name="Test",
            race="Human",
            character_class="Fighter",
            total_level=1,
            alignment="Neutral",
            background="Soldier"
        )
        result = serialize(base)

        assert result['subrace'] is None
        assert result['multiclass_levels'] is None
        assert result['lifestyle'] is None

    def test_nested_optional_types(self):
        """Nested optional types should serialize correctly."""
        action = CharacterAction(name="Test")
        result = serialize(action)

        assert result['activation'] is None
        assert result['usage'] is None
        assert result['damage'] is None
        assert result['save'] is None

    def test_union_types_serialize_correctly(self):
        """Union types like Union[bool, str] should work."""
        # material can be bool or str
        comp1 = SpellComponents(verbal=True, somatic=True, material=False)
        comp2 = SpellComponents(verbal=True, somatic=True, material="A diamond worth 100 gp")

        r1 = serialize(comp1)
        r2 = serialize(comp2)

        assert r1['material'] is False
        assert r2['material'] == "A diamond worth 100 gp"

    def test_literal_types_serialize_as_strings(self):
        """Literal types should serialize as their string values."""
        prof = Proficiency(type="skill", name="Stealth")
        mod = DamageModifier(damage_type="fire", modifier_type="resistance")
        obj = BaseObjective(
            id="1",
            name="Test",
            type="quest",
            status="Active",
            description="Test",
            priority="High"
        )

        assert serialize(prof)['type'] == "skill"
        assert serialize(mod)['modifier_type'] == "resistance"
        assert serialize(obj)['status'] == "Active"
        assert serialize(obj)['priority'] == "High"