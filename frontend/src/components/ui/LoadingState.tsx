import { Loader2 } from 'lucide-react'
import { clsx } from 'clsx'

interface LoadingStateProps {
  message?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
  inline?: boolean
}

export function LoadingState({ 
  message = 'Loading...', 
  size = 'md', 
  className,
  inline = false
}: LoadingStateProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  }

  const containerClasses = clsx(
    inline ? 'inline-flex' : 'flex',
    'items-center justify-center gap-2',
    className
  )

  return (
    <div className={containerClasses}>
      <Loader2 className={`${sizeClasses[size]} text-primary animate-spin`} />
      {!inline && message && <span className="text-text-secondary">{message}</span>}
      {inline && message && <span className="text-sm text-text-secondary">{message}</span>}
    </div>
  )
}

export function PageLoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="card">
      <div className="card-content py-16">
        <LoadingState message={message} size="lg" />
      </div>
    </div>
  )
}

export function TableLoadingState({ rows = 5, columns = 5 }: { rows?: number; columns?: number }) {
  return (
    <div className="card">
      <div className="card-content p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-surface-elevated/50">
                {Array.from({ length: columns }).map((_, i) => (
                  <th key={i} className="px-4 py-3">
                    <div className="h-4 w-3/4 bg-surface-elevated rounded animate-pulse" />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {Array.from({ length: rows }).map((_, rowIndex) => (
                <tr key={rowIndex}>
                  {Array.from({ length: columns }).map((_, colIndex) => (
                    <td key={colIndex} className="px-4 py-3">
                      <div className="h-4 w-full bg-surface-elevated rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export function ChartLoadingState({ height = '400px' }: { height?: string }) {
  return (
    <div className="card" style={{ minHeight: height }}>
      <div className="card-content p-0" style={{ height }}>
        <LoadingState message="Rendering chart..." size="lg" />
      </div>
    </div>
  )
}