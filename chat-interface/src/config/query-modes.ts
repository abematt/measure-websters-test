"use client";

import { type LucideIcon, Database, Globe, Sparkles } from "lucide-react";
import { type QueryMode } from "@/lib/api";

export interface QueryModeConfig {
  value: QueryMode;
  label: string;
  description: string;
  icon: LucideIcon;
  behavior: QueryMode;
  default?: boolean;
}

export const QUERY_MODES: QueryModeConfig[] = [
  {
    value: "basic",
    label: "Basic",
    icon: Database,
    description: "Database only",
    behavior: "basic",
  },
  {
    value: "combined",
    label: "Web Enhanced",
    icon: Globe,
    description: "Automatic web search",
    behavior: "combined",
  },
  {
    value: "enhanced",
    label: "Two Step",
    icon: Sparkles,
    description: "Controlled web search",
    behavior: "enhanced",
    default: true,
  },
];

export function getModeByValue(
  value: QueryMode,
  modes: QueryModeConfig[] = QUERY_MODES
): QueryModeConfig {
  return modes.find((m) => m.value === value) ?? modes[0];
}

export function getDefaultModeValue(
  modes: QueryModeConfig[] = QUERY_MODES
): QueryMode {
  return (modes.find((m) => m.default) ?? modes[0]).value;
}


