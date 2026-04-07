"""
Embedding service for transcription segments.
After transcription completes, generates vector embeddings for each segment
and stores them in the document_embeddings table with source_type='transcription'.
"""

import logging
from typing import List
from uuid import UUID

import psycopg2
from langchain_openai import OpenAIEmbeddings

from app.config import get_settings
from app.models import TranscriptionSegment

logger = logging.getLogger(__name__)
settings = get_settings()

# Chunk size: combine N segments for better semantic context
SEGMENT_CHUNK_SIZE = 3


class EmbeddingService:
    """
    Generates and stores vector embeddings for transcription segments.
    Embeddings are stored in document_embeddings with source_type='transcription'.
    """

    def __init__(self):
        self._embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )
        self._db_conn = None

    def _get_db(self):
        if self._db_conn is None or self._db_conn.closed:
            self._db_conn = psycopg2.connect(settings.database_url)
        return self._db_conn

    async def generate_and_store(
        self,
        student_id: UUID,
        recording_id: UUID,
        title: str,
        segments: List[TranscriptionSegment],
    ) -> int:
        """
        Generate embeddings for transcription segments and store in DB.

        Args:
            student_id: The student who owns this recording.
            recording_id: The lecture recording ID.
            title: Lecture title for context.
            segments: Transcription segments with text and timestamps.

        Returns:
            Number of embedding chunks stored.
        """
        if not segments:
            logger.info("No segments to embed for recording %s", recording_id)
            return 0

        stored = 0
        conn = self._get_db()
        cursor = conn.cursor()

        try:
            for i in range(0, len(segments), SEGMENT_CHUNK_SIZE):
                chunk = segments[i : i + SEGMENT_CHUNK_SIZE]
                chunk_text = " ".join(seg.text for seg in chunk)
                content = f"Lecture: {title}\nTranscript: {chunk_text}"
                source_id = f"{recording_id}_seg_{i}"

                # Generate embedding
                embedding = await self._embeddings.aembed_query(content)
                embedding_str = "[" + ",".join(map(str, embedding)) + "]"

                metadata = {
                    "title": title,
                    "recording_id": str(recording_id),
                    "start_time": chunk[0].start_time,
                    "end_time": chunk[-1].end_time,
                    "segment_index": i,
                }

                cursor.execute(
                    """
                    INSERT INTO document_embeddings
                        (student_id, source_type, source_id, content, metadata, embedding)
                    VALUES (%s, 'transcription', %s, %s, %s, %s::vector)
                    ON CONFLICT (student_id, source_type, source_id)
                    DO UPDATE SET
                        content   = EXCLUDED.content,
                        metadata  = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (str(student_id), source_id, content, psycopg2.extras.Json(metadata), embedding_str),
                )
                stored += 1

            conn.commit()
            logger.info(
                "Stored %d transcription embedding chunks for recording %s (student %s)",
                stored, recording_id, student_id,
            )
        except Exception as exc:
            conn.rollback()
            logger.error("Error storing transcription embeddings: %s", exc, exc_info=True)
            raise
        finally:
            cursor.close()

        return stored

    def close(self):
        if self._db_conn and not self._db_conn.closed:
            self._db_conn.close()


# ── Singleton ─────────────────────────────────────────────────────────────────

_instance: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _instance
    if _instance is None:
        _instance = EmbeddingService()
    return _instance
