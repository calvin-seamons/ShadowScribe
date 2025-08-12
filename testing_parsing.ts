import { readFileSync } from 'fs';
import * as fs from 'fs';
import * as path from 'path';
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf.mjs';

// Interfaces for the 7 JSON file structures
interface CharacterData {
  character_base: {
    name: string;
    race: string;
    subrace: string;
    class: string;
    [key: string]: any; // Dynamic class levels
    total_level: number;
    experience_points: number;
    alignment: string;
    background: string;
    lifestyle: string;
    hit_dice: { [key: string]: string };
  };
  characteristics: {
    alignment: string;
    gender: string;
    eyes: string;
    size: string;
    height: string;
    hair: string;
    skin: string;
    age: number;
    weight: string;
    faith?: string;
  };
  ability_scores: {
    strength: number;
    dexterity: number;
    constitution: number;
    intelligence: number;
    wisdom: number;
    charisma: number;
  };
  combat_stats: {
    max_hp: number;
    current_hp: number;
    temp_hp: number;
    armor_class: number;
    initiative_bonus: number;
    speed: number;
    inspiration: boolean;
  };
  proficiencies: any[];
  damage_modifiers: any[];
  passive_scores: {
    perception: number;
    investigation: number;
    insight: number;
  };
  senses: {
    darkvision?: number;
    [key: string]: any;
  };
}

interface InventoryData {
  inventory: {
    total_weight: number;
    weight_unit: string;
    equipped_items: {
      weapons: any[];
      armor: any[];
      wondrous_items: any[];
      rods: any[];
    };
    consumables: any[];
    utility_items: any[];
    clothing: any[];
  };
  metadata: any;
}

interface SpellData {
  spellcasting: {
    [className: string]: {
      spells: {
        cantrips?: any[];
        '1st_level'?: any[];
        '2nd_level'?: any[];
        '3rd_level'?: any[];
        '4th_level'?: any[];
        '5th_level'?: any[];
        '6th_level'?: any[];
        '7th_level'?: any[];
        '8th_level'?: any[];
        '9th_level'?: any[];
      };
      spell_save_dc?: number;
      spell_attack_bonus?: number;
      spellcasting_ability?: string;
    };
  };
  metadata: any;
}

interface ActionData {
  character_actions: {
    attacks_per_action: number;
    action_economy: {
      actions: any[];
      bonus_actions: any[];
      reactions: any[];
      other_actions: any[];
      special_abilities: any[];
    };
    combat_actions_reference: string[];
  };
  metadata: any;
}

interface BackgroundData {
  character_id: number;
  background: {
    name: string;
    feature: {
      name: string;
      description: string;
    };
  };
  characteristics: {
    alignment: string;
    gender: string;
    eyes: string;
    size: string;
    height: string;
    faith?: string;
    hair: string;
    skin: string;
    age: number;
    weight: string;
    personality_traits: string[];
    ideals: string[];
    bonds: string[];
    flaws: string[];
  };
  backstory: any;
  organizations: any[];
  allies: any[];
  enemies: any[];
  notes: any;
}

interface FeaturesData {
  features_and_traits: {
    class_features: { [className: string]: any };
    species_traits: any;
    feats: any[];
    calculated_features: any;
  };
  metadata: any;
}

interface ObjectivesData {
  objectives_and_contracts: {
    active_contracts: any[];
    current_objectives: any[];
    completed_objectives: any[];
    contract_templates: any;
  };
  metadata: any;
}

class DnDCharacterParser {
  private pdfText: string = '';
  private pages: string[] = [];
  
  // Class configurations for different D&D classes (including popular homebrew)
  private classConfigs: { [key: string]: any } = {
    'barbarian': { hitDie: 'd12', primaryAbility: 'STR', spellcaster: false },
    'bard': { hitDie: 'd8', primaryAbility: 'CHA', spellcaster: true },
    'cleric': { hitDie: 'd8', primaryAbility: 'WIS', spellcaster: true },
    'druid': { hitDie: 'd8', primaryAbility: 'WIS', spellcaster: true },
    'fighter': { hitDie: 'd10', primaryAbility: 'STR', spellcaster: false },
    'monk': { hitDie: 'd8', primaryAbility: 'DEX', spellcaster: false },
    'paladin': { hitDie: 'd10', primaryAbility: 'CHA', spellcaster: true },
    'ranger': { hitDie: 'd10', primaryAbility: 'DEX', spellcaster: true },
    'rogue': { hitDie: 'd8', primaryAbility: 'DEX', spellcaster: false },
    'sorcerer': { hitDie: 'd6', primaryAbility: 'CHA', spellcaster: true },
    'warlock': { hitDie: 'd8', primaryAbility: 'CHA', spellcaster: true },
    'wizard': { hitDie: 'd6', primaryAbility: 'INT', spellcaster: true },
    'artificer': { hitDie: 'd8', primaryAbility: 'INT', spellcaster: true },
    // Popular homebrew classes
    'blood hunter': { hitDie: 'd10', primaryAbility: 'WIS', spellcaster: false },
    'bloodhunter': { hitDie: 'd10', primaryAbility: 'WIS', spellcaster: false }
  };

  async parsePDF(pdfPath: string): Promise<void> {
    try {
      const dataBuffer = fs.readFileSync(pdfPath);
      const uint8Array = new Uint8Array(dataBuffer);
      
      // Load PDF using pdfjs-dist
      const loadingTask = pdfjsLib.getDocument({ data: uint8Array });
      const pdf = await loadingTask.promise;
      
      let fullText = '';
      const pages: string[] = [];
      
      // Extract text from each page
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        const pageText = textContent.items
          .map((item: any) => item.str)
          .join(' ');
        
        pages.push(pageText);
        fullText += pageText + '\n';
      }
      
      this.pdfText = fullText;
      this.pages = pages;
      console.log('📖 PDF text extracted, length:', this.pdfText.length);
      console.log('📄 Number of pages:', pages.length);

      const outputDir = './character_data';
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }

      // Parse and save each JSON file
      this.saveJSON(outputDir, 'character.json', this.parseCharacterBase());
      this.saveJSON(outputDir, 'inventory_list.json', this.parseInventory());
      this.saveJSON(outputDir, 'spell_list.json', this.parseSpells());
      this.saveJSON(outputDir, 'action_list.json', this.parseActions());
      this.saveJSON(outputDir, 'character_background.json', this.parseBackground());
      this.saveJSON(outputDir, 'feats_and_traits.json', this.parseFeatures());
      this.saveJSON(outputDir, 'objectives_and_contracts.json', this.parseObjectives());
      
    } catch (error) {
      console.error('❌ Error in parsing:', error);
      throw error;
    }
  }

  private parseCharacterBase(): CharacterData {
    const text = this.pdfText;
    
    // Extract character name - more robust pattern
    const namePatterns = [
      /CHARACTER NAME\s*([^\n]+)/i,
      /^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)/m
    ];
    let name = 'Unknown';
    for (const pattern of namePatterns) {
      const match = text.match(pattern);
      if (match && match[1].trim()) {
        name = match[1].trim();
        break;
      }
    }

    // Extract class and level - handle multiclass
    const classAndLevel = this.parseClassAndLevel(text);
    
    // Extract race/species - handle more race types including exotic races
    const raceMatch = text.match(/SPECIES\s*([^\n]+)/i) || 
                      text.match(/RACE\s*([^\n]+)/i) ||
                      text.match(/(Variant\s+)?(\w+\s+)?(Human|Elf|Dwarf|Halfling|Dragonborn|Gnome|Half-Elf|Half-Orc|Tiefling|Warforged|Aasimar|Genasi|Goliath|Tabaxi|Firbolg|Kenku|Lizardfolk|Tortle|Changeling|Kalashtar|Shifter|Githyanki|Githzerai|Hobgoblin|Orc|Yuan-ti|Kobold|Bugbear|Goblin|Centaur|Minotaur|Loxodon|Simic Hybrid|Vedalken)/i);
    
    let race = 'Unknown';
    let subrace = '';
    if (raceMatch) {
      race = raceMatch[1] ? raceMatch[1].trim() : raceMatch[0].replace(/SPECIES|RACE/i, '').trim();
      
      // Handle special cases
      if (race.toLowerCase().includes('half-elf')) {
        race = 'Half-Elf';
      } else if (race.toLowerCase().includes('half-orc')) {
        race = 'Half-Orc';
      } else if (race.toLowerCase().includes('warforged')) {
        race = 'Warforged';
      } else if (race.toLowerCase().includes('kalashtar')) {
        race = 'Kalashtar';
      } else if (race.toLowerCase().includes('mountain dwarf')) {
        race = 'Dwarf';
        subrace = 'Mountain';
      } else if (race.toLowerCase().includes('hill dwarf')) {
        race = 'Dwarf';
        subrace = 'Hill';
      }
      
      // Extract subrace if present and not already set
      if (!subrace) {
        const subracePattern = /(Hill|Mountain|High|Wood|Dark|Forest|Rock|Variant)\s*/i;
        const subraceMatch = race.match(subracePattern);
        if (subraceMatch) {
          subrace = subraceMatch[1];
          race = race.replace(subracePattern, '').trim();
        }
      }
    }

    // Extract ability scores with more flexible patterns
    const abilities = this.parseAbilityScores(text);

    // Extract HP, AC, Speed with multiple patterns
    const combatStats = this.parseCombatStats(text);

    // Extract alignment
    const alignmentMatch = text.match(/ALIGNMENT\s*([^\n]+)/i) ||
                          text.match(/(Lawful|Neutral|Chaotic)\s+(Good|Neutral|Evil)/i);
    const alignment = alignmentMatch ? alignmentMatch[1].trim() : 'True Neutral';

    // Extract background - handle multi-word backgrounds
    const backgroundMatch = text.match(/BACKGROUND\s*([^\n]+)/i);
    let background = 'Unknown';
    if (backgroundMatch) {
      background = backgroundMatch[1].trim();
      // Clean up common background names
      if (background.toLowerCase().includes('mercenary veteran')) {
        background = 'Mercenary Veteran';
      } else if (background.toLowerCase().includes('sage')) {
        background = 'Sage';
      } else if (background.toLowerCase().includes('entertainer')) {
        background = 'Entertainer';
      } else if (background.toLowerCase().includes('soldier')) {
        background = 'Soldier';
      } else if (background.toLowerCase().includes('noble')) {
        background = 'Noble';
      }
    }

    // Extract experience
    const xpMatch = text.match(/EXPERIENCE POINTS\s*([^\n]+)/i);
    const xp = xpMatch ? parseInt(xpMatch[1].replace(/[^\d]/g, '') || '0') : 0;

    // Build character base
    const characterBase: any = {
      name: name,
      race: race,
      subrace: subrace,
      class: classAndLevel.className,
      total_level: classAndLevel.totalLevel,
      experience_points: xp,
      alignment: alignment,
      background: background,
      lifestyle: 'Unknown',
      hit_dice: {}
    };

    // Add individual class levels
    Object.entries(classAndLevel.levels).forEach(([cls, level]) => {
      characterBase[`${cls}_level`] = level;
      const config = this.classConfigs[cls.toLowerCase()];
      if (config && (level as number) > 0) {
        characterBase.hit_dice[cls] = `${level}${config.hitDie}`;
      }
    });

    return {
      character_base: characterBase,
      characteristics: this.parseCharacteristics(text),
      ability_scores: abilities,
      combat_stats: combatStats,
      proficiencies: this.parseProficiencies(text),
      damage_modifiers: this.parseDamageModifiers(text),
      passive_scores: this.parsePassiveScores(text),
      senses: this.parseSenses(text)
    };
  }

  private parseClassAndLevel(text: string): any {
    const result = {
      className: 'Unknown',
      totalLevel: 1,
      levels: {} as { [key: string]: number }
    };

    // Try to find CLASS & LEVEL section
    const classLevelMatch = text.match(/CLASS & LEVEL\s*([^\n]+)/i);
    if (classLevelMatch) {
      const classText = classLevelMatch[1].trim();
      
      // Check for multiclass (contains / or numbers)
      if (classText.includes('/') || /\d/.test(classText)) {
        // Parse multiclass like "Paladin 13" or "Warlock 5 / Paladin 8"
        const classes = classText.split('/');
        const classNames: string[] = [];
        
        classes.forEach(cls => {
          const match = cls.trim().match(/(\w+)\s*(\d+)?/);
          if (match) {
            const className = match[1].toLowerCase();
            const level = parseInt(match[2] || '1');
            result.levels[className] = level;
            classNames.push(match[1]);
            result.totalLevel = Object.values(result.levels).reduce((a, b) => a + b, 0);
          }
        });
        
        result.className = classNames.join('/');
      } else {
        // Single class
        result.className = classText;
        const levelMatch = text.match(/Level\s*(\d+)/i) || 
                          text.match(/CHARACTER LEVEL\s*(\d+)/i);
        result.totalLevel = levelMatch ? parseInt(levelMatch[1]) : 1;
        result.levels[classText.toLowerCase()] = result.totalLevel;
      }
    }

    return result;
  }

  private parseAbilityScores(text: string): any {
    const scores: any = {
      strength: 10,
      dexterity: 10,
      constitution: 10,
      intelligence: 10,
      wisdom: 10,
      charisma: 10
    };

    // Multiple patterns for ability scores
    const patterns = {
      strength: [/STRENGTH\s*(\d+)/i, /STR\s*(\d+)/i, /Strength.*?(\d+)/i],
      dexterity: [/DEXTERITY\s*(\d+)/i, /DEX\s*(\d+)/i, /Dexterity.*?(\d+)/i],
      constitution: [/CONSTITUTION\s*(\d+)/i, /CON\s*(\d+)/i, /Constitution.*?(\d+)/i],
      intelligence: [/INTELLIGENCE\s*(\d+)/i, /INT\s*(\d+)/i, /Intelligence.*?(\d+)/i],
      wisdom: [/WISDOM\s*(\d+)/i, /WIS\s*(\d+)/i, /Wisdom.*?(\d+)/i],
      charisma: [/CHARISMA\s*(\d+)/i, /CHA\s*(\d+)/i, /Charisma.*?(\d+)/i]
    };

    Object.entries(patterns).forEach(([ability, patternList]) => {
      for (const pattern of patternList) {
        const match = text.match(pattern);
        if (match && match[1]) {
          scores[ability] = parseInt(match[1]);
          break;
        }
      }
    });

    return scores;
  }

  private parseCombatStats(text: string): any {
    // HP patterns
    const hpPatterns = [
      /Max HP\s*(\d+)/i,
      /HIT POINTS\s*(\d+)/i,
      /Maximum Hit Points[:\s]*(\d+)/i,
      /HP[:\s]*(\d+)/i
    ];
    let maxHp = 0;
    for (const pattern of hpPatterns) {
      const match = text.match(pattern);
      if (match) {
        maxHp = parseInt(match[1]);
        break;
      }
    }

    // AC patterns
    const acPatterns = [
      /ARMOR\s*CLASS\s*(\d+)/i,
      /AC\s*(\d+)/i,
      /Armor Class[:\s]*(\d+)/i
    ];
    let ac = 10;
    for (const pattern of acPatterns) {
      const match = text.match(pattern);
      if (match) {
        ac = parseInt(match[1]);
        break;
      }
    }

    // Speed patterns
    const speedPatterns = [
      /SPEED\s*(\d+)\s*ft/i,
      /Speed[:\s]*(\d+)/i,
      /(\d+)\s*ft\.?\s*\(?Walking\)?/i
    ];
    let speed = 30;
    for (const pattern of speedPatterns) {
      const match = text.match(pattern);
      if (match) {
        speed = parseInt(match[1]);
        break;
      }
    }

    // Initiative
    const initMatch = text.match(/INITIATIVE\s*([+-]?\d+)/i);
    const initiative = initMatch ? parseInt(initMatch[1]) : 0;

    // Inspiration
    const hasInspiration = text.includes('HEROIC INSPIRATION') || 
                          text.includes('Inspiration: Yes') ||
                          /Inspiration.*?✓/i.test(text);

    return {
      max_hp: maxHp,
      current_hp: maxHp, // Assume full HP
      temp_hp: 0,
      armor_class: ac,
      initiative_bonus: initiative,
      speed: speed,
      inspiration: hasInspiration
    };
  }

  private parseCharacteristics(text: string): any {
    return {
      alignment: this.extractField(text, 'ALIGNMENT', 'True Neutral'),
      gender: this.extractField(text, 'GENDER', 'Unknown'),
      eyes: this.extractField(text, 'EYES', 'Unknown'),
      size: this.extractField(text, 'SIZE', 'Medium'),
      height: this.extractField(text, 'HEIGHT', 'Unknown'),
      hair: this.extractField(text, 'HAIR', 'Unknown'),
      skin: this.extractField(text, 'SKIN', 'Unknown'),
      age: parseInt(this.extractField(text, 'AGE', '0').replace(/\D/g, '') || '0'),
      weight: this.extractField(text, 'WEIGHT', 'Unknown'),
      faith: this.extractField(text, 'FAITH', null)
    };
  }

  private extractField(text: string, field: string, defaultValue: any = null): any {
    const pattern = new RegExp(`${field}\\s*([^\\n]+)`, 'i');
    const match = text.match(pattern);
    return match ? match[1].trim() : defaultValue;
  }

  private parseProficiencies(text: string): any[] {
    const proficiencies: any[] = [];
    
    // Armor proficiencies
    const armorTypes = ['Light Armor', 'Medium Armor', 'Heavy Armor', 'Shields'];
    armorTypes.forEach(armor => {
      if (text.includes(armor)) {
        proficiencies.push({ type: 'armor', name: armor });
      }
    });

    // Weapon proficiencies
    const weaponTypes = ['Simple Weapons', 'Martial Weapons'];
    weaponTypes.forEach(weapon => {
      if (text.includes(weapon)) {
        proficiencies.push({ type: 'weapon', name: weapon });
      }
    });

    // Tool proficiencies - look for common tools
    const toolPatterns = [
      /TOOLS[\s\S]*?([A-Z][a-z]+(?:'s)?\s+(?:Tools?|Kit|Set|Supplies))/gi,
      /([A-Z][a-z]+(?:'s)?\s+(?:Tools?|Kit|Set|Supplies))/g
    ];
    
    const foundTools = new Set<string>();
    toolPatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(text)) !== null) {
        if (match[1] && !match[1].includes('TOOLS')) {
          foundTools.add(match[1].trim());
        }
      }
    });
    
    foundTools.forEach(tool => {
      proficiencies.push({ type: 'tool', name: tool });
    });

    // Language proficiencies
    const languageSection = this.extractSection(text, 'LANGUAGES', 100);
    const commonLanguages = [
      'Common', 'Dwarvish', 'Elvish', 'Giant', 'Gnomish', 'Goblin',
      'Halfling', 'Orc', 'Abyssal', 'Celestial', 'Draconic', 'Deep Speech',
      'Infernal', 'Primordial', 'Sylvan', 'Undercommon', 'Leonin'
    ];
    
    commonLanguages.forEach(lang => {
      if (text.includes(lang)) {
        proficiencies.push({ type: 'language', name: lang });
      }
    });

    return proficiencies;
  }

  private parseDamageModifiers(text: string): any[] {
    const modifiers: any[] = [];
    
    // Check for resistances - handle multiple types
    const resistanceSection = this.extractSection(text, 'Resistances', 200);
    if (resistanceSection) {
      // Parse specific damage types
      const damageTypes = ['Poison', 'Fire', 'Cold', 'Lightning', 'Thunder', 'Acid', 
                          'Necrotic', 'Radiant', 'Force', 'Psychic', 'Bludgeoning', 
                          'Piercing', 'Slashing'];
      
      damageTypes.forEach(type => {
        if (resistanceSection.includes(type) || text.includes(`Resistance.*${type}`)) {
          modifiers.push({
            damage_type: type.toLowerCase(),
            modifier_type: 'resistance',
            source: 'unknown'
          });
        }
      });
    }

    // Check for immunities - including special immunities
    const immunitySection = this.extractSection(text, 'Immunities', 200);
    if (immunitySection) {
      // Check for damage immunities
      const damageTypes = ['Poison', 'Fire', 'Cold', 'Lightning', 'Thunder', 'Acid', 
                          'Necrotic', 'Radiant', 'Force', 'Psychic'];
      
      damageTypes.forEach(type => {
        if (immunitySection.includes(type)) {
          modifiers.push({
            damage_type: type.toLowerCase(),
            modifier_type: 'immunity',
            source: 'unknown'
          });
        }
      });
      
      // Check for condition immunities
      const conditions = ['Disease', 'Charmed', 'Frightened', 'Paralyzed', 'Poisoned', 
                         'Stunned', 'Exhaustion', 'Petrified', 'Unconscious'];
      
      conditions.forEach(condition => {
        if (immunitySection.includes(condition)) {
          modifiers.push({
            damage_type: condition.toLowerCase(),
            modifier_type: 'immunity',
            source: 'condition'
          });
        }
      });
      
      // Check for special immunities like Critical Hits
      if (immunitySection.includes('Critical Hit') || text.includes('Immunities - Critical Hits')) {
        modifiers.push({
          damage_type: 'critical_hits',
          modifier_type: 'immunity',
          source: 'special'
        });
      }
      
      // Check for Magical Sleep immunity
      if (immunitySection.includes('Magical Sleep') || text.includes('Immunities - Magical Sleep')) {
        modifiers.push({
          damage_type: 'magical_sleep',
          modifier_type: 'immunity',
          source: 'racial'
        });
      }
    }

    // Also check main text for common patterns
    if (text.includes('Advantage against being charmed')) {
      modifiers.push({
        damage_type: 'charmed',
        modifier_type: 'advantage_saves',
        source: 'racial'
      });
    }
    
    if (text.includes('Advantage against Poison') || text.includes('Advantage Against Poison')) {
      modifiers.push({
        damage_type: 'poison',
        modifier_type: 'advantage_saves',
        source: 'racial'
      });
    }

    return modifiers;
  }

  private parsePassiveScores(text: string): any {
    return {
      perception: parseInt(this.extractField(text, 'PASSIVE PERCEPTION', '10').replace(/\D/g, '') || '10'),
      investigation: parseInt(this.extractField(text, 'PASSIVE INVESTIGATION', '10').replace(/\D/g, '') || '10'),
      insight: parseInt(this.extractField(text, 'PASSIVE INSIGHT', '10').replace(/\D/g, '') || '10')
    };
  }

  private parseSenses(text: string): any {
    const senses: any = {};
    
    // Darkvision
    const darkvisionMatch = text.match(/Darkvision\s*(\d+)\s*ft/i);
    if (darkvisionMatch) {
      senses.darkvision = parseInt(darkvisionMatch[1]);
    }

    // Other senses
    const otherSenses = ['Blindsight', 'Tremorsense', 'Truesight'];
    otherSenses.forEach(sense => {
      const pattern = new RegExp(`${sense}\\s*(\\d+)\\s*ft`, 'i');
      const match = text.match(pattern);
      if (match) {
        senses[sense.toLowerCase()] = parseInt(match[1]);
      }
    });

    return senses;
  }

  private parseInventory(): InventoryData {
    const text = this.pdfText;
    const inventory: InventoryData = {
      inventory: {
        total_weight: 0,
        weight_unit: 'lb',
        equipped_items: {
          weapons: [],
          armor: [],
          wondrous_items: [],
          rods: []
        },
        consumables: [],
        utility_items: [],
        clothing: []
      },
      metadata: {
        version: '1.0',
        last_updated: new Date().toISOString().split('T')[0],
        notes: ['Auto-parsed from PDF']
      }
    };

    // Parse weight
    const weightMatch = text.match(/WEIGHT CARRIED\s*([\d.]+)/i) || 
                       text.match(/Total Weight[:\s]*([\d.]+)/i);
    if (weightMatch) {
      inventory.inventory.total_weight = parseFloat(weightMatch[1]);
    }

    // Parse weapons from weapon attacks section - handle complex damage types
    const weaponSection = this.extractSection(text, 'WEAPON ATTACKS', 400);
    const weaponLines = weaponSection.split('\n');
    
    weaponLines.forEach(line => {
      // Skip headers
      if (line.includes('NAME') || line.includes('HIT') || line.includes('DAMAGE')) return;
      
      // Parse weapons with various formats
      // Format 1: "Weapon Name +X 1d8+Y damage_type"
      // Format 2: "Weapon Name +X 1d8+Y damage_type, special properties"
      const weaponMatch = line.match(/^([A-Za-z\s\(\)]+?)\s+([+-]\d+)\s+([\dd\+\-\s]+)\s+([A-Za-z,\s]+)/);
      
      if (weaponMatch && weaponMatch[1] && !weaponMatch[1].includes('Unarmed')) {
        const weaponName = weaponMatch[1].trim();
        const properties = weaponMatch[4] ? weaponMatch[4].split(',').map(p => p.trim()) : [];
        
        inventory.inventory.equipped_items.weapons.push({
          name: weaponName,
          type: 'Weapon',
          attack_bonus: weaponMatch[2],
          damage: weaponMatch[3].trim(),
          damage_type: properties[0] || 'Unknown',
          properties: properties.slice(1),
          rarity: weaponName.includes('Eldaryth') ? 'Artifact' : 'Common'
        });
      }
    });

    // Parse armor - more comprehensive
    const armorKeywords = [
      'Plate', 'Chain Mail', 'Splint', 'Scale Mail', 'Breastplate', 'Half Plate',
      'Studded Leather', 'Leather', 'Hide', 'Chain Shirt', 'Ring Mail', 'Shield',
      'Glamoured Studded Leather', 'Mithral', 'Adamantine'
    ];
    
    armorKeywords.forEach(armor => {
      const armorRegex = new RegExp(`\\b${armor}\\b`, 'i');
      if (armorRegex.test(text)) {
        // Check if it's not already added
        const exists = inventory.inventory.equipped_items.armor.some(a => 
          a.name.toLowerCase().includes(armor.toLowerCase())
        );
        
        if (!exists) {
          inventory.inventory.equipped_items.armor.push({
            name: armor,
            type: 'Armor',
            rarity: armor.includes('Glamoured') || armor.includes('Mithral') ? 'Rare' : 'Common'
          });
        }
      }
    });

    // Parse items from equipment section
    const equipmentSection = this.extractSection(text, 'EQUIPMENT', 1000);
    const itemLines = equipmentSection.split('\n').filter(line => line.trim());
    
    itemLines.forEach(line => {
      // Skip headers and totals
      if (line.includes('NAME') || line.includes('QTY') || line.includes('WEIGHT') || 
          line.includes('EQUIPMENT') || line.match(/^\d+\.?\d*\s*lb\.?$/) ||
          line.includes('ATTUNED')) {
        return;
      }

      // Parse item with quantity and weight - handle various formats
      const itemMatch = line.match(/([A-Za-z\s,'\(\)]+?)\s+(\d+)\s+([\d.-]+\s*lb\.?|\-\-?)/);
      if (itemMatch) {
        const itemName = itemMatch[1].trim();
        const quantity = parseInt(itemMatch[2]);
        
        // Skip if it's just a number or too short
        if (itemName.length < 2 || /^\d+$/.test(itemName)) return;
        
        // Categorize items
        if (itemName.toLowerCase().includes('potion')) {
          inventory.inventory.consumables.push({
            name: itemName,
            type: 'Potion',
            quantity: quantity,
            rarity: itemName.includes('Greater') ? 'Uncommon' : 'Common'
          });
        } else if (itemName.toLowerCase().match(/clothes|robe|cloak|vest|boots|belt/i)) {
          inventory.inventory.clothing.push({
            name: itemName,
            type: 'Clothing',
            quantity: quantity
          });
        } else if (itemName.toLowerCase().match(/bag|backpack|chest|sack|pouch/i)) {
          inventory.inventory.utility_items.push({
            name: itemName,
            type: 'Container',
            quantity: quantity
          });
        } else if (itemName.toLowerCase().match(/torch|tinderbox|rope|bedroll|rations|waterskin|oil/i)) {
          inventory.inventory.utility_items.push({
            name: itemName,
            type: 'Adventuring Gear',
            quantity: quantity
          });
        } else if (itemName.toLowerCase().match(/instrument|lute|flute|drum|viol|lyre/i)) {
          inventory.inventory.utility_items.push({
            name: itemName,
            type: 'Instrument',
            quantity: quantity
          });
        } else if (itemName.toLowerCase().match(/kit|tools|dice|cards/i)) {
          inventory.inventory.utility_items.push({
            name: itemName,
            type: 'Tools',
            quantity: quantity
          });
        }
      }
    });

    // Parse magic items
    const magicItemsSection = this.extractSection(text, 'ATTUNED MAGIC ITEMS', 300);
    if (magicItemsSection) {
      const magicItems = magicItemsSection.split('\n').filter(line => 
        line.trim() && !line.includes('ATTUNED') && !line.includes('QTY')
      );
      
      magicItems.forEach(item => {
        if (item.length > 2) {
          inventory.inventory.equipped_items.wondrous_items.push({
            name: item.trim(),
            type: 'Wondrous Item',
            attuned: true,
            rarity: 'Unknown'
          });
        }
      });
    }

    return inventory;
  }

  private parseSpells(): SpellData {
    const text = this.pdfText;
    const spellData: SpellData = {
      spellcasting: {},
      metadata: {
        version: '1.0',
        last_updated: new Date().toISOString().split('T')[0],
        notes: ['Auto-parsed from PDF']
      }
    };

    // Check if character has any spellcasting ability
    const hasSpells = text.includes('SPELL SAVE DC') || 
                     text.includes('SPELLCASTING') ||
                     text.includes('CANTRIPS') ||
                     /\d+\s*LEVEL.*SPELL/i.test(text);
    
    if (!hasSpells) {
      // Non-spellcaster
      return spellData;
    }

    // Find spell pages (usually pages 6-7, but check for spell-related content)
    let spellPages = '';
    for (let i = 5; i < Math.min(this.pages.length, 8); i++) {
      if (this.pages[i] && (this.pages[i].includes('SPELL') || this.pages[i].includes('CANTRIP'))) {
        spellPages += this.pages[i] + '\n';
      }
    }
    
    if (!spellPages) {
      spellPages = text; // Fallback to full text
    }
    
    // Detect spellcasting classes
    const spellcastingClasses = this.detectSpellcastingClasses(text);
    
    spellcastingClasses.forEach(className => {
      const classSpells = this.parseClassSpells(spellPages, className);
      
      // Get spell save DC and attack bonus
      const dcMatch = spellPages.match(/SPELL SAVE DC\s*(\d+)/i);
      const attackMatch = spellPages.match(/SPELL ATTACK\s*BONUS\s*([+-]?\d+)/i);
      const abilityMatch = spellPages.match(/SPELLCASTING\s*ABILITY\s*([A-Z]+)/i);
      
      spellData.spellcasting[className] = {
        spells: classSpells,
        spell_save_dc: dcMatch ? parseInt(dcMatch[1]) : undefined,
        spell_attack_bonus: attackMatch ? parseInt(attackMatch[1]) : undefined,
        spellcasting_ability: abilityMatch ? abilityMatch[1] : this.getSpellcastingAbility(className)
      };
    });

    return spellData;
  }

  private detectSpellcastingClasses(text: string): string[] {
    const classes: string[] = [];
    const spellcastingClasses = [
      'bard', 'cleric', 'druid', 'paladin', 'ranger', 
      'sorcerer', 'warlock', 'wizard', 'artificer'
    ];
    
    // Check for class in the character sheet
    spellcastingClasses.forEach(cls => {
      if (text.toLowerCase().includes(cls)) {
        classes.push(cls);
      }
    });

    // Check for Blood Hunter with Pact Magic
    if (text.toLowerCase().includes('blood hunter') && 
        (text.includes('Pact Magic') || text.includes('Order of the Profane Soul'))) {
      classes.push('blood hunter');
    }

    // Also check for explicit spellcasting class declaration
    const classMatch = text.match(/SPELLCASTING\s*CLASS\s*([A-Za-z/\s]+)/i);
    if (classMatch) {
      const declaredClasses = classMatch[1].toLowerCase().split(/[/\s]+/);
      declaredClasses.forEach(cls => {
        const cleanClass = cls.replace('blood', 'blood hunter').trim();
        if ((spellcastingClasses.includes(cleanClass) || cleanClass === 'blood hunter') && 
            !classes.includes(cleanClass)) {
          classes.push(cleanClass);
        }
      });
    }

    return classes.length > 0 ? classes : ['unknown'];
  }

  private parseClassSpells(text: string, className: string): any {
    const spells: any = {
      cantrips: [],
      '1st_level': [],
      '2nd_level': [],
      '3rd_level': [],
      '4th_level': [],
      '5th_level': [],
      '6th_level': [],
      '7th_level': [],
      '8th_level': [],
      '9th_level': []
    };

    // Parse spell list from the spell pages
    const spellLines = text.split('\n');
    let currentLevel = '';

    spellLines.forEach((line, index) => {
      // Detect spell level headers
      if (line.match(/CANTRIPS/i)) {
        currentLevel = 'cantrips';
      } else if (line.match(/1st\s*LEVEL/i)) {
        currentLevel = '1st_level';
      } else if (line.match(/2nd\s*LEVEL/i)) {
        currentLevel = '2nd_level';
      } else if (line.match(/3rd\s*LEVEL/i)) {
        currentLevel = '3rd_level';
      } else if (line.match(/4th\s*LEVEL/i)) {
        currentLevel = '4th_level';
      } else if (line.match(/5th\s*LEVEL/i)) {
        currentLevel = '5th_level';
      } else if (line.match(/6th\s*LEVEL/i)) {
        currentLevel = '6th_level';
      } else if (line.match(/7th\s*LEVEL/i)) {
        currentLevel = '7th_level';
      } else if (line.match(/8th\s*LEVEL/i)) {
        currentLevel = '8th_level';
      } else if (line.match(/9th\s*LEVEL/i)) {
        currentLevel = '9th_level';
      }

      // Parse spell entries - handle various formats
      // Format 1: "O SpellName Source SAVE/ATK TIME..."
      // Format 2: "SpellName Class -- 1A action..."
      if (currentLevel && spells[currentLevel]) {
        // Check for spell patterns
        const spellPatterns = [
          /^[OPC]?\s+([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*)\s+(?:Wizard|Bard|Cleric|Druid|Paladin|Ranger|Sorcerer|Warlock|Blood Hunter)/i,
          /^([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*)\s+(?:--|\w+)\s+\d+[mhA]/i,
          /^([A-Z][a-z]+(?:\s+(?:of|the|and|with|from|to|in)\s+)?[A-Z]?[a-z]+(?:\s+[A-Z]?[a-z]+)*)/
        ];
        
        for (const pattern of spellPatterns) {
          const spellMatch = line.match(pattern);
          if (spellMatch) {
            const spellName = spellMatch[1].trim();
            
            // Filter out non-spell words and headers
            const invalidWords = ['NAME', 'SOURCE', 'PREP', 'CLASS', 'SPELL', 'SAVE', 
                                 'TIME', 'RANGE', 'COMP', 'DURATION', 'PAGE', 'REF',
                                 'Slots', 'Level', 'Known', 'Prepared'];
            
            if (!invalidWords.includes(spellName) && 
                spellName.length > 2 && 
                !spellName.match(/^\d+/) &&
                !spells[currentLevel].find((s: any) => s.name === spellName)) {
              
              // Determine if spell is prepared (marked with O or P)
              const isPrepared = line.startsWith('O') || line.startsWith('P');
              
              spells[currentLevel].push({
                name: spellName,
                level: currentLevel === 'cantrips' ? 0 : parseInt(currentLevel[0]),
                school: this.detectSpellSchool(spellName, line),
                source: this.detectSpellSource(line),
                prepared: isPrepared,
                concentration: line.includes('Concentration') || line.includes('up to'),
                ritual: line.includes('Ritual') || line.includes('[R]')
              });
            }
            break;
          }
        }
      }
    });

    return spells;
  }

  private detectSpellSchool(spellName: string, line: string): string {
    // Common spell schools
    const schools: { [key: string]: string[] } = {
      'Evocation': ['Fireball', 'Lightning Bolt', 'Magic Missile', 'Eldritch Blast', 'Shocking Grasp'],
      'Abjuration': ['Shield', 'Counterspell', 'Dispel Magic', 'Protection', 'Armor of Agathys'],
      'Conjuration': ['Find Familiar', 'Find Steed', 'Summon', 'Create', 'Arms of Hadar'],
      'Divination': ['Detect', 'Identify', 'Augury', 'Scrying', 'True Seeing', 'Comprehend Languages'],
      'Enchantment': ['Charm Person', 'Hold Person', 'Sleep', 'Suggestion', 'Hex', 'Bane'],
      'Illusion': ['Minor Illusion', 'Invisibility', 'Mirror Image', 'Disguise Self'],
      'Necromancy': ['False Life', 'Inflict Wounds', 'Vampiric Touch', 'Animate Dead'],
      'Transmutation': ['Haste', 'Slow', 'Polymorph', 'Alter Self', 'Enhance Ability']
    };
    
    for (const [school, spellList] of Object.entries(schools)) {
      if (spellList.some(spell => spellName.includes(spell))) {
        return school;
      }
    }
    
    return 'Unknown';
  }

  private detectSpellSource(line: string): string {
    const sources = ['PHB', 'XGtE', 'TCoE', 'SCAG', 'EE', 'AI', 'FTD', 'SCC'];
    for (const source of sources) {
      if (line.includes(source)) {
        return source;
      }
    }
    return 'PHB'; // Default to Player's Handbook
  }

  private getSpellcastingAbility(className: string): string {
    const abilities: { [key: string]: string } = {
      'bard': 'Charisma',
      'cleric': 'Wisdom',
      'druid': 'Wisdom',
      'paladin': 'Charisma',
      'ranger': 'Wisdom',
      'sorcerer': 'Charisma',
      'warlock': 'Charisma',
      'wizard': 'Intelligence',
      'artificer': 'Intelligence'
    };
    return abilities[className] || 'Unknown';
  }

  private parseActions(): ActionData {
    const text = this.pdfText;
    
    return {
      character_actions: {
        attacks_per_action: this.parseExtraAttacks(text),
        action_economy: {
          actions: this.parseActionsOfType(text, 'action'),
          bonus_actions: this.parseActionsOfType(text, 'bonus_action'),
          reactions: this.parseActionsOfType(text, 'reaction'),
          other_actions: [],
          special_abilities: this.parseSpecialAbilities(text)
        },
        combat_actions_reference: [
          'Attack', 'Dash', 'Disengage', 'Dodge', 'Grapple',
          'Help', 'Hide', 'Improvise', 'Influence', 'Magic',
          'Ready', 'Search', 'Shove', 'Study', 'Utilize'
        ]
      },
      metadata: {
        version: '1.0',
        last_updated: new Date().toISOString().split('T')[0],
        notes: ['Auto-parsed from PDF']
      }
    };
  }

  private parseExtraAttacks(text: string): number {
    if (text.includes('Extra Attack')) {
      // Check for specific numbers
      if (text.includes('three attacks') || text.includes('Extra Attack (2)')) return 3;
      if (text.includes('two attacks') || text.includes('Extra Attack')) return 2;
    }
    return 1;
  }

  private parseActionsOfType(text: string, actionType: string): any[] {
    const actions: any[] = [];
    
    // Parse weapon attacks for action type
    if (actionType === 'action') {
      const weaponSection = this.extractSection(text, 'WEAPON ATTACKS', 400);
      const weaponLines = weaponSection.split('\n');
      
      weaponLines.forEach(line => {
        // Skip headers
        if (line.includes('NAME') || line.includes('HIT') || line.includes('DAMAGE') || line.trim().length < 3) {
          return;
        }
        
        // Parse different weapon formats
        // Format: "Weapon Name +X damage_dice damage_type, properties"
        const weaponMatch = line.match(/^([A-Za-z\s\(\),]+?)\s+([+-]\d+)\s+([\dd\+\-\s]+)\s+([A-Za-z,\s]+)/);
        
        if (weaponMatch && weaponMatch[1]) {
          const weaponName = weaponMatch[1].trim();
          const damageInfo = weaponMatch[4] ? weaponMatch[4].split(',').map(s => s.trim()) : [];
          
          actions.push({
            name: weaponName,
            type: 'weapon_attack',
            attack_bonus: weaponMatch[2],
            damage: weaponMatch[3].trim(),
            damage_type: damageInfo[0] || 'Unknown',
            properties: damageInfo.slice(1).filter(p => p.length > 0)
          });
        }
      });

      // Add class-specific actions based on detected classes
      if (text.includes('Divine Sense')) {
        actions.push({
          name: 'Divine Sense',
          type: 'action',
          description: 'Detect celestials, fiends, and undead within 60 feet'
        });
      }
      
      if (text.includes('Lay on Hands')) {
        const poolMatch = text.match(/Lay on Hands.*?(\d+)/i);
        actions.push({
          name: 'Lay on Hands',
          type: 'action',
          pool: poolMatch ? parseInt(poolMatch[1]) : 0,
          description: 'Heal creatures with a pool of hit points'
        });
      }

      if (text.includes('Rage') && text.includes('Barbarian')) {
        const rageMatch = text.match(/Rage.*?(\d+).*?Long Rest/i);
        actions.push({
          name: 'Rage',
          type: 'bonus_action',
          uses: rageMatch ? parseInt(rageMatch[1]) : 3,
          description: 'Enter a rage for damage bonus and resistance'
        });
      }
    }

    // Parse bonus actions
    if (actionType === 'bonus_action') {
      if (text.includes('Bardic Inspiration')) {
        const bardMatch = text.match(/Bardic Inspiration.*?(\d+)/i);
        actions.push({
          name: 'Bardic Inspiration',
          type: 'bonus_action',
          uses: bardMatch ? parseInt(bardMatch[1]) : 0,
          description: 'Give an ally an inspiration die'
        });
      }

      if (text.includes('Cunning Action')) {
        actions.push({
          name: 'Cunning Action',
          type: 'bonus_action',
          description: 'Dash, Disengage, or Hide as a bonus action'
        });
      }

      if (text.includes('Second Wind')) {
        actions.push({
          name: 'Second Wind',
          type: 'bonus_action',
          description: 'Regain 1d10 + fighter level hit points'
        });
      }
    }

    // Parse reactions
    if (actionType === 'reaction') {
      if (text.includes('Opportunity Attack')) {
        actions.push({
          name: 'Opportunity Attack',
          type: 'reaction',
          description: 'Make a melee attack when a creature leaves your reach'
        });
      }

      if (text.includes('Uncanny Dodge')) {
        actions.push({
          name: 'Uncanny Dodge',
          type: 'reaction',
          description: 'Halve damage from an attack you can see'
        });
      }
    }

    return actions;
  }

  private parseSpecialAbilities(text: string): any[] {
    const abilities: any[] = [];
    
    // Common special abilities
    const abilityPatterns = [
      { name: 'Divine Smite', pattern: /Divine Smite/i },
      { name: 'Sneak Attack', pattern: /Sneak Attack/i },
      { name: 'Action Surge', pattern: /Action Surge/i },
      { name: 'Second Wind', pattern: /Second Wind/i },
      { name: 'Lucky', pattern: /Lucky.*3.*luck.*points/i },
      { name: 'Rage', pattern: /Rage/i },
      { name: 'Wild Shape', pattern: /Wild Shape/i },
      { name: 'Channel Divinity', pattern: /Channel Divinity/i }
    ];

    abilityPatterns.forEach(({ name, pattern }) => {
      if (pattern.test(text)) {
        abilities.push({
          name: name,
          type: 'special'
        });
      }
    });

    return abilities;
  }

  private parseBackground(): BackgroundData {
    const text = this.pdfText;
    const backstoryPage = this.pages[4] || text; // Usually page 5
    
    return {
      character_id: 1,
      background: {
        name: this.extractField(text, 'BACKGROUND', 'Unknown'),
        feature: {
          name: 'Background Feature',
          description: 'See Player\'s Handbook for details'
        }
      },
      characteristics: {
        alignment: this.extractField(text, 'ALIGNMENT', 'True Neutral'),
        gender: this.extractField(text, 'GENDER', 'Unknown'),
        eyes: this.extractField(text, 'EYES', 'Unknown'),
        size: this.extractField(text, 'SIZE', 'Medium'),
        height: this.extractField(text, 'HEIGHT', 'Unknown'),
        faith: this.extractField(text, 'FAITH'),
        hair: this.extractField(text, 'HAIR', 'Unknown'),
        skin: this.extractField(text, 'SKIN', 'Unknown'),
        age: parseInt(this.extractField(text, 'AGE', '0').replace(/\D/g, '') || '0'),
        weight: this.extractField(text, 'WEIGHT', 'Unknown'),
        personality_traits: this.parseTraits(backstoryPage, 'PERSONALITY TRAITS'),
        ideals: this.parseTraits(backstoryPage, 'IDEALS'),
        bonds: this.parseTraits(backstoryPage, 'BONDS'),
        flaws: this.parseTraits(backstoryPage, 'FLAWS')
      },
      backstory: this.parseBackstory(backstoryPage),
      organizations: this.parseOrganizations(backstoryPage),
      allies: this.parseAllies(backstoryPage),
      enemies: [],
      notes: {}
    };
  }

  private parseTraits(text: string, traitType: string): string[] {
    const section = this.extractSection(text, traitType, 200);
    if (!section || section.length < 10) return [];
    
    const lines = section.split('\n')
      .filter(line => line.trim() && !line.includes(traitType))
      .map(line => line.trim())
      .filter(line => line.length > 5 && line.length < 200); // Filter reasonable trait lengths
    
    return lines.length > 0 ? lines : [`No ${traitType.toLowerCase()} defined`];
  }

  private parseBackstory(text: string): any {
    const backstorySection = this.extractSection(text, 'CHARACTER BACKSTORY', 1000) ||
                            this.extractSection(text, 'BACKSTORY', 1000);
    
    return {
      title: 'Character Backstory',
      sections: backstorySection ? [{
        heading: 'Background',
        content: backstorySection.trim()
      }] : []
    };
  }

  private parseOrganizations(text: string): any[] {
    const orgsSection = this.extractSection(text, 'ALLIES & ORGANIZATIONS', 300) ||
                       this.extractSection(text, 'ORGANIZATIONS', 300);
    const orgs: any[] = [];
    
    if (orgsSection) {
      const lines = orgsSection.split('\n').filter(line => line.trim() && line.length > 3);
      lines.forEach(line => {
        if (!line.includes('ORGANIZATIONS') && !line.includes('ALLIES')) {
          orgs.push({
            name: line.trim(),
            role: 'Member',
            description: ''
          });
        }
      });
    }

    return orgs;
  }

  private parseAllies(text: string): any[] {
    const alliesSection = this.extractSection(text, 'ALLIES', 200);
    const allies: any[] = [];
    
    if (alliesSection) {
      const lines = alliesSection.split('\n').filter(line => line.trim());
      lines.forEach(line => {
        if (!line.includes('ALLIES') && line.length > 2) {
          allies.push({
            name: line.trim(),
            description: 'Ally'
          });
        }
      });
    }

    return allies.length > 0 ? allies : [{
      name: 'The Party',
      description: 'Adventuring companions'
    }];
  }

  private parseFeatures(): FeaturesData {
    const text = this.pdfText;
    const featuresPages = this.pages.slice(1, 4).join('\n') || text; // Pages 2-4 usually
    
    return {
      features_and_traits: {
        class_features: this.parseClassFeatures(featuresPages),
        species_traits: this.parseSpeciesTraits(text),
        feats: this.parseFeats(featuresPages),
        calculated_features: {
          total_level: this.parseTotalLevel(text),
          proficiency_bonus: this.parseProficiencyBonus(text),
          aura_ranges: {},
          save_bonuses: {},
          hp_bonus_per_level: 0
        }
      },
      metadata: {
        version: '1.0',
        last_updated: new Date().toISOString().split('T')[0],
        notes: ['Auto-parsed from PDF']
      }
    };
  }

  private parseClassFeatures(text: string): any {
    const features: any = {};
    
    // Detect classes and their features - expanded list
    const classPatterns = [
      { 
        class: 'barbarian', 
        features: ['Rage', 'Unarmored Defense', 'Reckless Attack', 'Danger Sense', 
                   'Extra Attack', 'Fast Movement', 'Feral Instinct', 'Brutal Critical',
                   'Primal Path', 'Path of the Zealot', 'Divine Fury', 'Warrior of the Gods'] 
      },
      { 
        class: 'bard', 
        features: ['Bardic Inspiration', 'Jack of All Trades', 'Song of Rest', 
                   'Expertise', 'Font of Inspiration', 'Countercharm', 'Magical Secrets',
                   'College of Lore', 'Cutting Words', 'Additional Magical Secrets'] 
      },
      { 
        class: 'paladin', 
        features: ['Divine Smite', 'Lay on Hands', 'Divine Sense', 'Channel Divinity',
                   'Sacred Oath', 'Aura of Protection', 'Extra Attack', 'Improved Divine Smite'] 
      },
      { 
        class: 'warlock', 
        features: ['Eldritch Invocations', 'Pact', 'Mystic Arcanum', 'Hexblade\'s Curse',
                   'Hex Warrior', 'Pact of the Blade', 'Agonizing Blast'] 
      },
      { 
        class: 'fighter', 
        features: ['Action Surge', 'Second Wind', 'Fighting Style', 'Extra Attack',
                   'Indomitable', 'Champion', 'Battle Master'] 
      },
      { 
        class: 'rogue', 
        features: ['Sneak Attack', 'Cunning Action', 'Uncanny Dodge', 'Evasion',
                   'Reliable Talent', 'Thieves\' Cant', 'Expertise'] 
      },
      { 
        class: 'wizard', 
        features: ['Arcane Recovery', 'Spell Mastery', 'Signature Spell', 
                   'Arcane Tradition', 'School of', 'Portent'] 
      },
      { 
        class: 'cleric', 
        features: ['Channel Divinity', 'Divine Domain', 'Divine Intervention',
                   'Turn Undead', 'Destroy Undead', 'Divine Strike'] 
      },
      { 
        class: 'ranger', 
        features: ['Favored Enemy', 'Natural Explorer', 'Hunter\'s Mark', 
                   'Fighting Style', 'Primeval Awareness', 'Extra Attack'] 
      },
      { 
        class: 'druid', 
        features: ['Wild Shape', 'Druidic', 'Beast Spells', 'Circle', 
                   'Natural Recovery', 'Elemental Wild Shape'] 
      },
      { 
        class: 'monk', 
        features: ['Ki', 'Martial Arts', 'Unarmored Movement', 'Flurry of Blows',
                   'Patient Defense', 'Step of the Wind', 'Stunning Strike'] 
      },
      { 
        class: 'sorcerer', 
        features: ['Sorcery Points', 'Metamagic', 'Font of Magic', 'Sorcerous Origin',
                   'Flexible Casting', 'Subtle Spell', 'Twinned Spell'] 
      }
    ];

    classPatterns.forEach(({ class: className, features: classFeatures }) => {
      const foundFeatures = classFeatures.filter(feature => {
        // Use case-insensitive search and handle special characters
        const pattern = new RegExp(feature.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');
        return pattern.test(text);
      });
      
      if (foundFeatures.length > 0) {
        // Try to get class level
        const level = this.parseClassLevel(text, className);
        
        features[className] = {
          level: level,
          features: foundFeatures.map(f => ({
            name: f,
            source: 'PHB',
            description: this.getFeatureDescription(f, className)
          }))
        };
        
        // Add subclass if detected
        const subclass = this.detectSubclass(text, className);
        if (subclass) {
          features[className].subclass = subclass;
        }
      }
    });

    return features;
  }

  private detectSubclass(text: string, className: string): string | null {
    const subclassPatterns: { [key: string]: string[] } = {
      'barbarian': ['Path of the Zealot', 'Path of the Berserker', 'Path of the Totem Warrior', 
                    'Path of the Ancestral Guardian', 'Path of the Storm Herald'],
      'bard': ['College of Lore', 'College of Valor', 'College of Glamour', 
               'College of Whispers', 'College of Swords'],
      'paladin': ['Oath of Devotion', 'Oath of Vengeance', 'Oath of Redemption', 
                  'Oath of the Crown', 'Oath of Conquest'],
      'warlock': ['The Hexblade', 'The Fiend', 'The Great Old One', 'The Archfey', 
                  'The Celestial', 'The Undying'],
      'fighter': ['Champion', 'Battle Master', 'Eldritch Knight', 'Samurai', 'Cavalier'],
      'rogue': ['Thief', 'Assassin', 'Arcane Trickster', 'Swashbuckler', 'Scout'],
      'wizard': ['School of Evocation', 'School of Divination', 'School of Necromancy', 
                 'School of Abjuration', 'School of Transmutation'],
      'cleric': ['Life Domain', 'Light Domain', 'War Domain', 'Death Domain', 'Knowledge Domain'],
      'ranger': ['Hunter', 'Beast Master', 'Gloom Stalker', 'Horizon Walker'],
      'druid': ['Circle of the Land', 'Circle of the Moon', 'Circle of Dreams', 'Circle of the Shepherd'],
      'monk': ['Way of the Open Hand', 'Way of Shadow', 'Way of the Four Elements', 'Way of the Kensei'],
      'sorcerer': ['Draconic Bloodline', 'Wild Magic', 'Divine Soul', 'Shadow Magic', 'Storm Sorcery']
    };

    const patterns = subclassPatterns[className];
    if (patterns) {
      for (const pattern of patterns) {
        if (text.includes(pattern)) {
          return pattern;
        }
      }
    }
    return null;
  }

  private getFeatureDescription(feature: string, className: string): string {
    // Return a basic description based on the feature
    const descriptions: { [key: string]: string } = {
      'Rage': 'Enter a battle fury for increased damage and resistance',
      'Bardic Inspiration': 'Grant inspiration dice to allies',
      'Divine Smite': 'Expend spell slots to deal extra radiant damage',
      'Sneak Attack': 'Deal extra damage when you have advantage',
      'Action Surge': 'Take an additional action on your turn',
      'Wild Shape': 'Transform into beasts',
      'Ki': 'Use ki points to fuel special abilities',
      'Sorcery Points': 'Fuel metamagic and create spell slots',
      'Channel Divinity': 'Channel divine power for special effects',
      'Eldritch Invocations': 'Gain special warlock abilities'
    };
    
    return descriptions[feature] || `${className} class feature`;
  }

  private parseClassLevel(text: string, className: string): number {
    const pattern = new RegExp(`${className}\\s*(\\d+)`, 'i');
    const match = text.match(pattern);
    return match ? parseInt(match[1]) : 1;
  }

  private parseSpeciesTraits(text: string): any {
    const species = this.extractField(text, 'SPECIES', 'Unknown') ||
                   this.extractField(text, 'RACE', 'Unknown');
    
    const traits: any[] = [];
    
    // Common racial traits
    if (text.includes('Darkvision')) {
      traits.push({
        name: 'Darkvision',
        description: 'See in darkness up to 60 feet'
      });
    }
    
    if (species.toLowerCase().includes('dwarf')) {
      traits.push(
        { name: 'Dwarven Resilience', description: 'Advantage on saves vs poison' },
        { name: 'Stonecunning', description: 'Expertise on History checks about stonework' }
      );
    }
    
    if (species.toLowerCase().includes('elf')) {
      traits.push(
        { name: 'Keen Senses', description: 'Proficiency in Perception' },
        { name: 'Fey Ancestry', description: 'Advantage against being charmed' },
        { name: 'Trance', description: 'Don\'t need to sleep' }
      );
    }

    return {
      species: species,
      subrace: '',
      traits: traits
    };
  }

  private parseFeats(text: string): any[] {
    const feats: any[] = [];
    
    // Common feats
    const featPatterns = [
      { name: 'Lucky', pattern: /Lucky.*3.*luck.*points/i },
      { name: 'Great Weapon Fighting', pattern: /Great Weapon Fighting/i },
      { name: 'Great Weapon Master', pattern: /Great Weapon Master/i },
      { name: 'Sharpshooter', pattern: /Sharpshooter/i },
      { name: 'War Caster', pattern: /War Caster/i },
      { name: 'Sentinel', pattern: /Sentinel/i },
      { name: 'Alert', pattern: /Alert.*\+5.*initiative/i },
      { name: 'Mobile', pattern: /Mobile.*speed.*increases/i },
      { name: 'Tough', pattern: /Tough.*hit.*point.*maximum/i },
      { name: 'Fey Touched', pattern: /Fey Touched/i },
      { name: 'Shadow Touched', pattern: /Shadow Touched/i }
    ];

    featPatterns.forEach(({ name, pattern }) => {
      if (pattern.test(text)) {
        feats.push({
          name: name,
          source: 'PHB'
        });
      }
    });

    return feats;
  }

  private parseTotalLevel(text: string): number {
    // Try multiple patterns
    const patterns = [
      /Level\s*(\d+)/i,
      /CHARACTER LEVEL\s*(\d+)/i,
      /Total Level[:\s]*(\d+)/i
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) return parseInt(match[1]);
    }

    // Calculate from class levels
    const classAndLevel = this.parseClassAndLevel(text);
    return classAndLevel.totalLevel;
  }

  private parseProficiencyBonus(text: string): number {
    const profMatch = text.match(/PROFICIENCY BONUS\s*([+-]?\d+)/i);
    if (profMatch) return Math.abs(parseInt(profMatch[1]));
    
    // Calculate from level
    const level = this.parseTotalLevel(text);
    if (level >= 17) return 6;
    if (level >= 13) return 5;
    if (level >= 9) return 4;
    if (level >= 5) return 3;
    return 2;
  }

  private parseObjectives(): ObjectivesData {
    // Most character sheets won't have objectives
    return {
      objectives_and_contracts: {
        active_contracts: [],
        current_objectives: [],
        completed_objectives: [],
        contract_templates: {
          quest: {
            id: '',
            name: '',
            type: 'Quest',
            status: '',
            priority: '',
            quest_giver: '',
            location: '',
            description: '',
            objectives: [],
            rewards: [],
            deadline: '',
            notes: ''
          }
        }
      },
      metadata: {
        version: '1.0',
        last_updated: new Date().toISOString().split('T')[0],
        notes: ['No objectives found in PDF']
      }
    };
  }

  // Utility methods
  private extractSection(text: string, startMarker: string, maxLength: number = 500): string {
    const startIndex = text.search(new RegExp(startMarker, 'i'));
    if (startIndex === -1) return '';
    
    const section = text.substring(startIndex, startIndex + maxLength);
    return section;
  }

  private calculateModifier(score: number): number {
    return Math.floor((score - 10) / 2);
  }

  private saveJSON(dir: string, filename: string, data: any): void {
    const filepath = path.join(dir, filename);
    fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
    console.log(`✅ Saved ${filename}`);
  }
}

// Main execution
async function main() {
  const parser = new DnDCharacterParser();
  
  // Get PDF path from command line or use default
  const pdfPath = process.argv[2] || './ceej10_110736250.pdf';
  
  if (!fs.existsSync(pdfPath)) {
    console.error('❌ PDF file not found:', pdfPath);
    console.log('Usage: ts-node parse-character.ts <path-to-pdf>');
    process.exit(1);
  }

  console.log('📄 Parsing PDF:', pdfPath);
  
  try {
    await parser.parsePDF(pdfPath);
    console.log('✨ Character data successfully extracted!');
    console.log('📁 Files saved in ./character_data/');
  } catch (error) {
    console.error('❌ Error parsing PDF:', error);
    process.exit(1);
  }
}

// Run the main function
main();

export { DnDCharacterParser };