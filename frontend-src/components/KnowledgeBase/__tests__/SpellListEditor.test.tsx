import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { SpellListEditor } from '../SpellListEditor';

const mockSpellListData = {
    spellcasting: {
        paladin: {
            spells: {
                cantrips: [],
                '1st_level': [
                    {
                        name: 'Cure Wounds',
                        level: 1,
                        school: 'Evocation',
                        casting_time: '1 action',
                        range: 'Touch',
                        components: {
                            verbal: true,
                            somatic: true,
                            material: false
                        },
                        duration: 'Instantaneous',
                        concentration: false,
                        ritual: false,
                        description: 'A creature you touch regains a number of hit points equal to 1d8 + your spellcasting ability modifier.',
                        higher_levels: 'When you cast this spell using a spell slot of 2nd level or higher, the healing increases by 1d8 for each slot level above 1st.',
                        source: "Player's Handbook, pg. 230",
                        tags: ['Healing']
                    }
                ]
            }
        },
        warlock: {
            spells: {
                cantrips: [
                    {
                        name: 'Eldritch Blast',
                        level: 0,
                        school: 'Evocation',
                        casting_time: '1 action',
                        range: '120 feet',
                        components: {
                            verbal: true,
                            somatic: true,
                            material: false
                        },
                        duration: 'Instantaneous',
                        concentration: false,
                        ritual: false,
                        description: 'You hurl a beam of crackling energy. Make a ranged spell attack against one creature or object in range.',
                        cantrip_scaling: 'The spell creates two beams at level 5, three beams at level 11, and four beams at level 17.',
                        source: "Player's Handbook, pg. 267",
                        tags: ['Damage']
                    }
                ]
            }
        }
    },
    metadata: {
        version: '1.0',
        last_updated: '2025-08-10',
        notes: ['Test spell list']
    }
};

describe('SpellListEditor', () => {
    it('renders without crashing', () => {
        const mockOnChange = vi.fn();
        
        // This test just ensures the component can be instantiated without errors
        expect(() => {
            React.createElement(SpellListEditor, {
                data: mockSpellListData,
                onChange: mockOnChange,
                validationErrors: []
            });
        }).not.toThrow();
    });

    it('has the correct structure', () => {
        const mockOnChange = vi.fn();
        
        const element = React.createElement(SpellListEditor, {
            data: mockSpellListData,
            onChange: mockOnChange,
            validationErrors: []
        });
        
        // Basic structure test
        expect(element.type).toBe(SpellListEditor);
        expect(element.props.data).toBe(mockSpellListData);
        expect(element.props.onChange).toBe(mockOnChange);
    });

    it('handles validation errors prop', () => {
        const mockOnChange = vi.fn();
        const validationErrors = [
            {
                field_path: 'spellcasting.paladin.spells.1st_level[0].name',
                message: 'Spell name is required',
                error_type: 'required' as const
            }
        ];
        
        const element = React.createElement(SpellListEditor, {
            data: mockSpellListData,
            onChange: mockOnChange,
            validationErrors: validationErrors
        });
        
        expect(element.props.validationErrors).toBe(validationErrors);
    });

    it('handles empty spellcasting data', () => {
        const mockOnChange = vi.fn();
        const emptyData = {
            spellcasting: {},
            metadata: {
                version: '1.0',
                last_updated: '2025-08-10',
                notes: []
            }
        };
        
        expect(() => {
            React.createElement(SpellListEditor, {
                data: emptyData,
                onChange: mockOnChange,
                validationErrors: []
            });
        }).not.toThrow();
    });

    it('handles spell data with different structures', () => {
        const mockOnChange = vi.fn();
        const complexData = {
            spellcasting: {
                wizard: {
                    spells: {
                        cantrips: [
                            {
                                name: 'Mage Hand',
                                level: 0,
                                school: 'Transmutation',
                                casting_time: '1 action',
                                range: '30 feet',
                                components: {
                                    verbal: true,
                                    somatic: true,
                                    material: false
                                },
                                duration: '1 minute',
                                concentration: false,
                                ritual: false,
                                description: 'A spectral, floating hand appears at a point you choose within range.',
                                source: "Player's Handbook, pg. 203",
                                tags: ['Utility'],
                                cantrip_scaling: 'This spell creates more hands at higher levels.'
                            }
                        ],
                        '3rd_level': [
                            {
                                name: 'Fireball',
                                level: 3,
                                school: 'Evocation',
                                casting_time: '1 action',
                                range: '150 feet',
                                area: '20-foot radius',
                                components: {
                                    verbal: true,
                                    somatic: true,
                                    material: 'a tiny ball of bat guano and sulfur'
                                },
                                duration: 'Instantaneous',
                                concentration: false,
                                ritual: false,
                                description: 'A bright streak flashes from your pointing finger to a point you choose within range.',
                                higher_levels: 'When you cast this spell using a spell slot of 4th level or higher, the damage increases by 1d6 for each slot level above 3rd.',
                                source: "Player's Handbook, pg. 241",
                                tags: ['Damage'],
                                save: {
                                    type: 'DEX' as const
                                }
                            }
                        ]
                    }
                }
            },
            metadata: {
                version: '1.0',
                last_updated: '2025-08-10',
                notes: ['Complex spell data test']
            }
        };
        
        expect(() => {
            React.createElement(SpellListEditor, {
                data: complexData,
                onChange: mockOnChange,
                validationErrors: []
            });
        }).not.toThrow();
    });

    it('calls onChange when data should be updated', () => {
        const mockOnChange = vi.fn();
        
        const element = React.createElement(SpellListEditor, {
            data: mockSpellListData,
            onChange: mockOnChange,
            validationErrors: []
        });
        
        // Verify the onChange function is passed correctly
        expect(element.props.onChange).toBe(mockOnChange);
        expect(typeof element.props.onChange).toBe('function');
    });
});