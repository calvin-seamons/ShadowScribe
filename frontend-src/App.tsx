import { useEffect, useState } from 'react';
import { Layout } from './components/Common/Layout';
import { ChatContainer } from './components/Chat/ChatContainer';
import { CharacterSheet } from './components/Sidebar/CharacterSheet';
import { SourcesPanel } from './components/Sidebar/SourcesPanel';
import { SessionHistory } from './components/Sidebar/SessionHistory';
import { useSessionStore } from './stores/sessionStore';
import { validateSystem } from './services/api';

function App() {
  const [isValidated, setIsValidated] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { sessionId, initializeSession } = useSessionStore();

  useEffect(() => {
    // Initialize session and validate system
    const init = async () => {
      try {
        initializeSession();
        const validation = await validateSystem();
        setIsValidated(validation.status === 'success');
        if (validation.status !== 'success') {
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
        {/* Sidebar */}
        <div className="w-80 bg-gray-800 border-r border-gray-700 flex flex-col">
          <CharacterSheet />
          <SourcesPanel />
          <SessionHistory sessionId={sessionId} />
        </div>

        {/* Main Chat Area */}
        <div className="flex-1">
          <ChatContainer />
        </div>
      </div>
    </Layout>
  );
}

export default App;
