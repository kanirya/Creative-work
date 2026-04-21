'use client';

export type AIProvider = 'gemini' | 'openai' | 'deepseek';

export interface AISettings {
  provider: AIProvider;
  apiKey: string;
  model: string;
}

const STORAGE_KEY = 'aiSettings';
const BROWSER_STORAGE_KEY = 'edupilot.aiSettings';

const DEFAULT_MODELS: Record<AIProvider, string> = {
  gemini: 'gemini-2.5-flash-lite',
  openai: 'gpt-4.1-mini',
  deepseek: 'deepseek-chat',
};

export function getDefaultModel(provider: AIProvider): string {
  return DEFAULT_MODELS[provider];
}

export function getDefaultAISettings(): AISettings {
  return {
    provider: 'deepseek',
    apiKey: '',
    model: DEFAULT_MODELS.deepseek,
  };
}

export function getStoredAISettings(): AISettings {
  if (typeof window === 'undefined') {
    return getDefaultAISettings();
  }

  const saved =
    (window.electron?.getOfflineData(STORAGE_KEY) as Partial<AISettings> | null) ||
    getBrowserStoredAISettings();
  const provider = (saved?.provider as AIProvider) || 'deepseek';

  return {
    provider,
    apiKey: saved?.apiKey || '',
    model: saved?.model || getDefaultModel(provider),
  };
}

export function saveAISettings(settings: AISettings): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.electron?.setOfflineData(STORAGE_KEY, settings);
  window.localStorage.setItem(BROWSER_STORAGE_KEY, JSON.stringify(settings));
}

function getBrowserStoredAISettings(): Partial<AISettings> | null {
  try {
    const raw = window.localStorage.getItem(BROWSER_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Partial<AISettings>) : null;
  } catch {
    return null;
  }
}

export function maskApiKey(apiKey: string): string {
  const trimmed = apiKey.trim();
  if (!trimmed) {
    return 'Not saved';
  }
  if (trimmed.length <= 8) {
    return `${trimmed.slice(0, 2)}••••`;
  }
  return `${trimmed.slice(0, 4)}••••${trimmed.slice(-4)}`;
}

export function getProviderLabel(provider: AIProvider): string {
  switch (provider) {
    case 'gemini':
      return 'Google Gemini';
    case 'openai':
      return 'OpenAI';
    case 'deepseek':
      return 'DeepSeek';
    default:
      return provider;
  }
}
