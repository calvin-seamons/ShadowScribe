import React, { useState } from 'react';
import { 
  Plus, 
  Trash2, 
  GripVertical, 
  ChevronDown, 
  ChevronRight,
  Info
} from 'lucide-react';

interface FormField {
  key: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  label: string;
  required: boolean;
  description?: string;
  children?: FormField[];
  enum?: string[];
  minimum?: number;
  maximum?: number;
  pattern?: string;
}

interface ArrayEditorProps {
  items: any[];
  onChange: (items: any[]) => void;
  itemSchema?: FormField;
  label: string;
}

export const ArrayEditor: React.FC<ArrayEditorProps> = ({
  items,
  onChange,
  itemSchema,
  label
}) => {
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  const addItem = () => {
    let newItem: any;
    
    if (itemSchema?.type === 'object' && itemSchema.children) {
      // Create empty object with default values based on schema
      newItem = {};
      itemSchema.children.forEach(field => {
        if (field.type === 'boolean') {
          newItem[field.key.split('.').pop() || field.key] = false;
        } else if (field.type === 'number') {
          newItem[field.key.split('.').pop() || field.key] = field.minimum || 0;
        } else if (field.type === 'array') {
          newItem[field.key.split('.').pop() || field.key] = [];
        } else if (field.type === 'object') {
          newItem[field.key.split('.').pop() || field.key] = {};
        } else {
          newItem[field.key.split('.').pop() || field.key] = '';
        }
      });
    } else if (itemSchema?.type === 'number') {
      newItem = itemSchema.minimum || 0;
    } else if (itemSchema?.type === 'boolean') {
      newItem = false;
    } else if (itemSchema?.type === 'array') {
      newItem = [];
    } else {
      newItem = '';
    }

    onChange([...items, newItem]);
  };

  const removeItem = (index: number) => {
    const newItems = items.filter((_, i) => i !== index);
    onChange(newItems);
    
    // Update expanded items indices
    const newExpanded = new Set<number>();
    expandedItems.forEach(expandedIndex => {
      if (expandedIndex < index) {
        newExpanded.add(expandedIndex);
      } else if (expandedIndex > index) {
        newExpanded.add(expandedIndex - 1);
      }
    });
    setExpandedItems(newExpanded);
  };

  const updateItem = (index: number, newValue: any) => {
    const newItems = [...items];
    newItems[index] = newValue;
    onChange(newItems);
  };

  const moveItem = (fromIndex: number, toIndex: number) => {
    if (fromIndex === toIndex) return;
    
    const newItems = [...items];
    const [movedItem] = newItems.splice(fromIndex, 1);
    newItems.splice(toIndex, 0, movedItem);
    onChange(newItems);

    // Update expanded items indices
    const newExpanded = new Set<number>();
    expandedItems.forEach(expandedIndex => {
      if (expandedIndex === fromIndex) {
        newExpanded.add(toIndex);
      } else if (expandedIndex > fromIndex && expandedIndex <= toIndex) {
        newExpanded.add(expandedIndex - 1);
      } else if (expandedIndex < fromIndex && expandedIndex >= toIndex) {
        newExpanded.add(expandedIndex + 1);
      } else {
        newExpanded.add(expandedIndex);
      }
    });
    setExpandedItems(newExpanded);
  };

  const toggleItemExpansion = (index: number) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedItems(newExpanded);
  };

  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();
    if (draggedIndex !== null && draggedIndex !== dropIndex) {
      moveItem(draggedIndex, dropIndex);
    }
    setDraggedIndex(null);
  };

  const renderSimpleItem = (item: any, index: number) => {
    const baseClasses = "flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500";

    return (
      <div
        key={index}
        className={`flex items-center space-x-2 p-2 rounded-md border ${
          draggedIndex === index ? 'border-purple-500 bg-purple-900/20' : 'border-gray-600'
        }`}
        draggable
        onDragStart={(e) => handleDragStart(e, index)}
        onDragOver={handleDragOver}
        onDrop={(e) => handleDrop(e, index)}
      >
        <button
          type="button"
          className="text-gray-400 hover:text-white cursor-grab active:cursor-grabbing"
          title="Drag to reorder"
        >
          <GripVertical className="w-4 h-4" />
        </button>

        {itemSchema?.type === 'boolean' ? (
          <label className="flex items-center space-x-2 flex-1">
            <input
              type="checkbox"
              checked={item || false}
              onChange={(e) => updateItem(index, e.target.checked)}
              className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
            />
            <span className="text-sm text-gray-300">Item {index + 1}</span>
          </label>
        ) : itemSchema?.enum ? (
          <select
            value={item || ''}
            onChange={(e) => updateItem(index, e.target.value)}
            className={baseClasses}
          >
            <option value="">Select option</option>
            {itemSchema.enum.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        ) : itemSchema?.type === 'number' ? (
          <input
            type="number"
            value={item || ''}
            onChange={(e) => updateItem(index, e.target.value ? Number(e.target.value) : undefined)}
            min={itemSchema.minimum}
            max={itemSchema.maximum}
            className={baseClasses}
            placeholder={`Item ${index + 1}`}
          />
        ) : (
          <input
            type="text"
            value={item || ''}
            onChange={(e) => updateItem(index, e.target.value)}
            pattern={itemSchema?.pattern}
            className={baseClasses}
            placeholder={`Item ${index + 1}`}
          />
        )}

        <button
          type="button"
          onClick={() => removeItem(index)}
          className="text-red-400 hover:text-red-300 p-1"
          title="Remove item"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    );
  };

  const renderObjectItem = (item: any, index: number) => {
    const isExpanded = expandedItems.has(index);

    return (
      <div
        key={index}
        className={`border rounded-md ${
          draggedIndex === index ? 'border-purple-500 bg-purple-900/20' : 'border-gray-600'
        }`}
        draggable
        onDragStart={(e) => handleDragStart(e, index)}
        onDragOver={handleDragOver}
        onDrop={(e) => handleDrop(e, index)}
      >
        {/* Item Header */}
        <div className="flex items-center justify-between p-3 bg-gray-750">
          <div className="flex items-center space-x-2">
            <button
              type="button"
              className="text-gray-400 hover:text-white cursor-grab active:cursor-grabbing"
              title="Drag to reorder"
            >
              <GripVertical className="w-4 h-4" />
            </button>
            
            <button
              type="button"
              onClick={() => toggleItemExpansion(index)}
              className="flex items-center space-x-2 text-left"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-400" />
              )}
              <span className="font-medium text-white">
                {itemSchema?.label || 'Item'} {index + 1}
              </span>
            </button>
          </div>

          <button
            type="button"
            onClick={() => removeItem(index)}
            className="text-red-400 hover:text-red-300 p-1"
            title="Remove item"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>

        {/* Item Content */}
        {isExpanded && itemSchema?.children && (
          <div className="p-3 space-y-4 border-t border-gray-600">
            {itemSchema.children.map(field => {
              const fieldKey = field.key.split('.').pop() || field.key;
              const fieldValue = item[fieldKey];
              
              return (
                <div key={fieldKey} className="space-y-2">
                  <label className="block text-sm font-medium text-white">
                    {field.label}
                    {field.required && <span className="text-red-400 ml-1">*</span>}
                  </label>

                  {field.description && (
                    <div className="flex items-start space-x-2 text-sm text-gray-400">
                      <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      <p>{field.description}</p>
                    </div>
                  )}

                  {field.type === 'boolean' ? (
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={fieldValue || false}
                        onChange={(e) => updateItem(index, { ...item, [fieldKey]: e.target.checked })}
                        className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                      />
                      <span className="text-sm text-gray-300">Enable {field.label}</span>
                    </label>
                  ) : field.enum ? (
                    <select
                      value={fieldValue || ''}
                      onChange={(e) => updateItem(index, { ...item, [fieldKey]: e.target.value })}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      <option value="">Select {field.label}</option>
                      {field.enum.map(option => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                  ) : field.type === 'number' ? (
                    <input
                      type="number"
                      value={fieldValue || ''}
                      onChange={(e) => updateItem(index, { 
                        ...item, 
                        [fieldKey]: e.target.value ? Number(e.target.value) : undefined 
                      })}
                      min={field.minimum}
                      max={field.maximum}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder={`Enter ${field.label.toLowerCase()}`}
                    />
                  ) : field.type === 'array' ? (
                    <ArrayEditor
                      items={fieldValue || []}
                      onChange={(newItems) => updateItem(index, { ...item, [fieldKey]: newItems })}
                      itemSchema={field.children?.[0]} // Simplified for nested arrays
                      label={field.label}
                    />
                  ) : (
                    <input
                      type="text"
                      value={fieldValue || ''}
                      onChange={(e) => updateItem(index, { ...item, [fieldKey]: e.target.value })}
                      pattern={field.pattern}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder={`Enter ${field.label.toLowerCase()}`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-3">
      {/* Array Items */}
      {items.length > 0 ? (
        <div className="space-y-2">
          {items.map((item, index) => {
            if (itemSchema?.type === 'object' && itemSchema.children) {
              return renderObjectItem(item, index);
            } else {
              return renderSimpleItem(item, index);
            }
          })}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-400 border-2 border-dashed border-gray-600 rounded-md">
          <p className="text-sm">No items in {label.toLowerCase()}</p>
          <p className="text-xs mt-1">Click "Add Item" to get started</p>
        </div>
      )}

      {/* Add Button */}
      <button
        type="button"
        onClick={addItem}
        className="w-full flex items-center justify-center space-x-2 px-4 py-2 border-2 border-dashed border-gray-600 rounded-md text-gray-400 hover:border-purple-500 hover:text-purple-400 transition-colors"
      >
        <Plus className="w-4 h-4" />
        <span>Add Item</span>
      </button>

      {/* Item Count */}
      {items.length > 0 && (
        <p className="text-xs text-gray-500 text-center">
          {items.length} item{items.length !== 1 ? 's' : ''} in {label.toLowerCase()}
        </p>
      )}
    </div>
  );
};