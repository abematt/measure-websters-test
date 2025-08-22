"""
Standardized Local RAG Processing Module
Ensures consistent prompting, retrieval, and response formatting across all endpoints
"""

from typing import List, Dict, Any, Optional, Tuple
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.prompts import PromptTemplate
from llama_index.core.schema import NodeWithScore

from . import build_metadata_filters


class StandardLocalRAG:
    """Standardized local RAG processing for consistent results across endpoints"""
    
    # Standardized prompt template - detailed version for consistency
    STANDARD_QA_TEMPLATE = PromptTemplate(
        "Below are multiple sources containing data schemas, event types, and data samples.\n"
        "Sources are organized by category (e.g., appusage, social) and platform (e.g., ios, android).\n"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "Using the information above, please answer the following question: {query_str}\n"
        "Focus on providing specific details from the sources and mention which data sources you're using."
    )
    
    def __init__(self, index, top_k: int = 10):
        """Initialize with vector index and retrieval parameters"""
        self.index = index
        self.top_k = top_k
    
    def create_retriever(self, filters: Optional[Dict[str, Any]] = None) -> VectorIndexRetriever:
        """Create standardized retriever with optional filters"""
        filters_obj = build_metadata_filters(filters) if filters else None
        
        return VectorIndexRetriever(
            index=self.index,
            similarity_top_k=self.top_k,
            filters=filters_obj
        )
    
    def retrieve_nodes(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[NodeWithScore]:
        """Standardized node retrieval"""
        retriever = self.create_retriever(filters)
        return retriever.retrieve(query)
    
    def create_query_engine(self, filters: Optional[Dict[str, Any]] = None) -> RetrieverQueryEngine:
        """Create standardized query engine with consistent prompt"""
        retriever = self.create_retriever(filters)
        
        return RetrieverQueryEngine.from_args(
            retriever=retriever,
            text_qa_template=self.STANDARD_QA_TEMPLATE,
        )
    
    def execute_query(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Tuple[Any, List[NodeWithScore]]:
        """Execute standardized RAG query and return response + nodes"""
        query_engine = self.create_query_engine(filters)
        response = query_engine.query(query)
        
        # Extract nodes consistently - always from response.source_nodes for query engine results
        nodes = response.source_nodes if hasattr(response, 'source_nodes') and response.source_nodes else []
        
        return response, nodes
    
    def format_source_nodes(self, nodes: List[NodeWithScore]) -> List[Dict[str, Any]]:
        """Standardized source node formatting"""
        source_nodes = []
        
        for node in nodes:
            # Handle both direct NodeWithScore and nested node structures
            if hasattr(node, 'node'):
                content = node.node.get_content()
                metadata = node.node.metadata
                score = node.score if hasattr(node, 'score') else None
            else:
                # Fallback for different node structures
                content = node.get_content() if hasattr(node, 'get_content') else str(node)
                metadata = getattr(node, 'metadata', {})
                score = getattr(node, 'score', None)
            
            source_info = {
                "text": content,
                "metadata": metadata,
                "score": score
            }
            source_nodes.append(source_info)
        
        return source_nodes
    
    def get_context_string(self, nodes: List[NodeWithScore]) -> str:
        """Extract context string from nodes for external processing"""
        return "\n\n".join([
            node.node.get_content() if hasattr(node, 'node') 
            else (node.get_content() if hasattr(node, 'get_content') else str(node))
            for node in nodes
        ])
    
    def execute_full_pipeline(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute full standardized RAG pipeline and return structured results"""
        response, nodes = self.execute_query(query, filters)
        source_nodes = self.format_source_nodes(nodes)
        context_string = self.get_context_string(nodes)
        
        return {
            "response": str(response),
            "source_nodes": source_nodes,
            "context_string": context_string,
            "raw_nodes": nodes,
            "raw_response": response
        }


def create_standard_local_rag(index, top_k: int = 10) -> StandardLocalRAG:
    """Factory function to create standardized local RAG processor"""
    return StandardLocalRAG(index=index, top_k=top_k)