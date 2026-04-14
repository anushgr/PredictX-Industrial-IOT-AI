import * as React from "react";
import { cn } from "@/lib/utils";

export function Card({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-800/90 bg-slate-900/65 p-5 shadow-lg shadow-black/20 backdrop-blur",
        className,
      )}
      {...props}
    />
  );
}
