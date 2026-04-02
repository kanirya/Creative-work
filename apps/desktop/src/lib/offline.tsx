'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface OfflineContextType {
  isOnline: boolean;
  queueQuery: (query: string) => void;
  getQueuedQueries: () => string[];
  clearQueue: () => void;
}

const OfflineContext = createContext<OfflineContextType | undefined>(undefined);

export function OfflineProvider({ children }: { children: ReactNode }) {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Check initial status
    setIsOnline(navigator.onLine);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const queueQuery = (query: string) => {
    if (typeof window !== 'undefined' && window.electron) {
      const queue = window.electron.getOfflineData('queryQueue') || [];
      queue.push({ query, timestamp: Date.now() });
      window.electron.setOfflineData('queryQueue', queue);
    }
  };

  const getQueuedQueries = (): string[] => {
    if (typeof window !== 'undefined' && window.electron) {
      const queue = window.electron.getOfflineData('queryQueue') || [];
      return queue.map((item: any) => item.query);
    }
    return [];
  };

  const clearQueue = () => {
    if (typeof window !== 'undefined' && window.electron) {
      window.electron.setOfflineData('queryQueue', []);
    }
  };

  return (
    <OfflineContext.Provider value={{ isOnline, queueQuery, getQueuedQueries, clearQueue }}>
      {children}
    </OfflineContext.Provider>
  );
}

export function useOffline() {
  const context = useContext(OfflineContext);
  if (!context) {
    throw new Error('useOffline must be used within OfflineProvider');
  }
  return context;
}

// Type declaration for window.electron
declare global {
  interface Window {
    electron?: {
      getOfflineData: (key: string) => any;
      setOfflineData: (key: string, value: any) => void;
      clearOfflineData: () => void;
      checkNetworkStatus: () => Promise<boolean>;
      onUpdateAvailable: (callback: () => void) => void;
      onUpdateDownloaded: (callback: () => void) => void;
      installUpdate: () => void;
    };
  }
}
