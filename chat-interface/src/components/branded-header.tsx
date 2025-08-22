import React from 'react';
import { WebstersLogo } from './websters-logo';
import Image from 'next/image';

interface BrandedHeaderProps {
  className?: string;
}

export function BrandedHeader({ className = '' }: BrandedHeaderProps) {
  return (
    <header className={`w-full py-6 px-4 md:px-8 ${className}`}>
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between">
          {/* Primary Brand - Websters Logo */}
          <div className="flex items-center">
            <WebstersLogo size="lg" className="transition-opacity hover:opacity-80" />
          </div>
          
          {/* Secondary Brand - MSR Logo (subtle) */}
          <div className="flex items-center gap-3">
            <div className="relative">
              {/* Use MSR logo based on theme - you can conditionally switch between positive/negative */}
              <Image
                src="/msrlogo_positive.png"
                alt="MSR"
                width={80}
                height={24}
                className="opacity-60 hover:opacity-80 transition-opacity dark:hidden"
                priority
              />
              <Image
                src="/msrlogo_negative.png"
                alt="MSR"
                width={80}
                height={24}
                className="opacity-60 hover:opacity-80 transition-opacity hidden dark:block"
                priority
              />
            </div>
          </div>
        </div>
        
        {/* Subtitle */}
        <div className="mt-4 text-center">
          <p className="text-lg text-muted-foreground font-light">
            Intelligent Chat Interface for Measure&apos;s Data
          </p>
          <div className="w-16 h-0.5 bg-gradient-to-r from-primary to-sidebar-accent mx-auto mt-2 rounded-full"></div>
        </div>
      </div>
    </header>
  );
}

export function BrandedFooter({ className = '' }: { className?: string }) {
  return (
    <footer className={`w-full py-4 px-4 md:px-8 mt-8 border-t border-border/40 ${className}`}>
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground">
          <span>© 2024 Websters</span>
          <span className="w-1 h-1 bg-muted-foreground rounded-full"></span>
          <span>Powered by MSR</span>
          <span className="w-1 h-1 bg-muted-foreground rounded-full"></span>
          <span>Built with LlamaIndex</span>
        </div>
      </div>
    </footer>
  );
}