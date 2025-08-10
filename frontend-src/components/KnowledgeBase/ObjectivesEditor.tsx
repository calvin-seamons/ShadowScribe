import React, { useState, useCallback } from 'react';
import {
    Target,
    FileText,
    CheckCircle,
    XCircle,
    Clock,
    AlertTriangle,
    Plus,
    Trash2,
    ChevronDown,
    ChevronRight,
    Star,
    Users,
    Award,
    Zap
} from 'lucide-react';
import { ValidationError } from '../../services/knowledgeBaseApi';
import { ArrayEditor } from './ArrayEditor';

interface ContractParty {
    name: string;
    title?: string;
}

interface BaseObjective {
    id: string;
    name: string;
    type: 'Quest' | 'Contract' | 'Divine Mission' | 'Personal Goal' | 'Divine Covenant' | 'Guild Assignment';
    status: 'Active' | 'In Progress' | 'Completed' | 'Failed' | 'Suspended' | 'Abandoned';
    description?: string;
    priority?: 'Absolute' | 'Critical' | 'High' | 'Medium' | 'Low';
    deadline?: string;
    notes?: string;
}

interface Quest extends BaseObjective {
    type: 'Quest';
    quest_giver?: string;
    location?: string;
    objectives?: string[];
    rewards?: string[];
}

interface Contract extends BaseObjective {
    type: 'Contract';
    client?: string;
    contractor?: string;
    terms?: string;
    payment?: string;
    penalties?: string;
    special_conditions?: string[];
}

interface DivineMission extends BaseObjective {
    type: 'Divine Mission';
    deity?: string;
    purpose?: string;
    signs_received?: string[];
    objectives?: string[];
    divine_favor?: string;
    consequences_of_failure?: string[];
}

interface PersonalGoal extends BaseObjective {
    type: 'Personal Goal';
    motivation?: string;
    steps?: string[];
    obstacles?: string[];
    importance?: string;
}

interface DivineCovenant extends BaseObjective {
    type: 'Divine Covenant';
    completion_date?: string;
    parties?: {
        patron?: ContractParty;
        bound?: ContractParty;
    };
    outcome?: string;
    rewards?: string[];
    obligations_accepted?: string[];
    lasting_effects?: string[];
}

type ObjectiveType = Quest | Contract | DivineMission | PersonalGoal | DivineCovenant;

interface ContractTemplate {
    id: string;
    name: string;
    type: string;
    status: string;
    [key: string]: any;
}

interface ObjectivesAndContractsData {
    objectives_and_contracts: {
        active_contracts: ObjectiveType[];
        current_objectives: ObjectiveType[];
        completed_objectives: ObjectiveType[];
        contract_templates: Record<string, ContractTemplate>;
    };
    metadata: {
        version: string;
        last_updated: string;
        notes: string[];
    };
}

interface ObjectivesEditorProps {
    data: ObjectivesAndContractsData;
    onChange: (data: ObjectivesAndContractsData) => void;
    validationErrors?: ValidationError[];
}

export const ObjectivesEditor: React.FC<ObjectivesEditorProps> = ({
    data,
    onChange
}) => {
    const [activeTab, setActiveTab] = useState<'active_contracts' | 'current_objectives' | 'completed_objectives' | 'templates'>('active_contracts');
    const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
    const [showTemplateSelector, setShowTemplateSelector] = useState(false);

    const updateData = useCallback((updates: Partial<ObjectivesAndContractsData>) => {
        onChange({ ...data, ...updates });
    }, [data, onChange]);

    const updateObjectivesAndContracts = useCallback((objectivesAndContracts: ObjectivesAndContractsData['objectives_and_contracts']) => {
        updateData({
            objectives_and_contracts: objectivesAndContracts
        });
    }, [updateData]);

    const toggleItemExpansion = (itemKey: string) => {
        const newExpanded = new Set(expandedItems);
        if (newExpanded.has(itemKey)) {
            newExpanded.delete(itemKey);
        } else {
            newExpanded.add(itemKey);
        }
        setExpandedItems(newExpanded);
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'Active':
            case 'In Progress':
                return <Clock className="w-4 h-4 text-blue-400" />;
            case 'Completed':
                return <CheckCircle className="w-4 h-4 text-green-400" />;
            case 'Failed':
            case 'Abandoned':
                return <XCircle className="w-4 h-4 text-red-400" />;
            case 'Suspended':
                return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
            default:
                return <Target className="w-4 h-4 text-gray-400" />;
        }
    };

    const getTypeIcon = (type: string) => {
        switch (type) {
            case 'Quest':
                return <Target className="w-4 h-4 text-purple-400" />;
            case 'Contract':
                return <FileText className="w-4 h-4 text-blue-400" />;
            case 'Divine Mission':
                return <Star className="w-4 h-4 text-yellow-400" />;
            case 'Personal Goal':
                return <Users className="w-4 h-4 text-green-400" />;
            case 'Divine Covenant':
                return <Zap className="w-4 h-4 text-red-400" />;
            case 'Guild Assignment':
                return <Award className="w-4 h-4 text-orange-400" />;
            default:
                return <FileText className="w-4 h-4 text-gray-400" />;
        }
    };

    const getPriorityColor = (priority?: string) => {
        switch (priority) {
            case 'Absolute':
                return 'text-red-500 bg-red-900/20';
            case 'Critical':
                return 'text-red-400 bg-red-900/20';
            case 'High':
                return 'text-orange-400 bg-orange-900/20';
            case 'Medium':
                return 'text-yellow-400 bg-yellow-900/20';
            case 'Low':
                return 'text-green-400 bg-green-900/20';
            default:
                return 'text-gray-400 bg-gray-900/20';
        }
    };

    const createNewObjective = (category: 'active_contracts' | 'current_objectives' | 'completed_objectives', templateType?: string) => {
        const baseObjective: BaseObjective = {
            id: `obj_${Date.now()}`,
            name: '',
            type: 'Quest',
            status: category === 'completed_objectives' ? 'Completed' : 'Active',
            description: ''
        };

        let newObjective: ObjectiveType;

        if (templateType && data.objectives_and_contracts.contract_templates[templateType]) {
            const template = data.objectives_and_contracts.contract_templates[templateType];
            newObjective = {
                ...baseObjective,
                ...template,
                id: baseObjective.id,
                status: baseObjective.status
            } as ObjectiveType;
        } else {
            newObjective = baseObjective as ObjectiveType;
        }

        const updatedCategory = [...(data.objectives_and_contracts[category] as ObjectiveType[]), newObjective];
        updateObjectivesAndContracts({
            ...data.objectives_and_contracts,
            [category]: updatedCategory
        });

        setShowTemplateSelector(false);
    };

    const updateObjective = (category: 'active_contracts' | 'current_objectives' | 'completed_objectives', index: number, updatedObjective: ObjectiveType) => {
        const updatedCategory = [...(data.objectives_and_contracts[category] as ObjectiveType[])];
        updatedCategory[index] = updatedObjective;

        updateObjectivesAndContracts({
            ...data.objectives_and_contracts,
            [category]: updatedCategory
        });
    };

    const removeObjective = (category: 'active_contracts' | 'current_objectives' | 'completed_objectives', index: number) => {
        const updatedCategory = (data.objectives_and_contracts[category] as ObjectiveType[]).filter((_, i) => i !== index);
        updateObjectivesAndContracts({
            ...data.objectives_and_contracts,
            [category]: updatedCategory
        });
    };

    const renderBasicFields = (objective: ObjectiveType, category: 'active_contracts' | 'current_objectives' | 'completed_objectives', index: number) => (
        <div className="space-y-4">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">
                        Name <span className="text-red-400">*</span>
                    </label>
                    <input
                        type="text"
                        value={objective.name}
                        onChange={(e) => updateObjective(category, index, { ...objective, name: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Enter objective name"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Type</label>
                    <select
                        value={objective.type}
                        onChange={(e) => updateObjective(category, index, { ...objective, type: e.target.value as ObjectiveType['type'] })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                        <option value="Quest">Quest</option>
                        <option value="Contract">Contract</option>
                        <option value="Divine Mission">Divine Mission</option>
                        <option value="Personal Goal">Personal Goal</option>
                        <option value="Divine Covenant">Divine Covenant</option>
                        <option value="Guild Assignment">Guild Assignment</option>
                    </select>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Status</label>
                    <select
                        value={objective.status}
                        onChange={(e) => updateObjective(category, index, { ...objective, status: e.target.value as ObjectiveType['status'] })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                        <option value="Active">Active</option>
                        <option value="In Progress">In Progress</option>
                        <option value="Completed">Completed</option>
                        <option value="Failed">Failed</option>
                        <option value="Suspended">Suspended</option>
                        <option value="Abandoned">Abandoned</option>
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Priority</label>
                    <select
                        value={objective.priority || ''}
                        onChange={(e) => updateObjective(category, index, { ...objective, priority: e.target.value as ObjectiveType['priority'] })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                        <option value="">Select priority</option>
                        <option value="Absolute">Absolute</option>
                        <option value="Critical">Critical</option>
                        <option value="High">High</option>
                        <option value="Medium">Medium</option>
                        <option value="Low">Low</option>
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Deadline</label>
                    <input
                        type="text"
                        value={objective.deadline || ''}
                        onChange={(e) => updateObjective(category, index, { ...objective, deadline: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="e.g., 3 days, Next full moon"
                    />
                </div>
            </div>

            {/* Description */}
            <div>
                <label className="block text-sm font-medium text-white mb-2">Description</label>
                <textarea
                    value={objective.description || ''}
                    onChange={(e) => updateObjective(category, index, { ...objective, description: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    rows={3}
                    placeholder="Describe the objective"
                />
            </div>
        </div>
    );

    const renderQuestFields = (quest: Quest, category: 'active_contracts' | 'current_objectives' | 'completed_objectives', index: number) => (
        <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Quest Giver</label>
                    <input
                        type="text"
                        value={quest.quest_giver || ''}
                        onChange={(e) => updateObjective(category, index, { ...quest, quest_giver: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Who gave this quest?"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Location</label>
                    <input
                        type="text"
                        value={quest.location || ''}
                        onChange={(e) => updateObjective(category, index, { ...quest, location: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Where does this take place?"
                    />
                </div>
            </div>

            <div>
                <label className="block text-sm font-medium text-white mb-2">Objectives</label>
                <ArrayEditor
                    items={quest.objectives || []}
                    onChange={(objectives) => updateObjective(category, index, { ...quest, objectives })}
                    label="Objectives"
                    itemSchema={{
                        key: 'objective',
                        type: 'string',
                        label: 'Objective',
                        required: false
                    }}
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-white mb-2">Rewards</label>
                <ArrayEditor
                    items={quest.rewards || []}
                    onChange={(rewards) => updateObjective(category, index, { ...quest, rewards })}
                    label="Rewards"
                    itemSchema={{
                        key: 'reward',
                        type: 'string',
                        label: 'Reward',
                        required: false
                    }}
                />
            </div>
        </div>
    );

    const renderContractFields = (contract: Contract, category: 'active_contracts' | 'current_objectives' | 'completed_objectives', index: number) => (
        <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Client</label>
                    <input
                        type="text"
                        value={contract.client || ''}
                        onChange={(e) => updateObjective(category, index, { ...contract, client: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Who is the client?"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Contractor</label>
                    <input
                        type="text"
                        value={contract.contractor || ''}
                        onChange={(e) => updateObjective(category, index, { ...contract, contractor: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Who is fulfilling the contract?"
                    />
                </div>
            </div>

            <div>
                <label className="block text-sm font-medium text-white mb-2">Terms</label>
                <textarea
                    value={contract.terms || ''}
                    onChange={(e) => updateObjective(category, index, { ...contract, terms: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    rows={3}
                    placeholder="Contract terms and conditions"
                />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Payment</label>
                    <input
                        type="text"
                        value={contract.payment || ''}
                        onChange={(e) => updateObjective(category, index, { ...contract, payment: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Payment amount and terms"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Penalties</label>
                    <input
                        type="text"
                        value={contract.penalties || ''}
                        onChange={(e) => updateObjective(category, index, { ...contract, penalties: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Penalties for breach"
                    />
                </div>
            </div>

            <div>
                <label className="block text-sm font-medium text-white mb-2">Special Conditions</label>
                <ArrayEditor
                    items={contract.special_conditions || []}
                    onChange={(special_conditions) => updateObjective(category, index, { ...contract, special_conditions })}
                    label="Special Conditions"
                    itemSchema={{
                        key: 'condition',
                        type: 'string',
                        label: 'Condition',
                        required: false
                    }}
                />
            </div>
        </div>
    );

    const renderDivineMissionFields = (mission: DivineMission, category: 'active_contracts' | 'current_objectives' | 'completed_objectives', index: number) => (
        <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Deity</label>
                    <input
                        type="text"
                        value={mission.deity || ''}
                        onChange={(e) => updateObjective(category, index, { ...mission, deity: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Which deity gave this mission?"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Divine Favor</label>
                    <input
                        type="text"
                        value={mission.divine_favor || ''}
                        onChange={(e) => updateObjective(category, index, { ...mission, divine_favor: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Current standing with deity"
                    />
                </div>
            </div>

            <div>
                <label className="block text-sm font-medium text-white mb-2">Purpose</label>
                <textarea
                    value={mission.purpose || ''}
                    onChange={(e) => updateObjective(category, index, { ...mission, purpose: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    rows={2}
                    placeholder="Divine purpose of this mission"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-white mb-2">Signs Received</label>
                <ArrayEditor
                    items={mission.signs_received || []}
                    onChange={(signs_received) => updateObjective(category, index, { ...mission, signs_received })}
                    label="Signs Received"
                    itemSchema={{
                        key: 'sign',
                        type: 'string',
                        label: 'Sign',
                        required: false
                    }}
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-white mb-2">Objectives</label>
                <ArrayEditor
                    items={mission.objectives || []}
                    onChange={(objectives) => updateObjective(category, index, { ...mission, objectives })}
                    label="Objectives"
                    itemSchema={{
                        key: 'objective',
                        type: 'string',
                        label: 'Objective',
                        required: false
                    }}
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-white mb-2">Consequences of Failure</label>
                <ArrayEditor
                    items={mission.consequences_of_failure || []}
                    onChange={(consequences_of_failure) => updateObjective(category, index, { ...mission, consequences_of_failure })}
                    label="Consequences of Failure"
                    itemSchema={{
                        key: 'consequence',
                        type: 'string',
                        label: 'Consequence',
                        required: false
                    }}
                />
            </div>
        </div>
    );

    const renderPersonalGoalFields = (goal: PersonalGoal, category: 'active_contracts' | 'current_objectives' | 'completed_objectives', index: number) => (
        <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Motivation</label>
                    <textarea
                        value={goal.motivation || ''}
                        onChange={(e) => updateObjective(category, index, { ...goal, motivation: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        rows={2}
                        placeholder="What drives this goal?"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Importance</label>
                    <input
                        type="text"
                        value={goal.importance || ''}
                        onChange={(e) => updateObjective(category, index, { ...goal, importance: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="How important is this goal?"
                    />
                </div>
            </div>

            <div>
                <label className="block text-sm font-medium text-white mb-2">Steps</label>
                <ArrayEditor
                    items={goal.steps || []}
                    onChange={(steps) => updateObjective(category, index, { ...goal, steps })}
                    label="Steps"
                    itemSchema={{
                        key: 'step',
                        type: 'string',
                        label: 'Step',
                        required: false
                    }}
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-white mb-2">Obstacles</label>
                <ArrayEditor
                    items={goal.obstacles || []}
                    onChange={(obstacles) => updateObjective(category, index, { ...goal, obstacles })}
                    label="Obstacles"
                    itemSchema={{
                        key: 'obstacle',
                        type: 'string',
                        label: 'Obstacle',
                        required: false
                    }}
                />
            </div>
        </div>
    );

    const renderDivineCovenantFields = (covenant: DivineCovenant, category: 'active_contracts' | 'current_objectives' | 'completed_objectives', index: number) => (
        <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Completion Date</label>
                    <input
                        type="text"
                        value={covenant.completion_date || ''}
                        onChange={(e) => updateObjective(category, index, { ...covenant, completion_date: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="When was this covenant made?"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Outcome</label>
                    <input
                        type="text"
                        value={covenant.outcome || ''}
                        onChange={(e) => updateObjective(category, index, { ...covenant, outcome: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Result of the covenant"
                    />
                </div>
            </div>

            {/* Parties */}
            <div className="border border-gray-600 rounded-md p-3">
                <h4 className="text-sm font-medium text-white mb-3">Parties Involved</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Patron</label>
                        <div className="space-y-2">
                            <input
                                type="text"
                                value={covenant.parties?.patron?.name || ''}
                                onChange={(e) => updateObjective(category, index, {
                                    ...covenant,
                                    parties: {
                                        ...covenant.parties,
                                        patron: { ...covenant.parties?.patron, name: e.target.value }
                                    }
                                })}
                                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                placeholder="Patron name"
                            />
                            <input
                                type="text"
                                value={covenant.parties?.patron?.title || ''}
                                onChange={(e) => updateObjective(category, index, {
                                    ...covenant,
                                    parties: {
                                        ...covenant.parties,
                                        patron: { name: covenant.parties?.patron?.name || '', title: e.target.value }
                                    }
                                })}
                                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                placeholder="Patron title"
                            />
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Bound</label>
                        <div className="space-y-2">
                            <input
                                type="text"
                                value={covenant.parties?.bound?.name || ''}
                                onChange={(e) => updateObjective(category, index, {
                                    ...covenant,
                                    parties: {
                                        ...covenant.parties,
                                        bound: { ...covenant.parties?.bound, name: e.target.value }
                                    }
                                })}
                                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                placeholder="Bound party name"
                            />
                            <input
                                type="text"
                                value={covenant.parties?.bound?.title || ''}
                                onChange={(e) => updateObjective(category, index, {
                                    ...covenant,
                                    parties: {
                                        ...covenant.parties,
                                        bound: { name: covenant.parties?.bound?.name || '', title: e.target.value }
                                    }
                                })}
                                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                placeholder="Bound party title"
                            />
                        </div>
                    </div>
                </div>
            </div>

            <div>
                <label className="block text-sm font-medium text-white mb-2">Rewards</label>
                <ArrayEditor
                    items={covenant.rewards || []}
                    onChange={(rewards) => updateObjective(category, index, { ...covenant, rewards })}
                    label="Rewards"
                    itemSchema={{
                        key: 'reward',
                        type: 'string',
                        label: 'Reward',
                        required: false
                    }}
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-white mb-2">Obligations Accepted</label>
                <ArrayEditor
                    items={covenant.obligations_accepted || []}
                    onChange={(obligations_accepted) => updateObjective(category, index, { ...covenant, obligations_accepted })}
                    label="Obligations Accepted"
                    itemSchema={{
                        key: 'obligation',
                        type: 'string',
                        label: 'Obligation',
                        required: false
                    }}
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-white mb-2">Lasting Effects</label>
                <ArrayEditor
                    items={covenant.lasting_effects || []}
                    onChange={(lasting_effects) => updateObjective(category, index, { ...covenant, lasting_effects })}
                    label="Lasting Effects"
                    itemSchema={{
                        key: 'effect',
                        type: 'string',
                        label: 'Effect',
                        required: false
                    }}
                />
            </div>
        </div>
    );

    const renderTypeSpecificFields = (objective: ObjectiveType, category: 'active_contracts' | 'current_objectives' | 'completed_objectives', index: number) => {
        switch (objective.type) {
            case 'Quest':
                return renderQuestFields(objective as Quest, category, index);
            case 'Contract':
                return renderContractFields(objective as Contract, category, index);
            case 'Divine Mission':
                return renderDivineMissionFields(objective as DivineMission, category, index);
            case 'Personal Goal':
                return renderPersonalGoalFields(objective as PersonalGoal, category, index);
            case 'Divine Covenant':
                return renderDivineCovenantFields(objective as DivineCovenant, category, index);
            default:
                return null;
        }
    };

    const renderObjectiveEditor = (objective: ObjectiveType, category: 'active_contracts' | 'current_objectives' | 'completed_objectives', index: number) => {
        const itemKey = `${category}-${index}`;
        const isExpanded = expandedItems.has(itemKey);

        return (
            <div key={index} className="border border-gray-600 rounded-md">
                <div className="flex items-center justify-between p-3 bg-gray-750">
                    <div className="flex items-center space-x-2">
                        <button
                            type="button"
                            onClick={() => toggleItemExpansion(itemKey)}
                            className="flex items-center space-x-2"
                        >
                            {isExpanded ? (
                                <ChevronDown className="w-4 h-4 text-gray-400" />
                            ) : (
                                <ChevronRight className="w-4 h-4 text-gray-400" />
                            )}
                            {getTypeIcon(objective.type)}
                            <span className="font-medium text-white">
                                {objective.name || `${objective.type} ${index + 1}`}
                            </span>
                        </button>
                        <div className="flex items-center space-x-2">
                            {getStatusIcon(objective.status)}
                            <span className="text-sm text-gray-400">{objective.status}</span>
                            {objective.priority && (
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(objective.priority)}`}>
                                    {objective.priority}
                                </span>
                            )}
                        </div>
                    </div>
                    <button
                        type="button"
                        onClick={() => removeObjective(category, index)}
                        className="text-red-400 hover:text-red-300 p-1"
                        title="Remove objective"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>

                {isExpanded && (
                    <div className="p-4 space-y-6 border-t border-gray-600">
                        {renderBasicFields(objective, category, index)}
                        {renderTypeSpecificFields(objective, category, index)}

                        {/* Notes */}
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">Notes</label>
                            <textarea
                                value={objective.notes || ''}
                                onChange={(e) => updateObjective(category, index, { ...objective, notes: e.target.value })}
                                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                rows={2}
                                placeholder="Additional notes"
                            />
                        </div>
                    </div>
                )}
            </div>
        );
    };

    const renderTemplateSelector = () => {
        const templates = Object.entries(data.objectives_and_contracts.contract_templates);

        return (
            <div className="border border-gray-600 rounded-md p-4 bg-gray-750">
                <h3 className="text-lg font-semibold text-white mb-4">Create from Template</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {templates.map(([templateKey, template]) => (
                        <button
                            key={templateKey}
                            onClick={() => activeTab !== 'templates' && createNewObjective(activeTab, templateKey)}
                            className="flex items-center space-x-2 p-3 border border-gray-600 rounded-md hover:border-purple-500 hover:bg-gray-700 transition-colors"
                        >
                            {getTypeIcon(template.type)}
                            <span className="text-white">{template.name || templateKey}</span>
                        </button>
                    ))}
                    <button
                        onClick={() => activeTab !== 'templates' && createNewObjective(activeTab)}
                        className="flex items-center space-x-2 p-3 border border-dashed border-gray-600 rounded-md hover:border-purple-500 hover:bg-gray-700 transition-colors"
                    >
                        <Plus className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-400">Blank Objective</span>
                    </button>
                </div>
                <div className="mt-4 flex justify-end">
                    <button
                        onClick={() => setShowTemplateSelector(false)}
                        className="px-4 py-2 text-gray-400 hover:text-white"
                    >
                        Cancel
                    </button>
                </div>
            </div>
        );
    };

    const renderObjectivesList = (category: 'active_contracts' | 'current_objectives' | 'completed_objectives') => {
        const objectives = data.objectives_and_contracts[category] as ObjectiveType[];

        return (
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold text-white capitalize">
                        {category.replace('_', ' ')}
                    </h2>
                    <button
                        onClick={() => setShowTemplateSelector(true)}
                        className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                    >
                        <Plus className="w-4 h-4" />
                        <span>Add Objective</span>
                    </button>
                </div>

                {showTemplateSelector && renderTemplateSelector()}

                {objectives.length === 0 ? (
                    <div className="text-center py-8 text-gray-400">
                        <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>No {category.replace('_', ' ').toLowerCase()} yet.</p>
                        <p className="text-sm">Click "Add Objective" to get started.</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {objectives.map((objective, index) =>
                            renderObjectiveEditor(objective, category, index)
                        )}
                    </div>
                )}
            </div>
        );
    };

    const tabs = [
        { key: 'active_contracts', label: 'Active Contracts', icon: FileText },
        { key: 'current_objectives', label: 'Current Objectives', icon: Target },
        { key: 'completed_objectives', label: 'Completed', icon: CheckCircle },
        { key: 'templates', label: 'Templates', icon: Star }
    ] as const;

    return (
        <div className="space-y-6">
            {/* Tab Navigation */}
            <div className="border-b border-gray-600">
                <nav className="flex space-x-8">
                    {tabs.map(({ key, label, icon: Icon }) => (
                        <button
                            key={key}
                            onClick={() => {
                                setActiveTab(key);
                                setShowTemplateSelector(false);
                            }}
                            className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${activeTab === key
                                ? 'border-purple-500 text-purple-400'
                                : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                                }`}
                        >
                            <Icon className="w-4 h-4" />
                            <span>{label}</span>
                            {key !== 'templates' && (
                                <span className="bg-gray-700 text-gray-300 px-2 py-1 rounded-full text-xs">
                                    {data.objectives_and_contracts[key].length}
                                </span>
                            )}
                        </button>
                    ))}
                </nav>
            </div>

            {/* Tab Content */}
            <div className="min-h-96">
                {activeTab === 'templates' ? (
                    <div className="space-y-4">
                        <h2 className="text-xl font-semibold text-white">Contract Templates</h2>
                        <div className="text-gray-400">
                            <p>Templates are used to quickly create new objectives with predefined structures.</p>
                            <p className="text-sm mt-2">
                                Templates are automatically loaded from the contract_templates section of your objectives file.
                            </p>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {Object.entries(data.objectives_and_contracts.contract_templates).map(([templateKey, template]) => (
                                <div key={templateKey} className="border border-gray-600 rounded-md p-4">
                                    <div className="flex items-center space-x-2 mb-2">
                                        {getTypeIcon(template.type)}
                                        <h3 className="font-medium text-white">{template.name || templateKey}</h3>
                                    </div>
                                    <p className="text-sm text-gray-400">Type: {template.type}</p>
                                    <p className="text-sm text-gray-400">Status: {template.status}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    renderObjectivesList(activeTab)
                )}
            </div>
        </div>
    );
};