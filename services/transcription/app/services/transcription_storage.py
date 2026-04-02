import psycopg2
from typing import List, Dict, Any
from uuid import UUID
import logging
from langchain_openai import OpenAIEmbeddings
from datetime import datetime

from app.config import get_settings
from app.models import TranscriptionSegment

logger = logging.getLogger(__name__)
settings = get_settings()


class TranscriptionStorageService:
    def __init__(self):
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
    
    async def store_transcription(
        self,
        recording_id: UUID,
        text: str,
        segments: List[TranscriptionSegment],
        language: str,
        duration: float
    ) -> bool:
        """
        Store transcription in database and generate embeddings
        
        Args:
            recording_id: Recording ID
            text: Full transcription text
            segments: List of transcription segments with timestamps
            language: Detected language
            duration: Audio duration in seconds
        
        Returns:
            True if successful
        """
        logger.info(f"Storing transcription for recording {recording_id}")
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Get recording info to find student_id
            cursor.execute("""
                SELECT student_id, course_id, title
                FROM lecture_recordings
                WHERE id = %s
            """, (str(recording_id),))
            
            result = cursor.fetchone()
            if not result:
                logger.error(f"Recording not found: {recording_id}")
                return False
            
            student_id, course_id, title = result
            
            # Update or insert transcription
            cursor.execute("""
                INSERT INTO transcriptions (recording_id, full_text, language, duration, transcribed_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (recording_id) 
                DO UPDATE SET 
                    full_text = EXCLUDED.full_text,
                    language = EXCLUDED.language,
                    duration = EXCLUDED.duration,
                    transcribed_at = EXCLUDED.transcribed_at
                RETURNING id
            """, (
                str(recording_id),
                text,
                language,
                duration,
                datetime.utcnow()
            ))
            
            transcription_id = cursor.fetchone()[0]
            
            # Delete existing segments
            cursor.execute("""
                DELETE FROM transcription_segments
                WHERE transcription_id = %s
            """, (transcription_id,))
            
            # Insert segments
            for segment in segments:
                cursor.execute("""
                    INSERT INTO transcription_segments 
                    (transcription_id, segment_text, start_time, end_time)
                    VALUES (%s, %s, %s, %s)
                """, (
                    transcription_id,
                    segment.text,
                    segment.start_time,
                    segment.end_time
                ))
            
            conn.commit()
            
            # Generate and store embeddings for segments
            await self._store_segment_embeddings(
                student_id=UUID(student_id),
                recording_id=recording_id,
                title=title,
                segments=segments
            )
            
            cursor.close()
            logger.info(f"Transcription stored successfully for recording {recording_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error storing transcription: {str(e)}", exc_info=True)
            if self.db_connection:
                self.db_connection.rollback()
            return False
    
    async def _store_segment_embeddings(
        self,
        student_id: UUID,
        recording_id: UUID,
        title: str,
        segments: List[TranscriptionSegment]
    ):
        """
        Generate and store embeddings for transcription segments
        
        Args:
            student_id: Student ID
            recording_id: Recording ID
            title: Lecture title
            segments: List of transcription segments
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Group segments into chunks (every 3 segments for better context)
            chunk_size = 3
            for i in range(0, len(segments), chunk_size):
                chunk_segments = segments[i:i + chunk_size]
                
                # Combine segment texts
                chunk_text = " ".join([seg.text for seg in chunk_segments])
                
                # Create content with context
                content = f"Lecture: {title}\nTranscript: {chunk_text}"
                
                # Generate embedding
                embedding = await self.embeddings.aembed_query(content)
                embedding_str = "[" + ",".join(map(str, embedding)) + "]"
                
                # Store embedding
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
                    "lecture",
                    f"{recording_id}_segment_{i}",
                    content,
                    {
                        "title": title,
                        "recording_id": str(recording_id),
                        "start_time": chunk_segments[0].start_time,
                        "end_time": chunk_segments[-1].end_time
                    },
                    embedding_str
                ))
            
            conn.commit()
            cursor.close()
            logger.info(f"Stored {len(segments)} segment embeddings for recording {recording_id}")
        
        except Exception as e:
            logger.error(f"Error storing segment embeddings: {str(e)}", exc_info=True)
            if self.db_connection:
                self.db_connection.rollback()
            raise
    
    async def get_transcription(self, recording_id: UUID) -> Dict[str, Any]:
        """
        Get transcription for a recording
        
        Args:
            recording_id: Recording ID
        
        Returns:
            Dictionary with transcription data
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Get transcription
            cursor.execute("""
                SELECT full_text, language, duration
                FROM transcriptions
                WHERE recording_id = %s
            """, (str(recording_id),))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            full_text, language, duration = result
            
            # Get segments
            cursor.execute("""
                SELECT segment_text, start_time, end_time
                FROM transcription_segments ts
                JOIN transcriptions t ON ts.transcription_id = t.id
                WHERE t.recording_id = %s
                ORDER BY start_time
            """, (str(recording_id),))
            
            segments = []
            for row in cursor.fetchall():
                segments.append(TranscriptionSegment(
                    text=row[0],
                    start_time=row[1],
                    end_time=row[2]
                ))
            
            cursor.close()
            
            return {
                "text": full_text,
                "segments": segments,
                "language": language,
                "duration": duration
            }
        
        except Exception as e:
            logger.error(f"Error getting transcription: {str(e)}", exc_info=True)
            return None
    
    def close(self):
        """Close database connection"""
        if self.db_connection and not self.db_connection.closed:
            self.db_connection.close()


# Singleton instance
_transcription_storage_service = None


def get_transcription_storage_service() -> TranscriptionStorageService:
    """Get transcription storage service singleton instance"""
    global _transcription_storage_service
    if _transcription_storage_service is None:
        _transcription_storage_service = TranscriptionStorageService()
    return _transcription_storage_service
