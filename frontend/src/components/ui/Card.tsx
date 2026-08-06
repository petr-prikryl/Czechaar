import type { HTMLAttributes } from "react";

import { cn } from "../../utils/cn";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <section
      className={cn("rounded-lg border border-border bg-background p-4 shadow-sm", className)}
      {...props}
    />
  );
}
