import React, { useState } from 'react';
import { Menu, X, MessageSquare, BookOpen } from 'lucide-react';
import { useNavigationStore, AppView } from '../../stores/navigationStore';

interface MobileNavigationProps {
  className?: string;
}

export const MobileNavigation: React.FC<MobileNavigationProps> = ({ className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const { currentView, setCurrentView } = useNavigationStore();

  const navigationItems = [
    {
      id: 'chat' as AppView,
      label: 'Chat',
      icon: MessageSquare,
      description: 'Chat with ShadowScribe AI'
    },
    {
      id: 'knowledge-base' as AppView,
      label: 'Knowledge Base',
      icon: BookOpen,
      description: 'Edit character data and files'
    }
  ];

  const handleNavigation = (view: AppView) => {
    setCurrentView(view);
    setIsOpen(false);
  };

  return (
    <div className={`md:hidden ${className}`}>
      {/* Mobile menu button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-md transition-colors"
        aria-label="Toggle navigation menu"
      >
        {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Mobile menu overlay */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={() => setIsOpen(false)}
          />
          
          {/* Menu */}
          <div className="fixed top-16 left-0 right-0 bg-gray-800 border-b border-gray-700 z-50 shadow-lg">
            <nav className="p-4 space-y-2">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentView === item.id;
                
                return (
                  <button
                    key={item.id}
                    onClick={() => handleNavigation(item.id)}
                    className={`
                      w-full flex items-center px-3 py-3 text-sm font-medium rounded-md transition-colors
                      ${isActive 
                        ? 'bg-purple-600 text-white shadow-lg' 
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }
                    `}
                  >
                    <Icon className="w-5 h-5 mr-3" />
                    <div className="text-left">
                      <div>{item.label}</div>
                      <div className="text-xs opacity-75">{item.description}</div>
                    </div>
                    {isActive && (
                      <div className="ml-auto w-2 h-2 bg-white rounded-full" />
                    )}
                  </button>
                );
              })}
            </nav>
          </div>
        </>
      )}
    </div>
  );
};