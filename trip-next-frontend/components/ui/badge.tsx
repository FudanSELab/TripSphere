import * as React from 'react'
import { cn } from '@/lib/utils'
import { X } from 'lucide-react'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'secondary' | 'outline' | 'success' | 'warning' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  removable?: boolean
  onRemove?: () => void
}

const variantClasses = {
  default: 'bg-primary-100 text-primary-700',
  secondary: 'bg-gray-100 text-gray-700',
  outline: 'bg-transparent border border-gray-300 text-gray-700',
  success: 'bg-green-100 text-green-700',
  warning: 'bg-amber-100 text-amber-700',
  danger: 'bg-red-100 text-red-700',
}

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1.5 text-base',
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', removable = false, onRemove, children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center gap-1 rounded-full font-medium',
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      >
        {children}
        {removable && (
          <button
            type="button"
            onClick={onRemove}
            className="ml-1 rounded-full p-0.5 hover:bg-black/10 transition-colors"
          >
            <X className="w-3 h-3" />
          </button>
        )}
      </span>
    )
  }
)
Badge.displayName = 'Badge'

export { Badge }
