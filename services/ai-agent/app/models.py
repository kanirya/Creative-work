from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID


class QueryRequest(BaseModel):
    student_id: UUID = Field(..., description="Student ID")
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language query")
    type: str = Field(default="text", description="Query type: text or voice")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")


class SourceCitation(BaseModel):
    source_type: str = Field(..., description="Type of source: course, assignment, lecture, announcement")
    source_id: str = Field(..., description="ID of the source document")
    title: str = Field(..., description="Title of the source")
    excerpt: str = Field(..., description="Relevant excerpt from the source")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")


class QueryResponse(BaseModel):
    answer: str = Field(..., description="AI-generated answer")
    sources: List[SourceCitation] = Field(default_factory=list, description="Source citations")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
