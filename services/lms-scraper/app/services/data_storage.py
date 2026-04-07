"""
Data storage service for scraped Moodle data.
Stores all scraped data in PostgreSQL and generates vector embeddings.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None  # type: ignore

try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    OpenAIEmbeddings = None  # type: ignore

from app.config import get_settings
from app.models import (
    AnnouncementData,
    AssignmentData,
    CourseData,
    GradeData,
    QuizData,
    ScheduleEvent,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class DataStorageService:
    def __init__(self):
        if OpenAIEmbeddings and settings.openai_api_key and not settings.openai_api_key.startswith("sk-placeholder"):
            self.embeddings = OpenAIEmbeddings(
                model=settings.embedding_model,
                openai_api_key=settings.openai_api_key,
            )
        else:
            self.embeddings = None
        self._conn = None

    def _get_conn(self):
        if psycopg2 is None:
            raise RuntimeError("psycopg2 not installed")
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(
                settings.database_url,
                cursor_factory=psycopg2.extras.RealDictCursor,
            )
        return self._conn

    # ── Courses ───────────────────────────────────────────────────────────────

    async def store_courses(self, student_id: UUID, courses: List[CourseData]) -> int:
        logger.info(f"Storing {len(courses)} courses for student {student_id}")
        count = 0
        conn = self._get_conn()
        cur = conn.cursor()
        try:
            for c in courses:
                cur.execute(
                    """
                    INSERT INTO courses (course_code, course_name, instructor, semester, credits)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (course_code) DO UPDATE SET
                        course_name = EXCLUDED.course_name,
                        instructor  = EXCLUDED.instructor,
                        semester    = EXCLUDED.semester,
                        credits     = EXCLUDED.credits
                    RETURNING id
                    """,
                    (c.course_code, c.course_name, c.instructor, c.semester, c.credits),
                )
                row = cur.fetchone()
                db_course_id = row["id"]

                cur.execute(
                    """
                    INSERT INTO student_courses (student_id, course_id)
                    VALUES (%s, %s) ON CONFLICT DO NOTHING
                    """,
                    (str(student_id), db_course_id),
                )

                content = (
                    f"Course: {c.course_name} ({c.course_code})\n"
                    f"Instructor: {c.instructor}\nSemester: {c.semester}"
                )
                await self._store_embedding(
                    student_id, "course", str(db_course_id), content,
                    {"course_code": c.course_code, "course_name": c.course_name},
                )
                count += 1
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error storing courses: {e}", exc_info=True)
        finally:
            cur.close()
        return count

    # ── Assignments ───────────────────────────────────────────────────────────

    async def store_assignments(self, student_id: UUID, assignments: List[AssignmentData]) -> int:
        logger.info(f"Storing {len(assignments)} assignments for student {student_id}")
        count = 0
        conn = self._get_conn()
        cur = conn.cursor()
        try:
            for a in assignments:
                # Resolve DB course ID from Moodle course_id
                cur.execute(
                    "SELECT id FROM courses WHERE course_code = %s LIMIT 1",
                    (a.course_name,),  # fallback: match by name
                )
                row = cur.fetchone()
                if not row:
                    logger.debug(f"Course not found for assignment: {a.course_name}")
                    continue
                db_course_id = row["id"]

                cur.execute(
                    """
                    INSERT INTO assignments
                        (course_id, title, description, due_date, max_score, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (course_id, title) DO UPDATE SET
                        description = EXCLUDED.description,
                        due_date    = EXCLUDED.due_date,
                        max_score   = EXCLUDED.max_score,
                        status      = EXCLUDED.status
                    RETURNING id
                    """,
                    (
                        db_course_id, a.title, a.description,
                        a.due_date, a.max_score, a.submission_status,
                    ),
                )
                row = cur.fetchone()
                if not row:
                    continue
                assign_id = row["id"]

                content = (
                    f"Assignment: {a.title}\nCourse: {a.course_name}\n"
                    f"Description: {a.description}\nDue: {a.due_date}\n"
                    f"Status: {a.submission_status}"
                )
                await self._store_embedding(
                    student_id, "assignment", str(assign_id), content,
                    {"title": a.title, "course": a.course_name,
                     "due_date": str(a.due_date), "status": a.submission_status},
                )
                count += 1
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error storing assignments: {e}", exc_info=True)
        finally:
            cur.close()
        return count

    # ── Grades ────────────────────────────────────────────────────────────────

    async def store_grades(self, student_id: UUID, grades: List[GradeData]) -> int:
        logger.info(f"Storing {len(grades)} grade items for student {student_id}")
        count = 0
        conn = self._get_conn()
        cur = conn.cursor()
        try:
            for g in grades:
                cur.execute(
                    """
                    INSERT INTO grades
                        (student_id, course_name, item_name, grade, max_grade, percentage, feedback)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (student_id, course_name, item_name) DO UPDATE SET
                        grade      = EXCLUDED.grade,
                        max_grade  = EXCLUDED.max_grade,
                        percentage = EXCLUDED.percentage,
                        feedback   = EXCLUDED.feedback,
                        scraped_at = CURRENT_TIMESTAMP
                    RETURNING id
                    """,
                    (
                        str(student_id), g.course_name, g.item_name,
                        g.grade, g.max_grade, g.percentage, g.feedback,
                    ),
                )
                row = cur.fetchone()
                if not row:
                    continue
                grade_id = row["id"]

                content = (
                    f"Grade for {g.item_name} in {g.course_name}: "
                    f"{g.grade}/{g.max_grade} ({g.percentage}%)"
                )
                await self._store_embedding(
                    student_id, "grade", str(grade_id), content,
                    {"course": g.course_name, "item": g.item_name,
                     "grade": str(g.grade), "percentage": str(g.percentage)},
                )
                count += 1
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error storing grades: {e}", exc_info=True)
        finally:
            cur.close()
        return count

    # ── Announcements ─────────────────────────────────────────────────────────

    async def store_announcements(self, student_id: UUID, announcements: List[AnnouncementData]) -> int:
        logger.info(f"Storing {len(announcements)} announcements for student {student_id}")
        count = 0
        conn = self._get_conn()
        cur = conn.cursor()
        try:
            for ann in announcements:
                cur.execute(
                    "SELECT id FROM courses WHERE course_code = %s LIMIT 1",
                    (ann.course_name,),
                )
                row = cur.fetchone()
                db_course_id = row["id"] if row else None

                cur.execute(
                    """
                    INSERT INTO announcements
                        (course_id, title, content, posted_date, priority)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (course_id, title, posted_date) DO NOTHING
                    RETURNING id
                    """,
                    (db_course_id, ann.title, ann.content, ann.posted_date, ann.priority),
                )
                row = cur.fetchone()
                if not row:
                    continue
                ann_id = row["id"]

                content = (
                    f"Announcement: {ann.title}\nCourse: {ann.course_name}\n"
                    f"By: {ann.author}\n{ann.content}"
                )
                await self._store_embedding(
                    student_id, "announcement", str(ann_id), content,
                    {"title": ann.title, "course": ann.course_name, "priority": ann.priority},
                )
                count += 1
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error storing announcements: {e}", exc_info=True)
        finally:
            cur.close()
        return count

    # ── Schedule Events ───────────────────────────────────────────────────────

    async def store_schedule_events(self, student_id: UUID, events: List[ScheduleEvent]) -> int:
        logger.info(f"Storing {len(events)} schedule events for student {student_id}")
        count = 0
        conn = self._get_conn()
        cur = conn.cursor()
        try:
            for ev in events:
                cur.execute(
                    """
                    INSERT INTO schedule_events
                        (student_id, event_name, event_type, course_name,
                         start_datetime, end_datetime, description, url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (student_id, event_name, start_datetime) DO UPDATE SET
                        event_type  = EXCLUDED.event_type,
                        course_name = EXCLUDED.course_name,
                        scraped_at  = CURRENT_TIMESTAMP
                    RETURNING id
                    """,
                    (
                        str(student_id), ev.event_name, ev.event_type,
                        ev.course_name, ev.start_datetime, ev.end_datetime,
                        ev.description, ev.url,
                    ),
                )
                row = cur.fetchone()
                if not row:
                    continue
                ev_id = row["id"]

                content = (
                    f"Event: {ev.event_name} on {ev.start_datetime} "
                    f"for {ev.course_name} (type: {ev.event_type})"
                )
                await self._store_embedding(
                    student_id, "schedule_event", str(ev_id), content,
                    {"event": ev.event_name, "course": ev.course_name,
                     "type": ev.event_type, "date": str(ev.start_datetime)},
                )
                count += 1
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error storing schedule events: {e}", exc_info=True)
        finally:
            cur.close()
        return count

    # ── Quizzes ───────────────────────────────────────────────────────────────

    async def store_quizzes(self, student_id: UUID, quizzes: List[QuizData]) -> int:
        logger.info(f"Storing {len(quizzes)} quizzes for student {student_id}")
        count = 0
        conn = self._get_conn()
        cur = conn.cursor()
        try:
            for q in quizzes:
                cur.execute(
                    """
                    INSERT INTO quizzes
                        (student_id, course_name, quiz_name, opens_at, closes_at,
                         time_limit, attempts_allowed, attempt_status, best_grade, url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (student_id, course_name, quiz_name) DO UPDATE SET
                        opens_at        = EXCLUDED.opens_at,
                        closes_at       = EXCLUDED.closes_at,
                        attempt_status  = EXCLUDED.attempt_status,
                        best_grade      = EXCLUDED.best_grade,
                        scraped_at      = CURRENT_TIMESTAMP
                    RETURNING id
                    """,
                    (
                        str(student_id), q.course_name, q.quiz_name,
                        q.opens_at, q.closes_at, q.time_limit,
                        q.attempts_allowed, q.attempt_status, q.best_grade, q.url,
                    ),
                )
                row = cur.fetchone()
                if not row:
                    continue
                quiz_id = row["id"]

                content = (
                    f"Quiz: {q.quiz_name} in {q.course_name}. "
                    f"Opens: {q.opens_at}, Closes: {q.closes_at}. "
                    f"Status: {q.attempt_status}"
                )
                await self._store_embedding(
                    student_id, "quiz", str(quiz_id), content,
                    {"quiz": q.quiz_name, "course": q.course_name,
                     "status": q.attempt_status},
                )
                count += 1
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error storing quizzes: {e}", exc_info=True)
        finally:
            cur.close()
        return count

    # ── Embeddings ────────────────────────────────────────────────────────────

    async def _store_embedding(
        self,
        student_id: UUID,
        source_type: str,
        source_id: str,
        content: str,
        metadata: Dict[str, Any],
    ):
        try:
            embedding = await self.embeddings.aembed_query(content)
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"

            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO document_embeddings
                    (student_id, source_type, source_id, content, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT (student_id, source_type, source_id) DO UPDATE SET
                    content    = EXCLUDED.content,
                    metadata   = EXCLUDED.metadata,
                    embedding  = EXCLUDED.embedding,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    str(student_id), source_type, source_id,
                    content, json.dumps(metadata), embedding_str,
                ),
            )
            cur.close()
        except Exception as e:
            logger.error(f"Error storing embedding for {source_type}/{source_id}: {e}")

    async def get_embedding_counts(self, student_id: UUID) -> Dict[str, int]:
        """Return embedding counts per source_type for a student."""
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT source_type, COUNT(*) AS cnt
                FROM document_embeddings
                WHERE student_id = %s
                GROUP BY source_type
                """,
                (str(student_id),),
            )
            rows = cursor.fetchall()
            return {row["source_type"]: row["cnt"] for row in rows}
        except Exception as e:
            logger.error(f"Error fetching embedding counts for student {student_id}: {e}")
            return {}
        finally:
            cursor.close()

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()


# ── Singleton ─────────────────────────────────────────────────────────────────

_instance: Optional[DataStorageService] = None


def get_data_storage_service() -> DataStorageService:
    global _instance
    if _instance is None:
        _instance = DataStorageService()
    return _instance
