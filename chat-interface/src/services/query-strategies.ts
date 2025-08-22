import { api, type QueryMode, type QueryResponse, type LocalQueryResponse } from '@/lib/api';
import { QUERY_SETTINGS } from '@/constants/chat';
import type { Message } from '@/hooks/use-chat-state';

export interface QueryStrategy {
  execute(query: string): Promise<Message>;
}

class BasicQueryStrategy implements QueryStrategy {
  async execute(query: string): Promise<Message> {
    const response: QueryResponse = await api.query(
      {
        query,
        ...QUERY_SETTINGS.BASIC_MODE,
      },
      false // not combined
    );

    return {
      id: (Date.now() + 1).toString(),
      type: "assistant",
      content: response.response,
      timestamp: new Date(),
      sources: response.source_nodes,
    };
  }
}

class CombinedQueryStrategy implements QueryStrategy {
  async execute(query: string): Promise<Message> {
    const response: QueryResponse = await api.query(
      {
        query,
        ...QUERY_SETTINGS.BASIC_MODE,
      },
      true // combined with web search
    );

    return {
      id: (Date.now() + 1).toString(),
      type: "assistant",
      content: response.response,
      timestamp: new Date(),
      sources: response.source_nodes,
    };
  }
}

class EnhancedQueryStrategy implements QueryStrategy {
  async execute(query: string): Promise<Message> {
    const enhancedResponse: LocalQueryResponse = await api.queryEnhanced({
      query,
      ...QUERY_SETTINGS.ENHANCED_MODE,
    });

    return {
      id: (Date.now() + 1).toString(),
      type: "assistant",
      content: enhancedResponse.response,
      timestamp: new Date(),
      sources: enhancedResponse.source_nodes,
      enhancedResponse,
      showWebSearchButton: enhancedResponse.web_search_eligible,
    };
  }
}

export class QueryStrategyFactory {
  private static strategies: Record<QueryMode, QueryStrategy> = {
    basic: new BasicQueryStrategy(),
    combined: new CombinedQueryStrategy(),
    enhanced: new EnhancedQueryStrategy(),
  };

  static getStrategy(mode: QueryMode): QueryStrategy {
    const strategy = this.strategies[mode];
    if (!strategy) {
      throw new Error(`Unknown query mode: ${mode}`);
    }
    return strategy;
  }
}