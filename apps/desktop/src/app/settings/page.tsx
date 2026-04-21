'use client';

import { useEffect, useState } from 'react';
import { Button, Input, Card } from '@edupilot/ui';
import { isValidEmail } from '@edupilot/utils';
import { AIProvider, getDefaultAISettings, getDefaultModel, getProviderLabel, getStoredAISettings, maskApiKey, saveAISettings } from '@/lib/ai-settings';
import { lmsApi } from '@/lib/lms-api';
import { useOffline } from '@/lib/offline';

interface LmsCredentials { email: string; password: string }

export default function SettingsPage() {
  const { isOnline } = useOffline();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [saveMsg, setSaveMsg] = useState('');
  const [aiSaveMsg, setAiSaveMsg] = useState('');
  const [aiTestMsg, setAiTestMsg] = useState('');
  const [testingAI, setTestingAI] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<any>(null);
  const [serviceStatus, setServiceStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [aiProvider, setAiProvider] = useState<AIProvider>('gemini');
  const [aiModel, setAiModel] = useState(getDefaultModel('gemini'));
  const [aiApiKey, setAiApiKey] = useState('');
  const [savedAIKeyMask, setSavedAIKeyMask] = useState('Not saved');

  // Load saved credentials
  useEffect(() => {
    if (typeof window !== 'undefined' && window.electron) {
      const saved = window.electron.getOfflineData('lmsCredentials') as LmsCredentials | null;
      if (saved?.email) setEmail(saved.email);
      const savedAI = getStoredAISettings();
      setAiProvider(savedAI.provider);
      setAiModel(savedAI.model);
      setAiApiKey(savedAI.apiKey);
      setSavedAIKeyMask(maskApiKey(savedAI.apiKey));
    } else {
      const defaults = getDefaultAISettings();
      setAiProvider(defaults.provider);
      setAiModel(defaults.model);
    }
    // Check if lms-scraper service is reachable
    fetch('http://localhost:8002/health')
      .then(() => setServiceStatus('online'))
      .catch(() => setServiceStatus('offline'));
  }, []);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveMsg('');
    if (!isValidEmail(email)) { setSaveMsg('Invalid email'); return; }
    if (!password) { setSaveMsg('Password required'); return; }
    if (typeof window !== 'undefined' && window.electron) {
      window.electron.setOfflineData('lmsCredentials', { email, password });
      setSaveMsg('✓ Credentials saved securely');
      setPassword('');
    } else {
      setSaveMsg('✓ Credentials saved (browser mode)');
    }
  };

  const handleAISave = (e: React.FormEvent) => {
    e.preventDefault();
    setAiSaveMsg('');
    setAiTestMsg('');

    if (!aiApiKey.trim()) {
      setAiSaveMsg('API key required');
      return;
    }

    const normalizedModel = aiModel.trim() || getDefaultModel(aiProvider);
    saveAISettings({
      provider: aiProvider,
      apiKey: aiApiKey.trim(),
      model: normalizedModel,
    });
    setAiModel(normalizedModel);
    setSavedAIKeyMask(maskApiKey(aiApiKey));
    setAiSaveMsg(`${getProviderLabel(aiProvider)} settings saved for Ask AI`);
  };

  const applyProviderDefaults = (provider: AIProvider) => {
    setAiProvider(provider);
    setAiModel(getDefaultModel(provider));
    setAiSaveMsg('');
    setAiTestMsg('');
  };

  const handleAITest = async () => {
    setAiSaveMsg('');
    setAiTestMsg('');

    if (!aiApiKey.trim()) {
      setAiTestMsg('Add an API key before testing.');
      return;
    }

    setTestingAI(true);
    try {
      await lmsApi.queryAI('Reply with a short confirmation that the configured AI provider is working.', 'text', {
        ai_provider: aiProvider,
        api_key: aiApiKey.trim(),
        model: aiModel.trim() || getDefaultModel(aiProvider),
      });
      setAiTestMsg(`${getProviderLabel(aiProvider)} responded successfully.`);
    } catch (e: any) {
      setAiTestMsg(e?.message || 'AI test failed.');
    } finally {
      setTestingAI(false);
    }
  };

  const handleSyncNow = async () => {
    if (!isOnline) { setSyncStatus({ status: 'failed', errorMessage: 'Offline' }); return; }
    setSyncing(true);
    try {
      const data = await lmsApi.scrapeAll();
      setSyncStatus({
        status: 'completed',
        lastSyncAt: new Date().toISOString(),
        coursesCount: data.courses.length,
        assignmentsCount: data.assignments.length,
        gradesCount: data.grades_overview.length,
        errorMessage: null,
      });
    } catch (e: any) {
      setSyncStatus({ status: 'failed', errorMessage: e.message });
    } finally {
      setSyncing(false);
    }
  };

  const fmt = (iso: string | null) => iso ? new Date(iso).toLocaleString() : 'Never';

  return (
    <div className="p-8 max-w-3xl space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1 text-sm">LMS credentials and sync configuration</p>
      </div>

      {/* Service status */}
      <Card className="p-4 flex items-center gap-3">
        <div className={`w-3 h-3 rounded-full ${serviceStatus === 'online' ? 'bg-green-500' : serviceStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500'}`} />
        <div>
          <p className="text-sm font-medium text-gray-900">LMS Scraper Service</p>
          <p className="text-xs text-gray-500">
            {serviceStatus === 'online' ? 'Running on localhost:8002' :
             serviceStatus === 'offline' ? 'Not running — start with: cd services/lms-scraper && uvicorn app.main:app --port 8002' :
             'Checking...'}
          </p>
        </div>
      </Card>

      {/* LMS Credentials */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">Microsoft 365 Credentials</h2>
        <p className="text-sm text-gray-500 mb-4">
          Your Iqra University Microsoft credentials for LMS access. Stored securely on this device.
        </p>

        <form onSubmit={handleSave} className="space-y-4" aria-label="LMS credentials">
          {saveMsg && (
            <div className={`px-4 py-2 rounded text-sm border ${saveMsg.startsWith('✓') ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`} role="alert">
              {saveMsg}
            </div>
          )}
          <div>
            <label htmlFor="lms-email" className="block text-sm font-medium text-gray-700 mb-1.5">
              Microsoft Email
            </label>
            <Input id="lms-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="student@iqra.edu.pk" />
          </div>
          <div>
            <label htmlFor="lms-password" className="block text-sm font-medium text-gray-700 mb-1.5">
              Password
            </label>
            <Input id="lms-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Your Microsoft password" />
          </div>
          <Button type="submit" variant="primary">Save Credentials</Button>
        </form>
      </Card>

      <Card className="p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">AI Provider</h2>
        <p className="text-sm text-gray-500 mb-4">
          Paste and rotate your AI key here anytime. Ask AI will use these saved settings on the next message.
        </p>

        <form onSubmit={handleAISave} className="space-y-4" aria-label="AI provider settings">
          {aiSaveMsg && (
            <div className={`px-4 py-2 rounded text-sm border ${aiSaveMsg.toLowerCase().includes('saved') ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`} role="alert">
              {aiSaveMsg}
            </div>
          )}

          {aiTestMsg && (
            <div className={`px-4 py-2 rounded text-sm border ${aiTestMsg.toLowerCase().includes('successfully') ? 'bg-green-50 border-green-200 text-green-700' : 'bg-amber-50 border-amber-200 text-amber-700'}`} role="alert">
              {aiTestMsg}
            </div>
          )}

          <div className="grid gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:grid-cols-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Active provider</p>
              <p className="mt-1 text-sm font-medium text-slate-800">{getProviderLabel(aiProvider)}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Saved model</p>
              <p className="mt-1 text-sm font-medium text-slate-800">{aiModel || getDefaultModel(aiProvider)}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Saved key</p>
              <p className="mt-1 text-sm font-medium text-slate-800">{savedAIKeyMask}</p>
            </div>
          </div>

          <div>
            <label htmlFor="ai-provider" className="block text-sm font-medium text-gray-700 mb-1.5">
              Provider
            </label>
            <select
              id="ai-provider"
              value={aiProvider}
              onChange={(e) => applyProviderDefaults(e.target.value as AIProvider)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 shadow-sm transition-all duration-200 focus:border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-300"
            >
              <option value="gemini">Google Gemini</option>
              <option value="openai">OpenAI</option>
              <option value="deepseek">DeepSeek</option>
            </select>
          </div>

          <div>
            <label htmlFor="ai-model" className="block text-sm font-medium text-gray-700 mb-1.5">
              Model
            </label>
            <Input
              id="ai-model"
              value={aiModel}
              onChange={(e) => setAiModel(e.target.value)}
              placeholder={getDefaultModel(aiProvider)}
              helperText={`Recommended default for ${aiProvider}: ${getDefaultModel(aiProvider)}`}
            />
          </div>

          <div>
            <label htmlFor="ai-api-key" className="block text-sm font-medium text-gray-700 mb-1.5">
              API Key
            </label>
            <Input
              id="ai-api-key"
              type="password"
              value={aiApiKey}
              onChange={(e) => setAiApiKey(e.target.value)}
              placeholder={`Paste your ${aiProvider} API key`}
              helperText="Stored locally in the desktop app on this device."
            />
          </div>

          <div className="flex flex-wrap gap-3">
            <Button type="submit" variant="primary">Save AI Settings</Button>
            <Button
              type="button"
              variant="secondary"
              onClick={handleAITest}
              disabled={testingAI}
            >
              {testingAI ? 'Testing...' : 'Test API Key'}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                const defaults = getDefaultAISettings();
                setAiProvider(defaults.provider);
                setAiModel(defaults.model);
                setAiApiKey('');
                saveAISettings(defaults);
                setSavedAIKeyMask(maskApiKey(''));
                setAiSaveMsg('AI settings reset to defaults');
                setAiTestMsg('');
              }}
            >
              Reset
            </Button>
          </div>
        </form>
      </Card>

      {/* Sync */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">LMS Data Sync</h2>

        <div className="space-y-4">
          {syncStatus && (
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><span className="text-gray-500">Last sync:</span> <span className="font-medium">{fmt(syncStatus.lastSyncAt)}</span></div>
              <div><span className="text-gray-500">Status:</span> <span className={`font-medium capitalize ${syncStatus.status === 'completed' ? 'text-green-600' : 'text-red-600'}`}>{syncStatus.status}</span></div>
            </div>
          )}

          {syncStatus?.status === 'completed' && (
            <div className="grid grid-cols-3 gap-3 bg-gray-50 rounded-lg p-4 text-center">
              <div><p className="text-2xl font-bold text-blue-600">{syncStatus.coursesCount}</p><p className="text-xs text-gray-500">Courses</p></div>
              <div><p className="text-2xl font-bold text-blue-600">{syncStatus.assignmentsCount}</p><p className="text-xs text-gray-500">Assignments</p></div>
              <div><p className="text-2xl font-bold text-blue-600">{syncStatus.gradesCount}</p><p className="text-xs text-gray-500">Grades</p></div>
            </div>
          )}

          {syncStatus?.errorMessage && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded text-sm" role="alert">
              {syncStatus.errorMessage}
            </div>
          )}

          <Button variant="primary" onClick={handleSyncNow} disabled={syncing || !isOnline} aria-label="Sync LMS data now">
            {syncing ? '⟳ Syncing...' : '⟳ Sync Now'}
          </Button>

          {!isOnline && <p className="text-xs text-yellow-600">Sync unavailable while offline</p>}
        </div>
      </Card>
    </div>
  );
}
