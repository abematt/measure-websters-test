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
    label: "Basic Search",
    icon: Database,
    description: "Only Embedding Search",
    behavior: "basic",
  },
  {
    value: "enhanced",
    label: "Two Step",
    icon: Sparkles,
    description: "Embedding + Manual Web Search",
    behavior: "enhanced",
    default: true,
  },
  {
    value: "combined",
    label: "Auto Web Search",
    icon: Globe,
    description: "Embedding + ChatGPT Web Search",
    behavior: "combined",
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
