"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/auth-context";
import { LoginModal } from "@/components/login-modal";
import { AuthNavbar } from "@/components/auth-navbar";
import { Loader2 } from "lucide-react";

interface ProtectedWrapperProps {
  children: React.ReactNode;
}

export function ProtectedWrapper({ children }: ProtectedWrapperProps) {
  const { isAuthenticated, loading, user } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);

  useEffect(() => {
    if (!loading) {
      setShowLoginModal(!isAuthenticated());
    }
  }, [loading, isAuthenticated]);

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 mx-auto bg-gradient-to-br from-primary/10 to-sidebar-accent/10 rounded-2xl flex items-center justify-center">
            <Loader2 className="w-8 h-8 text-primary animate-spin" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              Loading...
            </h3>
            <p className="text-muted-foreground">
              Checking authentication status
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Show login modal if not authenticated
  if (!isAuthenticated() || !user) {
    return (
      <>
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
          <div className="text-center space-y-4 max-w-md">
            <div className="w-16 h-16 mx-auto bg-gradient-to-br from-primary/10 to-sidebar-accent/10 rounded-2xl flex items-center justify-center">
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
            <div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                Welcome to Websters
              </h3>
              <p className="text-muted-foreground">
                Please sign in to access the chat interface
              </p>
            </div>
          </div>
        </div>
        <LoginModal 
          isOpen={showLoginModal} 
          onClose={() => setShowLoginModal(false)} 
        />
      </>
    );
  }

  // Render authenticated content
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <AuthNavbar />
      <main className="flex-1 flex flex-col">
        {children}
      </main>
    </div>
  );
}