from typing import Any, Dict, List
from uuid import UUID
import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.models import QueryResponse, SourceCitation
from app.services.vector_store import get_vector_store
from app.utils.retry import retry_on_api_error

logger = logging.getLogger(__name__)
settings = get_settings()


class QueryProcessor:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.max_tokens,
            openai_api_key=settings.openai_api_key,
        )
        self.vector_store = get_vector_store()

    async def process_query(
        self,
        query: str,
        student_id: UUID,
        correlation_id: str = None,
    ) -> QueryResponse:
        """
        Process a query using RAG (Retrieval-Augmented Generation).
        """
        try:
            logger.info("Retrieving documents for query: %s...", query[:50])
            documents = await self.vector_store.similarity_search(
                query=query,
                student_id=student_id,
            )

            if not documents:
                logger.warning("No relevant documents found for student %s", student_id)
                return QueryResponse(
                    answer=(
                        "I couldn't find relevant information in your synced course materials "
                        "for that question. Try rephrasing it or sync more LMS content first."
                    ),
                    sources=[],
                    confidence=0.0,
                    correlation_id=correlation_id,
                )

            context = self._build_context(documents)

            logger.info("Generating answer with LLM...")
            answer = await self._generate_answer(query, context)

            sources = self._extract_sources(documents)
            confidence = self._calculate_confidence(documents)

            if confidence < 0.5:
                answer = (
                    "Low-confidence answer. Please verify important details with your instructor "
                    "or directly in LMS.\n\n"
                    f"{answer}"
                )

            return QueryResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                correlation_id=correlation_id,
            )
        except Exception as e:
            logger.error("Error processing query: %s", str(e), exc_info=True)
            raise

    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build a compact, source-labelled context string from retrieved documents."""
        context_parts: List[str] = []

        for i, doc in enumerate(documents, 1):
            source_type = doc.get("source_type", "unknown")
            metadata = doc.get("metadata", {}) or {}
            content = doc.get("content", "")

            if source_type == "course":
                header = f"Course: {metadata.get('course_name', 'Unknown')}"
            elif source_type == "assignment":
                header = f"Assignment: {metadata.get('title', 'Unknown')}"
            elif source_type in {"lecture", "transcription"}:
                header = f"Lecture: {metadata.get('title', 'Unknown')}"
            elif source_type == "announcement":
                header = f"Announcement: {metadata.get('title', 'Unknown')}"
            elif source_type == "quiz":
                header = f"Quiz: {metadata.get('quiz', 'Unknown')}"
            elif source_type == "schedule_event":
                header = f"Schedule Event: {metadata.get('event', 'Unknown')}"
            else:
                header = f"Document {i}"

            context_parts.append(f"[{header}]\n{content}\n")

        return "\n".join(context_parts)

    @retry_on_api_error(max_attempts=3)
    async def _generate_answer(self, query: str, context: str) -> str:
        """Generate an answer grounded in retrieved academic context."""
        system_prompt = """You are EduPilot, an AI assistant for university students.
Your role is to help students understand their course materials, assignments, lectures, deadlines, and academic updates.

Guidelines:
- Answer only from the provided context and clearly say when the context is insufficient
- Prefer concrete facts over generic advice
- When deadlines, status, grades, or schedule details are mentioned, use the exact values from context
- Mention the most relevant source titles naturally in the answer when helpful
- If the answer depends on incomplete or conflicting context, say that explicitly
- Be concise, helpful, and academically supportive"""

        user_prompt = f"""Context from the student's academic data:
{context}

Student question: {query}

Please provide a helpful answer based only on the context above.
If you reference a course item, mention its title in the answer."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = await self.llm.ainvoke(messages)
        return response.content

    def _extract_sources(self, documents: List[Dict[str, Any]]) -> List[SourceCitation]:
        """Extract source citations from retrieved documents."""
        sources: List[SourceCitation] = []

        for doc in documents:
            metadata = doc.get("metadata", {}) or {}
            content = doc.get("content", "")
            excerpt = content[:200] + "..." if len(content) > 200 else content

            source_type = doc.get("source_type", "unknown")
            if source_type == "course":
                title = metadata.get("course_name", "Unknown Course")
            elif source_type == "assignment":
                title = metadata.get("title", "Unknown Assignment")
            elif source_type in {"lecture", "transcription"}:
                title = metadata.get("title", "Unknown Lecture")
            elif source_type == "announcement":
                title = metadata.get("title", "Unknown Announcement")
            elif source_type == "quiz":
                title = metadata.get("quiz", "Unknown Quiz")
            elif source_type == "schedule_event":
                title = metadata.get("event", "Unknown Event")
            else:
                title = "Unknown Source"

            sources.append(
                SourceCitation(
                    source_type=source_type,
                    source_id=doc.get("source_id", ""),
                    title=title,
                    excerpt=excerpt,
                    similarity_score=doc.get("similarity", 0.0),
                    url=metadata.get("url"),
                )
            )

        return sources

    def _calculate_confidence(self, documents: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence score based on similarity of the top retrieved results.
        """
        if not documents:
            return 0.0

        similarities = [doc.get("similarity", 0.0) for doc in documents]
        top_similarities = sorted(similarities, reverse=True)[:3]
        avg_similarity = sum(top_similarities) / len(top_similarities)
        doc_count_factor = min(len(documents) / 3.0, 1.0)
        confidence = avg_similarity * (0.7 + 0.3 * doc_count_factor)

        return round(confidence, 2)


_query_processor = None


def get_query_processor() -> QueryProcessor:
    """Get query processor singleton instance."""
    global _query_processor
    if _query_processor is None:
        _query_processor = QueryProcessor()
    return _query_processor
