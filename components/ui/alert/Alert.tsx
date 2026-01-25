import { HTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils/cn'

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'success' | 'error' | 'warning' | 'info'
  title?: string
}

export const Alert = forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = 'info', title, children, ...props }, ref) => {
    const variantStyles = {
      success: 'bg-success/10 border-success text-success',
      error: 'bg-danger/10 border-danger text-danger',
      warning: 'bg-warning/10 border-warning text-warning',
      info: 'bg-info/10 border-info text-info',
    }

    return (
      <div
        ref={ref}
        role="alert"
        className={cn(
          'border rounded-md p-4',
          variantStyles[variant],
          className
        )}
        {...props}
      >
        {title && (
          <h4 className="font-semibold mb-2">{title}</h4>
        )}
        <div>{children}</div>
      </div>
    )
  }
)

Alert.displayName = 'Alert'
