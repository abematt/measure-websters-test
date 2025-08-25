export interface QueryRequest {
  query: string;
  top_k: number;
  filters?: Record<string, unknown>;
}

export interface SourceNode {
  text: string;
  metadata?: Record<string, unknown>;
  score?: number;
}

export interface QueryResponse {
  response: string;
  source_nodes: SourceNode[];
}

// Phase 1: Local query
export interface LocalQueryResponse {
  response: string;
  source_nodes: SourceNode[];
  metadata_context: Record<string, unknown>;
  web_search_eligible: boolean;
  preferred_sources: string[] | null;  // top-level, can be null
  suggested_search_context: string | null;
  message_id: string | null;  // ID of saved message for web enrichment
}

// Phase 2: Web enrichment
export interface WebEnrichmentRequest {
  query: string;
  message_id?: string;  // ID of existing message to update with web response
  local_context?: string;
  preferred_sources?: string[];
  keywords?: string[];
  max_results?: number;
  concise_mode?: boolean;
}

export interface WebEnrichmentResponse {
  synthesized_keywords: string[];
  web_search_results: Array<{
    title: string;
    link: string;       // URL field is "link"
    snippet: string;
    position: number;
  }>;
  enriched_response: string;
  sources_fetched: number;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded';
  index_loaded: boolean;
  index_path_exists?: boolean;
  version?: string;
}

export type QueryMode = 'basic' | 'combined' | 'enhanced';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL 

// Authentication error class
export class AuthenticationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AuthenticationError';
  }
}

// Get authentication headers
const getAuthHeaders = (): Record<string, string> => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  
  return headers;
};

// Handle authentication errors
const handleAuthError = (response: Response) => {
  if (response.status === 401) {
    // Clear invalid token
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
    }
    throw new AuthenticationError('Authentication failed. Please login again.');
  }
};

export const api = {
  async healthCheck(): Promise<HealthResponse> {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  },

  async query(request: QueryRequest, useWebSearch: boolean = true): Promise<QueryResponse> {
    const endpoint = useWebSearch ? '/query-combined' : '/query';
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    
    handleAuthError(response);
    
    if (!response.ok) {
      throw new Error(`Query failed: ${response.statusText}`);
    }
    
    return response.json();
  },

  // Phase 1: Local query (updated endpoint)
  async queryEnhanced(request: QueryRequest): Promise<LocalQueryResponse> {
    const response = await fetch(`${API_BASE_URL}/query-local`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    
    handleAuthError(response);
    
    if (!response.ok) {
      throw new Error(`Enhanced query failed: ${response.statusText}`);
    }
    
    return response.json();
  },

  // Phase 2: Web enrichment (updated endpoint and payload)
  async webSearchExplicit(request: WebEnrichmentRequest): Promise<WebEnrichmentResponse> {
    const response = await fetch(`${API_BASE_URL}/query-web-enrich`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });
    
    handleAuthError(response);
    
    if (!response.ok) {
      throw new Error(`Web search failed: ${response.statusText}`);
    }
    
    return response.json();
  },

  // New filters endpoint
  async getFilters(): Promise<Record<string, unknown>> {
    const response = await fetch(`${API_BASE_URL}/filters`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });
    
    handleAuthError(response);
    
    if (!response.ok) {
      throw new Error(`Get filters failed: ${response.statusText}`);
    }
    
    return response.json();
  },
};