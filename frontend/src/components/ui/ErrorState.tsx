import { AlertCircle, RefreshCw } from 'lucide-react'
import { clsx } from 'clsx'

interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
  retryLabel?: string
  className?: string
  inline?: boolean
}

export function ErrorState({ 
  title = 'Something went wrong', 
  message, 
  onRetry, 
  retryLabel = 'Try again',
  className,
  inline = false
}: ErrorStateProps) {
  const containerClasses = clsx(
    inline ? 'inline-flex' : 'flex',
    'flex-col items-center justify-center gap-4 text-center',
    className
  )

  const cardClasses = clsx(
    'card',
    inline ? '' : 'p-8',
    onRetry && 'border-error/50'
  )

  const content = (
    <div className={containerClasses}>
      <div className={clsx('w-12 h-12 rounded-full bg-error/10 flex items-center justify-center mb-4', inline && 'w-8 h-8')}>
        <AlertCircle className={clsx('w-6 h-6 text-error', inline && 'w-4 h-4')} />
      </div>
      <h3 className={clsx('font-semibold text-text-primary', inline && 'text-sm')}>{title}</h3>
      <p className={clsx('text-text-secondary', inline && 'text-sm')}>{message}</p>
      {onRetry && (
        <button 
          onClick={onRetry} 
          className={clsx('btn-primary mt-2', inline && 'btn-sm')}
        >
          <RefreshCw className="w-4 h-4" />
          {retryLabel}
        </button>
      )}
    </div>
  )

  if (inline) {
    return content
  }

  return <div className={cardClasses}>{content}</div>
}

export function PageErrorState({ 
  title, 
  message, 
  onRetry, 
  retryLabel 
}: Omit<ErrorStateProps, 'inline' | 'className'>) {
  return (
    <ErrorState 
      title={title} 
      message={message} 
      onRetry={onRetry} 
      retryLabel={retryLabel}
      className="py-16"
    />
  )
}