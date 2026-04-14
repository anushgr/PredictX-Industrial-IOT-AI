import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  asChild?: boolean;
  variant?: "default" | "secondary" | "ghost" | "outline" | "destructive";
  size?: "sm" | "md" | "lg" | "icon";
};

export function Button({
  className,
  variant = "default",
  size = "md",
  asChild,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : "button";

  return (
    <Comp
      className={cn(
        "inline-flex items-center justify-center rounded-xl font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 disabled:pointer-events-none disabled:opacity-50",
        {
          "bg-cyan-500 text-slate-950 hover:bg-cyan-400": variant === "default",
          "bg-slate-800 text-slate-100 hover:bg-slate-700": variant === "secondary",
          "hover:bg-slate-800 text-slate-200": variant === "ghost",
          "border border-slate-700 text-slate-200 hover:bg-slate-800":
            variant === "outline",
          "bg-red-500 text-white hover:bg-red-400": variant === "destructive",
          "h-8 px-3 text-xs": size === "sm",
          "h-10 px-4 text-sm": size === "md",
          "h-12 px-5 text-base": size === "lg",
          "h-10 w-10": size === "icon",
        },
        className,
      )}
      {...props}
    />
  );
}
