import { Button } from "@/components/ui/button";
import { Globe, Loader2 } from "lucide-react";
import { SafeMarkdown } from "@/utils/markdown";
import { SourcesList } from "@/components/sources-list";
import { WebSearchResults } from "@/components/web-search-results";
import { CHAT_CONSTANTS } from "@/constants/chat";
import type { LocalQueryResponse, WebEnrichmentResponse } from "@/lib/api";

interface Source {
  text: string;
  metadata?: Record<string, unknown>;
  score?: number;
}

interface Message {
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

interface MessageItemProps {
  message: Message;
  messages: Message[];
  onWebSearch: (messageId: string, originalQuery: string, enhancedResponse: LocalQueryResponse) => void;
}

export function MessageItem({ message, messages, onWebSearch }: MessageItemProps) {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const handleWebSearchClick = () => {
    const userQuery = messages.find(m => 
      m.type === "user" && 
      messages.indexOf(m) === messages.indexOf(message) - 1
    )?.content || "";
    
    if (message.enhancedResponse) {
      onWebSearch(message.id, userQuery, message.enhancedResponse);
    }
  };

  return (
    <div
      className={`flex ${
        message.type === "user" ? "justify-end" : "justify-start"
      }`}
    >
      <div
        className={`max-w-[${CHAT_CONSTANTS.MAX_MESSAGE_WIDTH}] space-y-2 min-w-0 chat-message-container`}
      >
        <div
          className={`rounded-lg px-3 py-2 ${
            message.type === "user"
              ? "bg-primary text-primary-foreground ml-auto"
              : "bg-muted"
          }`}
        >
          <div className="text-sm">
            {message.type === "assistant" ? (
              <SafeMarkdown 
                content={message.content}
              />
            ) : (
              <p className="break-words">
                {message.content}
              </p>
            )}
          </div>
        </div>

        {/* Web Search Button for Enhanced Mode */}
        {message.showWebSearchButton && message.enhancedResponse && !message.webSearchResponse && (
          <div className="flex justify-start">
            <Button
              variant="outline"
              size="sm"
              onClick={handleWebSearchClick}
              disabled={message.isWebSearchLoading}
              className="gap-2 border-blue-200 text-blue-700 hover:bg-blue-50 dark:border-blue-800 dark:text-blue-300 dark:hover:bg-blue-950/50"
              title={message.enhancedResponse.preferred_sources?.length 
                ? `Search will use: ${message.enhancedResponse.preferred_sources.slice(0, 2).join(', ')}${message.enhancedResponse.preferred_sources.length > 2 ? '...' : ''}`
                : 'Search the web for additional context'
              }
            >
              {message.isWebSearchLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Globe className="w-4 h-4" />
                  Web Search
                </>
              )}
            </Button>
          </div>
        )}

        {/* Web Search Results */}
        {message.webSearchResponse && (
          <WebSearchResults webResponse={message.webSearchResponse} />
        )}

        <div
          className={`text-xs text-muted-foreground ${
            message.type === "user" ? "text-right" : "text-left"
          }`}
        >
          {formatTime(message.timestamp)}
        </div>

        {/* Sources */}
        <SourcesList sources={message.sources || []} />
      </div>
    </div>
  );
}