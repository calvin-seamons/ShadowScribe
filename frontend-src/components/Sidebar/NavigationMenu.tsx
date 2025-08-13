import React from 'react';
import { MessageSquare, BookOpen, Upload } from 'lucide-react';
import { useNavigationStore, AppView } from '../../stores/navigationStore';

interface NavigationItem {
  id: AppView;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const navigationItems: NavigationItem[] = [
  {
    id: 'chat',
    label: 'Chat',
    icon: MessageSquare,
    description: 'Chat with ShadowScribe AI'
  },
  {
    id: 'knowledge-base',
    label: 'Knowledge Base',
    icon: BookOpen,
    description: 'Edit character data and files'
  },
  {
    id: 'pdf-import',
    label: 'PDF Import',
    icon: Upload,
    description: 'Import character from PDF'
  }
];

export const NavigationMenu: React.FC = () => {
  const { currentView, setCurrentView } = useNavigationStore();

  return (
    <div className="p-4 border-b border-gray-700">
      <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-3">
        Navigation
      </h3>
      <nav className="space-y-1">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => setCurrentView(item.id)}
              className={`
                w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors
                ${isActive 
                  ? 'bg-purple-600 text-white shadow-lg' 
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }
              `}
              title={item.description}
            >
              <Icon className="w-4 h-4 mr-3 flex-shrink-0" />
              <span className="truncate">{item.label}</span>
              {isActive && (
                <div className="ml-auto w-2 h-2 bg-white rounded-full flex-shrink-0" />
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
};