'use client';

import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Card, Button } from '@edupilot/ui';
import { lmsApi, LMSAssignment } from '@/lib/lms-api';

export default function AssignmentsPage() {
  const params = useSearchParams();
  const courseId = Number(params.get('course') || 0);
  const courseName = params.get('name') || 'Course';

  const [assignments, setAssignments] = useState<LMSAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState<number | null>(null);
  const [submitMsg, setSubmitMsg] = useState<{ id: number; msg: string; ok: boolean } | null>(null);
  const fileRefs = useRef<Record<number, HTMLInputElement | null>>({});

  useEffect(() => {
    if (!courseId) return;
    lmsApi.getAssignments(courseId)
      .then(setAssignments)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [courseId]);

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

    if (result.success) {
      // Refresh assignments
      const updated = await lmsApi.getAssignments(courseId);
      setAssignments(updated);
    }
  };

  const statusColor = (status: string) => {
    if (status.includes('submitted')) return 'text-green-700 bg-green-50';
    if (status.includes('overdue') || status.includes('late')) return 'text-red-700 bg-red-50';
    return 'text-yellow-700 bg-yellow-50';
  };

  if (loading) return <div className="p-8 text-gray-600">Loading assignments...</div>;
  if (error) return <div className="p-8 text-red-600">Error: {error}</div>;

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Assignments</h1>
        <p className="text-gray-600 mt-1 text-sm">{decodeURIComponent(courseName)}</p>
      </div>

      {assignments.length === 0 && (
        <Card className="p-6 text-center text-gray-600">No assignments found for this course</Card>
      )}

      <div className="space-y-4">
        {assignments.map((a) => (
          <Card key={a.id} className="p-5">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">{a.name}</h3>
                {a.description && (
                  <p className="text-sm text-gray-600 mt-1 line-clamp-2">{a.description}</p>
                )}
                <div className="flex flex-wrap gap-2 mt-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColor(a.submission_status)}`}>
                    {a.submission_status.replace(/_/g, ' ')}
                  </span>
                  {a.grade !== null && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 font-medium">
                      Grade: {a.grade} / {a.max_grade}
                    </span>
                  )}
                </div>
                {a.due_date && (
                  <p className="text-xs text-gray-500 mt-2">
                    Due: {new Date(a.due_date).toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })}
                  </p>
                )}
                {a.time_remaining && (
                  <p className="text-xs text-gray-500">{a.time_remaining}</p>
                )}
                {a.submitted_files.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs text-gray-500">Submitted files:</p>
                    {a.submitted_files.map((f, i) => (
                      <p key={i} className="text-xs text-blue-600">📎 {f}</p>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Submission form */}
            {a.can_submit && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-sm font-medium text-gray-700 mb-2">
                  {a.submit_btn_text || 'Submit Assignment'}
                </p>
                <div className="flex items-center gap-3">
                  <input
                    type="file"
                    ref={(el) => { fileRefs.current[a.id] = el; }}
                    className="text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-sm file:bg-gray-100 file:text-gray-700 hover:file:bg-gray-200"
                    accept=".pdf,.doc,.docx,.txt,.zip,.py,.java,.cpp,.c"
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
