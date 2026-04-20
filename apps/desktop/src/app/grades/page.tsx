'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card } from '@edupilot/ui';
import { lmsApi, LMSGrade, LMSCourseGrade } from '@/lib/lms-api';

function GradesContent() {
  const router = useRouter();
  const params = useSearchParams();
  const courseId = Number(params.get('course') || 0);
  const courseName = params.get('name') || '';

  const [overview, setOverview] = useState<LMSGrade[]>([]);
  const [detail, setDetail] = useState<LMSCourseGrade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const [ov, det] = await Promise.all([
          lmsApi.getGrades(),
          courseId ? lmsApi.getCourseGrades(courseId) : Promise.resolve([]),
        ]);
        setOverview(ov);
        setDetail(det);
      } catch (e: any) {
        if (e?.message?.includes('Please log in again')) {
          router.push('/login');
          return;
        }
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [courseId, router]);

  const gradeTone = (grade: number | null) => {
    if (grade === null) return 'text-slate-400';
    if (grade >= 80) return 'text-emerald-600';
    if (grade >= 60) return 'text-amber-600';
    return 'text-rose-600';
  };

  if (loading) {
    return <div className="app-page text-sm text-slate-500">Loading grade reports...</div>;
  }

  if (error) {
    return <div className="app-page text-sm text-red-600">Error: {error}</div>;
  }

  return (
    <div className="app-page space-y-8">
      <div className="page-header">
        <div>
          <h1 className="page-title">Grades</h1>
          {courseName && (
            <p className="page-subtitle">{decodeURIComponent(courseName)}</p>
          )}
        </div>
      </div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {overview.filter((g) => g.course_name).map((grade, index) => (
          <Card key={`${grade.course_id}-${index}`} className="section-card">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Overview</p>
                <p className="mt-3 text-sm leading-7 text-slate-700">{grade.course_name}</p>
              </div>
              <p className={`text-3xl font-semibold tracking-tight ${gradeTone(grade.grade)}`}>
                {grade.grade !== null ? `${grade.grade}%` : '--'}
              </p>
            </div>
          </Card>
        ))}
      </section>

      {detail.length > 0 && (
        <section className="section-card overflow-hidden">
          <div className="border-b border-slate-200/80 px-7 py-5">
            <h2 className="text-xl font-semibold tracking-tight text-slate-950">Grade breakdown</h2>
            <p className="mt-1 text-sm text-slate-500">Detailed items from the selected course.</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50/90 text-left text-slate-500">
                <tr>
                  <th className="px-7 py-4 font-medium">Item</th>
                  <th className="px-7 py-4 text-right font-medium">Grade</th>
                  <th className="px-7 py-4 text-right font-medium">Max</th>
                  <th className="px-7 py-4 text-right font-medium">Percent</th>
                </tr>
              </thead>
              <tbody>
                {detail.map((item, index) => (
                  <tr key={`${item.item_name}-${index}`} className="border-t border-slate-200/70">
                    <td className="px-7 py-4 text-slate-800">{item.item_name}</td>
                    <td className={`px-7 py-4 text-right font-medium ${gradeTone(item.grade)}`}>
                      {item.grade !== null ? item.grade : '--'}
                    </td>
                    <td className="px-7 py-4 text-right text-slate-500">
                      {item.max_grade !== null ? item.max_grade : '--'}
                    </td>
                    <td className={`px-7 py-4 text-right font-medium ${gradeTone(item.percentage)}`}>
                      {item.percentage !== null ? `${item.percentage}%` : '--'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}

export default function GradesPage() {
  return (
    <Suspense fallback={<div className="app-page text-sm text-slate-500">Loading grade reports...</div>}>
      <GradesContent />
    </Suspense>
  );
}
