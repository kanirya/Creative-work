'use client';

import { useEffect, useState } from 'react';
import { Card, Button } from '@edupilot/ui';
import { lmsApi, LMSCourse, LMSGrade, LMSEvent, LMSAssignment } from '@/lib/lms-api';
import { useOffline } from '@/lib/offline';
import Link from 'next/link';

export default function DashboardPage() {
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
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleSync = async () => {
    setSyncing(true);
    setSyncMsg('');
    try {
      await lmsApi.scrapeAll();
      setSyncMsg('✓ LMS data synced');
      await load();
    } catch (e: any) {
      setSyncMsg(`✗ ${e.message}`);
    } finally {
      setSyncing(false);
    }
  };

  const gradeColor = (g: number | null) => {
    if (g === null) return 'text-gray-400';
    if (g >= 80) return 'text-green-600 font-bold';
    if (g >= 60) return 'text-yellow-600 font-bold';
    return 'text-red-600 font-bold';
  };

  const eventIcon = (type: string) => {
    if (type === 'assignment_due') return '📝';
    if (type === 'quiz') return '📋';
    if (type === 'attendance') return '✅';
    return '📅';
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center gap-3 text-gray-600">
        <div className="animate-spin w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full" />
        Loading LMS data...
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {profile ? `Welcome, ${profile.name.split(' ')[0]}` : 'Dashboard'}
          </h1>
          <p className="text-gray-500 text-sm mt-1">{profile?.email}</p>
        </div>
        <div className="flex items-center gap-3">
          {syncMsg && (
            <span className={`text-sm ${syncMsg.startsWith('✓') ? 'text-green-600' : 'text-red-600'}`}>
              {syncMsg}
            </span>
          )}
          <Button
            variant="secondary"
            onClick={handleSync}
            disabled={syncing || !isOnline}
            aria-label="Sync LMS data"
          >
            {syncing ? '⟳ Syncing...' : '⟳ Sync LMS'}
          </Button>
        </div>
      </div>

      {!isOnline && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded text-sm" role="alert">
          You are offline — showing cached data
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm" role="alert">
          {error} — Make sure the LMS scraper service is running on port 8002
        </div>
      )}

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Courses', value: courses.length, icon: '📚', href: '/courses' },
          { label: 'Upcoming', value: events.length, icon: '📅', href: '/events' },
          { label: 'Avg Grade', value: grades.filter(g => g.grade !== null).length > 0
              ? Math.round(grades.filter(g => g.grade !== null).reduce((s, g) => s + (g.grade || 0), 0) / grades.filter(g => g.grade !== null).length) + '%'
              : '-', icon: '📊', href: '/grades' },
          { label: 'Assignments', value: '→', icon: '📝', href: '/assignments' },
        ].map((stat) => (
          <Link key={stat.label} href={stat.href}>
            <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex items-center justify-between">
                <span className="text-2xl">{stat.icon}</span>
                <span className="text-2xl font-bold text-gray-900">{stat.value}</span>
              </div>
              <p className="text-sm text-gray-600 mt-2">{stat.label}</p>
            </Card>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Courses */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-gray-900">My Courses</h2>
            <Link href="/courses" className="text-sm text-blue-600 hover:underline">View all</Link>
          </div>
          <div className="space-y-2">
            {courses.slice(0, 5).map((c) => (
              <Link key={c.id} href={`/assignments?course=${c.id}&name=${encodeURIComponent(c.name)}`}>
                <Card className="p-3 hover:shadow-md transition-shadow cursor-pointer">
                  <p className="text-sm font-medium text-gray-900 leading-tight">{c.name}</p>
                </Card>
              </Link>
            ))}
            {courses.length === 0 && (
              <Card className="p-4 text-center text-gray-500 text-sm">
                No courses — click Sync LMS to load
              </Card>
            )}
          </div>
        </section>

        {/* Grades */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-gray-900">Grades</h2>
            <Link href="/grades" className="text-sm text-blue-600 hover:underline">View all</Link>
          </div>
          <div className="space-y-2">
            {grades.filter(g => g.course_name).slice(0, 5).map((g, i) => (
              <Card key={i} className="p-3 flex items-center justify-between">
                <p className="text-sm text-gray-700 flex-1 pr-3 leading-tight">{g.course_name}</p>
                <span className={`text-lg ${gradeColor(g.grade)}`}>
                  {g.grade !== null ? `${g.grade}%` : '-'}
                </span>
              </Card>
            ))}
            {grades.length === 0 && (
              <Card className="p-4 text-center text-gray-500 text-sm">No grades yet</Card>
            )}
          </div>
        </section>
      </div>

      {/* Upcoming events */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">Upcoming Events</h2>
          <Link href="/events" className="text-sm text-blue-600 hover:underline">View all</Link>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {events.map((e, i) => {
            const lines = e.full_text.split('\n').filter(Boolean);
            const dateStr = lines[1]?.trim() || e.date_str;
            return (
              <Card key={i} className="p-3 flex items-start gap-3">
                <span className="text-xl">{eventIcon(e.event_type)}</span>
                <div>
                  <p className="text-sm font-medium text-gray-900">{e.name}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{dateStr}</p>
                  {e.course_name && (
                    <p className="text-xs text-gray-400">{e.course_name}</p>
                  )}
                </div>
              </Card>
            );
          })}
          {events.length === 0 && (
            <Card className="p-4 text-center text-gray-500 text-sm col-span-2">No upcoming events</Card>
          )}
        </div>
      </section>
    </div>
  );
}
