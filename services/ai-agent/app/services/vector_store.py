import psycopg2
from typing import List, Dict, Any
from uuid import UUID
import logging
from langchain_openai import OpenAIEmbeddings
from app.config import get_settings
from app.utils.retry import retry_on_api_error, retry_on_db_error

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStoreService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key
        )
        self.connection = None
    
    def _get_connection(self):
        """Get database connection"""
        if self.connection is None or self.connection.closed:
            self.connection = psycopg2.connect(settings.database_url)
        return self.connection
    
    def close(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()
    
    @retry_on_api_error(max_attempts=3)
    async def similarity_search(
        self,
        query: str,
        student_id: UUID,
        k: int = None,
        similarity_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search on document embeddings
        
        Args:
            query: Search query text
            student_id: Student ID for filtering
            k: Number of results to return (default from settings)
            similarity_threshold: Minimum similarity score (default from settings)
        
        Returns:
            List of documents with metadata and similarity scores
        """
        k = k or settings.max_search_results
        similarity_threshold = similarity_threshold or settings.similarity_threshold
        
        try:
            # Generate query embedding
            query_embedding = await self.embeddings.aembed_query(query)
            
            # Convert to pgvector format
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # Execute similarity search
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query_sql = """
                SELECT 
                    id,
                    student_id,
                    source_type,
                    source_id,
                    content,
                    metadata,
                    1 - (embedding <=> %s::vector) as similarity
                FROM document_embeddings
                WHERE student_id = %s
                    AND 1 - (embedding <=> %s::vector) >= %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            
            cursor.execute(
                query_sql,
                (embedding_str, str(student_id), embedding_str, similarity_threshold, embedding_str, k)
            )
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "student_id": row[1],
                    "source_type": row[2],
                    "source_id": row[3],
                    "content": row[4],
                    "metadata": row[5],
                    "similarity": float(row[6])
                })
            
            cursor.close()
            
            logger.info(f"Found {len(results)} documents for student {student_id}")
            return results
        
        except Exception as e:
            logger.error(f"Error performing similarity search: {str(e)}", exc_info=True)
            raise
    
    @retry_on_api_error(max_attempts=3)
    async def add_document(
        self,
        student_id: UUID,
        source_type: str,
        source_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Add a document to the vector store
        
        Args:
            student_id: Student ID
            source_type: Type of source (course, assignment, lecture, announcement)
            source_id: ID of the source
            content: Document content
            metadata: Additional metadata
        
        Returns:
            Document ID
        """
        try:
            # Generate embedding
            embedding = await self.embeddings.aembed_query(content)
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            
            # Insert into database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            insert_sql = """
                INSERT INTO document_embeddings 
                (student_id, source_type, source_id, content, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s::vector)
                RETURNING id
            """
            
            cursor.execute(
                insert_sql,
                (str(student_id), source_type, source_id, content, metadata, embedding_str)
            )
            
            doc_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            
            logger.info(f"Added document {doc_id} for student {student_id}")
            return str(doc_id)
        
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}", exc_info=True)
            if self.connection:
                self.connection.rollback()
            raise
    
    async def delete_documents_by_source(
        self,
        student_id: UUID,
        source_type: str,
        source_id: str
    ) -> int:
        """
        Delete documents by source
        
        Args:
            student_id: Student ID
            source_type: Type of source
            source_id: ID of the source
        
        Returns:
            Number of documents deleted
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            delete_sql = """
                DELETE FROM document_embeddings
                WHERE student_id = %s
                    AND source_type = %s
                    AND source_id = %s
            """
            
            cursor.execute(delete_sql, (str(student_id), source_type, source_id))
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            
            logger.info(f"Deleted {deleted_count} documents for source {source_id}")
            return deleted_count
        
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}", exc_info=True)
            if self.connection:
                self.connection.rollback()
            raise


# Singleton instance
_vector_store = None


def get_vector_store() -> VectorStoreService:
    """Get vector store singleton instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store
