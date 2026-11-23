import { useState, useEffect, useCallback } from 'react'
import { Download, Database, AlertCircle, RefreshCw } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { DataTable } from '@/components/datasets/DataTable'
import { api } from '@/services/api'
import { ColumnInfo, DataPreview } from '@/types/dataset'
import { useToast } from '@/hooks/useToast'

export function DataExplorerPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { success, error: toastError } = useToast()
  
  const datasetId = searchParams.get('dataset')
  const [page, setPage] = useState(Number(searchParams.get('page')) || 1)
  const [pageSize, setPageSize] = useState(Number(searchParams.get('pageSize')) || 50)
  const [search] = useState(searchParams.get('search') || '')
  const [sortColumn, setSortColumn] = useState(searchParams.get('sortColumn') || '')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>(searchParams.get('sortDirection') as 'asc' | 'desc' || 'asc')
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [visibleColumns, setVisibleColumns] = useState<string[]>([])
  const [columns, setColumns] = useState<ColumnInfo[]>([])

  useEffect(() => {
    const params = new URLSearchParams()
    params.set('page', String(page))
    params.set('pageSize', String(pageSize))
    if (search) params.set('search', search)
    if (sortColumn) params.set('sortColumn', sortColumn)
    if (sortDirection) params.set('sortDirection', sortDirection)
    setSearchParams(params, { replace: true })
  }, [page, pageSize, search, sortColumn, sortDirection, setSearchParams])

  const { data: preview, isLoading, error, refetch } = useQuery<DataPreview>({
    queryKey: ['data-preview', datasetId, page, pageSize, search, sortColumn, sortDirection, filters],
    queryFn: () => {
      if (!datasetId) return Promise.resolve({ columns: [], rows: [], total_rows: 0, page: 1, page_size: pageSize })
      return api.datasets.preview(datasetId, page, pageSize)
    },
    enabled: !!datasetId,
    staleTime: 30000,
  })

  const { data: columnsData } = useQuery<{ columns: ColumnInfo[] }>({
    queryKey: ['dataset-columns', datasetId],
    queryFn: () => api.datasets.getColumns(datasetId!),
    enabled: !!datasetId,
    staleTime: 60000,
  })

  useEffect(() => {
    if (columnsData?.columns) {
      setColumns(columnsData.columns)
      if (visibleColumns.length === 0) {
        setVisibleColumns(columnsData.columns.map((c: ColumnInfo) => c.name))
      }
    }
  }, [columnsData, visibleColumns.length])

  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage)
  }, [])

  const handlePageSizeChange = useCallback((newPageSize: number) => {
    setPageSize(newPageSize)
    setPage(1)
  }, [])

  const handleSort = useCallback((column: string, direction: 'asc' | 'desc') => {
    setSortColumn(column)
    setSortDirection(direction)
    setPage(1)
  }, [])

  const handleFilter = useCallback((column: string, value: string) => {
    setFilters(prev => ({ ...prev, [column]: value }))
    setPage(1)
  }, [])

  const handleColumnVisibilityChange = useCallback((column: string, visible: boolean) => {
    setVisibleColumns(prev => visible
      ? [...prev, column]
      : prev.filter(c => c !== column)
    )
  }, [])

  const handleExport = useCallback(async () => {
    if (!datasetId) return
    try {
      window.open(`/api/datasets/${datasetId}/download?format=csv`, '_blank')
      success('Export started')
    } catch {
      toastError('Export failed')
    }
  }, [datasetId, success, toastError])

  const handleRefresh = useCallback(() => {
    refetch()
  }, [refetch])

  if (!datasetId) {
    return (
      <div className="space-y-6 animate-in">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
              <Database className="text-primary" />
              Data Explorer
            </h1>
            <p className="mt-2 text-text-secondary">Select a dataset from the Datasets page to explore</p>
          </div>
        </div>
        <div className="card">
          <div className="card-content py-16 text-center">
            <div className="w-16 h-16 rounded-full bg-surface-elevated flex items-center justify-center mx-auto mb-4">
              <Database className="w-8 h-8 text-text-muted" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">No Dataset Selected</h3>
            <p className="text-text-secondary mb-6">Navigate to the Datasets page and click the Explore button on a dataset</p>
          </div>
        </div>
      </div>
    )
  }

  const totalRows = preview?.total_rows || 0
  const data = preview?.rows || []
  const previewColumns = preview?.columns || columns

  return (
    <div className="space-y-6 animate-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            <Database className="text-primary" />
            Data Explorer
          </h1>
          <p className="mt-2 text-text-secondary">Explore and filter your dataset interactively</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleRefresh} disabled={isLoading} className="btn-secondary">
            <RefreshCw className={clsx('w-4 h-4', isLoading && 'animate-spin')} />
            Refresh
          </button>
          <button onClick={handleExport} className="btn-secondary">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {error && (
        <div className="card border-error/50">
          <div className="card-content py-8 text-center">
            <div className="w-12 h-12 rounded-full bg-error/10 flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-6 h-6 text-error" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">Failed to load data</h3>
            <p className="text-text-secondary mb-4">{error.message}</p>
            <button onClick={handleRefresh} className="btn-primary">
              <RefreshCw className="w-4 h-4" />
              Retry
            </button>
          </div>
        </div>
      )}

      <DataTable
        columns={previewColumns}
        data={data}
        totalRows={totalRows}
        _page={page}
        _pageSize={pageSize}
        onPageChange={handlePageChange}
        onPageSizeChange={handlePageSizeChange}
        onSort={handleSort}
        onFilter={handleFilter}
        onColumnVisibilityChange={handleColumnVisibilityChange}
        onExport={handleExport}
        isLoading={isLoading}
        sortColumn={sortColumn}
        sortDirection={sortDirection}
        filters={filters}
        visibleColumns={visibleColumns}
      />

      {previewColumns.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Column Statistics</h3>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {previewColumns.slice(0, 8).map((col: ColumnInfo) => (
                <div key={col.name} className="p-4 bg-surface-elevated rounded-lg border border-border">
                  <p className="font-medium text-text-primary mb-1 truncate">{col.name}</p>
                  <p className="text-sm text-text-muted">{col.type}</p>
                  <div className="mt-2 space-y-1 text-xs text-text-secondary">
                    <div className="flex justify-between">
                      <span>Nulls:</span>
                      <span>{col.stats?.missing ?? 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Unique:</span>
                      <span>{col.stats?.unique ?? col.stats?.cardinality_ratio ? `${Math.round(col.stats.cardinality_ratio * 100)}%` : 'N/A'}</span>
                    </div>
                    {col.stats?.mean !== undefined && (
                      <div className="flex justify-between">
                        <span>Mean:</span>
                        <span>{Number(col.stats.mean).toFixed(2)}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

import { clsx } from 'clsx'