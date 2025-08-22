import { Globe, ExternalLink } from "lucide-react";
import { SafeMarkdown } from "@/utils/markdown";
import type { WebEnrichmentResponse } from "@/lib/api";

interface WebSearchResultsProps {
  webResponse: WebEnrichmentResponse;
}

export function WebSearchResults({ webResponse }: WebSearchResultsProps) {
  const results = webResponse.web_search_results || [];
  
  return (
    <div className="mt-4 border border-blue-200 dark:border-blue-800 rounded-lg bg-blue-50/30 dark:bg-blue-950/20">
      <div className="p-4 border-b border-blue-200 dark:border-blue-800">
        <div className="flex items-center gap-2">
          <Globe className="w-5 h-5 text-blue-500" />
          <h4 className="font-semibold text-blue-700 dark:text-blue-300">Web Context</h4>
        </div>
      </div>
      <div className="p-4">
        <div className="prose prose-sm max-w-none dark:prose-invert">
          <SafeMarkdown 
            content={webResponse.enriched_response || ''} 
            className="whitespace-pre-wrap break-words"
          />
        </div>
        
        {results.length > 0 && (
          <div className="mt-4 pt-4 border-t border-blue-200 dark:border-blue-800">
            <span className="text-sm font-medium text-muted-foreground mb-2 block">
              Sources ({webResponse.sources_fetched} fetched):
            </span>
            <div className="space-y-2">
              {results.map((result, index) => (
                <a
                  key={index}
                  href={result.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-start gap-2 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors group p-2 rounded hover:bg-blue-50/50 dark:hover:bg-blue-950/30"
                >
                  <ExternalLink className="w-3 h-3 opacity-70 group-hover:opacity-100 mt-0.5 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <div className="font-medium underline decoration-dotted hover:decoration-solid">
                      {result.title || result.link}
                    </div>
                    {result.snippet && (
                      <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {result.snippet}
                      </div>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground flex-shrink-0">
                    #{result.position}
                  </span>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}