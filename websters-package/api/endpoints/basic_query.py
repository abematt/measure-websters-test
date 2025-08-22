from fastapi import HTTPException
from typing import Dict, Any, Optional
import traceback

from ..models import QueryRequest, QueryResponse
from ..utils.local_rag import create_standard_local_rag
from ..auth.utils import save_chat_message

async def query_index(request: QueryRequest, index, user_id: Optional[str] = None) -> QueryResponse:
    """Basic RAG query endpoint using standardized local RAG processing"""
    if not index:
        raise HTTPException(status_code=503, detail="Index not loaded")
    
    try:
        # Create standardized local RAG processor
        local_rag = create_standard_local_rag(index, top_k=request.top_k)
        
        # Execute standardized RAG pipeline
        rag_results = local_rag.execute_full_pipeline(
            query=request.query,
            filters=request.filters
        )
        
        query_response = QueryResponse(
            response=rag_results["response"],
            source_nodes=rag_results["source_nodes"]
        )
        
        # Auto-save to database if user is authenticated
        if user_id:
            try:
                save_chat_message(
                    user_id=user_id,
                    message=request.query,
                    local_response=rag_results["response"],
                    local_citations=rag_results["source_nodes"],
                    endpoint_type="query",
                    metadata=request.filters
                )
            except Exception as e:
                print(f"Failed to save message: {e}")
                # Don't fail the query if save fails
        
        return query_response
    except Exception as e:
        print(f"Error in query: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))