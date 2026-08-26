"use client";

import { useId } from "react";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

interface ReviewRatingProps {
  value: number;
  onChange?: (value: number) => void;
  disabled?: boolean;
  label?: string;
  name?: string;
  className?: string;
}

const RATINGS = [1, 2, 3, 4, 5] as const;

export function ReviewRating({
  value,
  onChange,
  disabled = false,
  label = "评分",
  name,
  className,
}: ReviewRatingProps) {
  const generatedName = useId();
  const selectedRating = Math.max(0, Math.min(5, value));

  if (!onChange) {
    return (
      <span
        role="img"
        aria-label={`${label}：${selectedRating.toFixed(1)} 分（满分 5 分）`}
        className={cn("inline-flex gap-0.5", className)}
      >
        {RATINGS.map((rating) => (
          <Star
            key={rating}
            aria-hidden="true"
            className={cn(
              "size-4",
              rating <= Math.round(selectedRating)
                ? "fill-rating text-rating"
                : "text-muted-foreground/40",
            )}
          />
        ))}
      </span>
    );
  }

  return (
    <fieldset disabled={disabled} className={className}>
      <legend className="sr-only">{label}</legend>
      <div className="flex gap-1">
        {RATINGS.map((rating) => (
          <label
            key={rating}
            className="has-[:focus-visible]:ring-ring/50 cursor-pointer rounded-sm p-0.5 has-[:focus-visible]:ring-[3px] has-[:disabled]:cursor-not-allowed has-[:disabled]:opacity-50"
          >
            <input
              type="radio"
              name={name ?? generatedName}
              value={rating}
              checked={selectedRating === rating}
              onChange={() => onChange(rating)}
              className="sr-only"
            />
            <Star
              aria-hidden="true"
              className={cn(
                "size-6",
                rating <= selectedRating
                  ? "fill-rating text-rating"
                  : "text-muted-foreground/40",
              )}
            />
            <span className="sr-only">{rating} 分</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
