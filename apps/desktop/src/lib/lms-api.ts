const LMS_BASE = process.env.NEXT_PUBLIC_LMS_SCRAPER_URL || '/proxy/lms';

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
  course_name?: string;
  due_date: string | null;
  submission_status: string;
  grading_status: string;
  grade: number | null;
  max_grade?: number;
  time_remaining: string;
  submitted_files: Array<{
    name: string;
    url: string;
  }>;
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

export interface LMSQuerySource {
  title: string;
  source_type: string;
  url?: string | null;
}

export interface LMSQueryResponse {
  answer: string;
  confidence: number;
  sources: LMSQuerySource[];
}

export interface LMSRuntimeAIOptions {
  ai_provider?: 'gemini' | 'openai' | 'deepseek';
  api_key?: string;
  model?: string;
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
  // ── Login ──────────────────────────────────────────────────────────────────

  startLogin: (email: string, password: string) =>
    lmsFetch<{ status: string; message: string }>('/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  getLoginStatus: () =>
    lmsFetch<{
      status: 'idle' | 'logging_in' | 'mfa_pending' | 'logged_in' | 'failed';
      mfa_number: string | null;
      error: string | null;
      profile: LMSProfile | null;
    }>('/login/status'),

  clearSession: () =>
    lmsFetch<{ message: string }>('/login/clear', { method: 'POST' }),

  // ── Data ───────────────────────────────────────────────────────────────────

  getProfile: () => lmsFetch<LMSProfile>('/profile'),

  getCourses: () => lmsFetch<LMSCourse[]>('/courses'),

  getAllAssignments: () => lmsFetch<LMSAssignment[]>('/assignments/all'),

  getAssignments: (courseId: number) =>
    lmsFetch<LMSAssignment[]>(`/assignments/${courseId}`),

  getGrades: () => lmsFetch<LMSGrade[]>('/grades'),

  getCourseGrades: (courseId: number) =>
    lmsFetch<LMSCourseGrade[]>(`/grades/${courseId}`),

  getEvents: () => lmsFetch<LMSEvent[]>('/events'),

  getAnnouncements: (courseId: number) =>
    lmsFetch<LMSAnnouncement[]>(`/announcements/${courseId}`),

  getAttendance: (courseId: number) =>
    lmsFetch<{ course_id: number; records: any[]; summary: any }>(
      `/attendance/${courseId}`
    ),

  scrapeAll: () => lmsFetch<LMSScrapeAll>('/scrape/all'),

  queryAI: (
    query: string,
    type: 'text' | 'voice' = 'text',
    aiOptions?: LMSRuntimeAIOptions
  ) =>
    lmsFetch<LMSQueryResponse>('/query', {
      method: 'POST',
      body: JSON.stringify({ query, type, ...aiOptions }),
    }),

  submitAssignment: async (
    assignmentId: number,
    file?: File,
    onlineText?: string
  ): Promise<{ success: boolean; message: string }> => {
    const form = new FormData();
    if (file) form.append('file', file);
    if (onlineText) form.append('online_text', onlineText);

    const base = process.env.NEXT_PUBLIC_LMS_SCRAPER_URL || '/proxy/lms';

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
