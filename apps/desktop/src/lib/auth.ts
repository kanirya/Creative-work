'use client';

import { EduPilotClient } from '@edupilot/api-client';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export const apiClient = new EduPilotClient({
  baseURL: API_URL,
  onTokenRefresh: (accessToken, refreshToken) => {
    tokenStorage.setTokens({ accessToken, refreshToken });
  },
  onUnauthorized: () => {
    tokenStorage.clearTokens();
  },
});

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

// Token storage using electron-store
export const tokenStorage = {
  getTokens: (): AuthTokens | null => {
    if (typeof window === 'undefined' || !window.electron) return null;
    
    const tokens = window.electron.getOfflineData('authTokens');
    return tokens || null;
  },
  
  setTokens: (tokens: AuthTokens): void => {
    if (typeof window === 'undefined' || !window.electron) return;
    
    window.electron.setOfflineData('authTokens', tokens);
  },
  
  clearTokens: (): void => {
    if (typeof window === 'undefined' || !window.electron) return;
    
    window.electron.setOfflineData('authTokens', null);
  },
};

// Initialize client with stored tokens
if (typeof window !== 'undefined' && window.electron) {
  const tokens = tokenStorage.getTokens();
  if (tokens) {
    apiClient.setTokens(tokens.accessToken, tokens.refreshToken);
  }
}
