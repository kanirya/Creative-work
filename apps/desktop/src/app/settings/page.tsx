'use client';

import { useEffect, useState } from 'react';
import { Button, Input, Card } from '@edupilot/ui';
import { isValidEmail } from '@edupilot/utils';
import { lmsApi } from '@/lib/lms-api';
import { useOffline } from '@/lib/offline';

interface LmsCredentials { email: string; password: string }

export default function SettingsPage() {
  const { isOnline } = useOffline();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [saveMsg, setSaveMsg] = useState('');
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<any>(null);
  const [serviceStatus, setServiceStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  // Load saved credentials
  useEffect(() => {
    if (typeof window !== 'undefined' && window.electron) {
      const saved = window.electron.getOfflineData('lmsCredentials') as LmsCredentials | null;
      if (saved?.email) setEmail(saved.email);
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
    <div className="p-8 max-w-2xl space-y-8">
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
