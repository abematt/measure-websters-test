# API Module Structure

This directory contains the refactored API code, organized into logical modules for better maintainability.

## Directory Structure

```
api/
├── models/           # Pydantic models for request/response schemas
│   └── __init__.py   # QueryRequest, QueryResponse, EnhancedQueryResponse, etc.
├── endpoints/        # Individual query endpoint implementations
│   ├── __init__.py
│   ├── basic_query.py          # /query - Basic RAG query
│   ├── web_preview_query.py    # /query-web-preview - With web search
│   ├── combined_query.py       # /query-combined - Dual response
│   ├── enhanced_query.py       # /query-enhanced - With metadata context
│   └── web_search_explicit.py  # /web-search-explicit - Direct web search
└── utils/            # Shared utilities and helper functions
    └── __init__.py   # Filter building, source preferences, metadata extraction

## Key Benefits of This Structure

1. **Separation of Concerns**: Each endpoint has its own module
2. **Code Reuse**: Common utilities extracted to `utils/`
3. **Type Safety**: All models in one place
4. **Maintainability**: Easier to modify individual endpoints
5. **Testing**: Each module can be tested independently

## Usage

The refactored main.py (`main_refactored.py`) imports and uses these modules:

```python
from api.models import QueryRequest, QueryResponse
from api.endpoints import query_index, query_combined
from api.utils import load_source_preferences
```

## Migration Notes

To switch to the refactored version:
1. Rename `main.py` to `main_old.py`
2. Rename `main_refactored.py` to `main.py`
3. Restart the server

The API endpoints remain exactly the same - this is purely an internal reorganization.