from fastapi import APIRouter, Request, HTTPException
from app.models import QueryRequest, QueryResponse
from app.services.query_processor import get_query_processor
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/process", response_model=QueryResponse)
async def process_query(request: Request, query_request: QueryRequest):
    """
    Process a natural language query using RAG
    """
    logger_adapter = request.state.logger
    logger_adapter.info(f"Processing query for student {query_request.student_id}")
    
    try:
        query_processor = get_query_processor()
        
        response = await query_processor.process_query(
            query=query_request.query,
            student_id=query_request.student_id,
            correlation_id=query_request.correlation_id or request.state.correlation_id
        )
        
        logger_adapter.info(f"Query processed successfully with confidence {response.confidence}")
        return response
    
    except Exception as e:
        logger_adapter.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process query")
