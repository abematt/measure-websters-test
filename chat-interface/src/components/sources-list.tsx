import { useState } from "react";
import { ChevronDown, ChevronUp, Globe, FileText, ExternalLink } from "lucide-react";
import { CHAT_CONSTANTS } from "@/constants/chat";

interface Source {
  text: string;
  metadata?: Record<string, unknown>;
  score?: number;
}

interface SourcesListProps {
  sources: Source[];
}

export function SourcesList({ sources }: SourcesListProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const renderSourceContent = (source: Source, index: number) => {
    const isWebSource = source.metadata?.source_type === "web_search";
    const webSources = (source.metadata?.web_sources as Array<{ url: string; title?: string }>) || [];

    return (
      <div
        key={index}
        className={`p-4 border-b border-muted-foreground/10 last:border-b-0 first:rounded-t-lg last:rounded-b-lg ${
          isWebSource ? "bg-blue-50/50 dark:bg-blue-950/30" : "bg-muted/20"
        }`}
      >
        <div className="space-y-3">
          {/* Source Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {isWebSource ? (
                <Globe className="w-4 h-4 text-blue-500" />
              ) : (
                <FileText className="w-4 h-4 text-green-500" />
              )}
              <span className="text-sm font-medium text-foreground">
                {isWebSource ? "Web Search Result" : "Local Knowledge Base"}
              </span>
              <span className="text-xs text-muted-foreground">
                #{index + 1}
              </span>
            </div>
            {source.score && (
              <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                {(source.score * 100).toFixed(1)}% match
              </span>
            )}
          </div>

          {/* Web Sources Links */}
          {isWebSource && webSources.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-medium text-muted-foreground">
                Sources:
              </span>
              <div className="space-y-1">
                {webSources.map((webSource: { url: string; title?: string }, webIndex: number) => (
                  <a
                    key={webIndex}
                    href={webSource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="cursor-pointer flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors group"
                  >
                    <ExternalLink className="w-3 h-3 opacity-70 group-hover:opacity-100" />
                    <span className="truncate flex-1 underline decoration-dotted hover:decoration-solid">
                      {webSource.title || webSource.url}
                    </span>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Source Content */}
          <div className="text-sm text-foreground">
            <p className="leading-relaxed overflow-hidden">
              {source.text.length > CHAT_CONSTANTS.SOURCE_TEXT_PREVIEW_LENGTH
                ? source.text.substring(0, CHAT_CONSTANTS.SOURCE_TEXT_PREVIEW_LENGTH) + "..."
                : source.text}
            </p>
          </div>

          {/* Metadata Tags */}
          {source.metadata &&
            Object.keys(source.metadata).filter(
              (key) => !CHAT_CONSTANTS.EXCLUDED_METADATA_KEYS.includes(key as 'source_type' | 'web_sources')
            ).length > 0 && (
              <div className="pt-2 border-t border-muted-foreground/10">
                <div className="flex flex-wrap gap-1">
                  {Object.entries(source.metadata)
                    .filter(
                      ([key]) => !CHAT_CONSTANTS.EXCLUDED_METADATA_KEYS.includes(key as 'source_type' | 'web_sources')
                    )
                    .slice(0, CHAT_CONSTANTS.MAX_METADATA_TAGS)
                    .map(([key, value]) => {
                      // Handle arrays (like tags)
                      if (Array.isArray(value)) {
                        return value.map((item, idx) => (
                          <a 
                            key={`${key}-${idx}-${item}`} 
                            href={String(item)} 
                            target="_blank" 
                            rel="noopener noreferrer"
                          >
                            <span
                              className="inline-flex items-center px-2 py-1 rounded-md text-xs bg-primary/10 text-primary border border-primary/20"
                            >
                              {String(item)}
                            </span>
                          </a>
                        ));
                      }

                      // Handle other metadata
                      return (
                        <span
                          key={key}
                          className="inline-flex items-center px-2 py-1 rounded-md text-xs bg-muted text-muted-foreground border border-muted-foreground/20"
                          title={`${key}: ${String(value)}`}
                        >
                          <span className="font-medium">{key}:</span>
                          <span className="ml-1 max-w-[100px] truncate">
                            {String(value).substring(0, CHAT_CONSTANTS.METADATA_VALUE_PREVIEW_LENGTH)}
                          </span>
                        </span>
                      );
                    })}
                  {Object.keys(source.metadata).filter(
                    (key) => !CHAT_CONSTANTS.EXCLUDED_METADATA_KEYS.includes(key as 'source_type' | 'web_sources')
                  ).length > CHAT_CONSTANTS.MAX_METADATA_TAGS && (
                    <span className="text-xs text-muted-foreground italic">
                      +
                      {Object.keys(source.metadata).filter(
                        (key) => !CHAT_CONSTANTS.EXCLUDED_METADATA_KEYS.includes(key as 'source_type' | 'web_sources')
                      ).length - CHAT_CONSTANTS.MAX_METADATA_TAGS}{" "}
                      more
                    </span>
                  )}
                </div>
              </div>
            )}
        </div>
      </div>
    );
  };

  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="mt-3">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full text-left text-sm font-semibold text-muted-foreground flex items-center gap-2 hover:text-foreground transition-colors p-2 rounded hover:bg-muted/50"
      >
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
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <span>
          Sources & Citations ({sources.length})
        </span>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 ml-auto" />
        ) : (
          <ChevronDown className="w-4 h-4 ml-auto" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-0 max-h-[40vh] overflow-y-auto border border-muted-foreground/20 rounded-lg bg-background/50 shadow-sm">
          {sources.map((source, index) =>
            renderSourceContent(source, index)
          )}
        </div>
      )}
    </div>
  );
}