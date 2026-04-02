from typing import List, Dict, Any
from uuid import UUID
import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

from app.config import get_settings
from app.services.vector_store import get_vector_store
from app.models import QueryResponse, SourceCitation
from app.utils.retry import retry_on_api_error

logger = logging.getLogger(__name__)
settings = get_settings()


class QueryProcessor:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.max_tokens,
            openai_api_key=settings.openai_api_key
        )
        self.vector_store = get_vector_store()
    
    async def process_query(
        self,
        query: str,
        student_id: UUID,
        correlation_id: str = None
    ) -> QueryResponse:
        """
        Process a query using RAG (Retrieval-Augmented Generation)
        
        Args:
            query: User's natural language query
            student_id: Student ID for context filtering
            correlation_id: Request correlation ID
        
        Returns:
            QueryResponse with answer, sources, and confidence
        """
        try:
            # Step 1: Retrieve relevant documents
            logger.info(f"Retrieving documents for query: {query[:50]}...")
            documents = await self.vector_store.similarity_search(
                query=query,
                student_id=student_id
            )
            
            if not documents:
                logger.warning(f"No relevant documents found for student {student_id}")
                return QueryResponse(
                    answer="I couldn't find any relevant information in your course materials to answer this question. Please try rephrasing your question or contact your instructor.",
                    sources=[],
                    confidence=0.0,
                    correlation_id=correlation_id
                )
            
            # Step 2: Build context from retrieved documents
            context = self._build_context(documents)
            
            # Step 3: Generate answer using LLM
            logger.info("Generating answer with LLM...")
            answer = await self._generate_answer(query, context)
            
            # Step 4: Extract source citations
            sources = self._extract_sources(documents)
            
            # Step 5: Calculate confidence score
            confidence = self._calculate_confidence(documents)
            
            # Add low confidence warning if needed
            if confidence < 0.5:
                answer = f"⚠️ Low confidence answer - please verify with your instructor.\n\n{answer}"
            
            return QueryResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                correlation_id=correlation_id
            )
        
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            raise
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved documents"""
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            source_type = doc.get("source_type", "unknown")
            metadata = doc.get("metadata", {})
            content = doc.get("content", "")
            
            # Format based on source type
            if source_type == "course":
                header = f"Course: {metadata.get('course_name', 'Unknown')}"
            elif source_type == "assignment":
                header = f"Assignment: {metadata.get('title', 'Unknown')}"
            elif source_type == "lecture":
                header = f"Lecture: {metadata.get('title', 'Unknown')}"
            elif source_type == "announcement":
                header = f"Announcement: {metadata.get('title', 'Unknown')}"
            else:
                header = f"Document {i}"
            
            context_parts.append(f"[{header}]\n{content}\n")
        
        return "\n".join(context_parts)
    
    @retry_on_api_error(max_attempts=3)
    async def _generate_answer(self, query: str, context: str) -> str:
        """Generate answer using LLM with context"""
        system_prompt = """You are EduPilot, an AI assistant for university students. 
Your role is to help students understand their course materials, assignments, and lectures.

Guidelines:
- Provide clear, accurate answers based on the provided context
- If the context doesn't contain enough information, say so
- Cite specific sources when possible
- Be concise but thorough
- Use a friendly, supportive tone
- If asked about deadlines or dates, be precise
- For technical topics, explain concepts clearly"""

        user_prompt = f"""Context from student's course materials:
{context}

Student's question: {query}

Please provide a helpful answer based on the context above."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    def _extract_sources(self, documents: List[Dict[str, Any]]) -> List[SourceCitation]:
        """Extract source citations from documents"""
        sources = []
        
        for doc in documents:
            metadata = doc.get("metadata", {})
            content = doc.get("content", "")
            
            # Create excerpt (first 200 characters)
            excerpt = content[:200] + "..." if len(content) > 200 else content
            
            # Get title based on source type
            source_type = doc.get("source_type", "unknown")
            if source_type == "course":
                title = metadata.get("course_name", "Unknown Course")
            elif source_type == "assignment":
                title = metadata.get("title", "Unknown Assignment")
            elif source_type == "lecture":
                title = metadata.get("title", "Unknown Lecture")
            elif source_type == "announcement":
                title = metadata.get("title", "Unknown Announcement")
            else:
                title = "Unknown Source"
            
            sources.append(SourceCitation(
                source_type=source_type,
                source_id=doc.get("source_id", ""),
                title=title,
                excerpt=excerpt,
                similarity_score=doc.get("similarity", 0.0)
            ))
        
        return sources
    
    def _calculate_confidence(self, documents: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence score based on document similarity scores
        
        Confidence is based on:
        - Average similarity score of top documents
        - Number of relevant documents found
        """
        if not documents:
            return 0.0
        
        # Get similarity scores
        similarities = [doc.get("similarity", 0.0) for doc in documents]
        
        # Calculate average of top 3 documents
        top_similarities = sorted(similarities, reverse=True)[:3]
        avg_similarity = sum(top_similarities) / len(top_similarities)
        
        # Adjust based on number of documents
        doc_count_factor = min(len(documents) / 3.0, 1.0)
        
        # Final confidence score
        confidence = avg_similarity * (0.7 + 0.3 * doc_count_factor)
        
        return round(confidence, 2)


# Singleton instance
_query_processor = None


def get_query_processor() -> QueryProcessor:
    """Get query processor singleton instance"""
    global _query_processor
    if _query_processor is None:
        _query_processor = QueryProcessor()
    return _query_processor
