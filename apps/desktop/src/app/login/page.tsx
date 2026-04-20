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

  useEffect(() => {
    lmsApi.getProfile()
      .then((p) => {
        if (p?.name && p?.userid) router.push('/dashboard');
      })
      .catch(() => {});
  }, [router]);

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
          setTimeout(() => router.push('/dashboard'), 900);
        }

        if (s.status === 'failed') {
          stopPolling();
          setError(s.error || 'Login failed');
        }
      } catch {
        // Ignore polling glitches while the login flow is in progress.
      }
    }, 1500);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !password) {
      setError('Email and password are required');
      return;
    }

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

  return (
    <div className="relative min-h-screen overflow-hidden px-6 py-10 md:px-10">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-[-8rem] top-[-10rem] h-80 w-80 rounded-full bg-white blur-3xl" />
        <div className="absolute right-[-7rem] top-24 h-72 w-72 rounded-full bg-slate-200/55 blur-3xl" />
      </div>

      <div className="relative mx-auto grid min-h-[calc(100vh-5rem)] max-w-7xl gap-8 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="flex flex-col justify-between rounded-[40px] border border-white/70 bg-white/72 p-8 shadow-[0_20px_70px_rgba(15,23,42,0.08)] backdrop-blur-2xl md:p-12">
          <div>
            <div className="inline-flex items-center rounded-full border border-slate-200 bg-white/90 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
              EduPilot desktop
            </div>

            <h1 className="mt-8 max-w-xl text-5xl font-semibold leading-[1.02] tracking-tight text-slate-950">
              Professional academic workspace for Iqra LMS.
            </h1>

            <p className="mt-6 max-w-xl text-base leading-8 text-slate-600">
              One clean place for courses, assignments, grades, submissions, and AI-assisted study workflows.
              The new direction is intentionally minimal, bright, and distraction-light.
            </p>
          </div>

          <div className="mt-12 grid gap-4 md:grid-cols-3">
            {[
              ['Direct LMS Sync', 'Connect courses and assignments through the live Iqra LMS session.'],
              ['Submission Ready', 'Upload assignment files and review submitted documents from the same workspace.'],
              ['AI Study Layer', 'Move from admin work to academic focus without switching tools.'],
            ].map(([title, text]) => (
              <div key={title} className="rounded-[28px] border border-slate-200/80 bg-slate-50/85 p-5">
                <p className="text-sm font-semibold tracking-tight text-slate-900">{title}</p>
                <p className="mt-2 text-sm leading-6 text-slate-500">{text}</p>
              </div>
            ))}
          </div>
        </section>

        <div className="flex items-center">
          <Card className="w-full rounded-[36px] border-white/80 bg-white/88 shadow-[0_18px_60px_rgba(15,23,42,0.09)]">
            <div className="space-y-8">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Sign in</p>
                <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">Connect your LMS</h2>
                <p className="mt-2 text-sm leading-7 text-slate-500">
                  Use your Microsoft 365 university account to start a live LMS session.
                </p>
              </div>

              {status === 'mfa_pending' && mfaNumber && (
                <div className="rounded-[28px] border border-slate-200 bg-slate-50 p-6 text-center">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Authenticator step</p>
                  <div className="mt-4 text-6xl font-semibold tracking-tight text-slate-950">{mfaNumber}</div>
                  <p className="mt-4 text-sm leading-7 text-slate-500">
                    Open Microsoft Authenticator and enter the number above to approve the sign-in.
                  </p>
                  <div className="mt-4 inline-flex items-center gap-2 rounded-full bg-white px-3 py-2 text-xs font-medium text-slate-500">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-slate-900" />
                    Waiting for approval
                  </div>
                </div>
              )}

              {status === 'logged_in' && (
                <div className="rounded-[24px] border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
                  Connected successfully. Welcome{studentName ? `, ${studentName}` : ''}.
                </div>
              )}

              {error && (
                <div className="rounded-[24px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
                  {error}
                </div>
              )}

              {status !== 'mfa_pending' && status !== 'logged_in' && (
                <form onSubmit={handleLogin} className="space-y-4" aria-label="LMS login">
                  <Input
                    id="email"
                    type="email"
                    label="Microsoft 365 Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="student@iqra.edu.pk"
                    disabled={status === 'logging_in'}
                  />

                  <Input
                    id="password"
                    type="password"
                    label="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Your university password"
                    disabled={status === 'logging_in'}
                  />

                  <Button
                    type="submit"
                    variant="primary"
                    className="w-full justify-center"
                    disabled={status === 'logging_in'}
                  >
                    {status === 'logging_in' ? 'Connecting to Microsoft...' : 'Connect to Iqra LMS'}
                  </Button>
                </form>
              )}

              <div className="flex items-center justify-between rounded-[24px] border border-slate-200/80 bg-slate-50/80 px-4 py-3 text-xs text-slate-500">
                <span>Secure browser-based Microsoft flow</span>
                <span className="font-medium text-slate-700">White minimal UI refresh in progress</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
