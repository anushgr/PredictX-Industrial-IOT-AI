"use client";

import * as AvatarPrimitive from "@radix-ui/react-avatar";
import { cn } from "@/lib/utils";

export const Avatar = AvatarPrimitive.Root;

export function AvatarImage({
  className,
  ...props
}: AvatarPrimitive.AvatarImageProps) {
  return <AvatarPrimitive.Image className={cn("h-full w-full", className)} {...props} />;
}

export function AvatarFallback({
  className,
  ...props
}: AvatarPrimitive.AvatarFallbackProps) {
  return (
    <AvatarPrimitive.Fallback
      className={cn(
        "flex h-full w-full items-center justify-center bg-slate-700 text-xs font-semibold text-slate-100",
        className,
      )}
      {...props}
    />
  );
}
