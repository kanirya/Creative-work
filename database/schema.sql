-- EduPilot Database Schema
-- PostgreSQL 16 with pgvector extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================================================
-- STUDENTS TABLE
-- ============================================================================
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    university_id VARCHAR(50) UNIQUE NOT NULL,
    enrolled_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_students_email ON students(email);
CREATE INDEX idx_students_university_id ON students(university_id);
CREATE INDEX idx_students_is_active ON students(is_active);

CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COURSES TABLE
-- ============================================================================
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    instructor VARCHAR(255),
    semester VARCHAR(50) NOT NULL,
    credit_hours INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_courses_code ON courses(code);
CREATE INDEX idx_courses_semester ON courses(semester);

CREATE TRIGGER update_courses_updated_at BEFORE UPDATE ON courses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- STUDENT_COURSES JUNCTION TABLE
-- ============================================================================
CREATE TABLE student_courses (
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id, course_id)
);

CREATE INDEX idx_student_courses_student ON student_courses(student_id);
CREATE INDEX idx_student_courses_course ON student_courses(course_id);

-- ============================================================================
-- ASSIGNMENTS TABLE
-- ============================================================================
CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date TIMESTAMP NOT NULL,
    max_points INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_assignment_status CHECK (status IN ('pending', 'submitted', 'late', 'graded'))
);

CREATE INDEX idx_assignments_course ON assignments(course_id);
CREATE INDEX idx_assignments_due_date ON assignments(due_date);
CREATE INDEX idx_assignments_status ON assignments(status);

CREATE TRIGGER update_assignments_updated_at BEFORE UPDATE ON assignments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- STUDENT_ASSIGNMENTS TABLE
-- ============================================================================
CREATE TABLE student_assignments (
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    assignment_id UUID REFERENCES assignments(id) ON DELETE CASCADE,
    points_earned DECIMAL(5,2),
    submitted_at TIMESTAMP,
    graded_at TIMESTAMP,
    PRIMARY KEY (student_id, assignment_id)
);

CREATE INDEX idx_student_assignments_student ON student_assignments(student_id);
CREATE INDEX idx_student_assignments_assignment ON student_assignments(assignment_id);

-- ============================================================================
-- LECTURE_RECORDINGS TABLE
-- ============================================================================
CREATE TABLE lecture_recordings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    recorded_at TIMESTAMP NOT NULL,
    duration_seconds INTEGER NOT NULL,
    storage_url TEXT NOT NULL,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_recording_source CHECK (source IN ('Zoom', 'GoogleMeet', 'Manual'))
);

CREATE INDEX idx_recordings_course ON lecture_recordings(course_id);
CREATE INDEX idx_recordings_date ON lecture_recordings(recorded_at DESC);
CREATE INDEX idx_recordings_source ON lecture_recordings(source);

-- ============================================================================
-- TRANSCRIPTIONS TABLE
-- ============================================================================
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recording_id UUID REFERENCES lecture_recordings(id) ON DELETE CASCADE,
    full_text TEXT NOT NULL,
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    transcribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transcriptions_recording ON transcriptions(recording_id);
CREATE INDEX idx_transcriptions_language ON transcriptions(language);

-- ============================================================================
-- TRANSCRIPTION_SEGMENTS TABLE
-- ============================================================================
CREATE TABLE transcription_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcription_id UUID REFERENCES transcriptions(id) ON DELETE CASCADE,
    start_time_seconds DECIMAL(10,2) NOT NULL,
    end_time_seconds DECIMAL(10,2) NOT NULL,
    text TEXT NOT NULL,
    CONSTRAINT chk_segment_times CHECK (end_time_seconds > start_time_seconds)
);

CREATE INDEX idx_segments_transcription ON transcription_segments(transcription_id);
CREATE INDEX idx_segments_start_time ON transcription_segments(start_time_seconds);

-- ============================================================================
-- ANNOUNCEMENTS TABLE
-- ============================================================================
CREATE TABLE announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    posted_at TIMESTAMP NOT NULL,
    priority VARCHAR(20) DEFAULT 'Normal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_announcement_priority CHECK (priority IN ('Low', 'Normal', 'High', 'Urgent'))
);

CREATE INDEX idx_announcements_course ON announcements(course_id);
CREATE INDEX idx_announcements_posted ON announcements(posted_at DESC);
CREATE INDEX idx_announcements_priority ON announcements(priority);

-- ============================================================================
-- DOCUMENT_EMBEDDINGS TABLE (pgvector for RAG)
-- ============================================================================
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,
    document_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_document_type CHECK (document_type IN ('course', 'assignment', 'transcription', 'announcement'))
);

-- Create IVFFlat index for vector similarity search
CREATE INDEX idx_embeddings_vector ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX idx_embeddings_student ON document_embeddings(student_id);
CREATE INDEX idx_embeddings_type ON document_embeddings(document_type);
CREATE INDEX idx_embeddings_document ON document_embeddings(document_id);
CREATE INDEX idx_embeddings_metadata ON document_embeddings USING gin(metadata);

-- ============================================================================
-- REFRESH_TOKENS TABLE
-- ============================================================================
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP
);

CREATE INDEX idx_refresh_tokens_student ON refresh_tokens(student_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);

-- ============================================================================
-- SYNC_LOGS TABLE
-- ============================================================================
CREATE TABLE sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    records_updated INTEGER DEFAULT 0,
    error_message TEXT,
    CONSTRAINT chk_sync_status CHECK (status IN ('success', 'failed', 'partial'))
);

CREATE INDEX idx_sync_logs_student ON sync_logs(student_id);
CREATE INDEX idx_sync_logs_synced_at ON sync_logs(synced_at DESC);
CREATE INDEX idx_sync_logs_status ON sync_logs(status);

-- ============================================================================
-- JOB_EXECUTIONS TABLE
-- ============================================================================
CREATE TABLE job_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(50) NOT NULL,
    job_id VARCHAR(100) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    metadata JSONB,
    CONSTRAINT chk_job_status CHECK (status IN ('running', 'completed', 'failed'))
);

CREATE INDEX idx_job_executions_type ON job_executions(job_type);
CREATE INDEX idx_job_executions_started ON job_executions(started_at DESC);
CREATE INDEX idx_job_executions_status ON job_executions(status);

-- ============================================================================
-- SEED DATA (Optional - for development)
-- ============================================================================

-- Insert a test student
-- Note: Password hash uses BCrypt $2y$ format compatible with BCrypt.Net-Next 4.0.2+
-- Password: password
INSERT INTO students (email, password_hash, first_name, last_name, university_id, enrolled_at)
VALUES (
    'test@iqra.edu.pk',
    '$2y$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
    'Test',
    'Student',
    'IU2024001',
    CURRENT_TIMESTAMP
) ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash;

-- Insert sample courses
INSERT INTO courses (code, name, instructor, semester, credit_hours)
VALUES 
    ('CS101', 'Introduction to Computer Science', 'Dr. Ahmed Khan', 'Fall 2024', 3),
    ('MATH201', 'Calculus II', 'Dr. Sarah Ali', 'Fall 2024', 4),
    ('ENG102', 'English Composition', 'Prof. Maria Ahmed', 'Fall 2024', 3);

-- Link student to courses
INSERT INTO student_courses (student_id, course_id)
SELECT s.id, c.id
FROM students s
CROSS JOIN courses c
WHERE s.email = 'test@iqra.edu.pk';

-- Insert sample assignments
INSERT INTO assignments (course_id, title, description, due_date, max_points, status)
SELECT 
    c.id,
    'Assignment 1: ' || c.name,
    'Complete the first assignment for ' || c.name,
    CURRENT_TIMESTAMP + INTERVAL '7 days',
    100,
    'pending'
FROM courses c;

-- Insert sample announcement
INSERT INTO announcements (course_id, title, content, posted_at, priority)
SELECT 
    c.id,
    'Welcome to ' || c.name,
    'Welcome to the course! Please review the syllabus and complete the first assignment.',
    CURRENT_TIMESTAMP,
    'normal'
FROM courses c
LIMIT 1;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View for student dashboard data
CREATE OR REPLACE VIEW student_dashboard AS
SELECT 
    s.id as student_id,
    s.first_name,
    s.last_name,
    s.email,
    COUNT(DISTINCT sc.course_id) as total_courses,
    COUNT(DISTINCT CASE WHEN a.status = 'pending' THEN a.id END) as pending_assignments,
    COUNT(DISTINCT CASE WHEN a.due_date < CURRENT_TIMESTAMP AND a.status = 'pending' THEN a.id END) as overdue_assignments
FROM students s
LEFT JOIN student_courses sc ON s.id = sc.student_id
LEFT JOIN assignments a ON sc.course_id = a.course_id
WHERE s.is_active = true
GROUP BY s.id, s.first_name, s.last_name, s.email;

-- View for upcoming deadlines
CREATE OR REPLACE VIEW upcoming_deadlines AS
SELECT 
    s.id as student_id,
    a.id as assignment_id,
    a.title,
    a.due_date,
    c.name as course_name,
    c.code as course_code,
    a.max_points,
    a.status
FROM students s
JOIN student_courses sc ON s.id = sc.student_id
JOIN courses c ON sc.course_id = c.id
JOIN assignments a ON c.id = a.course_id
WHERE a.due_date > CURRENT_TIMESTAMP
  AND a.status IN ('pending', 'submitted')
ORDER BY a.due_date ASC;

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant permissions to edupilot user (adjust as needed)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO edupilot;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO edupilot;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO edupilot;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE students IS 'Stores student account information and credentials';
COMMENT ON TABLE courses IS 'Stores course information from LMS';
COMMENT ON TABLE assignments IS 'Stores assignment information with deadlines';
COMMENT ON TABLE lecture_recordings IS 'Stores lecture recording metadata from Zoom/Google Meet';
COMMENT ON TABLE transcriptions IS 'Stores full transcriptions of lecture recordings';
COMMENT ON TABLE document_embeddings IS 'Stores vector embeddings for RAG semantic search';
COMMENT ON TABLE sync_logs IS 'Tracks LMS synchronization history';
COMMENT ON TABLE job_executions IS 'Tracks background job execution history';

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✓ EduPilot database schema created successfully!';
    RAISE NOTICE '  - Tables: %', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE');
    RAISE NOTICE '  - Indexes: %', (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public');
    RAISE NOTICE '  - Extensions: uuid-ossp, vector';
END $$;
