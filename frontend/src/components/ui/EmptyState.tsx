import { LucideIcon } from 'lucide-react'
import { clsx } from 'clsx'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
    variant?: 'primary' | 'secondary'
  }
  secondaryAction?: {
    label: string
    onClick: () => void
  }
  className?: string
}

export function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  action, 
  secondaryAction,
  className 
}: EmptyStateProps) {
  return (
    <div className={clsx('py-16 text-center', className)}>
      <div className="w-16 h-16 rounded-full bg-surface-elevated flex items-center justify-center mx-auto mb-4">
        <Icon className="w-8 h-8 text-text-muted" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary mb-2">{title}</h3>
      <p className="text-text-secondary mb-6 max-w-md mx-auto">{description}</p>
      <div className="flex flex-col sm:flex-row items-center justify-center gap-2">
        {action && (
          <button
            onClick={action.onClick}
            className={clsx(
              'btn-sm px-4 py-2',
              action.variant === 'secondary' ? 'btn-secondary' : 'btn-primary'
            )}
          >
            {action.label}
          </button>
        )}
        {secondaryAction && (
          <button
            onClick={secondaryAction.onClick}
            className="btn-secondary btn-sm px-4 py-2"
          >
            {secondaryAction.label}
          </button>
        )}
      </div>
    </div>
  )
}