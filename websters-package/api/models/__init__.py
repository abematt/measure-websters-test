from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import auth models
from ..auth.models import LoginRequest, LoginResponse

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    response: str
    source_nodes: List[Dict[str, Any]]
    
class EnhancedQueryResponse(BaseModel):
    response: str
    source_nodes: List[Dict[str, Any]]
    metadata_context: Dict[str, Any]
    web_search_eligible: bool
    suggested_search_context: Optional[str] = None

class WebSearchRequest(BaseModel):
    query: str
    context: str
    constraints: Optional[Dict[str, Any]] = None
    max_tokens: int = 500

class FilterOptions(BaseModel):
    categories: List[str]
    platforms: List[str]
    tags: List[str]
    source_types: List[str]

# Haystack models
class HaystackQueryRequest(BaseModel):
    query: str = Field(..., description="User query")
    return_sources: bool = Field(False, description="Include source documents")

class HaystackQueryResponse(BaseModel):
    answer: str
    route: str
    query: str
    sources: Optional[List[Dict[str, Any]]] = None

# Two-step workflow models
class LocalQueryResponse(BaseModel):
    """Response from local RAG query with metadata for potential web enrichment"""
    response: str
    source_nodes: List[Dict[str, Any]]
    metadata_context: Dict[str, Any]
    web_search_eligible: bool
    preferred_sources: Optional[List[str]] = None
    suggested_search_context: Optional[str] = None
    
class WebEnrichmentRequest(BaseModel):
    """Request for web enrichment with optional override parameters"""
    query: str
    local_context: Optional[str] = None  # Can be provided from LocalQueryResponse or manually
    preferred_sources: Optional[List[str]] = None  # Can override local suggestions
    keywords: Optional[List[str]] = None  # Can provide manual keywords instead of synthesis
    max_results: int = 5
    concise_mode: bool = True  # For more concise synthesis
    
class WebEnrichmentResponse(BaseModel):
    """Response from web enrichment with synthesized results"""
    synthesized_keywords: List[str]
    web_search_results: List[Dict[str, Any]]
    enriched_response: str
    sources_fetched: int

# Chat message store models
class ChatMessage(BaseModel):
    """Chat message with response and citations, supporting two-step workflow"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="User ID from JWT token")
    message: str = Field(..., description="User's original message/query")
    
    # Local RAG response (always present)
    local_response: str = Field(..., description="Response from local knowledge base")
    local_citations: List[Dict[str, Any]] = Field(default=[], description="Local source nodes")
    
    # Web enrichment (optional, added later)
    web_response: Optional[str] = Field(None, description="Web-enriched response")
    web_citations: List[Dict[str, Any]] = Field(default=[], description="Web search results")
    is_web_enriched: bool = Field(default=False, description="Whether web search was performed")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = Field(None, description="Query filters, mode, etc.")

class SaveMessageRequest(BaseModel):
    """Request to save initial local response"""
    message: str
    local_response: str
    local_citations: List[Dict[str, Any]] = []
    metadata: Optional[Dict[str, Any]] = None

class UpdateWebResponseRequest(BaseModel):
    """Request to add web enrichment to existing message"""
    message_id: str
    web_response: str
    web_citations: List[Dict[str, Any]] = []

class GetMessagesResponse(BaseModel):
    """Response containing user's chat history"""
    messages: List[ChatMessage]
    total: int