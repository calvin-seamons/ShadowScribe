import { Moon, Settings } from 'lucide-react';
import { MobileNavigation } from './MobileNavigation';
import { useNavigationStore } from '../../stores/navigationStore';

export const Header: React.FC = () => {
  const { currentView } = useNavigationStore();
  
  const getViewTitle = () => {
    switch (currentView) {
      case 'knowledge-base':
        return 'Knowledge Base Editor';
      case 'chat':
      default:
        return 'D&D Intelligence Assistant';
    }
  };

  return (
    <header className="bg-gray-800 border-b border-gray-700 px-6 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <MobileNavigation />
          <Moon className="w-6 h-6 text-purple-500" />
          <div className="flex flex-col">
            <h1 className="text-xl font-bold text-white">ShadowScribe</h1>
            <span className="text-sm text-gray-400 hidden sm:block">{getViewTitle()}</span>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Current view indicator for mobile */}
          <span className="text-sm text-purple-400 sm:hidden">
            {currentView === 'knowledge-base' ? 'KB' : 'Chat'}
          </span>
          
          <button className="text-gray-400 hover:text-white transition-colors">
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  );
};
