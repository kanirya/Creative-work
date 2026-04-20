'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Card, Button } from '@edupilot/ui';
import { lmsApi, LMSCourse, LMSGrade, LMSEvent } from '@/lib/lms-api';
import { useOffline } from '@/lib/offline';

export default function DashboardPage() {
  const router = useRouter();
  const { isOnline } = useOffline();
  const [courses, setCourses] = useState<LMSCourse[]>([]);
  const [grades, setGrades] = useState<LMSGrade[]>([]);
  const [events, setEvents] = useState<LMSEvent[]>([]);
  const [profile, setProfile] = useState<{ name: string; email: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState('');
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');

    try {
      const [p, c, g, e] = await Promise.all([
        lmsApi.getProfile(),
        lmsApi.getCourses(),
        lmsApi.getGrades(),
        lmsApi.getEvents(),
      ]);

      setProfile(p);
      setCourses(c);
      setGrades(g);
      setEvents(e.slice(0, 6));
    } catch (err: any) {
      if (err?.message?.includes('Please log in again')) {
        router.push('/login');
        return;
      }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    setSyncMsg('');

    try {
      await lmsApi.scrapeAll();
      setSyncMsg('LMS synced successfully');
      await load();
    } catch (e: any) {
      setSyncMsg(e.message);
    } finally {
      setSyncing(false);
    }
  };

  const averageGrade = grades.filter((g) => g.grade !== null);
  const avgGradeValue = averageGrade.length
    ? `${Math.round(averageGrade.reduce((sum, g) => sum + (g.grade || 0), 0) / averageGrade.length)}%`
    : '--';

  const upcomingAssignments = events.filter((event) => event.event_type === 'assignment_due').length;

  const eventTone = (type: string) => {
    if (type === 'assignment_due') return 'bg-rose-50 text-rose-700';
    if (type === 'quiz') return 'bg-amber-50 text-amber-700';
    if (type === 'attendance') return 'bg-emerald-50 text-emerald-700';
    return 'bg-slate-100 text-slate-600';
  };

  if (loading) {
    return (
      <div className="app-page flex min-h-screen items-center">
        <div className="section-card w-full max-w-xl p-8">
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-slate-900" />
            Loading your LMS workspace...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-page space-y-8">
      <section className="section-card overflow-hidden">
        <div className="grid gap-8 px-7 py-8 md:grid-cols-[1.15fr_0.85fr] md:px-8 md:py-9">
          <div>
            <div className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
              Dashboard
            </div>
            <h1 className="mt-5 text-4xl font-semibold tracking-tight text-slate-950">
              {profile ? `Welcome back, ${profile.name.split(' ')[0]}` : 'Your academic workspace'}
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-500">
              Keep courses, deadlines, and grades in one clean flow with a calmer white interface.
            </p>

            <div className="mt-6 flex flex-wrap items-center gap-3 text-sm">
              <span className="pill">{profile?.email || 'No active profile'}</span>
              <span className={`pill ${isOnline ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'}`}>
                {isOnline ? 'Online sync available' : 'Offline cached mode'}
              </span>
            </div>
          </div>

          <div className="rounded-[30px] border border-slate-200/80 bg-slate-50/90 p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Quick sync</p>
                <p className="mt-2 text-sm leading-7 text-slate-500">
                  Refresh the live LMS session to update courses, grades, and upcoming events.
                </p>
              </div>
              <Button variant="primary" onClick={handleSync} disabled={syncing || !isOnline}>
                {syncing ? 'Syncing...' : 'Sync LMS'}
              </Button>
            </div>

            {syncMsg && (
              <div className={`mt-4 rounded-2xl px-4 py-3 text-sm ${syncMsg === 'LMS synced successfully' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
                {syncMsg}
              </div>
            )}
          </div>
        </div>
      </section>

      {error && (
        <div className="rounded-[24px] border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          ['Courses', String(courses.length), 'Enrolled and available now', '/courses'],
          ['Upcoming', String(events.length), 'Events visible in the LMS calendar', '/events'],
          ['Average', avgGradeValue, 'Grade overview across reported courses', '/grades'],
          ['Deadlines', String(upcomingAssignments), 'Assignment-related upcoming items', '/assignments'],
        ].map(([label, value, detail, href]) => (
          <Link key={label} href={href} className="metric-card block">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-slate-500">{label}</p>
                <p className="mt-4 text-4xl font-semibold tracking-tight text-slate-950">{value}</p>
              </div>
              <div className="rounded-2xl bg-slate-100 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                {label.slice(0, 2)}
              </div>
            </div>
            <p className="mt-5 text-sm leading-6 text-slate-500">{detail}</p>
          </Link>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Card className="section-card">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold tracking-tight text-slate-950">Courses</h2>
              <p className="mt-1 text-sm text-slate-500">Your active course list from Iqra LMS.</p>
            </div>
            <Link href="/courses" className="text-sm font-medium text-slate-700 hover:text-slate-950">
              View all
            </Link>
          </div>

          <div className="mt-5 space-y-3">
            {courses.slice(0, 5).map((course) => (
              <Link
                key={course.id}
                href={`/assignments?course=${course.id}&name=${encodeURIComponent(course.name)}`}
                className="flex items-center justify-between rounded-[24px] border border-slate-200/80 bg-slate-50/70 px-4 py-4 transition-all duration-200 hover:border-slate-300 hover:bg-white"
              >
                <div>
                  <p className="text-sm font-medium text-slate-900">{course.name}</p>
                  <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-400">{course.code || 'Course workspace'}</p>
                </div>
                <span className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-500">Open</span>
              </Link>
            ))}

            {courses.length === 0 && (
              <div className="rounded-[24px] border border-dashed border-slate-200 px-4 py-6 text-center text-sm text-slate-500">
                No courses yet. Use LMS sync after signing in.
              </div>
            )}
          </div>
        </Card>

        <Card className="section-card">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold tracking-tight text-slate-950">Upcoming events</h2>
              <p className="mt-1 text-sm text-slate-500">A cleaner view of what needs attention next.</p>
            </div>
            <Link href="/events" className="text-sm font-medium text-slate-700 hover:text-slate-950">
              Calendar
            </Link>
          </div>

          <div className="mt-5 space-y-3">
            {events.map((event, index) => {
              const lines = event.full_text.split('\n').filter(Boolean);
              const dateStr = lines[1]?.trim() || event.date_str || 'No date available';

              return (
                <div key={`${event.name}-${index}`} className="rounded-[24px] border border-slate-200/80 bg-white px-4 py-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-slate-900">{event.name}</p>
                      <p className="mt-1 text-sm text-slate-500">{dateStr}</p>
                      {event.course_name && (
                        <p className="mt-2 text-xs uppercase tracking-[0.16em] text-slate-400">{event.course_name}</p>
                      )}
                    </div>
                    <span className={`rounded-full px-3 py-1 text-xs font-medium ${eventTone(event.event_type)}`}>
                      {event.event_type.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>
              );
            })}

            {events.length === 0 && (
              <div className="rounded-[24px] border border-dashed border-slate-200 px-4 py-6 text-center text-sm text-slate-500">
                No upcoming events are visible right now.
              </div>
            )}
          </div>
        </Card>
      </section>
    </div>
  );
}
