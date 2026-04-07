-- Migration 004: Performance indexes for common query patterns

-- Index for assignments ordered by due date (upcoming assignments query)
CREATE INDEX IF NOT EXISTS idx_assignments_due_date
    ON assignments (due_date ASC)
    WHERE due_date IS NOT NULL;

-- Index for courses by student (student course listing)
CREATE INDEX IF NOT EXISTS idx_courses_student
    ON student_courses (student_id, course_id);

-- Index for embeddings by student and source type (vector search filtering)
CREATE INDEX IF NOT EXISTS idx_embeddings_student_source
    ON document_embeddings (student_id, source_type);

-- IVFFlat index for vector similarity search
-- probes=10 balances recall vs speed for typical dataset sizes
CREATE INDEX IF NOT EXISTS idx_embeddings_vector
    ON document_embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Set IVFFlat probe count for this session (tune at query time)
-- This can also be set per-connection: SET ivfflat.probes = 10;
ALTER DATABASE edupilot SET ivfflat.probes = 10;

-- Index for announcements by course and date
CREATE INDEX IF NOT EXISTS idx_announcements_course_date
    ON announcements (course_id, posted_date DESC);

-- Index for grades by student
CREATE INDEX IF NOT EXISTS idx_grades_student
    ON grades (student_id, course_id);

-- Index for schedule events by student and start time
CREATE INDEX IF NOT EXISTS idx_schedule_events_student_time
    ON schedule_events (student_id, start_datetime ASC);
