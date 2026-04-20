'use client';

import { Suspense, useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, Button } from '@edupilot/ui';
import { lmsApi, LMSAssignment, LMSCourse } from '@/lib/lms-api';

const LMS_FILE_DOWNLOAD_BASE =
  `${process.env.NEXT_PUBLIC_LMS_SCRAPER_URL || 'http://localhost:8002'}/api/lms/files/download?url=`;

function AssignmentsContent() {
  const router = useRouter();
  const params = useSearchParams();
  const courseId = params.get('course') ? Number(params.get('course')) : null;
  const initialCourseName = params.get('name') ? decodeURIComponent(params.get('name')!) : '';

  const [assignments, setAssignments] = useState<LMSAssignment[]>([]);
  const [courses, setCourses] = useState<LMSCourse[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<number | null>(courseId);
  const [selectedCourseName, setSelectedCourseName] = useState(initialCourseName);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState<number | null>(null);
  const [submitMsg, setSubmitMsg] = useState<{ id: number; msg: string; ok: boolean } | null>(null);
  const fileRefs = useRef<Record<number, HTMLInputElement | null>>({});
  const [onlineTextById, setOnlineTextById] = useState<Record<number, string>>({});

  useEffect(() => {
    lmsApi.getCourses()
      .then(setCourses)
      .catch((e) => {
        if (e?.message?.includes('Please log in again')) {
          router.push('/login');
        }
      });
  }, [router]);

  useEffect(() => {
    if (!selectedCourse) {
      setSelectedCourseName('');
      return;
    }

    const matchedCourse = courses.find((course) => course.id === selectedCourse);
    if (matchedCourse) {
      setSelectedCourseName(matchedCourse.name);
    }
  }, [courses, selectedCourse]);

  useEffect(() => {
    setLoading(true);
    setError('');

    const load = selectedCourse
      ? lmsApi.getAssignments(selectedCourse)
      : lmsApi.getAllAssignments();

    load
      .then(setAssignments)
      .catch((e) => {
        if (e?.message?.includes('Please log in again')) {
          router.push('/login');
          return;
        }
        setError(e.message);
      })
      .finally(() => setLoading(false));
  }, [router, selectedCourse]);

  const handleSubmit = async (assignment: LMSAssignment) => {
    const fileInput = fileRefs.current[assignment.id];
    const file = fileInput?.files?.[0];
    const onlineText = onlineTextById[assignment.id]?.trim();

    if (!file && !onlineText) {
      setSubmitMsg({ id: assignment.id, msg: 'Add a file or enter online text first', ok: false });
      return;
    }

    setSubmitting(assignment.id);
    setSubmitMsg(null);

    try {
      const result = await lmsApi.submitAssignment(assignment.id, file, onlineText);
      setSubmitMsg({ id: assignment.id, msg: result.message, ok: result.success });

      if (result.success) {
        const updated = selectedCourse
          ? await lmsApi.getAssignments(selectedCourse)
          : await lmsApi.getAllAssignments();

        setAssignments(updated);

        if (fileInput) {
          fileInput.value = '';
        }

        setOnlineTextById((current) => ({
          ...current,
          [assignment.id]: '',
        }));
      }
    } catch (e: any) {
      setSubmitMsg({
        id: assignment.id,
        msg: e?.message || 'Submission failed',
        ok: false,
      });
    } finally {
      setSubmitting(null);
    }
  };

  const statusTone = (status: string) => {
    if (status.includes('submitted')) return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    if (status.includes('overdue') || status.includes('late')) return 'border-rose-200 bg-rose-50 text-rose-700';
    return 'border-amber-200 bg-amber-50 text-amber-700';
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return 'No due date';
    try {
      return new Date(iso).toLocaleDateString('en-US', {
        weekday: 'short',
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="app-page space-y-8">
      <div className="page-header">
        <div>
          <h1 className="page-title">Assignments</h1>
          <p className="page-subtitle">
            {selectedCourse && selectedCourseName ? selectedCourseName : 'All courses'}
          </p>
        </div>

        <div className="rounded-[22px] border border-slate-200 bg-white px-4 py-3 shadow-sm">
          <label htmlFor="course-select" className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
            Filter course
          </label>
          <select
            id="course-select"
            value={selectedCourse ?? ''}
            onChange={(e) => setSelectedCourse(e.target.value ? Number(e.target.value) : null)}
            className="min-w-[220px] rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-300"
          >
            <option value="">All courses</option>
            {courses.map((course) => (
              <option key={course.id} value={course.id}>
                {course.name.split(' - ')[0]}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && (
        <div className="text-sm text-slate-500">Loading assignments...</div>
      )}

      {error && (
        <div className="rounded-[24px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!loading && !error && assignments.length === 0 && (
        <Card className="section-card">
          <p className="text-sm text-slate-500">No assignments found for this selection.</p>
        </Card>
      )}

      <div className="space-y-4">
        {assignments.map((assignment) => (
          <Card key={`${assignment.course_id}-${assignment.id}`} className="section-card">
            <div className="flex flex-col gap-5">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`rounded-full border px-3 py-1 text-xs font-medium ${statusTone(assignment.submission_status)}`}>
                      {assignment.submission_status.replace(/_/g, ' ')}
                    </span>
                    {assignment.grade !== null && assignment.grade !== undefined && (
                      <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600">
                        Grade {assignment.grade} / {assignment.max_grade ?? 100}
                      </span>
                    )}
                    {assignment.can_submit && (
                      <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600">
                        Submission open
                      </span>
                    )}
                  </div>

                  <h3 className="mt-4 text-xl font-semibold tracking-tight text-slate-950">{assignment.name}</h3>
                  <p className="mt-2 text-sm text-slate-500">
                    {assignment.course_name || `Course ${assignment.course_id}`}
                  </p>
                  {assignment.description && (
                    <p className="mt-3 max-w-4xl text-sm leading-7 text-slate-600">{assignment.description}</p>
                  )}
                </div>

                <div className="rounded-[24px] border border-slate-200 bg-slate-50/80 px-4 py-4 text-sm text-slate-500 md:min-w-[220px]">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Due date</p>
                  <p className="mt-3 font-medium text-slate-800">{formatDate(assignment.due_date)}</p>
                  {assignment.time_remaining && (
                    <p className="mt-2 text-sm text-slate-500">{assignment.time_remaining}</p>
                  )}
                </div>
              </div>

              {assignment.submitted_files && assignment.submitted_files.length > 0 && (
                <div className="rounded-[24px] border border-slate-200/80 bg-slate-50/70 px-4 py-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Submitted files</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {assignment.submitted_files.map((file, index) => (
                      <a
                        key={`${file.url}-${index}`}
                        href={`${LMS_FILE_DOWNLOAD_BASE}${encodeURIComponent(file.url)}`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition-all duration-200 hover:-translate-y-0.5 hover:border-slate-300"
                      >
                        Download {file.name}
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {assignment.can_submit && (
                <div className="rounded-[28px] border border-slate-200/80 bg-white">
                  <div className="border-b border-slate-200/80 px-5 py-4">
                    <p className="text-sm font-medium text-slate-800">
                      {assignment.submit_btn_text || 'Submit assignment'}
                    </p>
                  </div>

                  <div className="space-y-4 px-5 py-5">
                    <textarea
                      value={onlineTextById[assignment.id] || ''}
                      onChange={(e) =>
                        setOnlineTextById((current) => ({
                          ...current,
                          [assignment.id]: e.target.value,
                        }))
                      }
                      rows={5}
                      placeholder="Optional online text submission"
                      className="w-full rounded-[22px] border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-300"
                    />

                    <div className="flex flex-wrap items-center gap-3">
                      <input
                        type="file"
                        ref={(el) => { fileRefs.current[assignment.id] = el; }}
                        className="text-sm text-slate-600 file:mr-3 file:rounded-2xl file:border-0 file:bg-slate-100 file:px-4 file:py-2.5 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200"
                        accept=".pdf,.doc,.docx,.txt,.zip,.py,.java,.cpp,.c,.xlsx,.pptx"
                      />

                      <Button
                        variant="primary"
                        onClick={() => handleSubmit(assignment)}
                        disabled={submitting === assignment.id}
                        aria-label={`Submit ${assignment.name}`}
                      >
                        {submitting === assignment.id ? 'Submitting...' : 'Submit'}
                      </Button>
                    </div>

                    {submitMsg?.id === assignment.id && (
                      <p className={`text-sm ${submitMsg.ok ? 'text-emerald-600' : 'text-red-600'}`}>
                        {submitMsg.msg}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default function AssignmentsPage() {
  return (
    <Suspense fallback={<div className="app-page text-sm text-slate-500">Loading assignments...</div>}>
      <AssignmentsContent />
    </Suspense>
  );
}
