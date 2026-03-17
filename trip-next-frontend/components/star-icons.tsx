import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

interface StarIconsProps {
  count: number;
  className?: string;
}

export function StarIcons({ count, className }: StarIconsProps) {
  return (
    <span className="inline-flex gap-0.5">
      {Array.from({ length: count }).map((_, i) => (
        <Star
          key={i}
          className={cn("size-3 fill-amber-500 text-amber-500", className)}
        />
      ))}
    </span>
  );
}
