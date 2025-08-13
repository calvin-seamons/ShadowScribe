import React from 'react';
import { Upload, Edit, FileText, ArrowRight, X } from 'lucide-react';

interface CharacterCreationSelectionProps {
  onSelectPDFImport: () => void;
  onSelectManualWizard: () => void;
  onCancel: () => void;
}

export const CharacterCreationSelection: React.FC<CharacterCreationSelectionProps> = ({
  onSelectPDFImport,
  onSelectManualWizard,
  onCancel
}) => {
  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-700">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Create New Character</h1>
          <p className="text-gray-400">
            Choose how you'd like to create your character
          </p>
        </div>
        <button
          onClick={onCancel}
          className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-md transition-colors"
          title="Cancel"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="max-w-4xl w-full">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* PDF Import Option */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 hover:border-purple-500 transition-all duration-200 group">
              <div className="p-8">
                <div className="flex items-center justify-center w-16 h-16 bg-purple-600 rounded-lg mb-6 group-hover:bg-purple-500 transition-colors">
                  <Upload className="w-8 h-8 text-white" />
                </div>
                
                <h3 className="text-xl font-bold text-white mb-3">Import from PDF</h3>
                <p className="text-gray-400 mb-6 leading-relaxed">
                  Upload your existing character sheet PDF and let AI automatically extract and organize 
                  your character data. Supports D&D Beyond exports, Roll20 sheets, and other PDF formats.
                </p>
                
                <div className="space-y-2 mb-6">
                  <div className="flex items-center text-sm text-gray-300">
                    <div className="w-2 h-2 bg-green-400 rounded-full mr-3"></div>
                    Fast and automated
                  </div>
                  <div className="flex items-center text-sm text-gray-300">
                    <div className="w-2 h-2 bg-green-400 rounded-full mr-3"></div>
                    AI-powered data extraction
                  </div>
                  <div className="flex items-center text-sm text-gray-300">
                    <div className="w-2 h-2 bg-green-400 rounded-full mr-3"></div>
                    Review and edit before saving
                  </div>
                  <div className="flex items-center text-sm text-gray-300">
                    <div className="w-2 h-2 bg-yellow-400 rounded-full mr-3"></div>
                    Requires readable PDF file
                  </div>
                </div>

                <button
                  onClick={onSelectPDFImport}
                  className="w-full flex items-center justify-center px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors group"
                >
                  <span>Upload PDF Character Sheet</span>
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </div>

            {/* Manual Wizard Option */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 hover:border-blue-500 transition-all duration-200 group">
              <div className="p-8">
                <div className="flex items-center justify-center w-16 h-16 bg-blue-600 rounded-lg mb-6 group-hover:bg-blue-500 transition-colors">
                  <Edit className="w-8 h-8 text-white" />
                </div>
                
                <h3 className="text-xl font-bold text-white mb-3">Manual Creation Wizard</h3>
                <p className="text-gray-400 mb-6 leading-relaxed">
                  Create your character step-by-step using our guided wizard. Perfect for new characters 
                  or when you want full control over every detail.
                </p>
                
                <div className="space-y-2 mb-6">
                  <div className="flex items-center text-sm text-gray-300">
                    <div className="w-2 h-2 bg-green-400 rounded-full mr-3"></div>
                    Step-by-step guidance
                  </div>
                  <div className="flex items-center text-sm text-gray-300">
                    <div className="w-2 h-2 bg-green-400 rounded-full mr-3"></div>
                    Complete control over details
                  </div>
                  <div className="flex items-center text-sm text-gray-300">
                    <div className="w-2 h-2 bg-green-400 rounded-full mr-3"></div>
                    Built-in validation and help
                  </div>
                  <div className="flex items-center text-sm text-gray-300">
                    <div className="w-2 h-2 bg-blue-400 rounded-full mr-3"></div>
                    Takes more time to complete
                  </div>
                </div>

                <button
                  onClick={onSelectManualWizard}
                  className="w-full flex items-center justify-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors group"
                >
                  <span>Start Manual Wizard</span>
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </div>
          </div>

          {/* Help Section */}
          <div className="mt-12 bg-gray-800/50 rounded-lg border border-gray-700 p-6">
            <div className="flex items-start">
              <FileText className="w-6 h-6 text-blue-400 mt-1 mr-4 flex-shrink-0" />
              <div>
                <h4 className="text-white font-medium mb-2">Need Help Choosing?</h4>
                <div className="text-sm text-gray-300 space-y-2">
                  <p>
                    <strong className="text-white">Choose PDF Import if:</strong> You have an existing character sheet 
                    in PDF format (D&D Beyond export, Roll20 sheet, etc.) and want to save time on data entry.
                  </p>
                  <p>
                    <strong className="text-white">Choose Manual Wizard if:</strong> You're creating a new character 
                    from scratch, want complete control over the creation process, or don't have a PDF file.
                  </p>
                  <p className="text-gray-400 text-xs mt-3">
                    Both methods create the same standardized character files that work with all ShadowScribe features.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};