# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Webster's Package is a LlamaIndex-based data ingestion and query system that indexes CSV data from multiple sources to create a searchable knowledge base. The system provides both local RAG search and web-enriched query capabilities through a FastAPI server.

## Development Commands

### Environment Setup
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### Core Operations
```bash
# Build/rebuild the search index from CSV data
python scripts/build_index.py

# Start the API server (main application)
python main_refactored.py

# Run source discovery (utility)
python scripts/source_discovery.py

# Add user for authentication (admin only)
python scripts/add_user.py username password [email]
```

The API server runs on `http://localhost:8001` by default.

## Project Architecture

### Data Pipeline Architecture
- **Convention-based Discovery**: Uses hierarchical directory structure (`category/platform/subtype`) for auto-discovering data sources
- **Multi-format Processing**: Handles three CSV types - schema definitions, event specifications, and raw sample data
- **Enhanced Metadata**: Each document includes structured metadata for filtering and source tracking
- **Vector Index**: Uses OpenAI embeddings with persistent storage in `index_storage/`

### API Structure (Modular Design)
```
api/
├── models/          # Pydantic models for all request/response schemas
├── endpoints/       # Individual endpoint implementations (basic_query, combined_query, etc.)
└── utils/           # Shared utilities (filter building, source preferences, metadata extraction)
```

### Data Organization
```
data/sources/
├── category/        # e.g., appusage, social, commerce
│   └── platform/    # e.g., android, ios, tiktok
│       └── subtype/ # e.g., usage, notifications (optional)
│           ├── manifest.yaml    # Metadata and configuration
│           ├── schema.csv       # Column definitions
│           ├── samples.csv      # Data samples
│           └── events.csv       # Event specifications (optional)
```

### Key Components

- **SourceDiscovery**: Auto-discovers data sources from directory conventions, builds metadata
- **EnhancedIndexBuilder**: Processes different CSV types with semantic metadata tagging
- **Two-step Query Workflow**: 
  - Local RAG query (`/query-local`) with metadata for web eligibility
  - Web enrichment (`/query-web-enrich`) with source preferences and synthesis
- **Source Preferences**: YAML configuration in `config/source_preferences.yaml` defines trusted sources for web enrichment by category/platform
- **Authentication System**: JWT-based authentication with MongoDB user storage, admin-managed users

### Main Endpoints
- `/login` - User authentication (returns JWT token)
- `/query` - Basic RAG query (Protected)
- `/query-combined` - Single-step local + web search (Protected)
- `/query-local` - Phase 1: Local knowledge base search (Protected)
- `/query-web-enrich` - Phase 2: Web enrichment with synthesis (Protected)
- `/health` - Index status check (Public)
- `/filters` - Available filter options (Protected)

## Configuration Files

- `.env` - Environment variables (OpenAI API key, MongoDB connection, JWT settings)
- `.env.example` - Template for environment configuration
- `config/source_preferences.yaml` - Trusted web sources by data type
- Individual `manifest.yaml` files in data source directories for metadata

## Authentication Setup

1. **MongoDB Setup**: Ensure MongoDB is running locally or configure `MONGODB_URL` in `.env`
2. **Environment Configuration**: Copy `.env.example` to `.env` and set:
   - `MONGODB_URL`: MongoDB connection string
   - `DATABASE_NAME`: Database name for user storage
   - `JWT_SECRET_KEY`: Secret key for JWT token signing (change in production)
3. **User Management**: Use `python scripts/add_user.py username password [email]` to create users
4. **Frontend Integration**: Include JWT token in Authorization header: `Bearer <token>`

## Testing and Validation

No specific test framework is configured. To validate functionality:
1. Run `python scripts/build_index.py` to verify data ingestion
2. Start server with `python main_refactored.py` 
3. Test endpoints via `/health` and sample queries