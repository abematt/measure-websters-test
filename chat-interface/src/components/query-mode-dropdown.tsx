"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  QUERY_MODES,
  type QueryModeConfig,
  getModeByValue,
} from "@/config/query-modes";
import { type QueryMode } from "@/lib/api";

export interface QueryModeDropdownProps {
  value: QueryMode;
  onValueChange: (value: QueryMode) => void;
  modes?: QueryModeConfig[];
  buttonClassName?: string;
}

export function QueryModeDropdown({
  value,
  onValueChange,
  modes = QUERY_MODES,
  buttonClassName,
}: QueryModeDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentMode = getModeByValue(value, modes);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className={cn("justify-between min-w-[140px] gap-2", buttonClassName)}
      >
        <div className="flex items-center gap-2">
          {currentMode && <currentMode.icon className="w-4 h-4" />}
          <span>{currentMode?.label}</span>
        </div>
        <ChevronDown
          className={cn("w-4 h-4 transition-transform duration-200", isOpen && "rotate-180")}
        />
      </Button>

      {isOpen && (
        <div className="absolute top-full mt-1 w-full min-w-[200px] bg-background border border-border rounded-md shadow-lg z-50 overflow-hidden">
          {modes.map((mode) => {
            const Icon = mode.icon;
            const isSelected = mode.value === value;

            return (
              <button
                key={mode.value}
                onClick={() => {
                  onValueChange(mode.value);
                  setIsOpen(false);
                }}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2.5 text-left text-sm hover:bg-accent transition-colors",
                  isSelected && "bg-accent"
                )}
              >
                <Icon className="w-4 h-4 text-muted-foreground" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium">{mode.label}</div>
                  <div className="text-xs text-muted-foreground truncate">{mode.description}</div>
                </div>
                {isSelected && <Check className="w-4 h-4 text-primary" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default QueryModeDropdown;


