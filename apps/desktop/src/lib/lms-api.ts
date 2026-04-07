/**
 * LMS API client for the desktop app.
 * Uses Next.js proxy (/proxy/lms/*) to avoid CORS issues in the browser.
 * The proxy forwards to http://localhost:8002/api/lms/*
 */

// In browser: use the Next.js proxy. In Node/Electron: call directly.
const LMS_BASE =
  typeof window !== 'undefined'
    ? '/proxy/lms'
    : (process.env.NEXT_PUBLIC_LMS_SCRAPER_URL || 'http://localhost:8002') + '/api/lms';

async function lmsFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${LMS_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `LMS API error: ${res.status}`);
  }
  return res.json();
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface LMSProfile {
  name: string;
  email: string;
  userid: string;
}

export interface LMSCourse {
  id: number;
  name: string;
  code: string;
  url: string;
}

export interface LMSAssignment {
  id: number;
  name: string;
  course_id: number;
  due_date: string | null;
  submission_status: string;
  grading_status: string;
  grade: number | null;
  max_grade?: number;
  time_remaining: string;
  submitted_files: string[];
  can_submit: boolean;
  submit_btn_text?: string;
  description: string;
}

export interface LMSGrade {
  course_id: number;
  course_name: string;
  grade: number | null;
  grade_str: string;
}

export interface LMSCourseGrade {
  course_id: number;
  item_name: string;
  grade: number | null;
  max_grade: number | null;
  percentage: number | null;
}

export interface LMSEvent {
  name: string;
  event_type: string;
  course_name: string;
  date_str: string;
  date: string | null;
  url: string;
  full_text: string;
}

export interface LMSAnnouncement {
  course_id: number;
  title: string;
  author: string;
  date_str: string;
  date: string | null;
  url: string;
}

export interface LMSScrapeAll {
  profile: LMSProfile;
  courses: LMSCourse[];
  grades_overview: LMSGrade[];
  upcoming_events: LMSEvent[];
  assignments: LMSAssignment[];
  announcements: LMSAnnouncement[];
  course_grades: LMSCourseGrade[];
}

// ── API functions ─────────────────────────────────────────────────────────────

export const lmsApi = {
  getProfile: () => lmsFetch<LMSProfile>('/api/lms/profile'),

  getCourses: () => lmsFetch<LMSCourse[]>('/api/lms/courses'),

  getAssignments: (courseId: number) =>
    lmsFetch<LMSAssignment[]>(`/api/lms/assignments/${courseId}`),

  getGrades: () => lmsFetch<LMSGrade[]>('/api/lms/grades'),

  getCourseGrades: (courseId: number) =>
    lmsFetch<LMSCourseGrade[]>(`/api/lms/grades/${courseId}`),

  getEvents: () => lmsFetch<LMSEvent[]>('/api/lms/events'),

  getAnnouncements: (courseId: number) =>
    lmsFetch<LMSAnnouncement[]>(`/api/lms/announcements/${courseId}`),

  getAttendance: (courseId: number) =>
    lmsFetch<{ course_id: number; records: any[]; summary: any }>(
      `/api/lms/attendance/${courseId}`
    ),

  scrapeAll: () => lmsFetch<LMSScrapeAll>('/api/lms/scrape/all'),

  submitAssignment: async (
    assignmentId: number,
    file?: File,
    onlineText?: string
  ): Promise<{ success: boolean; message: string }> => {
    const form = new FormData();
    if (file) form.append('file', file);
    if (onlineText) form.append('online_text', onlineText);

    const base = typeof window !== 'undefined'
      ? '/proxy/lms'
      : (process.env.NEXT_PUBLIC_LMS_SCRAPER_URL || 'http://localhost:8002') + '/api/lms';

    const res = await fetch(
      `${base}/assignments/${assignmentId}/submit`,
      { method: 'POST', body: form }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      return { success: false, message: err.detail || 'Submission failed' };
    }
    return res.json();
  },
};
