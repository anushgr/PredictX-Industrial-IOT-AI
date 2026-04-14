import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const formatPercent = (value: number) => `${value.toFixed(1)}%`;

export const severityClasses: Record<string, string> = {
  Critical: "text-red-300 bg-red-500/20 border-red-500/40",
  High: "text-orange-300 bg-orange-500/20 border-orange-500/40",
  Medium: "text-amber-300 bg-amber-500/20 border-amber-500/40",
  Low: "text-emerald-300 bg-emerald-500/20 border-emerald-500/40",
};
