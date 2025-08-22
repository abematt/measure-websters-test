from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import json

parent_dir = Path(__file__).resolve().parent.parent
current_dir = Path(__file__).resolve().parent
sys.path.append(str(parent_dir))
sys.path.append(str(parent_dir / "scripts"))

from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

# Import API modules
from api.models import (
    QueryRequest, 
    QueryResponse, 
    FilterOptions,
    LocalQueryResponse,
    WebEnrichmentRequest,
    WebEnrichmentResponse,
    LoginRequest,
    LoginResponse,
    SaveMessageRequest,
    UpdateWebResponseRequest,
    GetMessagesResponse
)
from api.endpoints import (
    query_index,
    query_combined,
    local_query,
    web_enrichment
)
from api.endpoints.chat import (
    save_message,
    update_web_response,
    get_messages,
    delete_message
)
from api.utils import load_source_preferences
from api.auth.utils import authenticate_user, create_access_token, update_last_login
from api.auth.deps import get_current_active_user
from api.auth.models import UserInDB
from fastapi import Depends
from datetime import timedelta

load_dotenv(current_dir / '.env')

# Global variables
index = None
source_metadata = None
source_preferences = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await load_index()
    yield
    # Shutdown (nothing needed for now)

app = FastAPI(title="LlamaIndex V3 Query API", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def load_index():
    global index, source_metadata, source_preferences
    try:
        # Configure Settings - try different initialization methods
        try:
            Settings.llm = OpenAI(model="gpt-3.5-turbo")
            Settings.embed_model = OpenAIEmbedding()
        except TypeError:
            Settings.llm = OpenAI()
            Settings.embed_model = OpenAIEmbedding()
        
        index_path = current_dir / "index_storage"
        if not index_path.exists():
            raise FileNotFoundError(f"Index not found at {index_path}")
        
        storage_context = StorageContext.from_defaults(persist_dir=str(index_path))
        index = load_index_from_storage(storage_context)
        
        # Load source metadata for filtering
        metadata_path = index_path / "source_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                source_metadata = json.load(f)
        
        # Load source preferences
        source_preferences = load_source_preferences()
        if source_preferences:
            print("Source preferences loaded successfully!")
        else:
            print("No source preferences found, using defaults")
        
        print("V3 Index loaded successfully!")
    except Exception as e:
        print(f"Error loading index: {e}")
        # Don't raise - let the app start but with index=None
        # This allows health check to report the issue

# Root endpoint
@app.get("/")
async def root():
    return {"message": "LlamaIndex V3 Query API is running", "version": "3.0.0"}

# Health check
@app.get("/health")
async def health_check():
    index_path = current_dir / "index_storage"
    return {
        "status": "healthy" if index is not None else "degraded",
        "index_loaded": index is not None,
        "index_path_exists": index_path.exists(),
        "version": "3.0.0"
    }

# Filter options (Protected)
@app.get("/filters", response_model=FilterOptions)
async def get_available_filters(current_user: UserInDB = Depends(get_current_active_user)):
    """Get available filter options for queries"""
    if not source_metadata:
        return FilterOptions(
            categories=[],
            platforms=[],
            tags=[],
            source_types=[]
        )
    
    return FilterOptions(
        categories=source_metadata.get("categories", []),
        platforms=source_metadata.get("platforms", []),
        tags=source_metadata.get("all_tags", []),
        source_types=["schema", "supported_events", "raw"]
    )

# Query endpoints (Protected)
@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest, current_user: UserInDB = Depends(get_current_active_user)):
# async def query_endpoint(request: QueryRequest):
    """Basic RAG query endpoint"""
    return await query_index(request, index)


@app.post("/query-combined", response_model=QueryResponse)
async def query_combined_endpoint(request: QueryRequest, current_user: UserInDB = Depends(get_current_active_user)):
    """Combined local RAG + web search query"""
    return await query_combined(request, index, source_preferences)

# Two-step workflow endpoints - CURRENT MAIN COMBINED SEARCH (Protected)
@app.post("/query-local", response_model=LocalQueryResponse)
async def query_local_endpoint(request: QueryRequest, current_user: UserInDB = Depends(get_current_active_user)):
    """
    Step 1: Local RAG Query
    - Performs RAG retrieval from local index
    - Returns response with metadata for potential web enrichment
    - Includes web search eligibility and preferred sources
    """
    return await local_query(request, index, source_preferences)

@app.post("/query-web-enrich", response_model=WebEnrichmentResponse)
async def query_web_enrich_endpoint(request: WebEnrichmentRequest, current_user: UserInDB = Depends(get_current_active_user)):
    """
    Step 2: Web Enrichment
    - Synthesizes keywords from query and context
    - Performs web search with preferred sources
    - Fetches content and provides concise synthesis
    - Can be used standalone or with output from query-local
    """
    return await web_enrichment(request)

# Authentication endpoints
@app.post("/login", response_model=LoginResponse)
async def login_endpoint(request: LoginRequest):
    """
    Login endpoint
    - Validates username and password
    - Returns JWT token for authenticated access
    """
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)  # You can make this configurable
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Update last login
    update_last_login(user.username)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active
        }
    )

# Chat message endpoints (Protected)
@app.post("/chat/save")
async def save_chat_message_endpoint(
    request: SaveMessageRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Save a new chat message with local response"""
    return await save_message(request, current_user)

@app.put("/chat/update-web")
async def update_chat_web_response_endpoint(
    request: UpdateWebResponseRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Add web enrichment to existing message"""
    return await update_web_response(request, current_user)

@app.get("/chat/messages", response_model=GetMessagesResponse)
async def get_chat_messages_endpoint(
    limit: int = 50,
    offset: int = 0,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get user's chat message history"""
    return await get_messages(limit, offset, current_user)

@app.delete("/chat/messages/{message_id}")
async def delete_chat_message_endpoint(
    message_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a chat message"""
    return await delete_message(message_id, current_user)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_refactored:app", host="0.0.0.0", port=8001, reload=True)