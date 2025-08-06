import React from 'react';
import { Moon, Settings } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="bg-gray-800 border-b border-gray-700 px-6 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Moon className="w-6 h-6 text-purple-500" />
          <h1 className="text-xl font-bold text-white">ShadowScribe</h1>
          <span className="text-sm text-gray-400">D&D Intelligence Assistant</span>
        </div>
        
        <button className="text-gray-400 hover:text-white transition-colors">
          <Settings className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
};
