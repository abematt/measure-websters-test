# Webster's Package - LlamaIndex Query System

This package contains the core components for building and querying a knowledge base from structured CSV data.

## Structure

```
websters-package/
├── scripts/
│   ├── build_index.py      # Index building script
│   └── source_discovery.py # Data source discovery module
├── api/                    # FastAPI endpoints and models
├── data/
│   └── sources/           # CSV data files (schemas, samples, events)
├── main_refactored.py     # FastAPI server with all endpoints
├── requirements.txt       # Python dependencies
└── .env.example          # Environment variables template
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Build the index:**
   ```bash
   python scripts/build_index.py
   ```

4. **Start the API server:**
   ```bash
   python main_refactored.py
   ```

## API Endpoints

### Core Endpoints
- `GET /health` - Health check and index status
- `POST /query` - Basic query endpoint
- `POST /query-combined` - Combined query with automatic web search
- `POST /query-local` - Phase 1 of two-step query (local knowledge base)
- `POST /query-web-enrich` - Phase 2 of two-step query (web enrichment)

### Additional Endpoints
- `GET /filters` - Available filter options
- `POST /query-enhanced` - Enhanced query with metadata
- `POST /web-search-explicit` - Explicit web search
- `POST /query-web-enhanced` - Web-enhanced query workflow

The server runs on `http://localhost:8001` by default.