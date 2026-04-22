// Student
export interface StudentDto {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  studentId: string;
  enrollmentDate: string;
}

// Course
export interface CourseDto {
  id: string;
  courseCode: string;
  courseName: string;
  instructor: string;
  semester: string;
  credits: number;
}

// Assignment
export interface AssignmentDto {
  id: string;
  courseId: string;
  courseCode: string;
  courseName: string;
  title: string;
  description: string;
  dueDate: string;
  maxScore: number;
  earnedScore?: number;
  status: 'pending' | 'submitted' | 'graded';
}

// Lecture Recording
export interface LectureRecordingDto {
  id: string;
  courseId: string;
  courseCode: string;
  courseName: string;
  title: string;
  recordingDate: string;
  recordingUrl?: string;
  duration?: number;
  source: 'zoom' | 'google_meet' | 'manual';
  hasTranscription: boolean;
}

// Transcription
export interface TranscriptionSegment {
  text: string;
  startTime: number;
  endTime: number;
}

export interface TranscriptionDto {
  recordingId: string;
  fullText: string;
  segments: TranscriptionSegment[];
  language: string;
  duration: number;
}

// Announcement
export interface AnnouncementDto {
  id: string;
  courseId?: string;
  courseCode?: string;
  courseName?: string;
  title: string;
  content: string;
  postedDate: string;
  priority: 'low' | 'normal' | 'high';
}

// Query
export interface SourceCitation {
  documentType: 'course' | 'assignment' | 'lecture' | 'announcement' | string;
  title: string;
  excerpt: string;
  url?: string;
}

export interface QueryResponseDto {
  answer: string;
  sources: SourceCitation[];
  confidenceScore: number;
}

export interface QueryRequestDto {
  query: string;
  type: 'text' | 'voice';
  audioData?: string; // Base64 encoded
}

// Authentication
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  student: StudentDto;
}

export interface RefreshTokenRequest {
  refreshToken: string;
}

export interface ValidateTokenResponse {
  isValid: boolean;
  studentId?: string;
}
