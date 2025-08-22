# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Webster's is a full-stack RAG (Retrieval-Augmented Generation) system consisting of:
- **Backend**: FastAPI server with LlamaIndex for indexing and querying CSV data sources
- **Frontend**: Next.js chat interface with authentication and multiple query modes

The system indexes structured CSV data from various platforms (social media, commerce, apps, etc.) to create a searchable knowledge base with optional web enrichment capabilities.

## Development Commands

### Frontend (chat-interface/)
```bash
cd chat-interface
npm install          # Install dependencies
npm run dev          # Start development server (port 3000)
npm run build        # Build for production
npm run lint         # Run linting
```

### Backend (websters-package/)
```bash
cd websters-package
pip install -r requirements.txt      # Install Python dependencies
python scripts/build_index.py        # Build/rebuild search index from CSV data
python main_refactored.py            # Start API server (port 8001)
python scripts/add_user.py username password [email]  # Add user for authentication
```

## Architecture

### Backend (websters-package/)

#### Data Pipeline
- **Convention-based Discovery**: Hierarchical directory structure (`category/platform/subtype`) for auto-discovering data sources
- **Multi-format Processing**: Handles schema definitions, event specifications, and raw sample CSV data
- **Vector Index**: Uses OpenAI embeddings with persistent storage in `index_storage/`
- **MongoDB Authentication**: JWT-based auth with user management

#### API Endpoints (Protected with JWT unless noted)
- `POST /login` - User authentication (returns JWT token)
- `GET /health` - Health check and index status (Public)
- `POST /query` - Basic RAG query
- `POST /query-combined` - Single-step local + web search
- `POST /query-local` - Phase 1: Local knowledge base search
- `POST /query-web-enrich` - Phase 2: Web enrichment with synthesis
- `GET /filters` - Available filter options

#### Key Files
- `main_refactored.py` - FastAPI server with all endpoints
- `scripts/build_index.py` - Index building script
- `scripts/source_discovery.py` - Data source discovery module
- `api/endpoints/*.py` - Individual endpoint implementations
- `api/models/*.py` - Pydantic models for request/response schemas
- `config/source_preferences.yaml` - Trusted web sources configuration

### Frontend (chat-interface/)

#### Stack
- **Next.js 15.4** with App Router
- **TypeScript** with strict mode
- **Tailwind CSS v4** for styling
- **shadcn/ui** components
- **React Markdown** for message rendering

#### Query Modes
1. **Basic Mode**: Queries local knowledge base only
2. **Web Enhanced Mode**: Automatically performs web search with every query
3. **Two-Step Mode** (default): Returns local results first, then offers optional web search

#### Key Components
- `src/components/chat-interface.tsx` - Main chat component with message handling
- `src/components/auth-navbar.tsx` - Authentication UI
- `src/contexts/auth-context.tsx` - JWT authentication context
- `src/lib/api.ts` - Typed API client for backend communication
- `src/config/query-modes.ts` - Query mode configurations

## Data Organization

```
websters-package/data/sources/
├── category/        # e.g., social, commerce, apps
│   └── platform/    # e.g., tiktok, amazon, android
│       └── subtype/ # e.g., usage, notifications (optional)
│           ├── manifest.yaml    # Metadata configuration
│           ├── schema.csv       # Column definitions
│           ├── samples.csv      # Data samples
│           └── events.csv       # Event specifications (optional)
```

## Environment Configuration

Backend requires `.env` file with:
- `OPENAI_API_KEY` - OpenAI API key for embeddings and LLM
- `MONGODB_URL` - MongoDB connection string (default: mongodb://localhost:27017/)
- `DATABASE_NAME` - Database name for user storage
- `JWT_SECRET_KEY` - Secret key for JWT token signing
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time

## Authentication Flow

1. Backend: Create users with `python scripts/add_user.py username password`
2. Frontend: Login via modal to receive JWT token
3. All API requests include `Authorization: Bearer <token>` header
4. Token stored in localStorage and managed by AuthContext

## TypeScript Path Alias

Frontend uses `@/*` alias mapping to `./src/*` for cleaner imports.