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
          className={cn("fill-rating text-rating size-3", className)}
        />
      ))}
    </span>
  );
}
