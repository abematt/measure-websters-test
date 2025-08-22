export const CHAT_CONSTANTS = {
  // UI Dimensions
  MAX_MESSAGE_WIDTH: '85%',
  CHAT_HEIGHT: '80vh',
  MIN_CHAT_HEIGHT: '500px',
  MAX_CHAT_HEIGHT: '800px',
  
  // Content limits
  SOURCE_TEXT_PREVIEW_LENGTH: 400,
  MAX_METADATA_TAGS: 6,
  METADATA_VALUE_PREVIEW_LENGTH: 30,
  METADATA_KEY_MAX_WIDTH: '100px',
  
  // Query settings
  DEFAULT_TOP_K: 5,
  DEFAULT_WEB_SEARCH_RESULTS: 5,
  
  // Timeouts and delays
  SCROLL_ANIMATION_DELAY: 0,
  BOUNCE_ANIMATION_DELAY_1: '0.1s',
  BOUNCE_ANIMATION_DELAY_2: '0.2s',
  
  // Excluded metadata keys
  EXCLUDED_METADATA_KEYS: ['source_type', 'web_sources'] as const,
  
  // CSS Classes
  GRADIENT_BAR: 'w-1 h-6 bg-gradient-to-b from-primary to-sidebar-accent rounded-full',
  GRADIENT_TEXT: 'bg-gradient-to-r from-primary to-sidebar-accent bg-clip-text text-transparent font-semibold',
  GRADIENT_BUTTON: 'bg-gradient-to-r from-primary to-primary-darker hover:from-primary-darker hover:to-primary transition-all duration-200 shadow-sm',
  
  // Component IDs and refs
  MESSAGES_END_REF: 'messages-end',
} as const;

export const QUERY_SETTINGS = {
  ENHANCED_MODE: {
    top_k: CHAT_CONSTANTS.DEFAULT_TOP_K,
  },
  BASIC_MODE: {
    top_k: CHAT_CONSTANTS.DEFAULT_TOP_K,
  },
  WEB_SEARCH: {
    max_results: CHAT_CONSTANTS.DEFAULT_WEB_SEARCH_RESULTS,
    concise_mode: true,
  },
} as const;