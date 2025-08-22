from fastapi import HTTPException
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.prompts import PromptTemplate
from typing import Dict, Any
import traceback

from ..models import QueryRequest, QueryResponse
from ..utils import build_metadata_filters

async def query_index(request: QueryRequest, index) -> QueryResponse:
    """Basic RAG query endpoint"""
    if not index:
        raise HTTPException(status_code=503, detail="Index not loaded")
    
    try:
        # Create retriever with optional filters
        filters_obj = build_metadata_filters(request.filters)
        
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=request.top_k,
            filters=filters_obj
        )
        
        QA_TEMPLATE = PromptTemplate(
            "Below are multiple sources containing data schemas, event types, and data samples.\n"
            "Sources are organized by category (e.g., appusage, social) and platform (e.g., ios, android).\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "Using the information above, please answer the following question: {query_str}\n"
            "Focus on providing specific details from the sources and mention which data sources you're using."
        )
        
        custom_query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            text_qa_template=QA_TEMPLATE,
        )
        
        response = custom_query_engine.query(request.query)
        
        source_nodes = []
        for node in response.source_nodes:
            source_info = {
                "text": node.node.get_content(),
                "metadata": node.node.metadata,
                "score": node.score if hasattr(node, 'score') else None
            }
            source_nodes.append(source_info)
        
        return QueryResponse(
            response=str(response),
            source_nodes=source_nodes
        )
    except Exception as e:
        print(f"Error in query: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))