import { TextareaHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils/cn'

export interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean
}

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          'w-full px-4 py-2 border rounded-md bg-surface text-text',
          'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'resize-y min-h-[100px]',
          error && 'border-danger focus:ring-danger',
          !error && 'border-neutral/20',
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)

TextArea.displayName = 'TextArea'
