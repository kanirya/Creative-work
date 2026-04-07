'use client';

import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Card, Button } from '@edupilot/ui';
import { lmsApi, LMSAssignment, LMSCourse } from '@/lib/lms-api';

export default function AssignmentsPage() {
  const params = useSearchParams();
  const courseId = params.get('course') ? Number(params.get('course')) : null;
  const courseName = params.get('name') ? decodeURIComponent(params.get('name')!) : '';

  const [assignments, setAssignments] = useState<LMSAssignment[]>([]);
  const [courses, setCourses] = useState<LMSCourse[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<number | null>(courseId);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState<number | null>(null);
  const [submitMsg, setSubmitMsg] = useState<{ id: number; msg: string; ok: boolean } | null>(null);
  const fileRefs = useRef<Record<number, HTMLInputElement | null>>({});

  // Load courses for the selector
  useEffect(() => {
    lmsApi.getCourses().then(setCourses).catch(() => {});
  }, []);

  // Load assignments when course changes
  useEffect(() => {
    setLoading(true);
    setError('');
    const load = selectedCourse
      ? lmsApi.getAssignments(selectedCourse)
      : lmsApi.getAllAssignments();

    load
      .then(setAssignments)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [selectedCourse]);

  const handleSubmit = async (assignment: LMSAssignment) => {
    const fileInput = fileRefs.current[assignment.id];
    const file = fileInput?.files?.[0];
    if (!file) {
      setSubmitMsg({ id: assignment.id, msg: 'Please select a file first', ok: false });
      return;
    }
    setSubmitting(assignment.id);
    setSubmitMsg(null);
    const result = await lmsApi.submitAssignment(assignment.id, file);
    setSubmitMsg({ id: assignment.id, msg: result.message, ok: result.success });
    setSubmitting(null);
    if (result.success && selectedCourse) {
      const updated = await lmsApi.getAssignments(selectedCourse);
      setAssignments(updated);
    }
  };

  const statusColor = (s: string) => {
    if (s.includes('submitted')) return 'text-green-700 bg-green-50 border-green-200';
    if (s.includes('overdue') || s.includes('late')) return 'text-red-700 bg-red-50 border-red-200';
    return 'text-yellow-700 bg-yellow-50 border-yellow-200';
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return 'No due date';
    try {
      return new Date(iso).toLocaleDateString('en-US', {
        weekday: 'short', day: 'numeric', month: 'short', year: 'numeric',
      });
    } catch { return iso; }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Assignments</h1>
          <p className="text-gray-500 mt-1 text-sm">
            {selectedCourse && courseName ? courseName : 'All courses'}
          </p>
        </div>

        {/* Course selector */}
        <div className="flex items-center gap-2">
          <label htmlFor="course-select" className="text-sm text-gray-600">Course:</label>
          <select
            id="course-select"
            value={selectedCourse ?? ''}
            onChange={(e) => setSelectedCourse(e.target.value ? Number(e.target.value) : null)}
            className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All courses</option>
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name.split(' - ')[0]}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-gray-600 text-sm">
          <div className="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full" />
          Loading assignments...
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
          {error}
        </div>
      )}

      {!loading && !error && assignments.length === 0 && (
        <Card className="p-6 text-center text-gray-500 text-sm">
          No assignments found for this course
        </Card>
      )}

      <div className="space-y-4">
        {assignments.map((a) => (
          <Card key={`${a.course_id}-${a.id}`} className="p-5">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">{a.name}</h3>
                <p className="text-xs text-gray-500 mt-0.5">{a.course_name || `Course ${a.course_id}`}</p>
                {a.description && (
                  <p className="text-sm text-gray-600 mt-1.5 line-clamp-2">{a.description}</p>
                )}
                <div className="flex flex-wrap gap-2 mt-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${statusColor(a.submission_status)}`}>
                    {a.submission_status.replace(/_/g, ' ')}
                  </span>
                  {a.grade !== null && a.grade !== undefined && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-medium">
                      Grade: {a.grade} / {a.max_grade ?? 100}
                    </span>
                  )}
                  {a.can_submit && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-orange-50 text-orange-700 border border-orange-200 font-medium">
                      Submission open
                    </span>
                  )}
                </div>
              </div>
              <div className="text-right text-xs text-gray-500 flex-shrink-0">
                <p className="font-medium text-gray-700">{formatDate(a.due_date)}</p>
                {a.time_remaining && (
                  <p className="mt-0.5 text-gray-400">{a.time_remaining}</p>
                )}
              </div>
            </div>

            {/* Submitted files */}
            {a.submitted_files && a.submitted_files.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <p className="text-xs text-gray-500 mb-1">Submitted:</p>
                {a.submitted_files.map((f, i) => (
                  <p key={i} className="text-xs text-blue-600">📎 {f}</p>
                ))}
              </div>
            )}

            {/* Submission form */}
            {a.can_submit && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-sm font-medium text-gray-700 mb-2">
                  {a.submit_btn_text || 'Submit Assignment'}
                </p>
                <div className="flex items-center gap-3 flex-wrap">
                  <input
                    type="file"
                    ref={(el) => { fileRefs.current[a.id] = el; }}
                    className="text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-sm file:bg-gray-100 file:text-gray-700 hover:file:bg-gray-200"
                    accept=".pdf,.doc,.docx,.txt,.zip,.py,.java,.cpp,.c,.xlsx,.pptx"
                  />
                  <Button
                    variant="primary"
                    onClick={() => handleSubmit(a)}
                    disabled={submitting === a.id}
                    aria-label={`Submit ${a.name}`}
                  >
                    {submitting === a.id ? 'Submitting...' : 'Submit'}
                  </Button>
                </div>
                {submitMsg?.id === a.id && (
                  <p className={`text-sm mt-2 ${submitMsg.ok ? 'text-green-600' : 'text-red-600'}`}>
                    {submitMsg.msg}
                  </p>
                )}
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
