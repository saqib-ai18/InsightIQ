import { useState, useMemo, useCallback } from 'react'
import { ChevronUp, ChevronDown, Search, Columns, Download, Minus, Check, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'
import { clsx } from 'clsx'
import { ColumnInfo } from '@/types/dataset'

interface DataTableProps {
  columns: ColumnInfo[]
  data: any[][]
  totalRows: number
  _page: number
  _pageSize: number
  onPageChange: (_page: number) => void
  onPageSizeChange: (_pageSize: number) => void
  onSort: (_column: string, _direction: 'asc' | 'desc') => void
  onFilter: (_column: string, _value: string) => void
  onColumnVisibilityChange: (_column: string, _visible: boolean) => void
  onExport: () => void
  isLoading?: boolean
  sortColumn?: string
  sortDirection?: 'asc' | 'desc'
  filters?: Record<string, string>
  visibleColumns?: string[]
}

export function DataTable({
  columns,
  data,
  totalRows,
  _page,
  _pageSize,
  onPageChange,
  onPageSizeChange,
  onSort,
  onFilter,
  onColumnVisibilityChange,
  onExport,
  isLoading = false,
  sortColumn,
  sortDirection,
  filters = {},
  visibleColumns,
}: DataTableProps) {
  const [columnFilters, setColumnFilters] = useState<Record<string, string>>(filters)
  const [showColumnMenu, setShowColumnMenu] = useState(false)
  const [columnMenuAnchor, setColumnMenuAnchor] = useState<HTMLElement | null>(null)

  const allColumns = useMemo(() => columns.map(c => c.name), [columns])
  const defaultVisible = useMemo(() => columns.map(c => c.name), [columns])
  const visible = visibleColumns || defaultVisible
  const filteredColumns = columns.filter(c => visible.includes(c.name))

  const handleSort = useCallback((column: string) => {
    const direction = sortColumn === column && sortDirection === 'asc' ? 'desc' : 'asc'
    onSort(column, direction)
  }, [sortColumn, sortDirection, onSort])

  const handleFilterChange = (column: string, value: string) => {
    setColumnFilters(prev => ({ ...prev, [column]: value }))
    onFilter(column, value)
  }

  const handleColumnToggle = (column: string, checked: boolean) => {
    onColumnVisibilityChange(column, checked)
  }

  const totalPages = Math.ceil(totalRows / _pageSize)

  const getTypeBadge = (type: string) => {
    const badges: Record<string, string> = {
      integer: 'badge-primary',
      float: 'badge-primary',
      string: 'badge-default',
      boolean: 'badge-success',
      datetime: 'badge-warning',
      date: 'badge-warning',
      category: 'badge-secondary',
    }
    return badges[type] || 'badge-default'
  }

  if (isLoading) {
    return (
      <div className="card">
        <div className="card-content py-16 flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="card-header flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h3 className="card-title">Data Preview</h3>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search all columns..."
              className="input pl-10 w-64"
              onChange={(e) => {
                filteredColumns.forEach(col => handleFilterChange(col.name, e.target.value))
              }}
            />
          </div>
          <button
            onClick={() => setShowColumnMenu(!showColumnMenu)}
            className="btn-secondary btn-sm"
            ref={el => { if (el) setColumnMenuAnchor(el) }}
          >
            <Columns className="w-4 h-4" />
            Columns
          </button>
          <button onClick={onExport} className="btn-secondary btn-sm">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-surface-elevated/50">
              {filteredColumns.map((col) => (
                <th
                  key={col.name}
                  className={clsx(
                    'px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider whitespace-nowrap cursor-pointer hover:bg-surface-hover',
                    sortColumn === col.name && 'text-primary'
                  )}
                  onClick={() => handleSort(col.name)}
                  style={{ userSelect: 'none' }}
                >
                  <div className="flex items-center gap-1.5">
                    <span>{col.name}</span>
                    <span className={clsx('badge text-xs px-1.5 py-0.5', getTypeBadge(col.type))}>
                      {col.type}
                    </span>
                    {col.nullable && <span className="text-xs text-warning" title="Nullable">?</span>}
                    {col.unique && <span className="text-xs text-success" title="Unique">!</span>}
                    {sortColumn === col.name && (
                      sortDirection === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                    )}
                  </div>
                  <input
                    type="text"
                    placeholder="Filter"
                    value={columnFilters[col.name] || ''}
                    onChange={(e) => {
                      e.stopPropagation()
                      handleFilterChange(col.name, e.target.value)
                    }}
                    onClick={(e) => e.stopPropagation()}
                    className="mt-1.5 w-full px-2 py-1 text-xs bg-surface border border-border rounded focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary"
                  />
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {data.map((row, rowIndex) => (
              <tr key={rowIndex} className="hover:bg-surface-elevated/50 transition-colors">
                {filteredColumns.map((_col, colIndex) => (
                  <td key={colIndex} className="px-4 py-3 text-sm text-text-secondary font-mono truncate max-w-xs" title={String(row[colIndex] ?? '')}>
                    {row[colIndex] ?? <span className="text-text-muted italic">null</span>}
                  </td>
                ))}
              </tr>
            ))}
            {data.length === 0 && (
              <tr>
                <td colSpan={filteredColumns.length} className="px-4 py-8 text-center text-text-muted">
                  No data available
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="border-t border-border px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4 text-sm text-text-secondary">
          <span>
            Showing {totalRows > 0 ? (_page - 1) * _pageSize + 1 : 0} to {Math.min(_page * _pageSize, totalRows)} of {totalRows} rows
          </span>
          <select
            value={_pageSize}
            onChange={(e) => { onPageSizeChange(Number(e.target.value)); onPageChange(1); }}
            className="input w-auto px-3 py-1.5 text-sm"
          >
            <option value={10}>10 per page</option>
            <option value={25}>25 per page</option>
            <option value={50}>50 per page</option>
            <option value={100}>100 per page</option>
            <option value={500}>500 per page</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onPageChange(Math.max(1, _page - 1))}
            disabled={_page === 1}
            className="p-2 rounded-lg hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="px-3 text-sm text-text-secondary">
            Page {_page} of {totalPages || 1}
          </span>
          <button
            onClick={() => onPageChange(Math.min(totalPages, _page + 1))}
            disabled={_page === totalPages || totalPages === 0}
            className="p-2 rounded-lg hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {showColumnMenu && columnMenuAnchor && (
        <div
          className="fixed z-popover mt-1 w-56 bg-surface border border-border rounded-xl shadow-xl p-3 animate-in"
          style={{
            top: columnMenuAnchor.getBoundingClientRect().bottom + window.scrollY,
            left: columnMenuAnchor.getBoundingClientRect().left + window.scrollX,
          }}
        >
          <div className="flex items-center justify-between mb-3">
            <p className="font-medium text-text-primary">Visible Columns</p>
            <button onClick={() => setShowColumnMenu(false)} className="p-1 rounded hover:bg-surface-hover">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {allColumns.map((colName) => {
              const col = columns.find(c => c.name === colName)
              const isVisible = visible.includes(colName)
              return (
                <label key={colName} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isVisible}
                    onChange={(e) => handleColumnToggle(colName, e.target.checked)}
                    className="w-4 h-4 rounded border-border text-primary focus-visible:ring-primary"
                  />
                  <span className="text-sm text-text-primary truncate flex-1">{colName}</span>
                  {col && <span className={clsx('badge text-xs', getTypeBadge(col.type))}>{col.type}</span>}
                </label>
              )
            })}
          </div>
          <div className="mt-3 pt-3 border-t border-border flex gap-2">
            <button
              onClick={() => allColumns.forEach(c => onColumnVisibilityChange(c, true))}
              className="btn-secondary btn-sm flex-1"
            >
              <Check className="w-3 h-3" />
              All
            </button>
            <button
              onClick={() => allColumns.forEach(c => onColumnVisibilityChange(c, false))}
              className="btn-secondary btn-sm flex-1"
            >
              <Minus className="w-3 h-3" />
              None
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

import { X } from 'lucide-react'