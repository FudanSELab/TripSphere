import * as React from 'react'
import * as AvatarPrimitive from '@radix-ui/react-avatar'
import { cn, getAvatarColor, getInitials } from '@/lib/utils'

interface AvatarProps extends React.ComponentPropsWithoutRef<typeof AvatarPrimitive.Root> {
  src?: string
  alt?: string
  name?: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
}

const sizeClasses = {
  xs: 'w-6 h-6 text-xs',
  sm: 'w-8 h-8 text-sm',
  md: 'w-10 h-10 text-base',
  lg: 'w-12 h-12 text-lg',
  xl: 'w-16 h-16 text-xl',
}

const Avatar = React.forwardRef<
  React.ElementRef<typeof AvatarPrimitive.Root>,
  AvatarProps
>(({ className, src, alt, name, size = 'md', ...props }, ref) => {
  const initials = name ? getInitials(name) : '?'
  const bgColor = name ? getAvatarColor(name) : 'bg-gray-400'

  return (
    <AvatarPrimitive.Root
      ref={ref}
      className={cn(
        'relative rounded-full overflow-hidden flex items-center justify-center font-semibold text-white',
        sizeClasses[size],
        bgColor,
        className
      )}
      {...props}
    >
      {src && (
        <AvatarPrimitive.Image
          src={src}
          alt={alt || name || 'Avatar'}
          className="w-full h-full object-cover"
        />
      )}
      <AvatarPrimitive.Fallback
        className={cn('w-full h-full flex items-center justify-center', bgColor)}
      >
        {initials}
      </AvatarPrimitive.Fallback>
    </AvatarPrimitive.Root>
  )
})
Avatar.displayName = 'Avatar'

export { Avatar }
