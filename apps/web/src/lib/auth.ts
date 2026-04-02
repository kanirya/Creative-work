'use client';

import { EduPilotClient } from '@edupilot/api-client';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export const apiClient = new EduPilotClient(API_URL);

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

// Token storage using localStorage (client-side only)
export const tokenStorage = {
  getTokens: (): AuthTokens | null => {
    if (typeof window === 'undefined') return null;
    
    const accessToken = localStorage.getItem('accessToken');
    const refreshToken = localStorage.getItem('refreshToken');
    
    if (!accessToken || !refreshToken) return null;
    
    return { accessToken, refreshToken };
  },
  
  setTokens: (tokens: AuthTokens): void => {
    if (typeof window === 'undefined') return;
    
    localStorage.setItem('accessToken', tokens.accessToken);
    localStorage.setItem('refreshToken', tokens.refreshToken);
  },
  
  clearTokens: (): void => {
    if (typeof window === 'undefined') return;
    
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  },
};

// Initialize client with stored tokens
if (typeof window !== 'undefined') {
  const tokens = tokenStorage.getTokens();
  if (tokens) {
    apiClient.setAccessToken(tokens.accessToken);
  }
}
