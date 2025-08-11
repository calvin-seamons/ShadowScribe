import React, { useState, useCallback, useEffect } from 'react';
import {
  User,
  Zap,
  BookOpen,
  Sword,
  Sparkles,
  Eye,
  CheckCircle,
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  X,
  Loader2,
  Plus,
  Minus,
  Shield,
  Heart,
  Dice6,
  Star,
  Info
} from 'lucide-react';
import { CharacterCreationRequest, createNewCharacter } from '../../services/knowledgeBaseApi';
import { ValidationError } from '../../types';

interface WizardStep {
  id: string;
  title: string;
  icon: React.ReactNode;
  description: string;
  isComplete: boolean;
  isValid: boolean;
}

interface CharacterBasics {
  name: string;
  race: string;
  subrace?: string;
  character_class: string;
  level: number;
  background: string;
  alignment: string;
  hit_points?: number;
  armor_class?: number;
  speed?: number;
  proficiency_bonus?: number;
}

interface AbilityScores {
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
}

interface BackgroundStory {
  personality_traits: string[];
  ideals: string[];
  bonds: string[];
  flaws: string[];
  backstory_sections: Array<{
    title: string;
    content: string;
  }>;
}

interface Equipment {
  weapons: Array<{
    name: string;
    type: string;
    damage: string;
    properties: string[];
    equipped: boolean;
  }>;
  armor: Array<{
    name: string;
    type: string;
    ac: number;
    equipped: boolean;
  }>;
  items: Array<{
    name: string;
    quantity: number;
    category: string;
    description?: string;
  }>;
  starting_gold?: number;
}

interface SpellsAndAbilities {
  spells: Array<{
    name: string;
    level: number;
    school: string;
    prepared: boolean;
    casting_time: string;
    range: string;
    components: string[];
    duration: string;
    description: string;
  }>;
  class_features: Array<{
    name: string;
    level: number;
    description: string;
    uses?: number;
    recharge?: string;
  }>;
  racial_traits: Array<{
    name: string;
    description: string;
    source: string;
  }>;
  cantrips_known?: number;
  spells_known?: number;
  spell_slots?: Record<string, number>;
}

interface CharacterCreationWizardProps {
  onComplete: (characterName: string, filesCreated: string[]) => void;
  onCancel: () => void;
}

export const CharacterCreationWizard: React.FC<CharacterCreationWizardProps> = ({
  onComplete,
  onCancel
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isCreating, setIsCreating] = useState(false);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);

  // Step data
  const [characterBasics, setCharacterBasics] = useState<CharacterBasics>({
    name: '',
    race: '',
    subrace: '',
    character_class: '',
    level: 1,
    background: '',
    alignment: '',
    hit_points: 0,
    armor_class: 10,
    speed: 30,
    proficiency_bonus: 2
  });

  const [abilityScores, setAbilityScores] = useState<AbilityScores>({
    strength: 10,
    dexterity: 10,
    constitution: 10,
    intelligence: 10,
    wisdom: 10,
    charisma: 10
  });

  const [backgroundStory, setBackgroundStory] = useState<BackgroundStory>({
    personality_traits: [''],
    ideals: [''],
    bonds: [''],
    flaws: [''],
    backstory_sections: [{ title: 'Origin', content: '' }]
  });

  const [equipment, setEquipment] = useState<Equipment>({
    weapons: [],
    armor: [],
    items: [],
    starting_gold: 0
  });

  const [spellsAndAbilities, setSpellsAndAbilities] = useState<SpellsAndAbilities>({
    spells: [],
    class_features: [],
    racial_traits: [],
    cantrips_known: 0,
    spells_known: 0,
    spell_slots: {}
  });

  // Define wizard steps
  const steps: WizardStep[] = [
    {
      id: 'basics',
      title: 'Character Basics',
      icon: <User className="w-5 h-5" />,
      description: 'Name, race, class, level, and background',
      isComplete: false,
      isValid: false
    },
    {
      id: 'abilities',
      title: 'Ability Scores',
      icon: <Zap className="w-5 h-5" />,
      description: 'Strength, Dexterity, Constitution, Intelligence, Wisdom, Charisma',
      isComplete: false,
      isValid: true // Ability scores always have defaults
    },
    {
      id: 'background',
      title: 'Background & Story',
      icon: <BookOpen className="w-5 h-5" />,
      description: 'Personality traits, ideals, bonds, flaws, and backstory',
      isComplete: false,
      isValid: false
    },
    {
      id: 'equipment',
      title: 'Equipment & Inventory',
      icon: <Sword className="w-5 h-5" />,
      description: 'Starting weapons, armor, and items',
      isComplete: false,
      isValid: true // Equipment can be empty initially
    },
    {
      id: 'spells',
      title: 'Spells & Abilities',
      icon: <Sparkles className="w-5 h-5" />,
      description: 'Class features, racial traits, and spells',
      isComplete: false,
      isValid: true // Can be empty for non-casters
    },
    {
      id: 'review',
      title: 'Review & Create',
      icon: <Eye className="w-5 h-5" />,
      description: 'Review all information and create character files',
      isComplete: false,
      isValid: true
    }
  ];

  // Validation functions
  const validateBasics = useCallback((): boolean => {
    const errors: ValidationError[] = [];

    if (!characterBasics.name.trim()) {
      errors.push({
        field_path: 'name',
        message: 'Character name is required',
        error_type: 'required'
      });
    }

    if (!characterBasics.race.trim()) {
      errors.push({
        field_path: 'race',
        message: 'Race is required',
        error_type: 'required'
      });
    }

    if (!characterBasics.character_class.trim()) {
      errors.push({
        field_path: 'character_class',
        message: 'Class is required',
        error_type: 'required'
      });
    }

    if (characterBasics.level < 1 || characterBasics.level > 20) {
      errors.push({
        field_path: 'level',
        message: 'Level must be between 1 and 20',
        error_type: 'custom'
      });
    }

    setValidationErrors(errors);
    return errors.length === 0;
  }, [characterBasics]);

  const validateBackground = useCallback((): boolean => {
    const errors: ValidationError[] = [];

    if (backgroundStory.personality_traits.every(trait => !trait.trim())) {
      errors.push({
        field_path: 'personality_traits',
        message: 'At least one personality trait is required',
        error_type: 'required'
      });
    }

    setValidationErrors(errors);
    return errors.length === 0;
  }, [backgroundStory]);

  // Helper functions for calculating derived stats
  const calculateModifier = useCallback((score: number): number => {
    return Math.floor((score - 10) / 2);
  }, []);

  const calculateProficiencyBonus = useCallback((level: number): number => {
    return Math.ceil(level / 4) + 1;
  }, []);

  const calculateHitPoints = useCallback((level: number, constitution: number, characterClass: string): number => {
    const hitDie = getClassHitDie(characterClass);
    const conModifier = calculateModifier(constitution);
    return hitDie + conModifier + ((level - 1) * (Math.floor(hitDie / 2) + 1 + conModifier));
  }, [calculateModifier]);

  const getClassHitDie = useCallback((characterClass: string): number => {
    const hitDice: Record<string, number> = {
      'Barbarian': 12,
      'Fighter': 10,
      'Paladin': 10,
      'Ranger': 10,
      'Bard': 8,
      'Cleric': 8,
      'Druid': 8,
      'Monk': 8,
      'Rogue': 8,
      'Warlock': 8,
      'Sorcerer': 6,
      'Wizard': 6
    };
    return hitDice[characterClass] || 8;
  }, []);

  const getClassSpellcasting = useCallback((characterClass: string, level: number) => {
    const spellcastingClasses = ['Bard', 'Cleric', 'Druid', 'Sorcerer', 'Warlock', 'Wizard'];
    const halfCasters = ['Paladin', 'Ranger'];

    if (spellcastingClasses.includes(characterClass)) {
      return {
        cantrips_known: Math.min(4, Math.floor(level / 4) + 2),
        spells_known: characterClass === 'Wizard' ? level + 5 : Math.min(15, level + 1),
        spell_slots: getSpellSlots(characterClass, level)
      };
    } else if (halfCasters.includes(characterClass) && level >= 2) {
      const casterLevel = Math.floor(level / 2);
      return {
        cantrips_known: 0,
        spells_known: Math.min(5, casterLevel + 1),
        spell_slots: getSpellSlots(characterClass, casterLevel)
      };
    }
    return { cantrips_known: 0, spells_known: 0, spell_slots: {} };
  }, []);

  const getSpellSlots = useCallback((_characterClass: string, level: number): Record<string, number> => {
    // Simplified spell slot calculation
    const slots: Record<string, number> = {};
    if (level >= 1) slots['1'] = Math.min(4, level + 1);
    if (level >= 3) slots['2'] = Math.min(3, Math.floor(level / 2));
    if (level >= 5) slots['3'] = Math.min(3, Math.floor(level / 4) + 1);
    if (level >= 7) slots['4'] = Math.min(3, Math.floor(level / 6) + 1);
    if (level >= 9) slots['5'] = Math.min(2, Math.floor(level / 8) + 1);
    return slots;
  }, []);

  const populateClassFeatures = useCallback((characterClass: string, level: number) => {
    const features: Array<{ name: string; level: number; description: string; uses?: number; recharge?: string }> = [];

    // Add basic class features based on class and level
    switch (characterClass) {
      case 'Fighter':
        features.push({ name: 'Fighting Style', level: 1, description: 'Choose a fighting style that reflects your combat training.' });
        features.push({ name: 'Second Wind', level: 1, description: 'Regain hit points as a bonus action.', uses: 1, recharge: 'short rest' });
        if (level >= 2) features.push({ name: 'Action Surge', level: 2, description: 'Take an additional action on your turn.', uses: 1, recharge: 'short rest' });
        break;
      case 'Wizard':
        features.push({ name: 'Spellcasting', level: 1, description: 'Cast wizard spells using Intelligence as your spellcasting ability.' });
        features.push({ name: 'Arcane Recovery', level: 1, description: 'Recover spell slots during a short rest.', uses: 1, recharge: 'long rest' });
        break;
      case 'Rogue':
        features.push({ name: 'Expertise', level: 1, description: 'Double proficiency bonus for chosen skills.' });
        features.push({ name: 'Sneak Attack', level: 1, description: `Deal extra ${Math.ceil(level / 2)}d6 damage when you have advantage.` });
        if (level >= 2) features.push({ name: 'Cunning Action', level: 2, description: 'Dash, Disengage, or Hide as a bonus action.' });
        break;
      // Add more classes as needed
    }

    return features;
  }, []);

  const populateRacialTraits = useCallback((race: string, subrace?: string) => {
    const traits: Array<{ name: string; description: string; source: string }> = [];

    switch (race) {
      case 'Human':
        traits.push({ name: 'Extra Language', description: 'You can speak, read, and write one extra language.', source: 'Human' });
        traits.push({ name: 'Extra Skill', description: 'You gain proficiency in one skill of your choice.', source: 'Human' });
        break;
      case 'Elf':
        traits.push({ name: 'Darkvision', description: 'You can see in dim light within 60 feet as if it were bright light.', source: 'Elf' });
        traits.push({ name: 'Keen Senses', description: 'You have proficiency in the Perception skill.', source: 'Elf' });
        traits.push({ name: 'Fey Ancestry', description: 'You have advantage on saving throws against being charmed.', source: 'Elf' });
        if (subrace === 'High Elf') {
          traits.push({ name: 'Cantrip', description: 'You know one cantrip of your choice from the wizard spell list.', source: 'High Elf' });
        }
        break;
      case 'Dwarf':
        traits.push({ name: 'Darkvision', description: 'You can see in dim light within 60 feet as if it were bright light.', source: 'Dwarf' });
        traits.push({ name: 'Dwarven Resilience', description: 'You have advantage on saving throws against poison.', source: 'Dwarf' });
        traits.push({ name: 'Stonecunning', description: 'You have proficiency with mason\'s tools and double proficiency on History checks related to stonework.', source: 'Dwarf' });
        break;
      // Add more races as needed
    }

    return traits;
  }, []);

  const populateStartingEquipment = useCallback((characterClass: string, background: string) => {
    const equipment: Equipment = {
      weapons: [],
      armor: [],
      items: [],
      starting_gold: 0
    };

    // Add class-based starting equipment
    switch (characterClass) {
      case 'Fighter':
        equipment.weapons.push({ name: 'Longsword', type: 'Martial Melee', damage: '1d8 slashing', properties: ['Versatile'], equipped: true });
        equipment.armor.push({ name: 'Chain Mail', type: 'Heavy', ac: 16, equipped: true });
        equipment.items.push({ name: 'Shield', quantity: 1, category: 'Equipment', description: '+2 AC' });
        equipment.starting_gold = 125;
        break;
      case 'Wizard':
        equipment.weapons.push({ name: 'Dagger', type: 'Simple Melee', damage: '1d4 piercing', properties: ['Finesse', 'Light', 'Thrown'], equipped: true });
        equipment.items.push({ name: 'Spellbook', quantity: 1, category: 'Equipment', description: 'Contains your known spells' });
        equipment.items.push({ name: 'Component Pouch', quantity: 1, category: 'Equipment', description: 'Spellcasting focus' });
        equipment.starting_gold = 75;
        break;
      case 'Rogue':
        equipment.weapons.push({ name: 'Shortsword', type: 'Martial Melee', damage: '1d6 piercing', properties: ['Finesse', 'Light'], equipped: true });
        equipment.weapons.push({ name: 'Shortbow', type: 'Simple Ranged', damage: '1d6 piercing', properties: ['Ammunition', 'Two-Handed'], equipped: false });
        equipment.armor.push({ name: 'Leather Armor', type: 'Light', ac: 11, equipped: true });
        equipment.items.push({ name: 'Thieves\' Tools', quantity: 1, category: 'Equipment', description: 'For picking locks and disarming traps' });
        equipment.starting_gold = 100;
        break;
    }

    // Add background-based equipment
    switch (background) {
      case 'Soldier':
        equipment.items.push({ name: 'Insignia of Rank', quantity: 1, category: 'Equipment', description: 'Shows your military rank' });
        equipment.items.push({ name: 'Playing Card Set', quantity: 1, category: 'Equipment', description: 'For entertainment' });
        break;
      case 'Criminal':
        equipment.items.push({ name: 'Crowbar', quantity: 1, category: 'Equipment', description: 'Useful for breaking and entering' });
        equipment.items.push({ name: 'Dark Common Clothes', quantity: 1, category: 'Equipment', description: 'Inconspicuous clothing' });
        break;
    }

    return equipment;
  }, []);

  // Auto-calculate derived stats when relevant values change
  useEffect(() => {
    if (characterBasics.level && characterBasics.character_class) {
      const newProficiencyBonus = calculateProficiencyBonus(characterBasics.level);
      const newHitPoints = calculateHitPoints(characterBasics.level, abilityScores.constitution, characterBasics.character_class);

      setCharacterBasics(prev => ({
        ...prev,
        proficiency_bonus: newProficiencyBonus,
        hit_points: newHitPoints
      }));

      // Update spellcasting info
      const spellcastingInfo = getClassSpellcasting(characterBasics.character_class, characterBasics.level);
      setSpellsAndAbilities(prev => ({
        ...prev,
        ...spellcastingInfo,
        class_features: populateClassFeatures(characterBasics.character_class, characterBasics.level)
      }));
    }
  }, [characterBasics.level, characterBasics.character_class, abilityScores.constitution, calculateProficiencyBonus, calculateHitPoints, getClassSpellcasting, populateClassFeatures]);

  // Update racial traits when race changes
  useEffect(() => {
    if (characterBasics.race) {
      const racialTraits = populateRacialTraits(characterBasics.race, characterBasics.subrace);
      setSpellsAndAbilities(prev => ({
        ...prev,
        racial_traits: racialTraits
      }));
    }
  }, [characterBasics.race, characterBasics.subrace, populateRacialTraits]);

  // Update equipment when class or background changes
  useEffect(() => {
    if (characterBasics.character_class && characterBasics.background) {
      const startingEquipment = populateStartingEquipment(characterBasics.character_class, characterBasics.background);
      setEquipment(startingEquipment);
    }
  }, [characterBasics.character_class, characterBasics.background, populateStartingEquipment]);

  // Update step validation status
  useEffect(() => {
    steps[0].isValid = validateBasics();
    steps[2].isValid = validateBackground();
  }, [characterBasics, backgroundStory, validateBasics, validateBackground]);

  // Navigation functions
  const canGoNext = useCallback((): boolean => {
    if (currentStep >= steps.length - 1) return false;
    return steps[currentStep].isValid;
  }, [currentStep, steps]);

  const canGoPrevious = useCallback((): boolean => {
    return currentStep > 0;
  }, [currentStep]);

  const goNext = useCallback(() => {
    if (canGoNext()) {
      steps[currentStep].isComplete = true;
      setCurrentStep(prev => prev + 1);
    }
  }, [canGoNext, currentStep, steps]);

  const goPrevious = useCallback(() => {
    if (canGoPrevious()) {
      setCurrentStep(prev => prev - 1);
    }
  }, [canGoPrevious]);

  // Character creation function
  const createCharacter = useCallback(async () => {
    setIsCreating(true);
    try {
      const request: CharacterCreationRequest = {
        character_name: characterBasics.name,
        race: characterBasics.race,
        character_class: characterBasics.character_class,
        level: characterBasics.level,
        background: characterBasics.background,
        alignment: characterBasics.alignment,
        ability_scores: {
          strength: abilityScores.strength,
          dexterity: abilityScores.dexterity,
          constitution: abilityScores.constitution,
          intelligence: abilityScores.intelligence,
          wisdom: abilityScores.wisdom,
          charisma: abilityScores.charisma
        }
      };

      const response = await createNewCharacter(request);
      onComplete(response.character_name, response.files_created);
    } catch (error) {
      console.error('Failed to create character:', error);
      setValidationErrors([{
        field_path: 'creation',
        message: 'Failed to create character. Please try again.',
        error_type: 'custom'
      }]);
    } finally {
      setIsCreating(false);
    }
  }, [characterBasics, abilityScores, onComplete]);

  // Render step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return renderBasicsStep();
      case 1:
        return renderAbilitiesStep();
      case 2:
        return renderBackgroundStep();
      case 3:
        return renderEquipmentStep();
      case 4:
        return renderSpellsStep();
      case 5:
        return renderReviewStep();
      default:
        return null;
    }
  };

  const renderBasicsStep = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="block text-sm font-medium text-white">
            Character Name <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={characterBasics.name}
            onChange={(e) => setCharacterBasics(prev => ({ ...prev, name: e.target.value }))}
            placeholder="Enter character name"
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-white">
            Race <span className="text-red-400">*</span>
          </label>
          <select
            value={characterBasics.race}
            onChange={(e) => setCharacterBasics(prev => ({ ...prev, race: e.target.value }))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">Select race</option>
            <option value="Human">Human</option>
            <option value="Elf">Elf</option>
            <option value="Dwarf">Dwarf</option>
            <option value="Halfling">Halfling</option>
            <option value="Dragonborn">Dragonborn</option>
            <option value="Gnome">Gnome</option>
            <option value="Half-Elf">Half-Elf</option>
            <option value="Half-Orc">Half-Orc</option>
            <option value="Tiefling">Tiefling</option>
          </select>
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-white">Subrace</label>
          <input
            type="text"
            value={characterBasics.subrace || ''}
            onChange={(e) => setCharacterBasics(prev => ({ ...prev, subrace: e.target.value }))}
            placeholder="e.g., Hill Dwarf, High Elf"
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-white">
            Class <span className="text-red-400">*</span>
          </label>
          <select
            value={characterBasics.character_class}
            onChange={(e) => setCharacterBasics(prev => ({ ...prev, character_class: e.target.value }))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">Select class</option>
            <option value="Barbarian">Barbarian</option>
            <option value="Bard">Bard</option>
            <option value="Cleric">Cleric</option>
            <option value="Druid">Druid</option>
            <option value="Fighter">Fighter</option>
            <option value="Monk">Monk</option>
            <option value="Paladin">Paladin</option>
            <option value="Ranger">Ranger</option>
            <option value="Rogue">Rogue</option>
            <option value="Sorcerer">Sorcerer</option>
            <option value="Warlock">Warlock</option>
            <option value="Wizard">Wizard</option>
          </select>
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-white">Level</label>
          <input
            type="number"
            value={characterBasics.level}
            onChange={(e) => setCharacterBasics(prev => ({ ...prev, level: Number(e.target.value) || 1 }))}
            min={1}
            max={20}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-white">Background</label>
          <select
            value={characterBasics.background}
            onChange={(e) => setCharacterBasics(prev => ({ ...prev, background: e.target.value }))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">Select background</option>
            <option value="Acolyte">Acolyte</option>
            <option value="Criminal">Criminal</option>
            <option value="Folk Hero">Folk Hero</option>
            <option value="Noble">Noble</option>
            <option value="Sage">Sage</option>
            <option value="Soldier">Soldier</option>
            <option value="Charlatan">Charlatan</option>
            <option value="Entertainer">Entertainer</option>
            <option value="Guild Artisan">Guild Artisan</option>
            <option value="Hermit">Hermit</option>
            <option value="Outlander">Outlander</option>
            <option value="Sailor">Sailor</option>
          </select>
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-white">Alignment</label>
          <select
            value={characterBasics.alignment}
            onChange={(e) => setCharacterBasics(prev => ({ ...prev, alignment: e.target.value }))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">Select alignment</option>
            <option value="Lawful Good">Lawful Good</option>
            <option value="Neutral Good">Neutral Good</option>
            <option value="Chaotic Good">Chaotic Good</option>
            <option value="Lawful Neutral">Lawful Neutral</option>
            <option value="True Neutral">True Neutral</option>
            <option value="Chaotic Neutral">Chaotic Neutral</option>
            <option value="Lawful Evil">Lawful Evil</option>
            <option value="Neutral Evil">Neutral Evil</option>
            <option value="Chaotic Evil">Chaotic Evil</option>
          </select>
        </div>
      </div>

      {/* Combat Stats Section */}
      {characterBasics.character_class && (
        <div className="mt-8 p-4 bg-gray-750 rounded-md">
          <h4 className="text-white font-medium mb-4 flex items-center">
            <Shield className="w-5 h-5 mr-2" />
            Combat Statistics
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <label className="block text-sm font-medium text-gray-300 mb-1">Hit Points</label>
              <div className="flex items-center justify-center">
                <Heart className="w-4 h-4 text-red-400 mr-1" />
                <span className="text-xl font-bold text-white">{characterBasics.hit_points}</span>
              </div>
              <div className="text-xs text-gray-400">
                Level {characterBasics.level} {characterBasics.character_class}
              </div>
            </div>

            <div className="text-center">
              <label className="block text-sm font-medium text-gray-300 mb-1">Armor Class</label>
              <div className="flex items-center justify-center">
                <Shield className="w-4 h-4 text-blue-400 mr-1" />
                <span className="text-xl font-bold text-white">{characterBasics.armor_class}</span>
              </div>
              <div className="text-xs text-gray-400">Base AC</div>
            </div>

            <div className="text-center">
              <label className="block text-sm font-medium text-gray-300 mb-1">Speed</label>
              <div className="flex items-center justify-center">
                <span className="text-xl font-bold text-white">{characterBasics.speed}</span>
                <span className="text-sm text-gray-400 ml-1">ft</span>
              </div>
              <div className="text-xs text-gray-400">Movement</div>
            </div>

            <div className="text-center">
              <label className="block text-sm font-medium text-gray-300 mb-1">Proficiency</label>
              <div className="flex items-center justify-center">
                <Star className="w-4 h-4 text-yellow-400 mr-1" />
                <span className="text-xl font-bold text-white">+{characterBasics.proficiency_bonus}</span>
              </div>
              <div className="text-xs text-gray-400">Bonus</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderAbilitiesStep = () => {
    const totalPointsUsed = Object.values(abilityScores).reduce((total, score) => {
      if (score <= 13) return total + (score - 8);
      if (score === 14) return total + 7;
      if (score === 15) return total + 9;
      return total + 9; // Cap at 15 for point buy
    }, 0);

    const pointsRemaining = 27 - totalPointsUsed;

    return (
      <div className="space-y-6">
        <div className="text-center mb-6">
          <p className="text-gray-300 mb-2">
            Set your character's ability scores. You can use standard array, point buy (27 points), or manual entry.
          </p>
          <div className="bg-blue-900/20 border border-blue-500/30 p-3 rounded-md inline-block">
            <span className="text-blue-300 font-medium">Point Buy: </span>
            <span className={`font-bold ${pointsRemaining >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {pointsRemaining} points remaining
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          {Object.entries(abilityScores).map(([ability, score]) => {
            const modifier = calculateModifier(score);
            const isRecommendedForClass = getRecommendedAbilities(characterBasics.character_class).includes(ability);

            return (
              <div key={ability} className={`text-center p-4 rounded-md border-2 ${isRecommendedForClass ? 'border-yellow-500/50 bg-yellow-900/10' : 'border-gray-600'
                }`}>
                <label className="block text-sm font-medium text-white capitalize mb-2 flex items-center justify-center">
                  {ability}
                  {isRecommendedForClass && (
                    <Star className="w-4 h-4 text-yellow-400 ml-1" />
                  )}
                </label>

                <div className="flex items-center justify-center space-x-2 mb-2">
                  <button
                    type="button"
                    onClick={() => {
                      if (score > 8) {
                        setAbilityScores(prev => ({
                          ...prev,
                          [ability]: score - 1
                        }));
                      }
                    }}
                    disabled={score <= 8}
                    className="w-8 h-8 bg-red-600 text-white rounded-full hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                  >
                    <Minus className="w-4 h-4" />
                  </button>

                  <input
                    type="number"
                    value={score}
                    onChange={(e) => setAbilityScores(prev => ({
                      ...prev,
                      [ability]: Math.max(1, Math.min(30, Number(e.target.value) || 8))
                    }))}
                    min={1}
                    max={30}
                    className="w-16 h-16 text-center text-xl font-bold bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />

                  <button
                    type="button"
                    onClick={() => {
                      if (score < 15) {
                        setAbilityScores(prev => ({
                          ...prev,
                          [ability]: score + 1
                        }));
                      }
                    }}
                    disabled={score >= 15}
                    className="w-8 h-8 bg-green-600 text-white rounded-full hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>

                <div className="text-xs text-gray-400">
                  Modifier: {modifier >= 0 ? '+' : ''}{modifier}
                </div>

                {isRecommendedForClass && (
                  <div className="text-xs text-yellow-400 mt-1">
                    Primary for {characterBasics.character_class}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="flex justify-center space-x-4 mt-6">
          <button
            type="button"
            onClick={() => {
              setAbilityScores({
                strength: 15,
                dexterity: 14,
                constitution: 13,
                intelligence: 12,
                wisdom: 10,
                charisma: 8
              });
            }}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
          >
            Use Standard Array
          </button>

          <button
            type="button"
            onClick={() => {
              // Roll 4d6 drop lowest for each ability
              const rollAbilityScore = () => {
                const rolls = Array.from({ length: 4 }, () => Math.floor(Math.random() * 6) + 1);
                rolls.sort((a, b) => b - a);
                return rolls.slice(0, 3).reduce((sum, roll) => sum + roll, 0);
              };

              setAbilityScores({
                strength: rollAbilityScore(),
                dexterity: rollAbilityScore(),
                constitution: rollAbilityScore(),
                intelligence: rollAbilityScore(),
                wisdom: rollAbilityScore(),
                charisma: rollAbilityScore()
              });
            }}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors flex items-center"
          >
            <Dice6 className="w-4 h-4 mr-2" />
            Roll Stats
          </button>

          <button
            type="button"
            onClick={() => {
              setAbilityScores({
                strength: 10,
                dexterity: 10,
                constitution: 10,
                intelligence: 10,
                wisdom: 10,
                charisma: 10
              });
            }}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
          >
            Reset to 10s
          </button>
        </div>
      </div>
    );
  };

  const getRecommendedAbilities = useCallback((characterClass: string): string[] => {
    const recommendations: Record<string, string[]> = {
      'Barbarian': ['strength', 'constitution'],
      'Bard': ['charisma', 'dexterity'],
      'Cleric': ['wisdom', 'constitution'],
      'Druid': ['wisdom', 'constitution'],
      'Fighter': ['strength', 'constitution'],
      'Monk': ['dexterity', 'wisdom'],
      'Paladin': ['strength', 'charisma'],
      'Ranger': ['dexterity', 'wisdom'],
      'Rogue': ['dexterity', 'intelligence'],
      'Sorcerer': ['charisma', 'constitution'],
      'Warlock': ['charisma', 'constitution'],
      'Wizard': ['intelligence', 'constitution']
    };
    return recommendations[characterClass] || [];
  }, []);

  const getBackgroundPrompts = useCallback((background: string) => {
    const prompts: Record<string, {
      description: string;
      personalityPrompts: string[];
      idealPrompts: string[];
      bondPrompts: string[];
      flawPrompts: string[];
    }> = {
      'Soldier': {
        description: 'You served in a military organization, learning discipline and tactics.',
        personalityPrompts: [
          'I\'m always polite and respectful.',
          'I\'m haunted by memories of war.',
          'I face problems head-on.',
          'I enjoy being strong and like breaking things.'
        ],
        idealPrompts: [
          'Greater Good: Our lot is to lay down our lives in defense of others.',
          'Responsibility: I do what I must and obey just authority.',
          'Independence: When people follow orders blindly, they embrace a kind of tyranny.',
          'Might: In life as in war, the stronger force wins.'
        ],
        bondPrompts: [
          'I would still lay down my life for the people I served with.',
          'Someone saved my life on the battlefield.',
          'My honor is my life.',
          'I\'ll never forget the crushing defeat my company suffered.'
        ],
        flawPrompts: [
          'The monstrous enemy we faced in battle still leaves me quivering with fear.',
          'I have little respect for anyone who is not a proven warrior.',
          'I made a terrible mistake in battle that cost many lives.',
          'My hatred of my enemies is blind and unreasoning.'
        ]
      },
      'Criminal': {
        description: 'You lived on the wrong side of the law, developing skills in stealth and deception.',
        personalityPrompts: [
          'I always have a plan for what to do when things go wrong.',
          'I am incredibly slow to trust.',
          'I don\'t pay attention to the risks in a situation.',
          'The best way to get me to do something is to tell me I can\'t do it.'
        ],
        idealPrompts: [
          'Honor: I don\'t steal from others in the trade.',
          'Freedom: Chains are meant to be broken.',
          'Charity: I steal from the wealthy so that I can help people in need.',
          'Greed: I will do whatever it takes to become wealthy.'
        ],
        bondPrompts: [
          'I\'m trying to pay off an old debt I owe to a generous benefactor.',
          'My ill-gotten gains go to support my family.',
          'Something important was taken from me, and I aim to steal it back.',
          'I will become the greatest thief that ever lived.'
        ],
        flawPrompts: [
          'When I see something valuable, I can\'t think about anything but how to steal it.',
          'When faced with a choice between money and my friends, I usually choose the money.',
          'If there\'s a plan, I\'ll forget it. If I don\'t forget it, I\'ll ignore it.',
          'I have a "tell" that reveals when I\'m lying.'
        ]
      },
      'Folk Hero': {
        description: 'You came from humble origins but rose to defend your community against tyranny.',
        personalityPrompts: [
          'I judge people by their actions, not their words.',
          'If someone is in trouble, I\'m always ready to lend help.',
          'When I set my mind to something, I follow through no matter what gets in my way.',
          'I have a strong sense of fair play and always try to find the most equitable solution.'
        ],
        idealPrompts: [
          'Respect: People deserve to be treated with dignity and respect.',
          'Fairness: No one should get preferential treatment before the law.',
          'Freedom: Tyrants must not be allowed to oppress the people.',
          'Might: If I become strong, I can take what I want.'
        ],
        bondPrompts: [
          'I have a family, but I have no idea where they are.',
          'I worked the land, I love the land, and I will protect the land.',
          'A proud noble once gave me a horrible beating, and I will take my revenge.',
          'My tools are symbols of my past life, and I carry them so that I will never forget my roots.'
        ],
        flawPrompts: [
          'The tyrant who rules my land will stop at nothing to see me killed.',
          'I\'m convinced of the significance of my destiny, and blind to my shortcomings.',
          'The people who knew me when I was young know my shameful secret.',
          'I have trouble trusting in my allies.'
        ]
      }
    };

    return prompts[background] || {
      description: 'A unique background that shapes your character\'s past.',
      personalityPrompts: [],
      idealPrompts: [],
      bondPrompts: [],
      flawPrompts: []
    };
  }, []);

  const renderBackgroundStep = () => {
    const backgroundPrompts = getBackgroundPrompts(characterBasics.background);

    return (
      <div className="space-y-6">
        {/* Background-specific guidance */}
        {characterBasics.background && (
          <div className="bg-blue-900/20 border border-blue-500/30 p-4 rounded-md">
            <h4 className="text-blue-300 font-medium mb-2 flex items-center">
              <Info className="w-4 h-4 mr-2" />
              {characterBasics.background} Background Guide
            </h4>
            <p className="text-blue-200 text-sm">
              {backgroundPrompts.description}
            </p>
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Personality Traits <span className="text-red-400">*</span>
            </label>
            {backgroundPrompts.personalityPrompts.length > 0 && (
              <div className="mb-3 p-3 bg-gray-750 rounded-md">
                <p className="text-gray-300 text-sm mb-2">Suggestions for {characterBasics.background}:</p>
                <div className="flex flex-wrap gap-2">
                  {backgroundPrompts.personalityPrompts.map((prompt, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => {
                        const emptyIndex = backgroundStory.personality_traits.findIndex(trait => !trait.trim());
                        if (emptyIndex !== -1) {
                          const newTraits = [...backgroundStory.personality_traits];
                          newTraits[emptyIndex] = prompt;
                          setBackgroundStory(prev => ({ ...prev, personality_traits: newTraits }));
                        } else {
                          setBackgroundStory(prev => ({
                            ...prev,
                            personality_traits: [...prev.personality_traits, prompt]
                          }));
                        }
                      }}
                      className="px-2 py-1 bg-purple-600/20 text-purple-300 rounded text-xs hover:bg-purple-600/40 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {backgroundStory.personality_traits.map((trait, index) => (
              <div key={index} className="flex space-x-2 mb-2">
                <input
                  type="text"
                  value={trait}
                  onChange={(e) => {
                    const newTraits = [...backgroundStory.personality_traits];
                    newTraits[index] = e.target.value;
                    setBackgroundStory(prev => ({ ...prev, personality_traits: newTraits }));
                  }}
                  placeholder="Describe a personality trait"
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                {backgroundStory.personality_traits.length > 1 && (
                  <button
                    type="button"
                    onClick={() => {
                      const newTraits = backgroundStory.personality_traits.filter((_, i) => i !== index);
                      setBackgroundStory(prev => ({ ...prev, personality_traits: newTraits }));
                    }}
                    className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={() => {
                setBackgroundStory(prev => ({
                  ...prev,
                  personality_traits: [...prev.personality_traits, '']
                }));
              }}
              className="px-3 py-1 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm"
            >
              Add Trait
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-white mb-2">Ideals</label>
            {backgroundPrompts.idealPrompts.length > 0 && (
              <div className="mb-3 p-3 bg-gray-750 rounded-md">
                <p className="text-gray-300 text-sm mb-2">Suggestions for {characterBasics.background}:</p>
                <div className="space-y-1">
                  {backgroundPrompts.idealPrompts.map((prompt, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => {
                        const emptyIndex = backgroundStory.ideals.findIndex(ideal => !ideal.trim());
                        if (emptyIndex !== -1) {
                          const newIdeals = [...backgroundStory.ideals];
                          newIdeals[emptyIndex] = prompt;
                          setBackgroundStory(prev => ({ ...prev, ideals: newIdeals }));
                        } else {
                          setBackgroundStory(prev => ({
                            ...prev,
                            ideals: [...prev.ideals, prompt]
                          }));
                        }
                      }}
                      className="block w-full text-left px-2 py-1 bg-purple-600/20 text-purple-300 rounded text-xs hover:bg-purple-600/40 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {backgroundStory.ideals.map((ideal, index) => (
              <div key={index} className="flex space-x-2 mb-2">
                <input
                  type="text"
                  value={ideal}
                  onChange={(e) => {
                    const newIdeals = [...backgroundStory.ideals];
                    newIdeals[index] = e.target.value;
                    setBackgroundStory(prev => ({ ...prev, ideals: newIdeals }));
                  }}
                  placeholder="Describe an ideal"
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                {backgroundStory.ideals.length > 1 && (
                  <button
                    type="button"
                    onClick={() => {
                      const newIdeals = backgroundStory.ideals.filter((_, i) => i !== index);
                      setBackgroundStory(prev => ({ ...prev, ideals: newIdeals }));
                    }}
                    className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={() => {
                setBackgroundStory(prev => ({
                  ...prev,
                  ideals: [...prev.ideals, '']
                }));
              }}
              className="px-3 py-1 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm"
            >
              Add Ideal
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-white mb-2">Bonds</label>
            {backgroundPrompts.bondPrompts.length > 0 && (
              <div className="mb-3 p-3 bg-gray-750 rounded-md">
                <p className="text-gray-300 text-sm mb-2">Suggestions for {characterBasics.background}:</p>
                <div className="space-y-1">
                  {backgroundPrompts.bondPrompts.map((prompt, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => {
                        const emptyIndex = backgroundStory.bonds.findIndex(bond => !bond.trim());
                        if (emptyIndex !== -1) {
                          const newBonds = [...backgroundStory.bonds];
                          newBonds[emptyIndex] = prompt;
                          setBackgroundStory(prev => ({ ...prev, bonds: newBonds }));
                        } else {
                          setBackgroundStory(prev => ({
                            ...prev,
                            bonds: [...prev.bonds, prompt]
                          }));
                        }
                      }}
                      className="block w-full text-left px-2 py-1 bg-purple-600/20 text-purple-300 rounded text-xs hover:bg-purple-600/40 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {backgroundStory.bonds.map((bond, index) => (
              <div key={index} className="flex space-x-2 mb-2">
                <input
                  type="text"
                  value={bond}
                  onChange={(e) => {
                    const newBonds = [...backgroundStory.bonds];
                    newBonds[index] = e.target.value;
                    setBackgroundStory(prev => ({ ...prev, bonds: newBonds }));
                  }}
                  placeholder="Describe a bond"
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                {backgroundStory.bonds.length > 1 && (
                  <button
                    type="button"
                    onClick={() => {
                      const newBonds = backgroundStory.bonds.filter((_, i) => i !== index);
                      setBackgroundStory(prev => ({ ...prev, bonds: newBonds }));
                    }}
                    className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={() => {
                setBackgroundStory(prev => ({
                  ...prev,
                  bonds: [...prev.bonds, '']
                }));
              }}
              className="px-3 py-1 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm"
            >
              Add Bond
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-white mb-2">Flaws</label>
            {backgroundPrompts.flawPrompts.length > 0 && (
              <div className="mb-3 p-3 bg-gray-750 rounded-md">
                <p className="text-gray-300 text-sm mb-2">Suggestions for {characterBasics.background}:</p>
                <div className="space-y-1">
                  {backgroundPrompts.flawPrompts.map((prompt, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => {
                        const emptyIndex = backgroundStory.flaws.findIndex(flaw => !flaw.trim());
                        if (emptyIndex !== -1) {
                          const newFlaws = [...backgroundStory.flaws];
                          newFlaws[emptyIndex] = prompt;
                          setBackgroundStory(prev => ({ ...prev, flaws: newFlaws }));
                        } else {
                          setBackgroundStory(prev => ({
                            ...prev,
                            flaws: [...prev.flaws, prompt]
                          }));
                        }
                      }}
                      className="block w-full text-left px-2 py-1 bg-purple-600/20 text-purple-300 rounded text-xs hover:bg-purple-600/40 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {backgroundStory.flaws.map((flaw, index) => (
              <div key={index} className="flex space-x-2 mb-2">
                <input
                  type="text"
                  value={flaw}
                  onChange={(e) => {
                    const newFlaws = [...backgroundStory.flaws];
                    newFlaws[index] = e.target.value;
                    setBackgroundStory(prev => ({ ...prev, flaws: newFlaws }));
                  }}
                  placeholder="Describe a flaw"
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                {backgroundStory.flaws.length > 1 && (
                  <button
                    type="button"
                    onClick={() => {
                      const newFlaws = backgroundStory.flaws.filter((_, i) => i !== index);
                      setBackgroundStory(prev => ({ ...prev, flaws: newFlaws }));
                    }}
                    className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={() => {
                setBackgroundStory(prev => ({
                  ...prev,
                  flaws: [...prev.flaws, '']
                }));
              }}
              className="px-3 py-1 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm"
            >
              Add Flaw
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-white mb-2">Backstory Sections</label>
            {backgroundStory.backstory_sections.map((section, index) => (
              <div key={index} className="space-y-2 mb-4 p-4 bg-gray-750 rounded-md">
                <input
                  type="text"
                  value={section.title}
                  onChange={(e) => {
                    const newSections = [...backgroundStory.backstory_sections];
                    newSections[index] = { ...newSections[index], title: e.target.value };
                    setBackgroundStory(prev => ({ ...prev, backstory_sections: newSections }));
                  }}
                  placeholder="Section title"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <textarea
                  value={section.content}
                  onChange={(e) => {
                    const newSections = [...backgroundStory.backstory_sections];
                    newSections[index] = { ...newSections[index], content: e.target.value };
                    setBackgroundStory(prev => ({ ...prev, backstory_sections: newSections }));
                  }}
                  placeholder="Write your character's backstory..."
                  rows={4}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                {backgroundStory.backstory_sections.length > 1 && (
                  <button
                    type="button"
                    onClick={() => {
                      const newSections = backgroundStory.backstory_sections.filter((_, i) => i !== index);
                      setBackgroundStory(prev => ({ ...prev, backstory_sections: newSections }));
                    }}
                    className="px-3 py-1 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
                  >
                    Remove Section
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={() => {
                setBackgroundStory(prev => ({
                  ...prev,
                  backstory_sections: [...prev.backstory_sections, { title: '', content: '' }]
                }));
              }}
              className="px-3 py-1 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm"
            >
              Add Section
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderEquipmentStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <p className="text-gray-300">
          Starting equipment based on your {characterBasics.character_class} class and {characterBasics.background} background.
          You can modify this equipment after character creation.
        </p>
        {equipment.starting_gold && equipment.starting_gold > 0 && (
          <div className="mt-2 inline-block bg-yellow-900/20 border border-yellow-500/30 px-3 py-1 rounded-md">
            <span className="text-yellow-300">Starting Gold: {equipment.starting_gold} gp</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Weapons */}
        <div className="bg-gray-750 p-4 rounded-md">
          <h4 className="text-white font-medium mb-3 flex items-center">
            <Sword className="w-4 h-4 mr-2" />
            Weapons ({equipment.weapons.length})
          </h4>
          {equipment.weapons.length > 0 ? (
            <div className="space-y-2">
              {equipment.weapons.map((weapon, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-700 rounded">
                  <div>
                    <div className="text-white text-sm font-medium">{weapon.name}</div>
                    <div className="text-gray-400 text-xs">{weapon.damage} • {weapon.type}</div>
                    {weapon.properties.length > 0 && (
                      <div className="text-gray-500 text-xs">{weapon.properties.join(', ')}</div>
                    )}
                  </div>
                  {weapon.equipped && (
                    <div className="text-green-400 text-xs">Equipped</div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">No starting weapons</p>
          )}
        </div>

        {/* Armor */}
        <div className="bg-gray-750 p-4 rounded-md">
          <h4 className="text-white font-medium mb-3 flex items-center">
            <Shield className="w-4 h-4 mr-2" />
            Armor ({equipment.armor.length})
          </h4>
          {equipment.armor.length > 0 ? (
            <div className="space-y-2">
              {equipment.armor.map((armor, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-700 rounded">
                  <div>
                    <div className="text-white text-sm font-medium">{armor.name}</div>
                    <div className="text-gray-400 text-xs">AC {armor.ac} • {armor.type}</div>
                  </div>
                  {armor.equipped && (
                    <div className="text-green-400 text-xs">Equipped</div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">No starting armor</p>
          )}
        </div>

        {/* Items */}
        <div className="bg-gray-750 p-4 rounded-md">
          <h4 className="text-white font-medium mb-3 flex items-center">
            <BookOpen className="w-4 h-4 mr-2" />
            Equipment ({equipment.items.length})
          </h4>
          {equipment.items.length > 0 ? (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {equipment.items.map((item, index) => (
                <div key={index} className="p-2 bg-gray-700 rounded">
                  <div className="flex items-center justify-between">
                    <div className="text-white text-sm font-medium">{item.name}</div>
                    {item.quantity > 1 && (
                      <div className="text-gray-400 text-xs">×{item.quantity}</div>
                    )}
                  </div>
                  <div className="text-gray-400 text-xs">{item.category}</div>
                  {item.description && (
                    <div className="text-gray-500 text-xs mt-1">{item.description}</div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">No starting equipment</p>
          )}
        </div>
      </div>

      {/* Equipment customization options */}
      <div className="bg-blue-900/20 border border-blue-500/30 p-4 rounded-md">
        <h4 className="text-blue-300 font-medium mb-2">Equipment Options</h4>
        <p className="text-blue-200 text-sm mb-3">
          You can customize your starting equipment by adding or removing items:
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => {
              setEquipment(prev => ({
                ...prev,
                items: [...prev.items, { name: 'Rope (50 feet)', quantity: 1, category: 'Adventuring Gear', description: 'Hemp rope' }]
              }));
            }}
            className="px-3 py-1 bg-purple-600 text-white rounded text-sm hover:bg-purple-700 transition-colors"
          >
            Add Rope
          </button>
          <button
            type="button"
            onClick={() => {
              setEquipment(prev => ({
                ...prev,
                items: [...prev.items, { name: 'Torch', quantity: 5, category: 'Adventuring Gear', description: 'Provides bright light' }]
              }));
            }}
            className="px-3 py-1 bg-purple-600 text-white rounded text-sm hover:bg-purple-700 transition-colors"
          >
            Add Torches
          </button>
          <button
            type="button"
            onClick={() => {
              setEquipment(prev => ({
                ...prev,
                items: [...prev.items, { name: 'Rations', quantity: 10, category: 'Adventuring Gear', description: 'Trail rations for 10 days' }]
              }));
            }}
            className="px-3 py-1 bg-purple-600 text-white rounded text-sm hover:bg-purple-700 transition-colors"
          >
            Add Rations
          </button>
        </div>
      </div>
    </div>
  );

  const renderSpellsStep = () => {
    const isSpellcaster = ['Bard', 'Cleric', 'Druid', 'Sorcerer', 'Warlock', 'Wizard'].includes(characterBasics.character_class);
    const isHalfCaster = ['Paladin', 'Ranger'].includes(characterBasics.character_class) && characterBasics.level >= 2;

    return (
      <div className="space-y-6">
        <div className="text-center mb-6">
          <p className="text-gray-300">
            Abilities and features for your level {characterBasics.level} {characterBasics.race} {characterBasics.character_class}.
            You can modify these after character creation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Class Features */}
          <div className="bg-gray-750 p-4 rounded-md">
            <h4 className="text-white font-medium mb-3 flex items-center">
              <Star className="w-4 h-4 mr-2" />
              Class Features ({spellsAndAbilities.class_features.length})
            </h4>
            {spellsAndAbilities.class_features.length > 0 ? (
              <div className="space-y-3 max-h-48 overflow-y-auto">
                {spellsAndAbilities.class_features.map((feature, index) => (
                  <div key={index} className="p-3 bg-gray-700 rounded">
                    <div className="flex items-center justify-between mb-1">
                      <div className="text-white text-sm font-medium">{feature.name}</div>
                      <div className="text-gray-400 text-xs">Level {feature.level}</div>
                    </div>
                    <div className="text-gray-300 text-xs mb-1">{feature.description}</div>
                    {(feature.uses || feature.recharge) && (
                      <div className="text-blue-400 text-xs">
                        {feature.uses && `${feature.uses} use${feature.uses > 1 ? 's' : ''}`}
                        {feature.uses && feature.recharge && ' • '}
                        {feature.recharge && `Recharges on ${feature.recharge}`}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-sm">No class features at this level</p>
            )}
          </div>

          {/* Racial Traits */}
          <div className="bg-gray-750 p-4 rounded-md">
            <h4 className="text-white font-medium mb-3 flex items-center">
              <User className="w-4 h-4 mr-2" />
              Racial Traits ({spellsAndAbilities.racial_traits.length})
            </h4>
            {spellsAndAbilities.racial_traits.length > 0 ? (
              <div className="space-y-3 max-h-48 overflow-y-auto">
                {spellsAndAbilities.racial_traits.map((trait, index) => (
                  <div key={index} className="p-3 bg-gray-700 rounded">
                    <div className="flex items-center justify-between mb-1">
                      <div className="text-white text-sm font-medium">{trait.name}</div>
                      <div className="text-gray-400 text-xs">{trait.source}</div>
                    </div>
                    <div className="text-gray-300 text-xs">{trait.description}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-sm">No racial traits available</p>
            )}
          </div>
        </div>

        {/* Spellcasting Section */}
        {(isSpellcaster || isHalfCaster) && (
          <div className="bg-gray-750 p-4 rounded-md">
            <h4 className="text-white font-medium mb-3 flex items-center">
              <Sparkles className="w-4 h-4 mr-2" />
              Spellcasting
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              {spellsAndAbilities.cantrips_known && spellsAndAbilities.cantrips_known > 0 && (
                <div className="text-center p-3 bg-gray-700 rounded">
                  <div className="text-purple-400 text-lg font-bold">{spellsAndAbilities.cantrips_known}</div>
                  <div className="text-gray-300 text-sm">Cantrips Known</div>
                </div>
              )}

              {spellsAndAbilities.spells_known && spellsAndAbilities.spells_known > 0 && (
                <div className="text-center p-3 bg-gray-700 rounded">
                  <div className="text-blue-400 text-lg font-bold">{spellsAndAbilities.spells_known}</div>
                  <div className="text-gray-300 text-sm">Spells Known</div>
                </div>
              )}

              {spellsAndAbilities.spell_slots && Object.keys(spellsAndAbilities.spell_slots).length > 0 && (
                <div className="text-center p-3 bg-gray-700 rounded">
                  <div className="text-green-400 text-lg font-bold">
                    {spellsAndAbilities.spell_slots ? Object.values(spellsAndAbilities.spell_slots).reduce((sum, slots) => sum + slots, 0) : 0}
                  </div>
                  <div className="text-gray-300 text-sm">Total Spell Slots</div>
                </div>
              )}
            </div>

            {/* Spell Slots Breakdown */}
            {spellsAndAbilities.spell_slots && Object.keys(spellsAndAbilities.spell_slots).length > 0 && (
              <div className="mb-4">
                <h5 className="text-gray-300 text-sm font-medium mb-2">Spell Slots by Level:</h5>
                <div className="flex flex-wrap gap-2">
                  {spellsAndAbilities.spell_slots && Object.entries(spellsAndAbilities.spell_slots).map(([level, slots]) => (
                    <div key={level} className="px-3 py-1 bg-gray-600 rounded text-sm">
                      <span className="text-white">Level {level}:</span>
                      <span className="text-green-400 ml-1">{slots}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Sample Spells */}
            <div className="bg-blue-900/20 border border-blue-500/30 p-3 rounded">
              <h5 className="text-blue-300 text-sm font-medium mb-2">Sample Starting Spells:</h5>
              <p className="text-blue-200 text-xs">
                {characterBasics.character_class === 'Wizard' && 'You start with 6 1st-level spells in your spellbook, plus spells equal to your Intelligence modifier.'}
                {characterBasics.character_class === 'Sorcerer' && 'You know 2 cantrips and 2 1st-level spells of your choice.'}
                {characterBasics.character_class === 'Cleric' && 'You know all cleric cantrips and can prepare spells equal to your Wisdom modifier + cleric level.'}
                {characterBasics.character_class === 'Bard' && 'You know 2 cantrips and 4 1st-level spells of your choice.'}
                {isHalfCaster && 'You gain spellcasting at 2nd level with limited spell selection.'}
              </p>
            </div>
          </div>
        )}

        {/* Non-spellcaster note */}
        {!isSpellcaster && !isHalfCaster && (
          <div className="bg-gray-750 p-4 rounded-md text-center">
            <p className="text-gray-400">
              {characterBasics.character_class} is not a spellcasting class, but may gain magical abilities through class features or racial traits.
            </p>
          </div>
        )}
      </div>
    );
  };

  const renderReviewStep = () => (
    <div className="space-y-6">
      {/* Character Summary */}
      <div className="bg-gray-750 p-6 rounded-md">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center">
          <User className="w-6 h-6 mr-2" />
          Character Summary
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mb-6">
          <div>
            <span className="text-gray-400">Name:</span>
            <span className="text-white ml-2 font-medium">{characterBasics.name}</span>
          </div>
          <div>
            <span className="text-gray-400">Race:</span>
            <span className="text-white ml-2">
              {characterBasics.race}{characterBasics.subrace ? ` (${characterBasics.subrace})` : ''}
            </span>
          </div>
          <div>
            <span className="text-gray-400">Class:</span>
            <span className="text-white ml-2">{characterBasics.character_class}</span>
          </div>
          <div>
            <span className="text-gray-400">Level:</span>
            <span className="text-white ml-2">{characterBasics.level}</span>
          </div>
          <div>
            <span className="text-gray-400">Background:</span>
            <span className="text-white ml-2">{characterBasics.background || 'None'}</span>
          </div>
          <div>
            <span className="text-gray-400">Alignment:</span>
            <span className="text-white ml-2">{characterBasics.alignment || 'None'}</span>
          </div>
        </div>

        {/* Combat Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 bg-gray-700 rounded">
            <div className="flex items-center justify-center mb-1">
              <Heart className="w-4 h-4 text-red-400 mr-1" />
              <span className="text-white font-bold">{characterBasics.hit_points}</span>
            </div>
            <div className="text-gray-400 text-xs">Hit Points</div>
          </div>
          <div className="text-center p-3 bg-gray-700 rounded">
            <div className="flex items-center justify-center mb-1">
              <Shield className="w-4 h-4 text-blue-400 mr-1" />
              <span className="text-white font-bold">{characterBasics.armor_class}</span>
            </div>
            <div className="text-gray-400 text-xs">Armor Class</div>
          </div>
          <div className="text-center p-3 bg-gray-700 rounded">
            <div className="text-white font-bold">{characterBasics.speed} ft</div>
            <div className="text-gray-400 text-xs">Speed</div>
          </div>
          <div className="text-center p-3 bg-gray-700 rounded">
            <div className="flex items-center justify-center mb-1">
              <Star className="w-4 h-4 text-yellow-400 mr-1" />
              <span className="text-white font-bold">+{characterBasics.proficiency_bonus}</span>
            </div>
            <div className="text-gray-400 text-xs">Proficiency</div>
          </div>
        </div>

        {/* Ability Scores */}
        <div>
          <h4 className="text-white font-medium mb-3">Ability Scores</h4>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
            {Object.entries(abilityScores).map(([ability, score]) => {
              const modifier = calculateModifier(score);
              const isRecommended = getRecommendedAbilities(characterBasics.character_class).includes(ability);

              return (
                <div key={ability} className={`text-center p-2 rounded ${isRecommended ? 'bg-yellow-900/20 border border-yellow-500/30' : 'bg-gray-700'
                  }`}>
                  <div className="text-gray-400 capitalize text-xs">{ability.slice(0, 3)}</div>
                  <div className="text-white font-bold text-lg">{score}</div>
                  <div className="text-gray-500 text-xs">
                    ({modifier >= 0 ? '+' : ''}{modifier})
                  </div>
                  {isRecommended && (
                    <Star className="w-3 h-3 text-yellow-400 mx-auto mt-1" />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Features Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-750 p-4 rounded-md">
          <h4 className="text-white font-medium mb-3">Features & Abilities</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Class Features:</span>
              <span className="text-white">{spellsAndAbilities.class_features.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Racial Traits:</span>
              <span className="text-white">{spellsAndAbilities.racial_traits.length}</span>
            </div>
            {spellsAndAbilities.cantrips_known && spellsAndAbilities.cantrips_known > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-400">Cantrips Known:</span>
                <span className="text-purple-400">{spellsAndAbilities.cantrips_known}</span>
              </div>
            )}
            {spellsAndAbilities.spells_known && spellsAndAbilities.spells_known > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-400">Spells Known:</span>
                <span className="text-blue-400">{spellsAndAbilities.spells_known}</span>
              </div>
            )}
          </div>
        </div>

        <div className="bg-gray-750 p-4 rounded-md">
          <h4 className="text-white font-medium mb-3">Equipment Summary</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Weapons:</span>
              <span className="text-white">{equipment.weapons.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Armor Pieces:</span>
              <span className="text-white">{equipment.armor.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Other Items:</span>
              <span className="text-white">{equipment.items.length}</span>
            </div>
            {equipment.starting_gold && equipment.starting_gold > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-400">Starting Gold:</span>
                <span className="text-yellow-400">{equipment.starting_gold} gp</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Background Summary */}
      <div className="bg-gray-750 p-4 rounded-md">
        <h4 className="text-white font-medium mb-3">Background & Personality</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-gray-400 mb-1">Personality Traits:</div>
            <div className="text-white">
              {backgroundStory.personality_traits.filter(t => t.trim()).length} defined
            </div>
          </div>
          <div>
            <div className="text-gray-400 mb-1">Ideals:</div>
            <div className="text-white">
              {backgroundStory.ideals.filter(i => i.trim()).length} defined
            </div>
          </div>
          <div>
            <div className="text-gray-400 mb-1">Bonds:</div>
            <div className="text-white">
              {backgroundStory.bonds.filter(b => b.trim()).length} defined
            </div>
          </div>
          <div>
            <div className="text-gray-400 mb-1">Flaws:</div>
            <div className="text-white">
              {backgroundStory.flaws.filter(f => f.trim()).length} defined
            </div>
          </div>
        </div>
        <div className="mt-3">
          <div className="text-gray-400 mb-1">Backstory Sections:</div>
          <div className="text-white">
            {backgroundStory.backstory_sections.filter(s => s.title.trim() || s.content.trim()).length} sections
          </div>
        </div>
      </div>

      {/* Files to be Created */}
      <div className="bg-blue-900/20 border border-blue-500/30 p-4 rounded-md">
        <h4 className="text-blue-300 font-medium mb-3 flex items-center">
          <CheckCircle className="w-4 h-4 mr-2" />
          Files to be Created
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
          {[
            { name: 'character.json', desc: 'Basic character information and stats' },
            { name: 'character_background.json', desc: 'Personality, backstory, and relationships' },
            { name: 'feats_and_traits.json', desc: 'Class features and racial traits' },
            { name: 'action_list.json', desc: 'Combat actions and abilities' },
            { name: 'inventory_list.json', desc: 'Equipment and items' },
            { name: 'objectives_and_contracts.json', desc: 'Quests and goals' },
            { name: 'spell_list.json', desc: 'Spells and magical abilities' }
          ].map((file, index) => (
            <div key={index} className="flex items-start space-x-2 p-2 bg-blue-900/10 rounded">
              <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
              <div>
                <div className="text-blue-200 font-medium">
                  {characterBasics.name.toLowerCase().replace(/\s+/g, '_')}_{file.name}
                </div>
                <div className="text-blue-300 text-xs">{file.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Final Confirmation */}
      <div className="bg-green-900/20 border border-green-500/30 p-4 rounded-md text-center">
        <h4 className="text-green-300 font-medium mb-2">Ready to Create Character</h4>
        <p className="text-green-200 text-sm">
          All character information has been configured. Click "Create Character" to generate all files and complete the character creation process.
        </p>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-2xl font-bold text-white">Create New Character</h2>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="px-6 py-4 border-b border-gray-700">
          <div className="flex items-center justify-between mb-2">
            {steps.map((step, index) => (
              <div
                key={step.id}
                className={`flex items-center space-x-2 ${index === currentStep ? 'text-purple-400' :
                  step.isComplete ? 'text-green-400' : 'text-gray-500'
                  }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${index === currentStep ? 'border-purple-400 bg-purple-400/20' :
                  step.isComplete ? 'border-green-400 bg-green-400/20' : 'border-gray-500'
                  }`}>
                  {step.isComplete ? (
                    <CheckCircle className="w-5 h-5" />
                  ) : (
                    step.icon
                  )}
                </div>
                <span className="text-sm font-medium hidden md:block">{step.title}</span>
              </div>
            ))}
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-purple-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Step Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="mb-6">
            <h3 className="text-xl font-bold text-white mb-2">
              {steps[currentStep].title}
            </h3>
            <p className="text-gray-400">{steps[currentStep].description}</p>
          </div>

          {renderStepContent()}

          {/* Validation Errors */}
          {validationErrors.length > 0 && (
            <div className="mt-6 bg-red-900/20 border border-red-500/30 p-4 rounded-md">
              <div className="flex items-center space-x-2 mb-2">
                <AlertCircle className="w-5 h-5 text-red-400" />
                <h4 className="text-red-300 font-medium">Please fix the following errors:</h4>
              </div>
              <ul className="text-sm text-red-200 space-y-1">
                {validationErrors.map((error, index) => (
                  <li key={index}>• {error.message}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-700">
          <button
            onClick={goPrevious}
            disabled={!canGoPrevious()}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Previous</span>
          </button>

          <div className="text-sm text-gray-400">
            Step {currentStep + 1} of {steps.length}
          </div>

          {currentStep < steps.length - 1 ? (
            <button
              onClick={goNext}
              disabled={!canGoNext()}
              className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <span>Next</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={createCharacter}
              disabled={!canGoNext() || isCreating}
              className="flex items-center space-x-2 px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isCreating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Creating...</span>
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  <span>Create Character</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};