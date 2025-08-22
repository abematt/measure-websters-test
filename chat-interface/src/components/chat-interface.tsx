"use client";

import { useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api, type LocalQueryResponse, type QueryMode, AuthenticationError } from "@/lib/api";
import QueryModeDropdown from "@/components/query-mode-dropdown";
import { getModeByValue } from "@/config/query-modes";
import { MessageItem } from "@/components/message-item";
import { useChatState, type Message } from "@/hooks/use-chat-state";
import { useAuth } from "@/contexts/auth-context";
import { QueryStrategyFactory } from "@/services/query-strategies";
import { CHAT_CONSTANTS, QUERY_SETTINGS } from "@/constants/chat";

export function ChatInterface() {
  const { state, actions } = useChatState();
  const { messages, input, isLoading, error, isHealthy, queryMode, healthDetails } = state;
  const { logout } = useAuth();
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check API health on component mount
  useEffect(() => {
    checkHealth();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    // Use requestAnimationFrame to ensure DOM updates are complete
    requestAnimationFrame(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({
          behavior: "smooth",
          block: "end",
        });
      }
    });
  };

  const checkHealth = async () => {
    try {
      const health = await api.healthCheck();
      actions.setHealth(health.status === "healthy" && health.index_loaded, health);
    } catch (err) {
      actions.setHealth(false);
      console.error("Health check failed:", err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    actions.addMessage(userMessage);
    const queryText = input.trim();
    actions.clearInput();
    actions.setLoading(true);
    actions.setError(null);

    try {
      const strategy = QueryStrategyFactory.getStrategy(queryMode);
      const assistantMessage = await strategy.execute(queryText);
      actions.addMessage(assistantMessage);
    } catch (err) {
      if (err instanceof AuthenticationError) {
        logout();
        return;
      }
      actions.setError(err instanceof Error ? err.message : "An error occurred");
      console.error("Query failed:", err);
    } finally {
      actions.setLoading(false);
    }
  };

  const handleWebSearch = async (messageId: string, originalQuery: string, enhancedResponse: LocalQueryResponse) => {
    // Set loading state for this specific message
    actions.updateMessage(messageId, { isWebSearchLoading: true });

    try {
      const webSearchResponse = await api.webSearchExplicit({
        query: originalQuery,
        message_id: enhancedResponse.message_id || undefined,
        local_context: enhancedResponse.suggested_search_context || undefined,
        preferred_sources: enhancedResponse.preferred_sources || undefined,
        ...QUERY_SETTINGS.WEB_SEARCH,
      });

      // Update the message with web search results
      actions.updateMessage(messageId, {
        webSearchResponse,
        isWebSearchLoading: false,
        showWebSearchButton: false,
      });
    } catch (err) {
      if (err instanceof AuthenticationError) {
        logout();
        return;
      }
      actions.setError(`Web search failed: ${err instanceof Error ? err.message : "Unknown error"}`);
      actions.updateMessage(messageId, { isWebSearchLoading: false });
    }
  };

  const getCurrentModeConfig = () => {
    const cfg = getModeByValue(queryMode);
    return {
      icon: cfg.icon,
      label: cfg.label,
      description: cfg.description,
    };
  };

  return (
    <Card className="w-full h-full flex flex-col py-0">
      <CardHeader className="pb-2 pt-3 px-3 border-b border-border/40">
        <div className="flex items-center justify-between mb-2">
          {/* Query Mode Dropdown - Top Left */}
          <div className="flex items-center gap-2">
            <QueryModeDropdown value={queryMode} onValueChange={(v) => actions.setQueryMode(v as QueryMode)} />
          </div>

          {/* Health Status - Top Right */}
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full transition-colors ${
                healthDetails?.status === "degraded"
                  ? "bg-orange-500 shadow-sm shadow-orange-500/20"
                  : isHealthy === true
                  ? "bg-green-500 shadow-sm shadow-green-500/20"
                  : isHealthy === false
                  ? "bg-red-500 shadow-sm shadow-red-500/20"
                  : "bg-yellow-500 shadow-sm shadow-yellow-500/20"
              }`}
              title={healthDetails ? `Index: ${healthDetails.index_loaded ? 'Loaded' : 'Not loaded'}, Path: ${healthDetails.index_path_exists ? 'Exists' : 'Missing'}` : ''}
            />
            <span className="text-sm font-medium text-muted-foreground">
              {healthDetails?.status === "degraded"
                ? "Degraded (Index issue)"
                : isHealthy === true
                ? "Connected"
                : isHealthy === false
                ? "Disconnected"
                : "Checking..."}
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col gap-3 p-3 min-h-0">
        <ScrollArea className="flex-1 pr-4 overflow-hidden" ref={scrollAreaRef}>
          <div className="space-y-2 min-h-0">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <div className="mb-4">
                  <div className="w-16 h-16 mx-auto bg-gradient-to-br from-primary/10 to-sidebar-accent/10 rounded-2xl flex items-center justify-center mb-4">
                    <svg
                      className="w-8 h-8 text-primary"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                      />
                    </svg>
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  Welcome to Websters
                </h3>
                <p className="text-muted-foreground max-w-md mx-auto">
                  Start a conversation by asking a question about the different
                  retro data Measure collects.
                </p>
              </div>
            )}

            {messages.map((message) => (
              <MessageItem
                key={message.id}
                message={message}
                messages={messages}
                onWebSearch={handleWebSearch}
              />
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-muted rounded-lg px-4 py-2 max-w-[80%]">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
                    <div
                      className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"
                      style={{ animationDelay: CHAT_CONSTANTS.BOUNCE_ANIMATION_DELAY_1 }}
                    />
                    <div
                      className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"
                      style={{ animationDelay: CHAT_CONSTANTS.BOUNCE_ANIMATION_DELAY_2 }}
                    />
                    <span className="text-muted-foreground text-sm ml-2">
                      Thinking...
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Invisible element to scroll to */}
            <div ref={messagesEndRef} className="h-0" />
          </div>
        </ScrollArea>

        {error && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3">
            <p className="text-destructive text-sm">{error}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => actions.setError(null)}
              className="mt-2"
            >
              Dismiss
            </Button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => actions.setInput(e.target.value)}
            placeholder="Ask a question..."
            disabled={isLoading || isHealthy === false}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={!input.trim() || isLoading || isHealthy === false}
            className={CHAT_CONSTANTS.GRADIENT_BUTTON}
          >
            {isLoading ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Sending...
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
                Send
              </div>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}