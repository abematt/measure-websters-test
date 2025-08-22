# Chat Interface for LlamaIndex Query API

A simple and functional chat interface built with Next.js and shadcn/ui components that connects to a LlamaIndex query API.

## API Requirements

The interface connects to an API running on `http://localhost:8000` with the following endpoints:

- **GET /health** - Health check endpoint
- **POST /query** - Query endpoint that accepts:
  ```json
  {
    "query": "string",
    "top_k": number
  }
  ```
  
  And returns:
  ```json
  {
    "response": "string",
    "source_nodes": [
      {
        "text": "string",
        "metadata": {}
      }
    ]
  }
  ```

## Features

- Clean, responsive chat interface using shadcn/ui components
- Real-time health check with connection status indicator
- Message history with timestamps
- Source nodes display for query responses
- Loading states and error handling
- Auto-scroll to latest messages
- Form validation and disabled states

## Getting Started

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Make sure your API is running on http://localhost:8000**

4. **Open http://localhost:3000 in your browser**

## Components Used

- **Card** - Main chat container
- **Input** - Message input field
- **Button** - Send button and error dismissal
- **ScrollArea** - Scrollable message history

## Project Structure

```
src/
├── app/
│   ├── page.tsx              # Main page with chat interface
│   └── layout.tsx            # Root layout
├── components/
│   ├── ui/                   # shadcn/ui components
│   └── chat-interface.tsx    # Main chat component
└── lib/
    ├── api.ts                # API client and types
    └── utils.ts              # Utility functions
```

## Build

```bash
npm run build
```

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.
