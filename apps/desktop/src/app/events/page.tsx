'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@edupilot/ui';
import { lmsApi, LMSEvent } from '@/lib/lms-api';

const EVENT_SHORT: Record<string, string> = {
  assignment_due: 'AS',
  quiz: 'QZ',
  attendance: 'AT',
  other: 'EV',
};

const EVENT_TONE: Record<string, string> = {
  assignment_due: 'bg-rose-50 text-rose-700',
  quiz: 'bg-amber-50 text-amber-700',
  attendance: 'bg-emerald-50 text-emerald-700',
  other: 'bg-slate-100 text-slate-600',
};

export default function EventsPage() {
  const router = useRouter();
  const [events, setEvents] = useState<LMSEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    lmsApi.getEvents()
      .then(setEvents)
      .catch((e) => {
        if (e?.message?.includes('Please log in again')) {
          router.push('/login');
          return;
        }
        setError(e.message);
      })
      .finally(() => setLoading(false));
  }, [router]);

  const formatDate = (event: LMSEvent) => {
    const lines = event.full_text.split('\n').filter(Boolean);
    return lines[1]?.trim() || event.date_str || 'No date available';
  };

  if (loading) {
    return <div className="app-page text-sm text-slate-500">Loading upcoming events...</div>;
  }

  if (error) {
    return <div className="app-page text-sm text-red-600">Error: {error}</div>;
  }

  return (
    <div className="app-page space-y-8">
      <div className="page-header">
        <div>
          <h1 className="page-title">Calendar</h1>
          <p className="page-subtitle">{events.length} upcoming items from your LMS calendar feed.</p>
        </div>
      </div>

      {events.length === 0 && (
        <Card className="section-card">
          <p className="text-sm text-slate-500">No upcoming events are visible right now.</p>
        </Card>
      )}

      <div className="space-y-4">
        {events.map((event, index) => (
          <Card key={`${event.name}-${index}`} className="section-card">
            <div className="flex items-start gap-4">
              <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl text-xs font-semibold tracking-[0.18em] ${EVENT_TONE[event.event_type] || EVENT_TONE.other}`}>
                {EVENT_SHORT[event.event_type] || 'EV'}
              </div>

              <div className="min-w-0 flex-1">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <h3 className="text-base font-semibold tracking-tight text-slate-950">{event.name}</h3>
                    <p className="mt-2 text-sm leading-7 text-slate-500">{formatDate(event)}</p>
                    {event.course_name && (
                      <p className="mt-2 text-xs uppercase tracking-[0.16em] text-slate-400">{event.course_name}</p>
                    )}
                  </div>

                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${EVENT_TONE[event.event_type] || EVENT_TONE.other}`}>
                    {event.event_type.replace(/_/g, ' ')}
                  </span>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
