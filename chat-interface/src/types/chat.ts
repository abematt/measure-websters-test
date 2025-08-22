import { type LocalQueryResponse, type WebEnrichmentResponse } from '@/lib/api';

export interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
  sources?: Array<{
    text: string;
    metadata?: Record<string, unknown>;
    score?: number;
  }>;
  enhancedResponse?: LocalQueryResponse;
  webSearchResponse?: WebEnrichmentResponse;
  isWebSearchLoading?: boolean;
  showWebSearchButton?: boolean;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  expandedSources: Set<string>;
}

export type ChatAction =
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'TOGGLE_SOURCES'; payload: string }
  | { type: 'UPDATE_MESSAGE_WEB_SEARCH'; payload: { messageId: string; webSearchResponse: WebEnrichmentResponse } }
  | { type: 'SET_MESSAGE_WEB_SEARCH_LOADING'; payload: { messageId: string; loading: boolean } }
  | { type: 'CLEAR_MESSAGES' };