import React, { useState, useCallback, useMemo } from 'react';
import { 
  FileText, 
  Edit3, 
  Check, 
  X, 
  AlertTriangle, 
  CheckCircle, 
  Info,
  Eye,
  EyeOff
} from 'lucide-react';
import { PDFStructureInfo } from '../../types';

interface PDFContentPreviewProps {
  extractedText: string;
  structureInfo: PDFStructureInfo;
  onConfirm: (finalText: string) => void;
  onReject: () => void;
  onEdit?: (editedText: string) => void;
}

interface TextQualityIndicator {
  level: 'high' | 'medium' | 'low';
  color: string;
  icon: React.ReactNode;
  message: string;
  suggestions: string[];
}

export const PDFContentPreview: React.FC<PDFContentPreviewProps> = ({
  extractedText,
  structureInfo,
  onConfirm,
  onReject,
  onEdit
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState(extractedText);
  const [showRawText, setShowRawText] = useState(false);

  // Calculate text quality indicators
  const qualityIndicator: TextQualityIndicator = useMemo(() => {
    const indicators: Record<string, TextQualityIndicator> = {
      high: {
        level: 'high',
        color: 'text-green-400',
        icon: <CheckCircle className="h-5 w-5" />,
        message: 'Excellent text quality detected',
        suggestions: [
          'Text appears well-structured and readable',
          'Should parse accurately with minimal corrections needed'
        ]
      },
      medium: {
        level: 'medium',
        color: 'text-yellow-400',
        icon: <AlertTriangle className="h-5 w-5" />,
        message: 'Good text quality with minor issues',
        suggestions: [
          'Some formatting irregularities detected',
          'Review extracted content for accuracy',
          'Consider minor edits if needed'
        ]
      },
      low: {
        level: 'low',
        color: 'text-red-400',
        icon: <AlertTriangle className="h-5 w-5" />,
        message: 'Poor text quality detected',
        suggestions: [
          'Significant formatting issues found',
          'Manual review and editing recommended',
          'Consider using a higher quality PDF if available'
        ]
      }
    };
    
    return indicators[structureInfo.text_quality] || indicators.medium;
  }, [structureInfo.text_quality]);

  // Format detection info
  const formatInfo = useMemo(() => {
    const formats: Record<string, { name: string; description: string; color: string }> = {
      dnd_beyond: {
        name: 'D&D Beyond Export',
        description: 'Structured character sheet from D&D Beyond',
        color: 'text-blue-400'
      },
      roll20: {
        name: 'Roll20 Character Sheet',
        description: 'Character sheet exported from Roll20',
        color: 'text-purple-400'
      },
      handwritten: {
        name: 'Handwritten/Filled Sheet',
        description: 'Manually filled or handwritten character sheet',
        color: 'text-orange-400'
      },
      unknown: {
        name: 'Unknown Format',
        description: 'Format not automatically recognized',
        color: 'text-gray-400'
      }
    };
    
    return formats[structureInfo.detected_format] || formats.unknown;
  }, [structureInfo.detected_format]);

  // Text statistics
  const textStats = useMemo(() => {
    const lines = extractedText.split('\n').length;
    const words = extractedText.trim().split(/\s+/).length;
    const characters = extractedText.length;
    
    return { lines, words, characters };
  }, [extractedText]);

  const handleEditToggle = useCallback(() => {
    if (isEditing) {
      // Save changes
      onEdit?.(editedText);
    }
    setIsEditing(!isEditing);
  }, [isEditing, editedText, onEdit]);

  const handleTextChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setEditedText(e.target.value);
  }, []);

  const handleConfirm = useCallback(() => {
    const finalText = isEditing ? editedText : extractedText;
    onConfirm(finalText);
  }, [isEditing, editedText, extractedText, onConfirm]);

  const handleResetEdit = useCallback(() => {
    setEditedText(extractedText);
    setIsEditing(false);
  }, [extractedText]);

  const displayText = isEditing ? editedText : extractedText;

  return (
    <div className="w-full max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Review Extracted Content</h2>
          <p className="text-gray-400">
            Review the text extracted from your PDF and make any necessary corrections before proceeding.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowRawText(!showRawText)}
            className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-300 hover:text-white transition-colors"
          >
            {showRawText ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
            {showRawText ? 'Hide Raw' : 'Show Raw'}
          </button>
        </div>
      </div>

      {/* Quality and Format Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Text Quality Indicator */}
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center mb-3">
            <div className={qualityIndicator.color}>
              {qualityIndicator.icon}
            </div>
            <h3 className="text-white font-medium ml-2">Text Quality</h3>
          </div>
          <p className={`text-sm mb-2 ${qualityIndicator.color}`}>
            {qualityIndicator.message}
          </p>
          <ul className="text-xs text-gray-400 space-y-1">
            {qualityIndicator.suggestions.map((suggestion, index) => (
              <li key={index}>• {suggestion}</li>
            ))}
          </ul>
        </div>

        {/* Format Detection */}
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center mb-3">
            <FileText className={`h-5 w-5 ${formatInfo.color}`} />
            <h3 className="text-white font-medium ml-2">Detected Format</h3>
          </div>
          <p className={`text-sm mb-2 ${formatInfo.color}`}>
            {formatInfo.name}
          </p>
          <p className="text-xs text-gray-400">
            {formatInfo.description}
          </p>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            {structureInfo.has_form_fields && (
              <span className="px-2 py-1 bg-blue-900/30 text-blue-300 rounded">
                Form Fields
              </span>
            )}
            {structureInfo.has_tables && (
              <span className="px-2 py-1 bg-green-900/30 text-green-300 rounded">
                Tables
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Text Statistics */}
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center mb-3">
          <Info className="h-5 w-5 text-gray-400" />
          <h3 className="text-white font-medium ml-2">Content Statistics</h3>
        </div>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-400">Lines:</span>
            <span className="text-white ml-2">{textStats.lines}</span>
          </div>
          <div>
            <span className="text-gray-400">Words:</span>
            <span className="text-white ml-2">{textStats.words}</span>
          </div>
          <div>
            <span className="text-gray-400">Characters:</span>
            <span className="text-white ml-2">{textStats.characters}</span>
          </div>
        </div>
      </div>

      {/* Text Content */}
      <div className="bg-gray-800 rounded-lg">
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h3 className="text-white font-medium">Extracted Text Content</h3>
          <div className="flex items-center space-x-2">
            {isEditing && (
              <button
                onClick={handleResetEdit}
                className="inline-flex items-center px-3 py-1 text-sm font-medium text-gray-400 hover:text-white transition-colors"
              >
                Reset
              </button>
            )}
            <button
              onClick={handleEditToggle}
              className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded transition-colors ${
                isEditing 
                  ? 'bg-green-600 hover:bg-green-700 text-white' 
                  : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
              }`}
            >
              {isEditing ? (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Save Changes
                </>
              ) : (
                <>
                  <Edit3 className="h-4 w-4 mr-2" />
                  Edit Text
                </>
              )}
            </button>
          </div>
        </div>

        <div className="p-4">
          {isEditing ? (
            <textarea
              value={editedText}
              onChange={handleTextChange}
              className="w-full h-96 bg-gray-900 text-gray-100 border border-gray-600 rounded p-3 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Edit the extracted text content..."
            />
          ) : (
            <div className="relative">
              <pre className={`w-full h-96 overflow-auto bg-gray-900 text-gray-100 border border-gray-600 rounded p-3 font-mono text-sm whitespace-pre-wrap ${
                showRawText ? 'whitespace-pre' : 'whitespace-pre-wrap'
              }`}>
                {displayText}
              </pre>
              {displayText.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <p className="text-gray-500">No text content extracted</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-4">
        <button
          onClick={onReject}
          className="inline-flex items-center px-6 py-3 text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
        >
          <X className="h-4 w-4 mr-2" />
          Cancel Import
        </button>

        <div className="flex items-center space-x-3">
          <div className="text-sm text-gray-400">
            {isEditing && editedText !== extractedText && (
              <span className="text-yellow-400">• Unsaved changes</span>
            )}
          </div>
          <button
            onClick={handleConfirm}
            className="inline-flex items-center px-6 py-3 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
          >
            <Check className="h-4 w-4 mr-2" />
            Continue to Parsing
          </button>
        </div>
      </div>

      {/* Help Text */}
      <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
        <div className="flex items-start">
          <Info className="h-5 w-5 text-blue-400 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <p className="text-blue-300 font-medium mb-1">Review Tips</p>
            <ul className="text-blue-200 text-sm space-y-1">
              <li>• Check that character names, stats, and abilities are clearly visible</li>
              <li>• Look for any garbled text or missing information</li>
              <li>• Edit any obvious errors before proceeding to AI parsing</li>
              <li>• The AI will work better with clean, well-formatted text</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};