import ReactMarkdown from 'react-markdown';
import { ReactNode } from 'react';

interface MarkdownProps {
  content: string;
  className?: string;
}

export function SafeMarkdown({ content, className = '' }: MarkdownProps): ReactNode {
  return (
    <div className={className}>
      <ReactMarkdown
        components={{
          p: ({ children }) => (
            <p className="break-words">
              {children}
            </p>
          ),
          ul: ({ children }) => (
            <ul className="list-disc list-inside">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-inside">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="break-words">
              {children}
            </li>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="italic">{children}</em>
          ),
          code: ({ children }) => (
            <code className="bg-muted px-1 py-0.5 rounded text-sm">{children}</code>
          ),
          script: () => null,
          iframe: () => null,
          object: () => null,
          embed: () => null,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

// For basic text formatting without full markdown parsing
export function formatBasicText(content: string): string {
  return content
    .replace(/\n\n/g, '\n')
    .replace(/\n/g, '\n');
}