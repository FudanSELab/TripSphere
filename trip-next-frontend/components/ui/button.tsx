import { cn } from "@/lib/utils";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import * as React from "react";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 btn-press",
  {
    variants: {
      variant: {
        default:
          "bg-primary-600 text-white hover:bg-primary-700 shadow-sm hover:shadow-md",
        primary:
          "bg-primary-600 text-white hover:bg-primary-700 shadow-sm hover:shadow-md",
        secondary:
          "bg-secondary-600 text-white hover:bg-secondary-700 shadow-sm hover:shadow-md",
        outline:
          "border-2 border-primary-600 text-primary-600 hover:bg-primary-50",
        ghost: "text-gray-700 hover:bg-gray-100",
        link: "text-primary-600 underline-offset-4 hover:underline",
        destructive: "bg-red-600 text-white hover:bg-red-700 shadow-sm",
        success: "bg-green-600 text-white hover:bg-green-700 shadow-sm",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4",
        lg: "h-12 px-6 text-base",
        xl: "h-14 px-8 text-lg",
        icon: "h-10 w-10",
        "icon-sm": "h-8 w-8",
        "icon-lg": "h-12 w-12",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  },
);

export interface ButtonProps
  extends
    React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      asChild = false,
      loading = false,
      children,
      disabled,
      ...props
    },
    ref,
  ) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? <Loader2 className="h-4 w-4" /> : children}
      </Comp>
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
