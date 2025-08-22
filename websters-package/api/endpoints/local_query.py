"""
Local Query Endpoint
Performs RAG retrieval and provides metadata for potential web enrichment
"""

from fastapi import HTTPException
from typing import Dict, Any, Optional
import traceback

from ..models import QueryRequest, LocalQueryResponse
from ..utils import extract_metadata_context
from ..utils.local_rag import create_standard_local_rag
from ..auth.utils import save_chat_message


async def local_query(request: QueryRequest, index, source_preferences, user_id: Optional[str] = None) -> LocalQueryResponse:
    """
    Perform local RAG query and return results with web enrichment metadata
    
    Steps:
    1. Retrieve from local index with filters
    2. Extract metadata context and preferred sources
    3. Generate RAG response
    4. Determine web search eligibility
    5. Return comprehensive local results
    """
    if not index:
        raise HTTPException(status_code=503, detail="Index not loaded")
    
    try:
        # Execute standardized local RAG processing
        local_rag = create_standard_local_rag(index, top_k=request.top_k)
        rag_results = local_rag.execute_full_pipeline(
            query=request.query,
            filters=request.filters
        )
        
        # Extract metadata context for web search decisions using raw nodes
        nodes = rag_results["raw_nodes"]
        metadata_context = extract_metadata_context(nodes, source_preferences)
        
        # Determine web search eligibility
        preferred_sources = metadata_context.get('preferred_sources', [])
        web_search_eligible = bool(preferred_sources)
        
        # Create suggested search context if eligible
        suggested_context = None
        if web_search_eligible and nodes:
            # Take first node's content as sample
            first_node = nodes[0]
            sample_content = (first_node.node.get_content() if hasattr(first_node, 'node') 
                            else first_node.get_content())[:300]
            context_summary = metadata_context.get('context_summary', '')
            suggested_context = f"{context_summary} | Sample: {sample_content}..."
        
        # Auto-save to database if user is authenticated
        message_id = None
        if user_id:
            try:
                message_id = save_chat_message(
                    user_id=user_id,
                    message=request.query,
                    local_response=rag_results["response"],
                    local_citations=rag_results["source_nodes"],
                    endpoint_type="query-local",
                    metadata=request.filters
                )
            except Exception as e:
                print(f"Failed to save message: {e}")
                # Don't fail the query if save fails
        
        # Return comprehensive local query response
        return LocalQueryResponse(
            response=rag_results["response"],
            source_nodes=rag_results["source_nodes"],
            metadata_context=metadata_context,
            web_search_eligible=web_search_eligible,
            preferred_sources=preferred_sources if preferred_sources else None,
            suggested_search_context=suggested_context,
            message_id=message_id
        )
        
    except Exception as e:
        print(f"Error in local query: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))