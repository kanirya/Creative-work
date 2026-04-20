'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Card, Button } from '@edupilot/ui';
import { lmsApi, LMSCourse, LMSGrade, LMSEvent } from '@/lib/lms-api';
import { useOffline } from '@/lib/offline';
import { DashboardSkeleton } from '@/components/loading-skeletons';

const staggerContainer = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.06,
    },
  },
};

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.28,
      ease: [0.22, 1, 0.36, 1] as const,
    },
  },
};

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Something went wrong';
}

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

  const load = useCallback(async () => {
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
      setEvents(e.slice(0, 5));
    } catch (err: unknown) {
      const message = getErrorMessage(err);
      if (message.includes('Please log in again')) {
        router.push('/login');
        return;
      }
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSync = async () => {
    setSyncing(true);
    setSyncMsg('');

    try {
      await lmsApi.scrapeAll();
      setSyncMsg('LMS synced successfully');
      await load();
    } catch (e: unknown) {
      setSyncMsg(getErrorMessage(e));
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
    return <DashboardSkeleton />;
  }

  return (
    <motion.div
      className="app-page space-y-6"
      variants={staggerContainer}
      initial="hidden"
      animate="show"
    >
      <motion.section variants={fadeUp} className="section-card overflow-hidden">
        <div className="grid gap-6 px-6 py-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(280px,0.85fr)] xl:px-7 xl:py-7">
          <div>
            <div className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">
              Dashboard
            </div>
            <h1 className="mt-4 text-[2rem] font-semibold tracking-tight text-slate-950">
              {profile ? `Welcome back, ${profile.name.split(' ')[0]}` : 'Your academic workspace'}
            </h1>
            <p className="mt-2.5 max-w-xl text-sm leading-7 text-slate-500">
              Courses, deadlines, grades, and submissions in a calmer white workspace.
            </p>

            <div className="mt-5 flex flex-wrap items-center gap-2.5 text-sm">
              <span className="pill">{profile?.email || 'No active profile'}</span>
              <span className={`pill ${isOnline ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'}`}>
                {isOnline ? 'Online sync available' : 'Offline cached mode'}
              </span>
            </div>
          </div>

          <div className="rounded-[24px] border border-slate-200/80 bg-slate-50/90 p-4">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">Quick sync</p>
                <p className="mt-2 text-sm leading-6 text-slate-500">
                  Refresh the live LMS session to pull the latest activity.
                </p>
              </div>
              <Button variant="primary" size="sm" onClick={handleSync} disabled={syncing || !isOnline}>
                {syncing ? 'Syncing...' : 'Sync LMS'}
              </Button>
            </div>

            {syncMsg && (
              <div className={`mt-4 rounded-2xl px-3.5 py-3 text-sm ${syncMsg === 'LMS synced successfully' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
                {syncMsg}
              </div>
            )}
          </div>
        </div>
      </motion.section>

      {error && (
        <motion.div variants={fadeUp} className="rounded-[22px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </motion.div>
      )}

      <motion.section variants={fadeUp} className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {[
          ['Courses', String(courses.length), 'Enrolled and available now', '/courses'],
          ['Upcoming', String(events.length), 'Visible in the LMS calendar', '/events'],
          ['Average', avgGradeValue, 'Grade overview across courses', '/grades'],
          ['Deadlines', String(upcomingAssignments), 'Assignment-related upcoming items', '/assignments'],
        ].map(([label, value, detail, href], index) => (
          <motion.div key={label} variants={fadeUp} transition={{ delay: index * 0.03 }}>
            <Link href={href} className="metric-card block">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">{label}</p>
                  <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">{value}</p>
                </div>
                <div className="rounded-2xl bg-slate-100 px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                  {label.slice(0, 2)}
                </div>
              </div>
              <p className="mt-4 text-xs leading-6 text-slate-500">{detail}</p>
            </Link>
          </motion.div>
        ))}
      </motion.section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.04fr)_minmax(320px,0.96fr)]">
        <motion.div variants={fadeUp}>
          <Card className="section-card">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold tracking-tight text-slate-950">Courses</h2>
                <p className="mt-1 text-xs leading-6 text-slate-500">Your active course list from Iqra LMS.</p>
              </div>
              <Link href="/courses" className="text-sm font-medium text-slate-700 hover:text-slate-950">
                View all
              </Link>
            </div>

            <div className="mt-4 space-y-2.5">
              {courses.slice(0, 5).map((course) => (
                <Link
                  key={course.id}
                  href={`/assignments?course=${course.id}&name=${encodeURIComponent(course.name)}`}
                  className="flex items-center justify-between rounded-[20px] border border-slate-200/80 bg-slate-50/70 px-4 py-3 transition-all duration-200 hover:border-slate-300 hover:bg-white"
                >
                  <div className="min-w-0 pr-4">
                    <p className="text-sm font-medium text-slate-900">{course.name}</p>
                    <p className="mt-1 text-[11px] uppercase tracking-[0.16em] text-slate-400">{course.code || 'Course workspace'}</p>
                  </div>
                  <span className="rounded-full bg-white px-3 py-1 text-[11px] font-medium text-slate-500">Open</span>
                </Link>
              ))}

              {courses.length === 0 && (
                <div className="rounded-[20px] border border-dashed border-slate-200 px-4 py-5 text-center text-sm text-slate-500">
                  No courses yet. Use LMS sync after signing in.
                </div>
              )}
            </div>
          </Card>
        </motion.div>

        <motion.div variants={fadeUp}>
          <Card className="section-card">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold tracking-tight text-slate-950">Upcoming events</h2>
                <p className="mt-1 text-xs leading-6 text-slate-500">What needs attention next.</p>
              </div>
              <Link href="/events" className="text-sm font-medium text-slate-700 hover:text-slate-950">
                Calendar
              </Link>
            </div>

            <div className="mt-4 space-y-2.5">
              {events.map((event, index) => {
                const lines = event.full_text.split('\n').filter(Boolean);
                const dateStr = lines[1]?.trim() || event.date_str || 'No date available';

                return (
                  <div key={`${event.name}-${index}`} className="rounded-[20px] border border-slate-200/80 bg-white px-4 py-3.5">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-900">{event.name}</p>
                        <p className="mt-1 text-xs leading-6 text-slate-500">{dateStr}</p>
                        {event.course_name && (
                          <p className="mt-1.5 text-[11px] uppercase tracking-[0.16em] text-slate-400">{event.course_name}</p>
                        )}
                      </div>
                      <span className={`rounded-full px-3 py-1 text-[11px] font-medium ${eventTone(event.event_type)}`}>
                        {event.event_type.replace(/_/g, ' ')}
                      </span>
                    </div>
                  </div>
                );
              })}

              {events.length === 0 && (
                <div className="rounded-[20px] border border-dashed border-slate-200 px-4 py-5 text-center text-sm text-slate-500">
                  No upcoming events are visible right now.
                </div>
              )}
            </div>
          </Card>
        </motion.div>
      </section>
    </motion.div>
  );
}
