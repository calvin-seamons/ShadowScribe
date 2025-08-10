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
  Loader2
} from 'lucide-react';
import { CharacterCreationRequest, createNewCharacter, getFileTemplate } from '../../services/knowledgeBaseApi';
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
    equipped: boolean;
  }>;
  armor: Array<{
    name: string;
    type: string;
    equipped: boolean;
  }>;
  items: Array<{
    name: string;
    quantity: number;
    category: string;
  }>;
}

interface SpellsAndAbilities {
  spells: Array<{
    name: string;
    level: number;
    school: string;
    prepared: boolean;
  }>;
  class_features: Array<{
    name: string;
    level: number;
    description: string;
  }>;
  racial_traits: Array<{
    name: string;
    description: string;
  }>;
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
    alignment: ''
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
    items: []
  });

  const [spellsAndAbilities, setSpellsAndAbilities] = useState<SpellsAndAbilities>({
    spells: [],
    class_features: [],
    racial_traits: []
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
        ability_scores: abilityScores
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
    </div>
  );

  const renderAbilitiesStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <p className="text-gray-300">
          Set your character's ability scores. You can use standard array (15, 14, 13, 12, 10, 8), 
          point buy, or roll for stats.
        </p>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
        {Object.entries(abilityScores).map(([ability, score]) => (
          <div key={ability} className="text-center">
            <label className="block text-sm font-medium text-white capitalize mb-2">
              {ability}
            </label>
            <input
              type="number"
              value={score}
              onChange={(e) => setAbilityScores(prev => ({
                ...prev,
                [ability]: Number(e.target.value) || 0
              }))}
              min={1}
              max={30}
              className="w-20 h-20 text-center text-xl font-bold bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <div className="text-xs text-gray-400 mt-1">
              Modifier: {Math.floor((score - 10) / 2) >= 0 ? '+' : ''}{Math.floor((score - 10) / 2)}
            </div>
          </div>
        ))}
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

  const renderBackgroundStep = () => (
    <div className="space-y-6">
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-white mb-2">
            Personality Traits <span className="text-red-400">*</span>
          </label>
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

  const renderEquipmentStep = () => (
    <div className="space-y-6">
      <p className="text-gray-300 text-center">
        Equipment will be automatically populated based on your class and background choices.
        You can modify it later in the inventory editor.
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-750 p-4 rounded-md">
          <h4 className="text-white font-medium mb-2">Starting Weapons</h4>
          <p className="text-gray-400 text-sm">
            Based on your {characterBasics.character_class} class
          </p>
        </div>
        
        <div className="bg-gray-750 p-4 rounded-md">
          <h4 className="text-white font-medium mb-2">Starting Armor</h4>
          <p className="text-gray-400 text-sm">
            Based on your class proficiencies
          </p>
        </div>
        
        <div className="bg-gray-750 p-4 rounded-md">
          <h4 className="text-white font-medium mb-2">Background Equipment</h4>
          <p className="text-gray-400 text-sm">
            Based on your {characterBasics.background} background
          </p>
        </div>
      </div>
    </div>
  );

  const renderSpellsStep = () => (
    <div className="space-y-6">
      <p className="text-gray-300 text-center">
        Spells and abilities will be automatically populated based on your class, race, and level.
        You can modify them later in the respective editors.
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-750 p-4 rounded-md">
          <h4 className="text-white font-medium mb-2">Class Features</h4>
          <p className="text-gray-400 text-sm">
            Level {characterBasics.level} {characterBasics.character_class} features
          </p>
        </div>
        
        <div className="bg-gray-750 p-4 rounded-md">
          <h4 className="text-white font-medium mb-2">Racial Traits</h4>
          <p className="text-gray-400 text-sm">
            {characterBasics.race} racial abilities and traits
          </p>
        </div>
        
        {['Bard', 'Cleric', 'Druid', 'Paladin', 'Ranger', 'Sorcerer', 'Warlock', 'Wizard'].includes(characterBasics.character_class) && (
          <div className="bg-gray-750 p-4 rounded-md md:col-span-2">
            <h4 className="text-white font-medium mb-2">Spells</h4>
            <p className="text-gray-400 text-sm">
              Starting spells for level {characterBasics.level} {characterBasics.character_class}
            </p>
          </div>
        )}
      </div>
    </div>
  );

  const renderReviewStep = () => (
    <div className="space-y-6">
      <div className="bg-gray-750 p-6 rounded-md">
        <h3 className="text-xl font-bold text-white mb-4">Character Summary</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-400">Name:</span>
            <span className="text-white ml-2">{characterBasics.name}</span>
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

        <div className="mt-4">
          <h4 className="text-white font-medium mb-2">Ability Scores</h4>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-2 text-xs">
            {Object.entries(abilityScores).map(([ability, score]) => (
              <div key={ability} className="text-center">
                <div className="text-gray-400 capitalize">{ability.slice(0, 3)}</div>
                <div className="text-white font-bold">{score}</div>
                <div className="text-gray-500">
                  ({Math.floor((score - 10) / 2) >= 0 ? '+' : ''}{Math.floor((score - 10) / 2)})
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-blue-900/20 border border-blue-500/30 p-4 rounded-md">
        <h4 className="text-blue-300 font-medium mb-2">Files to be Created</h4>
        <ul className="text-sm text-blue-200 space-y-1">
          <li>• {characterBasics.name.toLowerCase().replace(/\s+/g, '_')}_character.json</li>
          <li>• {characterBasics.name.toLowerCase().replace(/\s+/g, '_')}_character_background.json</li>
          <li>• {characterBasics.name.toLowerCase().replace(/\s+/g, '_')}_feats_and_traits.json</li>
          <li>• {characterBasics.name.toLowerCase().replace(/\s+/g, '_')}_action_list.json</li>
          <li>• {characterBasics.name.toLowerCase().replace(/\s+/g, '_')}_inventory_list.json</li>
          <li>• {characterBasics.name.toLowerCase().replace(/\s+/g, '_')}_objectives_and_contracts.json</li>
          <li>• {characterBasics.name.toLowerCase().replace(/\s+/g, '_')}_spell_list.json</li>
        </ul>
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
                className={`flex items-center space-x-2 ${
                  index === currentStep ? 'text-purple-400' : 
                  step.isComplete ? 'text-green-400' : 'text-gray-500'
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                  index === currentStep ? 'border-purple-400 bg-purple-400/20' :
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