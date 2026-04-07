'use client';

import { useEffect, useState } from 'react';
import { Card } from '@edupilot/ui';
import { lmsApi, LMSEvent } from '@/lib/lms-api';

const EVENT_ICONS: Record<string, string> = {
  assignment_due: '📝',
  quiz: '📋',
  attendance: '✅',
  other: '📅',
};

const EVENT_COLORS: Record<string, string> = {
  assignment_due: 'border-l-4 border-red-400',
  quiz: 'border-l-4 border-purple-400',
  attendance: 'border-l-4 border-green-400',
  other: 'border-l-4 border-blue-400',
};

export default function EventsPage() {
  const [events, setEvents] = useState<LMSEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    lmsApi.getEvents()
      .then(setEvents)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const formatDate = (e: LMSEvent) => {
    const lines = e.full_text.split('\n').filter(Boolean);
    return lines[1]?.trim() || e.date_str || '';
  };

  if (loading) return <div className="p-8 text-gray-600">Loading calendar events...</div>;
  if (error) return <div className="p-8 text-red-600">Error: {error}</div>;

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Upcoming Events</h1>
        <p className="text-gray-600 mt-1">{events.length} upcoming events</p>
      </div>

      {events.length === 0 && (
        <Card className="p-6 text-center text-gray-600">No upcoming events</Card>
      )}

      <div className="space-y-3">
        {events.map((e, i) => (
          <Card key={i} className={`p-4 ${EVENT_COLORS[e.event_type] || EVENT_COLORS.other}`}>
            <div className="flex items-start gap-3">
              <span className="text-xl">{EVENT_ICONS[e.event_type] || '📅'}</span>
              <div className="flex-1">
                <p className="font-semibold text-gray-900">{e.name}</p>
                <p className="text-sm text-gray-600 mt-0.5">{formatDate(e)}</p>
                {e.course_name && (
                  <p className="text-xs text-gray-500 mt-1">{e.course_name}</p>
                )}
              </div>
              <span className="text-xs text-gray-400 capitalize">
                {e.event_type.replace(/_/g, ' ')}
              </span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
