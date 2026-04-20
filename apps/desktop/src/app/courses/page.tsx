'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Card } from '@edupilot/ui';
import { lmsApi, LMSCourse } from '@/lib/lms-api';

export default function CoursesPage() {
  const router = useRouter();
  const [courses, setCourses] = useState<LMSCourse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    lmsApi.getCourses()
      .then(setCourses)
      .catch((e) => {
        if (e?.message?.includes('Please log in again')) {
          router.push('/login');
          return;
        }
        setError(e.message);
      })
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) {
    return <div className="app-page text-sm text-slate-500">Loading your course spaces...</div>;
  }

  if (error) {
    return <div className="app-page text-sm text-red-600">Error: {error}</div>;
  }

  return (
    <div className="app-page space-y-8">
      <div className="page-header">
        <div>
          <h1 className="page-title">Courses</h1>
          <p className="page-subtitle">{courses.length} enrolled course spaces connected to your LMS session.</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
        {courses.map((course, index) => (
          <Card key={course.id} className="section-card">
            <div className="flex h-full flex-col">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                    Course {String(index + 1).padStart(2, '0')}
                  </p>
                  <h3 className="mt-3 text-lg font-semibold tracking-tight text-slate-950">{course.name}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-500">{course.code || 'Iqra University course workspace'}</p>
                </div>
                <div className="rounded-2xl bg-slate-100 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                  CR
                </div>
              </div>

              <div className="mt-6 flex gap-3">
                <Link
                  href={`/assignments?course=${course.id}&name=${encodeURIComponent(course.name)}`}
                  className="inline-flex rounded-2xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-slate-800"
                >
                  Assignments
                </Link>
                <Link
                  href={`/grades?course=${course.id}&name=${encodeURIComponent(course.name)}`}
                  className="inline-flex rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition-all duration-200 hover:-translate-y-0.5 hover:border-slate-300 hover:bg-slate-50"
                >
                  Grades
                </Link>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
