'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Card } from '@edupilot/ui';
import { lmsApi, LMSGrade, LMSCourseGrade } from '@/lib/lms-api';

export default function GradesPage() {
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
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [courseId]);

  const gradeColor = (g: number | null) => {
    if (g === null) return 'text-gray-400';
    if (g >= 80) return 'text-green-600';
    if (g >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) return <div className="p-8 text-gray-600">Loading grades...</div>;
  if (error) return <div className="p-8 text-red-600">Error: {error}</div>;

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Grades</h1>
        {courseName && <p className="text-gray-600 mt-1 text-sm">{decodeURIComponent(courseName)}</p>}
      </div>

      {/* Overview */}
      <section>
        <h2 className="text-xl font-semibold text-gray-900 mb-3">All Courses</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {overview.filter(g => g.course_name).map((g, i) => (
            <Card key={i} className="p-4 flex items-center justify-between">
              <p className="text-sm text-gray-700 flex-1 pr-4">{g.course_name}</p>
              <span className={`text-xl font-bold ${gradeColor(g.grade)}`}>
                {g.grade !== null ? `${g.grade}%` : '-'}
              </span>
            </Card>
          ))}
        </div>
      </section>

      {/* Detailed breakdown */}
      {detail.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">Grade Breakdown</h2>
          <Card className="overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left p-3 text-gray-600 font-medium">Item</th>
                  <th className="text-right p-3 text-gray-600 font-medium">Grade</th>
                  <th className="text-right p-3 text-gray-600 font-medium">Max</th>
                  <th className="text-right p-3 text-gray-600 font-medium">%</th>
                </tr>
              </thead>
              <tbody>
                {detail.map((g, i) => (
                  <tr key={i} className="border-t border-gray-100 hover:bg-gray-50">
                    <td className="p-3 text-gray-800">{g.item_name}</td>
                    <td className={`p-3 text-right font-medium ${gradeColor(g.grade)}`}>
                      {g.grade !== null ? g.grade : '-'}
                    </td>
                    <td className="p-3 text-right text-gray-500">
                      {g.max_grade !== null ? g.max_grade : '-'}
                    </td>
                    <td className={`p-3 text-right font-medium ${gradeColor(g.percentage)}`}>
                      {g.percentage !== null ? `${g.percentage}%` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </section>
      )}
    </div>
  );
}
