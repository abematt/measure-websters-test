import { useReducer, useCallback } from 'react';
import type { QueryMode, LocalQueryResponse, WebEnrichmentResponse } from '@/lib/api';

interface Source {
  text: string;
  metadata?: Record<string, unknown>;
  score?: number;
}

export interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
  sources?: Source[];
  enhancedResponse?: LocalQueryResponse;
  webSearchResponse?: WebEnrichmentResponse;
  isWebSearchLoading?: boolean;
  showWebSearchButton?: boolean;
}

interface ChatState {
  messages: Message[];
  input: string;
  isLoading: boolean;
  error: string | null;
  isHealthy: boolean | null;
  healthDetails?: {
    status: 'healthy' | 'degraded';
    index_loaded: boolean;
    index_path_exists?: boolean;
    version?: string;
  };
  expandedSources: Set<string>;
  queryMode: QueryMode;
}

type ChatAction =
  | { type: 'SET_INPUT'; payload: string }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_HEALTH'; payload: { isHealthy: boolean | null; details?: ChatState['healthDetails'] } }
  | { type: 'SET_QUERY_MODE'; payload: QueryMode }
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'UPDATE_MESSAGE'; payload: { id: string; updates: Partial<Message> } }
  | { type: 'CLEAR_INPUT' }
  | { type: 'TOGGLE_SOURCES'; payload: string };

const initialState: ChatState = {
  messages: [],
  input: '',
  isLoading: false,
  error: null,
  isHealthy: null,
  healthDetails: undefined,
  expandedSources: new Set(),
  queryMode: 'enhanced',
};

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'SET_INPUT':
      return { ...state, input: action.payload };
    
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    
    case 'SET_HEALTH':
      return { 
        ...state, 
        isHealthy: action.payload.isHealthy,
        healthDetails: action.payload.details 
      };
    
    case 'SET_QUERY_MODE':
      return { ...state, queryMode: action.payload };
    
    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };
    
    case 'UPDATE_MESSAGE':
      return {
        ...state,
        messages: state.messages.map(msg =>
          msg.id === action.payload.id
            ? { ...msg, ...action.payload.updates }
            : msg
        ),
      };
    
    case 'CLEAR_INPUT':
      return { ...state, input: '' };
    
    case 'TOGGLE_SOURCES': {
      const newExpandedSources = new Set(state.expandedSources);
      if (newExpandedSources.has(action.payload)) {
        newExpandedSources.delete(action.payload);
      } else {
        newExpandedSources.add(action.payload);
      }
      return { ...state, expandedSources: newExpandedSources };
    }
    
    default:
      return state;
  }
}

export function useChatState() {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  const actions = {
    setInput: useCallback((input: string) => {
      dispatch({ type: 'SET_INPUT', payload: input });
    }, []),

    setLoading: useCallback((loading: boolean) => {
      dispatch({ type: 'SET_LOADING', payload: loading });
    }, []),

    setError: useCallback((error: string | null) => {
      dispatch({ type: 'SET_ERROR', payload: error });
    }, []),

    setHealth: useCallback((health: boolean | null, details?: ChatState['healthDetails']) => {
      dispatch({ type: 'SET_HEALTH', payload: { isHealthy: health, details } });
    }, []),

    setQueryMode: useCallback((mode: QueryMode) => {
      dispatch({ type: 'SET_QUERY_MODE', payload: mode });
    }, []),

    addMessage: useCallback((message: Message) => {
      dispatch({ type: 'ADD_MESSAGE', payload: message });
    }, []),

    updateMessage: useCallback((id: string, updates: Partial<Message>) => {
      dispatch({ type: 'UPDATE_MESSAGE', payload: { id, updates } });
    }, []),

    clearInput: useCallback(() => {
      dispatch({ type: 'CLEAR_INPUT' });
    }, []),

    toggleSources: useCallback((messageId: string) => {
      dispatch({ type: 'TOGGLE_SOURCES', payload: messageId });
    }, []),
  };

  return { state, actions };
}