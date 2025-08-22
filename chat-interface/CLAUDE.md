# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Next.js chat interface that connects to a LlamaIndex query API backend. The interface provides three query modes (basic, web-enhanced, and two-step) for searching and retrieving information from an indexed knowledge base with optional web enrichment.

## Development Commands

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linting
npm run lint
```

## Architecture

### Frontend Stack
- **Next.js 15.4** with App Router
- **TypeScript** for type safety
- **Tailwind CSS v4** for styling
- **shadcn/ui** components (Card, Button, Input, ScrollArea)
- **Lucide React** for icons

### Key Components

- **`src/components/chat-interface.tsx`**: Main chat component handling message display, query submission, source expansion, and web search functionality
- **`src/lib/api.ts`**: API client with typed interfaces for health checks, queries, and web enrichment
- **`src/config/query-modes.ts`**: Query mode configurations (basic, combined, enhanced)

### API Integration

Connects to backend API on `http://localhost:8001` with endpoints:
- `GET /health` - Health check and index status
- `POST /query` - Basic query endpoint
- `POST /query-combined` - Combined query with automatic web search
- `POST /query-local` - Phase 1 of two-step query (local knowledge base)
- `POST /query-web-enrich` - Phase 2 of two-step query (web enrichment)

### Query Modes

1. **Basic Mode**: Queries local knowledge base only
2. **Web Enhanced Mode**: Automatically performs web search with every query
3. **Two-Step Mode** (default): Returns local results first, then offers optional web search button

### Response Types

- **QueryResponse**: Basic response with text and source nodes
- **LocalQueryResponse**: Enhanced response with metadata context and web search eligibility
- **WebEnrichmentResponse**: Web search results with synthesized keywords and enriched response

## Project Structure

```
src/
├── app/
│   ├── page.tsx              # Main page with branded header/footer
│   └── layout.tsx            # Root layout
├── components/
│   ├── ui/                   # shadcn/ui components
│   ├── chat-interface.tsx    # Main chat component
│   ├── query-mode-dropdown.tsx # Mode selector
│   └── branded-header.tsx    # Header/footer components
├── lib/
│   ├── api.ts                # API client and types
│   └── utils.ts              # Utility functions
└── config/
    └── query-modes.ts        # Query mode configurations
```

## TypeScript Configuration

- Strict mode enabled
- Path alias `@/*` maps to `./src/*`
- Target ES2017 with ESNext library features