'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, Button, Input } from '@edupilot/ui';
import { lmsApi } from '@/lib/lms-api';

type LoginStatus = 'idle' | 'logging_in' | 'mfa_pending' | 'logged_in' | 'failed';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('muhammad.141510.isb@iqra.edu.pk');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState<LoginStatus>('idle');
  const [mfaNumber, setMfaNumber] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [studentName, setStudentName] = useState('');
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  // Check if already logged in on mount
  useEffect(() => {
    lmsApi.getProfile()
      .then((p) => {
        if (p?.name) router.push('/dashboard');
      })
      .catch(() => {/* not logged in */});
  }, []);

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const startPolling = () => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const s = await lmsApi.getLoginStatus();
        setStatus(s.status);

        if (s.status === 'mfa_pending' && s.mfa_number) {
          setMfaNumber(s.mfa_number);
        }

        if (s.status === 'logged_in') {
          stopPolling();
          if (s.profile?.name) setStudentName(s.profile.name);
          setTimeout(() => router.push('/dashboard'), 1000);
        }

        if (s.status === 'failed') {
          stopPolling();
          setError(s.error || 'Login failed');
        }
      } catch {
        // ignore poll errors
      }
    }, 1500);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) { setError('Email and password are required'); return; }

    setError('');
    setMfaNumber(null);
    setStatus('logging_in');

    try {
      await lmsApi.startLogin(email, password);
      startPolling();
    } catch (err: any) {
      setStatus('failed');
      setError(err.message || 'Failed to start login');
    }
  };

  useEffect(() => () => stopPolling(), []);

  const statusMessages: Record<LoginStatus, string> = {
    idle: '',
    logging_in: 'Connecting to Microsoft login...',
    mfa_pending: '',
    logged_in: `Welcome, ${studentName || 'student'}! Redirecting...`,
    failed: '',
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 px-4">
      <Card className="w-full max-w-md p-8">
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">🎓</div>
          <h1 className="text-3xl font-bold text-gray-900">EduPilot</h1>
          <p className="text-gray-500 mt-1 text-sm">Iqra University LMS</p>
        </div>

        {/* MFA prompt */}
        {status === 'mfa_pending' && mfaNumber && (
          <div className="mb-6 bg-blue-50 border-2 border-blue-400 rounded-xl p-5 text-center">
            <p className="text-blue-800 font-semibold text-sm mb-2">
              Microsoft Authenticator — Number Matching
            </p>
            <div className="text-5xl font-bold text-blue-700 my-3">{mfaNumber}</div>
            <p className="text-blue-600 text-sm">
              Open your Authenticator app and enter this number
            </p>
            <div className="mt-3 flex items-center justify-center gap-2 text-blue-500 text-xs">
              <div className="animate-spin w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full" />
              Waiting for approval...
            </div>
          </div>
        )}

        {/* Success */}
        {status === 'logged_in' && (
          <div className="mb-6 bg-green-50 border border-green-300 rounded-lg p-4 text-center text-green-700 text-sm font-medium">
            ✓ {statusMessages.logged_in}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm" role="alert">
            {error}
          </div>
        )}

        {/* Login form — hide during MFA/success */}
        {status !== 'mfa_pending' && status !== 'logged_in' && (
          <form onSubmit={handleLogin} className="space-y-4" aria-label="LMS login">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">
                Microsoft 365 Email
              </label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="student@iqra.edu.pk"
                disabled={status === 'logging_in'}
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1.5">
                Password
              </label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Your Microsoft password"
                disabled={status === 'logging_in'}
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              disabled={status === 'logging_in'}
            >
              {status === 'logging_in' ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                  {statusMessages.logging_in}
                </span>
              ) : (
                'Connect to Iqra LMS'
              )}
            </Button>
          </form>
        )}

        <p className="mt-5 text-center text-xs text-gray-400">
          Uses your Microsoft 365 / Iqra University credentials
        </p>
      </Card>
    </div>
  );
}
