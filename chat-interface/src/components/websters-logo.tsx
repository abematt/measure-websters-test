import React from 'react';

interface WebstersLogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'white' | 'dark';
}

export function WebstersLogo({ 
  className = '', 
  size = 'md', 
  variant = 'default' 
}: WebstersLogoProps) {
  // Size classes for text
  const sizeClasses = {
    sm: 'text-xl',
    md: 'text-2xl',
    lg: 'text-3xl',
    xl: 'text-4xl'
  };

  // Color variants
  const getVariantClasses = () => {
    switch (variant) {
      case 'white':
        return 'text-white';
      case 'dark':
        return 'text-gray-900 dark:text-gray-100';
      default:
        return 'text-gray-900 dark:text-white';
    }
  };

  return (
    <div className={`flex items-center ${className}`}>
      <h1 
        className={`
          font-inter font-semibold tracking-tight
          ${sizeClasses[size]}
          ${getVariantClasses()}
          bg-gradient-to-r from-primary via-primary-darker to-primary-lighter
          bg-clip-text text-transparent
          hover:from-primary-darker hover:via-primary hover:to-primary-lighter
          transition-all duration-300
        `}
        role="img"
        aria-label="Websters Logo"
      >
        Websters
      </h1>
    </div>
  );
}

// Optional: Export a simplified icon-only version with just "W" 
export function WebstersIcon({ 
  className = '', 
  size = 'md'
}: { 
  className?: string; 
  size?: 'sm' | 'md' | 'lg';
}) {
  const sizeClasses = {
    sm: 'text-lg',
    md: 'text-xl', 
    lg: 'text-2xl'
  };

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <span 
        className={`
          font-inter font-bold tracking-tight
          ${sizeClasses[size]}
          bg-gradient-to-r from-primary via-primary-darker to-primary-lighter
          bg-clip-text text-transparent
          hover:from-primary-darker hover:via-primary hover:to-primary-lighter
          transition-all duration-300
        `}
        role="img"
        aria-label="Websters Icon"
      >
        W
      </span>
    </div>
  );
}