"""
Local Query Endpoint
Performs RAG retrieval and provides metadata for potential web enrichment
"""

from fastapi import HTTPException
from typing import Dict, Any, Optional
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.prompts import PromptTemplate
import traceback

from ..models import QueryRequest, LocalQueryResponse
from ..utils import build_metadata_filters, extract_metadata_context
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
        # Build filters from request
        filters_obj = build_metadata_filters(request.filters)
        
        # Create retriever
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=request.top_k,
            filters=filters_obj
        )
        
        # Retrieve relevant nodes
        nodes = retriever.retrieve(request.query)
        
        # Extract metadata context for web search decisions
        metadata_context = extract_metadata_context(nodes, source_preferences)
        
        # Determine web search eligibility
        preferred_sources = metadata_context.get('preferred_sources', [])
        web_search_eligible = bool(preferred_sources)
        
        # Create suggested search context if eligible
        suggested_context = None
        if web_search_eligible and nodes:
            # Take first node's content as sample
            sample_content = nodes[0].node.get_content()[:300]
            context_summary = metadata_context.get('context_summary', '')
            suggested_context = f"{context_summary} | Sample: {sample_content}..."
        
        # Generate RAG response with custom prompt
        QA_TEMPLATE = PromptTemplate(
            "Below are multiple sources containing data schemas, event types, and data samples.\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "Using the information above, please answer the following question: {query_str}\n"
            "Focus on providing specific details from the sources and mention which data sources you're using."
        )
        
        # Create query engine
        custom_query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            text_qa_template=QA_TEMPLATE,
        )
        
        # Execute query
        response = custom_query_engine.query(request.query)
        
        # Build source nodes for response
        source_nodes = []
        for node in nodes:
            source_info = {
                "text": node.node.get_content(),
                "metadata": node.node.metadata,
                "score": node.score if hasattr(node, 'score') else None
            }
            source_nodes.append(source_info)
        
        # Auto-save to database if user is authenticated
        message_id = None
        if user_id:
            try:
                message_id = save_chat_message(
                    user_id=user_id,
                    message=request.query,
                    local_response=str(response),
                    local_citations=source_nodes,
                    endpoint_type="query-local",
                    metadata=request.filters
                )
            except Exception as e:
                print(f"Failed to save message: {e}")
                # Don't fail the query if save fails
        
        # Return comprehensive local query response
        return LocalQueryResponse(
            response=str(response),
            source_nodes=source_nodes,
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