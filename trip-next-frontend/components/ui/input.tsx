import { cn } from "@/lib/utils";
import * as React from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
  hint?: string;
  prepend?: React.ReactNode;
  append?: React.ReactNode;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, label, hint, prepend, append, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="mb-1.5 block text-sm font-medium text-gray-700">
            {label}
          </label>
        )}
        <div className="relative">
          {prepend && (
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
              {prepend}
            </div>
          )}
          <input
            type={type}
            className={cn(
              "w-full rounded-lg border bg-white px-4 py-2.5 text-gray-900 transition-all duration-200",
              "placeholder:text-gray-400",
              "focus:ring-primary-500 focus:border-transparent focus:ring-2 focus:outline-none",
              "disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500",
              error
                ? "border-red-500 focus:ring-red-500"
                : "border-gray-200 hover:border-gray-300",
              prepend && "pl-10",
              append && "pr-10",
              className,
            )}
            ref={ref}
            {...props}
          />
          {append && (
            <div className="absolute inset-y-0 right-0 flex items-center pr-3">
              {append}
            </div>
          )}
        </div>
        {error && <p className="mt-1.5 text-sm text-red-600">{error}</p>}
        {hint && !error && (
          <p className="mt-1.5 text-sm text-gray-500">{hint}</p>
        )}
      </div>
    );
  },
);
Input.displayName = "Input";

export { Input };
