"use client";

import { Button } from "@/components/ui/button";
import { LogOut, User, Shield } from "lucide-react";
import { useAuth } from "@/contexts/auth-context";
import { WebstersLogo } from "./websters-logo";
import Image from "next/image";

interface AuthNavbarProps {
  className?: string;
}

export function AuthNavbar({ className = "" }: AuthNavbarProps) {
  const { user, logout, isAuthenticated } = useAuth();

  if (!isAuthenticated() || !user) {
    return null;
  }

  const handleLogout = () => {
    logout();
  };

  return (
    <div
      className={`flex items-center justify-between py-4 px-4 md:px-8 border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 ${className}`}
    >
      {/* Left side - Websters Logo */}
      <div className="flex-col items-baseline gap-2">
        <div>
          {/* Center - MSR Logo */}
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

        <WebstersLogo
          size="md"
          className="transition-opacity hover:opacity-80"
        />
      </div>

      {/* Right side - User info and logout */}
      <div className="flex items-center gap-4">
        {/* User info */}
        <div className="flex items-center gap-2 text-sm">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-muted/50 rounded-full">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <User className="w-4 h-4 text-muted-foreground" />
            <span className="font-medium text-foreground">{user.username}</span>
            {user.is_active && <Shield className="w-3 h-3 text-green-600" />}
          </div>
        </div>

        {/* Logout button */}
        <Button
          variant="outline"
          size="sm"
          onClick={handleLogout}
          className="gap-2 hover:bg-destructive/10 hover:text-destructive hover:border-destructive/20"
          title="Sign out"
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden sm:inline">Sign Out</span>
        </Button>
      </div>
    </div>
  );
}
