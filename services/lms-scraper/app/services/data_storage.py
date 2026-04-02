import httpx
import psycopg2
from typing import List, Dict, Any
from uuid import UUID
import logging
from langchain_openai import OpenAIEmbeddings

from app.config import get_settings
from app.models import CourseData, AssignmentData, AnnouncementData

logger = logging.getLogger(__name__)
settings = get_settings()


class DataStorageService:
    def __init__(self):
        self.api_gateway_url = settings.api_gateway_url
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key
        )
        self.db_connection = None
    
    def _get_db_connection(self):
        """Get database connection"""
        if self.db_connection is None or self.db_connection.closed:
            self.db_connection = psycopg2.connect(settings.database_url)
        return self.db_connection
    
    async def store_courses(self, student_id: UUID, courses: List[CourseData]) -> int:
        """
        Store courses in database and generate embeddings
        
        Args:
            student_id: Student ID
            courses: List of CourseData objects
        
        Returns:
            Number of courses stored
        """
        logger.info(f"Storing {len(courses)} courses for student {student_id}")
        stored_count = 0
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            for course in courses:
                try:
                    # Insert or update course
                    cursor.execute("""
                        INSERT INTO courses (course_code, course_name, instructor, semester, credits)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (course_code) 
                        DO UPDATE SET 
                            course_name = EXCLUDED.course_name,
                            instructor = EXCLUDED.instructor,
                            semester = EXCLUDED.semester,
                            credits = EXCLUDED.credits
                        RETURNING id
                    """, (
                        course.course_code,
                        course.course_name,
                        course.instructor,
                        course.semester,
                        course.credits
                    ))
                    
                    course_id = cursor.fetchone()[0]
                    
                    # Link student to course
                    cursor.execute("""
                        INSERT INTO student_courses (student_id, course_id)
                        VALUES (%s, %s)
                        ON CONFLICT (student_id, course_id) DO NOTHING
                    """, (str(student_id), course_id))
                    
                    # Generate embedding for course content
                    content = f"Course: {course.course_name} ({course.course_code})\nInstructor: {course.instructor}\nSemester: {course.semester}"
                    await self._store_embedding(
                        student_id=student_id,
                        source_type="course",
                        source_id=str(course_id),
                        content=content,
                        metadata={
                            "course_code": course.course_code,
                            "course_name": course.course_name,
                            "instructor": course.instructor,
                            "semester": course.semester
                        }
                    )
                    
                    stored_count += 1
                    logger.info(f"Stored course: {course.course_code}")
                
                except Exception as e:
                    logger.error(f"Error storing course {course.course_code}: {str(e)}")
                    continue
            
            conn.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error storing courses: {str(e)}", exc_info=True)
            if self.db_connection:
                self.db_connection.rollback()
        
        return stored_count
    
    async def store_assignments(self, student_id: UUID, assignments: List[AssignmentData]) -> int:
        """
        Store assignments in database and generate embeddings
        
        Args:
            student_id: Student ID
            assignments: List of AssignmentData objects
        
        Returns:
            Number of assignments stored
        """
        logger.info(f"Storing {len(assignments)} assignments for student {student_id}")
        stored_count = 0
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            for assignment in assignments:
                try:
                    # Get course_id from course_code
                    cursor.execute("SELECT id FROM courses WHERE course_code = %s", (assignment.course_code,))
                    result = cursor.fetchone()
                    if not result:
                        logger.warning(f"Course not found: {assignment.course_code}")
                        continue
                    
                    course_id = result[0]
                    
                    # Insert or update assignment
                    cursor.execute("""
                        INSERT INTO assignments (course_id, title, description, due_date, max_score, status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (course_id, title) 
                        DO UPDATE SET 
                            description = EXCLUDED.description,
                            due_date = EXCLUDED.due_date,
                            max_score = EXCLUDED.max_score,
                            status = EXCLUDED.status
                        RETURNING id
                    """, (
                        course_id,
                        assignment.title,
                        assignment.description,
                        assignment.due_date,
                        assignment.max_score,
                        assignment.status
                    ))
                    
                    assignment_id = cursor.fetchone()[0]
                    
                    # Generate embedding for assignment content
                    content = f"Assignment: {assignment.title}\nCourse: {assignment.course_code}\nDescription: {assignment.description}\nDue Date: {assignment.due_date}"
                    await self._store_embedding(
                        student_id=student_id,
                        source_type="assignment",
                        source_id=str(assignment_id),
                        content=content,
                        metadata={
                            "title": assignment.title,
                            "course_code": assignment.course_code,
                            "due_date": assignment.due_date.isoformat(),
                            "status": assignment.status
                        }
                    )
                    
                    stored_count += 1
                    logger.info(f"Stored assignment: {assignment.title}")
                
                except Exception as e:
                    logger.error(f"Error storing assignment {assignment.title}: {str(e)}")
                    continue
            
            conn.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error storing assignments: {str(e)}", exc_info=True)
            if self.db_connection:
                self.db_connection.rollback()
        
        return stored_count
    
    async def store_announcements(self, student_id: UUID, announcements: List[AnnouncementData]) -> int:
        """
        Store announcements in database and generate embeddings
        
        Args:
            student_id: Student ID
            announcements: List of AnnouncementData objects
        
        Returns:
            Number of announcements stored
        """
        logger.info(f"Storing {len(announcements)} announcements for student {student_id}")
        stored_count = 0
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            for announcement in announcements:
                try:
                    # Get course_id from course_code
                    cursor.execute("SELECT id FROM courses WHERE course_code = %s", (announcement.course_code,))
                    result = cursor.fetchone()
                    course_id = result[0] if result else None
                    
                    # Insert announcement
                    cursor.execute("""
                        INSERT INTO announcements (course_id, title, content, posted_date, priority)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (course_id, title, posted_date) DO NOTHING
                        RETURNING id
                    """, (
                        course_id,
                        announcement.title,
                        announcement.content,
                        announcement.posted_date,
                        announcement.priority
                    ))
                    
                    result = cursor.fetchone()
                    if not result:
                        continue
                    
                    announcement_id = result[0]
                    
                    # Generate embedding for announcement content
                    content = f"Announcement: {announcement.title}\nCourse: {announcement.course_code}\nContent: {announcement.content}"
                    await self._store_embedding(
                        student_id=student_id,
                        source_type="announcement",
                        source_id=str(announcement_id),
                        content=content,
                        metadata={
                            "title": announcement.title,
                            "course_code": announcement.course_code,
                            "priority": announcement.priority,
                            "posted_date": announcement.posted_date.isoformat()
                        }
                    )
                    
                    stored_count += 1
                    logger.info(f"Stored announcement: {announcement.title}")
                
                except Exception as e:
                    logger.error(f"Error storing announcement {announcement.title}: {str(e)}")
                    continue
            
            conn.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error storing announcements: {str(e)}", exc_info=True)
            if self.db_connection:
                self.db_connection.rollback()
        
        return stored_count
    
    async def _store_embedding(
        self,
        student_id: UUID,
        source_type: str,
        source_id: str,
        content: str,
        metadata: Dict[str, Any]
    ):
        """
        Generate and store embedding for content
        
        Args:
            student_id: Student ID
            source_type: Type of source (course, assignment, announcement, lecture)
            source_id: ID of the source
            content: Content to embed
            metadata: Additional metadata
        """
        try:
            # Generate embedding
            embedding = await self.embeddings.aembed_query(content)
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            
            # Store in database
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO document_embeddings 
                (student_id, source_type, source_id, content, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT (student_id, source_type, source_id) 
                DO UPDATE SET 
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                str(student_id),
                source_type,
                source_id,
                content,
                metadata,
                embedding_str
            ))
            
            cursor.close()
            logger.debug(f"Stored embedding for {source_type} {source_id}")
        
        except Exception as e:
            logger.error(f"Error storing embedding: {str(e)}", exc_info=True)
            raise
    
    def close(self):
        """Close database connection"""
        if self.db_connection and not self.db_connection.closed:
            self.db_connection.close()


# Singleton instance
_data_storage_service = None


def get_data_storage_service() -> DataStorageService:
    """Get data storage service singleton instance"""
    global _data_storage_service
    if _data_storage_service is None:
        _data_storage_service = DataStorageService()
    return _data_storage_service
