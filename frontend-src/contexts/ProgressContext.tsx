import { createContext, useContext, useState, ReactNode } from 'react';
import type { Progress } from '../types/index';

interface ProgressContextType {
  currentProgress: Progress | null;
  setCurrentProgress: (progress: Progress | null) => void;
  activeSources: string[];
  setActiveSources: (sources: string[]) => void;
  lastUsedSources: string[];
  setLastUsedSources: (sources: string[]) => void;
}

const ProgressContext = createContext<ProgressContextType | undefined>(undefined);

export const useProgress = () => {
  const context = useContext(ProgressContext);
  if (context === undefined) {
    throw new Error('useProgress must be used within a ProgressProvider');
  }
  return context;
};

interface ProgressProviderProps {
  children: ReactNode;
}

export const ProgressProvider: React.FC<ProgressProviderProps> = ({ children }) => {
  const [currentProgress, setCurrentProgress] = useState<Progress | null>(null);
  const [activeSources, setActiveSources] = useState<string[]>([]);
  const [lastUsedSources, setLastUsedSources] = useState<string[]>([]);

  return (
    <ProgressContext.Provider 
      value={{ 
        currentProgress, 
        setCurrentProgress, 
        activeSources, 
        setActiveSources,
        lastUsedSources,
        setLastUsedSources
      }}
    >
      {children}
    </ProgressContext.Provider>
  );
};
