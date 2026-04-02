'use client';

import { useState } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { DashboardLayout } from '@/components/DashboardLayout';
import { Card } from '@edupilot/ui';
import { formatDisplayDate, formatDateTime } from '@edupilot/utils';

// Mock data - will be replaced with actual API calls
const mockLectures = [
  {
    id: '1',
    title: 'Introduction to Data Structures',
    courseCode: 'CS201',
    courseName: 'Data Structures',
    recordedAt: '2024-01-15T10:00:00Z',
    duration: 3600,
    videoUrl: 'https://example.com/video1.mp4',
    hasTranscription: true,
  },
  {
    id: '2',
    title: 'Arrays and Linked Lists',
    courseCode: 'CS201',
    courseName: 'Data Structures',
    recordedAt: '2024-01-17T10:00:00Z',
    duration: 3900,
    videoUrl: 'https://example.com/video2.mp4',
    hasTranscription: true,
  },
];

const mockTranscription = {
  segments: [
    {
      id: '1',
      startTime: 0,
      endTime: 30,
      text: 'Welcome to today\'s lecture on Data Structures. We\'ll be covering arrays and linked lists.',
    },
    {
      id: '2',
      startTime: 30,
      endTime: 60,
      text: 'Let\'s start with arrays. An array is a collection of elements stored in contiguous memory locations.',
    },
    {
      id: '3',
      startTime: 60,
      endTime: 90,
      text: 'Arrays provide constant time access to elements using their index.',
    },
  ],
};

export default function LecturesPage() {
  const [selectedLecture, setSelectedLecture] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatTimestamp = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSegmentClick = (startTime: number) => {
    setCurrentTime(startTime);
    // In a real implementation, this would seek the video player
  };

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="space-y-6">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Lecture Recordings</h1>
            <p className="text-gray-600 mt-2">
              Watch recorded lectures and browse transcriptions
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Lecture List */}
            <div className="lg:col-span-1 space-y-3" role="navigation" aria-label="Lecture recordings list">
              <h2 className="text-lg font-semibold text-gray-900">Recordings</h2>
              {mockLectures.map((lecture) => (
                <Card
                  key={lecture.id}
                  className={`p-4 cursor-pointer transition-all ${
                    selectedLecture === lecture.id
                      ? 'ring-2 ring-blue-500 shadow-md'
                      : 'hover:shadow-md'
                  }`}
                  onClick={() => setSelectedLecture(lecture.id)}
                  role="button"
                  tabIndex={0}
                  aria-label={`Select lecture: ${lecture.title}`}
                  aria-pressed={selectedLecture === lecture.id}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      setSelectedLecture(lecture.id);
                    }
                  }}
                >
                  <h3 className="font-semibold text-gray-900 text-sm">
                    {lecture.title}
                  </h3>
                  <p className="text-xs text-gray-600 mt-1">
                    {lecture.courseCode} - {lecture.courseName}
                  </p>
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-xs text-gray-500">
                      {formatDisplayDate(lecture.recordedAt)}
                    </span>
                    <span className="text-xs text-gray-500">
                      {formatDuration(lecture.duration)}
                    </span>
                  </div>
                </Card>
              ))}
            </div>

            {/* Video Player and Transcription */}
            <div className="lg:col-span-2 space-y-4">
              {selectedLecture ? (
                <>
                  {/* Video Player Placeholder */}
                  <Card className="p-6">
                    <div className="aspect-video bg-gray-900 rounded-lg flex items-center justify-center">
                      <div className="text-center text-white">
                        <p className="text-lg mb-2">Video Player</p>
                        <p className="text-sm text-gray-400">
                          Video playback will be implemented here
                        </p>
                      </div>
                    </div>
                    <div className="mt-4">
                      <h3 className="text-xl font-semibold text-gray-900">
                        {mockLectures.find((l) => l.id === selectedLecture)?.title}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        {formatDateTime(
                          mockLectures.find((l) => l.id === selectedLecture)?.recordedAt || ''
                        )}
                      </p>
                    </div>
                  </Card>

                  {/* Transcription */}
                  <Card className="p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Transcription
                    </h3>
                    <div className="space-y-3 max-h-96 overflow-y-auto" role="list" aria-label="Lecture transcription segments">
                      {mockTranscription.segments.map((segment) => (
                        <div
                          key={segment.id}
                          className="flex gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                          onClick={() => handleSegmentClick(segment.startTime)}
                          role="button"
                          tabIndex={0}
                          aria-label={`Jump to ${formatTimestamp(segment.startTime)}: ${segment.text}`}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              handleSegmentClick(segment.startTime);
                            }
                          }}
                        >
                          <span className="text-sm font-medium text-blue-600 flex-shrink-0">
                            {formatTimestamp(segment.startTime)}
                          </span>
                          <p className="text-sm text-gray-700">{segment.text}</p>
                        </div>
                      ))}
                    </div>
                  </Card>
                </>
              ) : (
                <Card className="p-12 text-center">
                  <p className="text-gray-600">
                    Select a lecture recording to view
                  </p>
                </Card>
              )}
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}
