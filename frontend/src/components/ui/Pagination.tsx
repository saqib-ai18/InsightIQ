import { ChevronLeft, ChevronRight } from 'lucide-react'
import { clsx } from 'clsx'

interface PaginationProps {
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
  onPageSizeChange: (pageSize: number) => void
  pageSizeOptions?: number[]
  showPageSize?: boolean
  className?: string
}

export function Pagination({ 
  page, 
  pageSize, 
  total, 
  onPageChange, 
  onPageSizeChange,
  pageSizeOptions = [10, 25, 50, 100],
  showPageSize = true,
  className
}: PaginationProps) {
  const totalPages = Math.ceil(total / pageSize)
  const start = total > 0 ? (page - 1) * pageSize + 1 : 0
  const end = Math.min(page * pageSize, total)

  if (totalPages <= 1 && !showPageSize) {
    return null
  }

  return (
    <div className={clsx('card border-t', className)}>
      <div className="border-t border-border px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4 text-sm text-text-secondary">
          {total > 0 && (
            <span>Showing {start.toLocaleString()} to {end.toLocaleString()} of {total.toLocaleString()}</span>
          )}
          {showPageSize && (
            <select
              value={pageSize}
              onChange={(e) => { onPageSizeChange(Number(e.target.value)); onPageChange(1); }}
              className="input w-auto px-3 py-1.5 text-sm"
              aria-label="Rows per page"
            >
              {pageSizeOptions.map((size) => (
                <option key={size} value={size}>{size} per page</option>
              ))}
            </select>
          )}
        </div>
        
        {totalPages > 1 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(Math.max(1, page - 1))}
              disabled={page === 1}
              className={clsx(
                'p-2 rounded-lg hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors',
                page === 1 && 'text-text-muted'
              )}
              aria-label="Previous page"
              aria-disabled={page === 1}
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-3 text-sm text-text-secondary" aria-live="polite">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => onPageChange(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className={clsx(
                'p-2 rounded-lg hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors',
                page === totalPages && 'text-text-muted'
              )}
              aria-label="Next page"
              aria-disabled={page === totalPages}
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}