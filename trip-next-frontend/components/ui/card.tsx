import { cn } from "@/lib/utils";
import * as React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  padding?: "none" | "sm" | "md" | "lg";
  hover?: boolean;
  clickable?: boolean;
}

const paddingClasses = {
  none: "",
  sm: "p-3",
  md: "p-5",
  lg: "p-7",
};

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    { className, padding = "md", hover = false, clickable = false, ...props },
    ref,
  ) => (
    <div
      ref={ref}
      className={cn(
        "rounded-xl border border-gray-100 bg-white shadow-sm",
        paddingClasses[padding],
        hover && "card-hover",
        clickable && "cursor-pointer",
        className,
      )}
      {...props}
    />
  ),
);
Card.displayName = "Card";

export { Card };
