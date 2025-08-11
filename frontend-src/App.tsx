import { useEffect, useState } from 'react';
import { Layout } from './components/Common/Layout';
import { ChatContainer } from './components/Chat/ChatContainer';
import { CharacterSheet } from './components/Sidebar/CharacterSheet';
import { SourcesPanel } from './components/Sidebar/SourcesPanel';
import { SessionHistory } from './components/Sidebar/SessionHistory';
import { ModelSelector } from './components/Sidebar/ModelSelector';
import { NavigationMenu } from './components/Sidebar/NavigationMenu';
import { IntegratedKnowledgeBaseEditor } from './components/KnowledgeBase/IntegratedKnowledgeBaseEditor';
import { useSessionStore } from './stores/sessionStore';
import { useNavigationStore } from './stores/navigationStore';
import { validateSystem } from './services/api';
import { ProgressProvider, useProgress } from './contexts/ProgressContext';

function AppContent() {
  const [isValidated, setIsValidated] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { sessionId, initializeSession } = useSessionStore();
  const { currentView } = useNavigationStore();
  const { currentProgress, activeSources, lastUsedSources } = useProgress();

  useEffect(() => {
    // Initialize session and validate system
    const init = async () => {
      try {
        initializeSession();
        const validation = await validateSystem();
        setIsValidated(validation.status === 'success' || validation.status === 'partial');
        if (validation.status === 'error') {
          setError('System validation failed');
        }
      } catch (err) {
        setError('Failed to initialize ShadowScribe');
        console.error(err);
      }
    };

    init();
  }, [initializeSession]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Error</h1>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!isValidated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Initializing ShadowScribe...</h1>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto"></div>
        </div>
      </div>
    );
  }

  return (
    <Layout>
      <div className="flex h-full">
        {/* Sidebar - Only show for chat view, responsive width */}
        {currentView === 'chat' && (
          <div className="w-80 lg:w-80 md:w-64 sm:w-full bg-gray-800 border-r border-gray-700 flex flex-col">
            <NavigationMenu />
            <ModelSelector />
            <CharacterSheet />
            <SourcesPanel 
              currentProgress={currentProgress} 
              activeSources={activeSources} 
              lastUsedSources={lastUsedSources}
            />
            <SessionHistory sessionId={sessionId} />
          </div>
        )}

        {/* Main Content Area */}
        <div className="flex-1 min-w-0">
          {currentView === 'chat' && <ChatContainer />}
          {currentView === 'knowledge-base' && <IntegratedKnowledgeBaseEditor />}
        </div>
      </div>
    </Layout>
  );
}

function App() {
  return (
    <ProgressProvider>
      <AppContent />
    </ProgressProvider>
  );
}

export default App;
