-- Migration: Add grades, schedule_events, and quizzes tables
-- Requirements: Iqra LMS scraper - real data storage

-- ============================================================================
-- GRADES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS grades (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id  UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_name VARCHAR(255) NOT NULL,
    item_name   VARCHAR(255) NOT NULL,
    grade       NUMERIC(6,2),
    max_grade   NUMERIC(6,2),
    percentage  NUMERIC(5,2),
    feedback    TEXT DEFAULT '',
    scraped_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_grades UNIQUE (student_id, course_name, item_name)
);

CREATE INDEX IF NOT EXISTS idx_grades_student ON grades(student_id);
CREATE INDEX IF NOT EXISTS idx_grades_course  ON grades(course_name);

CREATE TRIGGER update_grades_updated_at
    BEFORE UPDATE ON grades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE grades IS 'Student grades scraped from Iqra LMS grade reports';

-- ============================================================================
-- SCHEDULE_EVENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS schedule_events (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id     UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    event_name     VARCHAR(500) NOT NULL,
    event_type     VARCHAR(50)  NOT NULL DEFAULT 'other',
    course_name    VARCHAR(255) DEFAULT '',
    start_datetime TIMESTAMP,
    end_datetime   TIMESTAMP,
    description    TEXT DEFAULT '',
    url            VARCHAR(1000) DEFAULT '',
    scraped_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_schedule_events UNIQUE (student_id, event_name, start_datetime)
);

CREATE INDEX IF NOT EXISTS idx_schedule_student    ON schedule_events(student_id);
CREATE INDEX IF NOT EXISTS idx_schedule_start_date ON schedule_events(start_datetime);
CREATE INDEX IF NOT EXISTS idx_schedule_event_type ON schedule_events(event_type);

CREATE TRIGGER update_schedule_events_updated_at
    BEFORE UPDATE ON schedule_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE schedule_events IS 'Calendar events scraped from Iqra LMS (assignments due, quizzes, etc.)';

-- ============================================================================
-- QUIZZES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS quizzes (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id       UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_name      VARCHAR(255) NOT NULL,
    quiz_name        VARCHAR(500) NOT NULL,
    opens_at         TIMESTAMP,
    closes_at        TIMESTAMP,
    time_limit       INTEGER,   -- minutes
    attempts_allowed INTEGER,
    attempt_status   VARCHAR(50) DEFAULT 'not_attempted',
    best_grade       NUMERIC(6,2),
    url              VARCHAR(1000) DEFAULT '',
    scraped_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_quizzes UNIQUE (student_id, course_name, quiz_name)
);

CREATE INDEX IF NOT EXISTS idx_quizzes_student ON quizzes(student_id);
CREATE INDEX IF NOT EXISTS idx_quizzes_closes  ON quizzes(closes_at);

CREATE TRIGGER update_quizzes_updated_at
    BEFORE UPDATE ON quizzes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE quizzes IS 'Quiz activities scraped from Iqra LMS';

-- ============================================================================
-- COMPLETION
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✓ Migration 003 completed: grades, schedule_events, quizzes tables created';
END $$;
