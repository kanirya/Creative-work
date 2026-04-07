'use client';

import { useEffect, useState } from 'react';
import { Card } from '@edupilot/ui';
import { lmsApi, LMSCourse } from '@/lib/lms-api';
import Link from 'next/link';

export default function CoursesPage() {
  const [courses, setCourses] = useState<LMSCourse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    lmsApi.getCourses()
      .then(setCourses)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-gray-600">Loading courses from LMS...</div>;
  if (error) return <div className="p-8 text-red-600">Error: {error}</div>;

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">My Courses</h1>
        <p className="text-gray-600 mt-1">{courses.length} enrolled courses</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {courses.map((course) => (
          <Card key={course.id} className="p-5 hover:shadow-lg transition-shadow">
            <h3 className="font-semibold text-gray-900 text-sm leading-tight">{course.name}</h3>
            <p className="text-xs text-gray-500 mt-1">{course.code}</p>
            <div className="flex gap-3 mt-4">
              <Link
                href={`/assignments?course=${course.id}&name=${encodeURIComponent(course.name)}`}
                className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded hover:bg-blue-700"
              >
                Assignments
              </Link>
              <Link
                href={`/grades?course=${course.id}&name=${encodeURIComponent(course.name)}`}
                className="text-xs bg-gray-100 text-gray-700 px-3 py-1.5 rounded hover:bg-gray-200"
              >
                Grades
              </Link>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
