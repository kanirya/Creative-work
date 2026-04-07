'use client';

import { useState } from 'react';
import { Card } from '@edupilot/ui';
import { formatDisplayDate } from '@edupilot/utils';
import { useOffline } from '@/lib/offline';

// Mock data — replace with real API calls when endpoint is available
const mockLectures = [
  {
    id: '1',
    title: 'Introduction to Data Structures',
    courseCode: 'CS201',
    courseName: 'Data Structures',
    recordedAt: '2024-01-15T10:00:00Z',
    duration: 3600,
    hasTranscription: true,
    transcriptionStatus: 'completed',
  },
  {
    id: '2',
    title: 'Arrays and Linked Lists',
    courseCode: 'CS201',
    courseName: 'Data Structures',
    recordedAt: '2024-01-17T10:00:00Z',
    duration: 3900,
    hasTranscription: false,
    transcriptionStatus: 'pending',
  },
];

const mockTranscription = {
  segments: [
    { id: '1', startTime: 0, endTime: 30, text: "Welcome to today's lecture on Data Structures." },
    { id: '2', startTime: 30, endTime: 60, text: "Let's start with arrays — a collection of elements in contiguous memory." },
    { id: '3', startTime: 60, endTime: 90, text: 'Arrays provide constant time access using their index.' },
  ],
};

export default function LecturesPage() {
  const [selectedLecture, setSelectedLecture] = useState<string | null>(null);
  const { isOnline } = useOffline();

  const formatDuration = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
  };

  const formatTimestamp = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      completed: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      failed: 'bg-red-100 text-red-800',
    };
    return (
      <span className={`text-xs px-2 py-0.5 rounded-full ${colors[status] ?? 'bg-gray-100 text-gray-600'}`}>
        {status}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Lecture Recordings</h1>
        <p className="text-gray-600 mt-2">Watch recorded lectures and browse transcriptions</p>
      </div>

      {!isOnline && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded" role="alert">
          You are offline. Showing cached recordings.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lecture list */}
        <div className="lg:col-span-1 space-y-3" role="navigation" aria-label="Lecture recordings list">
          <h2 className="text-lg font-semibold text-gray-900">Recordings</h2>
          {mockLectures.map((lecture) => (
            <Card
              key={lecture.id}
              className={`p-4 cursor-pointer transition-all ${
                selectedLecture === lecture.id ? 'ring-2 ring-blue-500 shadow-md' : 'hover:shadow-md'
              }`}
              onClick={() => setSelectedLecture(lecture.id)}
            >
              <h3 className="font-semibold text-gray-900 text-sm">{lecture.title}</h3>
              <p className="text-xs text-gray-600 mt-1">{lecture.courseCode} — {lecture.courseName}</p>
              <div className="flex justify-between items-center mt-2">
                <span className="text-xs text-gray-500">{formatDisplayDate(lecture.recordedAt)}</span>
                <span className="text-xs text-gray-500">{formatDuration(lecture.duration)}</span>
              </div>
              <div className="mt-2">
                {statusBadge(lecture.transcriptionStatus)}
              </div>
            </Card>
          ))}
        </div>

        {/* Player + transcription */}
        <div className="lg:col-span-2 space-y-4">
          {selectedLecture ? (
            <>
              <Card className="p-6">
                <div className="aspect-video bg-gray-900 rounded-lg flex items-center justify-center">
                  <div className="text-center text-white">
                    <p className="text-lg mb-2">Video Player</p>
                    <p className="text-sm text-gray-400">Video playback will be implemented here</p>
                  </div>
                </div>
                <div className="mt-4">
                  <h3 className="text-xl font-semibold text-gray-900">
                    {mockLectures.find((l) => l.id === selectedLecture)?.title}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {formatDisplayDate(mockLectures.find((l) => l.id === selectedLecture)?.recordedAt || '')}
                  </p>
                </div>
              </Card>

              {mockLectures.find((l) => l.id === selectedLecture)?.transcriptionStatus === 'completed' ? (
                <Card className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Transcription</h3>
                  <div className="space-y-3 max-h-96 overflow-y-auto" role="list" aria-label="Transcription segments">
                    {mockTranscription.segments.map((seg) => (
                      <div
                        key={seg.id}
                        className="flex gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                        role="button"
                        tabIndex={0}
                        aria-label={`${formatTimestamp(seg.startTime)}: ${seg.text}`}
                        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') e.preventDefault(); }}
                      >
                        <span className="text-sm font-medium text-blue-600 flex-shrink-0">
                          {formatTimestamp(seg.startTime)}
                        </span>
                        <p className="text-sm text-gray-700">{seg.text}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              ) : (
                <Card className="p-6 text-center text-gray-600">
                  Transcription is {mockLectures.find((l) => l.id === selectedLecture)?.transcriptionStatus}
                </Card>
              )}
            </>
          ) : (
            <Card className="p-12 text-center">
              <p className="text-gray-600">Select a lecture recording to view</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
