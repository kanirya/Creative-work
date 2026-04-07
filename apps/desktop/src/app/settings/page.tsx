'use client';

import { useState, useEffect } from 'react';
import { Button, Input, Card } from '@edupilot/ui';
import { isValidEmail } from '@edupilot/utils';
import { apiClient } from '@/lib/auth';
import { useOffline } from '@/lib/offline';

interface LmsCredentials {
  email: string;
  password: string;
}

interface SyncStatus {
  lastSyncAt: string | null;
  status: string;
  coursesCount: number;
  assignmentsCount: number;
  gradesCount: number;
  errorMessage: string | null;
}

export default function SettingsPage() {
  const { isOnline } = useOffline();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [saveMessage, setSaveMessage] = useState('');
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);

  // Load saved credentials on mount
  useEffect(() => {
    if (typeof window !== 'undefined' && window.electron) {
      const saved = window.electron.getOfflineData('lmsCredentials') as LmsCredentials | null;
      if (saved) {
        setEmail(saved.email || '');
        // Don't pre-fill password for security
      }
    }
  }, []);

  const handleSaveCredentials = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveMessage('');

    if (!isValidEmail(email)) {
      setSaveMessage('Please enter a valid email address');
      return;
    }

    if (!password) {
      setSaveMessage('Please enter your password');
      return;
    }

    if (typeof window !== 'undefined' && window.electron) {
      window.electron.setOfflineData('lmsCredentials', { email, password });
      setSaveMessage('Credentials saved successfully');
      setPassword(''); // Clear password field after saving
    } else {
      setSaveMessage('Secure storage not available');
    }
  };

  const handleSyncNow = async () => {
    if (!isOnline) {
      setSyncStatus((prev) => ({
        ...(prev ?? { lastSyncAt: null, coursesCount: 0, assignmentsCount: 0, gradesCount: 0 }),
        status: 'failed',
        errorMessage: 'Cannot sync while offline',
      }));
      return;
    }

    setSyncing(true);
    try {
      await apiClient.post('/api/v1/students/sync', {});
      setSyncStatus((prev) => ({
        ...(prev ?? { coursesCount: 0, assignmentsCount: 0, gradesCount: 0, errorMessage: null }),
        lastSyncAt: new Date().toISOString(),
        status: 'in_progress',
        errorMessage: null,
      }));

      // Poll for status
      setTimeout(async () => {
        try {
          const status = await apiClient.get('/api/scrape/status/me');
          setSyncStatus({
            lastSyncAt: status.last_scraped_at,
            status: status.status,
            coursesCount: status.courses_count ?? 0,
            assignmentsCount: status.assignments_count ?? 0,
            gradesCount: status.grades_count ?? 0,
            errorMessage: status.error_message ?? null,
          });
        } catch {
          // ignore poll error
        }
        setSyncing(false);
      }, 5000);
    } catch (err: any) {
      setSyncStatus((prev) => ({
        ...(prev ?? { lastSyncAt: null, coursesCount: 0, assignmentsCount: 0, gradesCount: 0 }),
        status: 'failed',
        errorMessage: err.message || 'Sync failed',
      }));
      setSyncing(false);
    }
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return 'Never';
    return new Date(iso).toLocaleString();
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">Manage your LMS credentials and sync preferences</p>
      </div>

      {/* LMS Credentials */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">LMS Credentials</h2>
        <p className="text-sm text-gray-600 mb-4">
          Enter your Microsoft 365 credentials used to access Iqra University LMS.
          These are stored securely on your device.
        </p>

        <form onSubmit={handleSaveCredentials} className="space-y-4" aria-label="LMS credentials form">
          {saveMessage && (
            <div
              className={`px-4 py-3 rounded border ${
                saveMessage.includes('success')
                  ? 'bg-green-50 border-green-200 text-green-700'
                  : 'bg-red-50 border-red-200 text-red-700'
              }`}
              role="alert"
              aria-live="polite"
            >
              {saveMessage}
            </div>
          )}

          <div>
            <label htmlFor="lms-email" className="block text-sm font-medium text-gray-700 mb-2">
              Microsoft 365 Email
            </label>
            <Input
              id="lms-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="student@iqra.edu.pk"
            />
          </div>

          <div>
            <label htmlFor="lms-password" className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <Input
              id="lms-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your Microsoft password"
            />
          </div>

          <Button type="submit" variant="primary" aria-label="Save LMS credentials">
            Save Credentials
          </Button>
        </form>
      </Card>

      {/* Sync */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">LMS Data Sync</h2>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Last Sync:</span>
              <p className="font-medium text-gray-900">{formatDate(syncStatus?.lastSyncAt ?? null)}</p>
            </div>
            <div>
              <span className="text-gray-600">Status:</span>
              <p className="font-medium text-gray-900 capitalize">{syncStatus?.status ?? 'Unknown'}</p>
            </div>
          </div>

          {syncStatus && syncStatus.status === 'completed' && (
            <div className="grid grid-cols-3 gap-4 text-sm bg-gray-50 rounded-lg p-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">{syncStatus.coursesCount}</p>
                <p className="text-gray-600">Courses</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">{syncStatus.assignmentsCount}</p>
                <p className="text-gray-600">Assignments</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">{syncStatus.gradesCount}</p>
                <p className="text-gray-600">Grades</p>
              </div>
            </div>
          )}

          {syncStatus?.errorMessage && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded" role="alert">
              {syncStatus.errorMessage}
            </div>
          )}

          <Button
            variant="primary"
            onClick={handleSyncNow}
            disabled={syncing || !isOnline}
            aria-label="Sync LMS data now"
          >
            {syncing ? 'Syncing...' : 'Sync Now'}
          </Button>

          {!isOnline && (
            <p className="text-sm text-yellow-700">Sync is unavailable while offline.</p>
          )}
        </div>
      </Card>
    </div>
  );
}
