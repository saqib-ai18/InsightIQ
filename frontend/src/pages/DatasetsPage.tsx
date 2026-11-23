import { useState } from 'react'
import { Database, Trash2, Eye, Download, RefreshCw, Loader2, Search } from 'lucide-react'
import { clsx } from 'clsx'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileUpload } from '@/components/datasets/FileUpload'
import { api } from '@/services/api'
import { DatasetMetadata, DatasetListResponse } from '@/types/dataset'
import { useToast } from '@/hooks/useToast'
import { EmptyState, LoadingState, ErrorState, Pagination } from '@/components/ui'

interface DatasetRow extends DatasetMetadata {
  qualityPercent: number
}

export function DatasetsPage() {
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')

  const { data: datasetsResponse, isLoading, error, refetch } = useQuery<DatasetListResponse>({
    queryKey: ['datasets', page, pageSize, search],
    queryFn: () => api.datasets.list(page, pageSize, search),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.datasets.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      success('Dataset deleted')
    },
    onError: (error: Error) => {
      toastError(error.message)
    },
  })

  const handleUploadComplete = () => {
    queryClient.invalidateQueries({ queryKey: ['datasets'] })
  }

  const datasets = datasetsResponse?.datasets || []
  const total = datasetsResponse?.total || 0

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  if (isLoading) {
    return (
      <div className="space-y-6 animate-in">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
              <Database className="text-primary" />
              Datasets
            </h1>
            <p className="mt-2 text-text-secondary">Manage and explore your uploaded datasets</p>
          </div>
        </div>
        <LoadingState message="Loading datasets..." size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6 animate-in">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
              <Database className="text-primary" />
              Datasets
            </h1>
            <p className="mt-2 text-text-secondary">Manage and explore your uploaded datasets</p>
          </div>
        </div>
        <ErrorState
          title="Failed to load datasets"
          message={error.message}
          onRetry={() => refetch()}
        />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            <Database className="text-primary" />
            Datasets
          </h1>
          <p className="mt-2 text-text-secondary">Manage and explore your uploaded datasets</p>
        </div>
        <FileUpload onUploadComplete={handleUploadComplete} />
      </div>

      <div className="card">
        <div className="card-content py-4">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              type="text"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search datasets..."
              className="input pl-10"
            />
          </div>
        </div>
      </div>

      {datasets.length === 0 ? (
        <EmptyState
          icon={Database}
          title="No Datasets Yet"
          description="Upload your first dataset to start analyzing"
          action={{
            label: 'Upload Dataset',
            onClick: () => {}, // FileUpload handles its own click
            variant: 'primary'
          }}
        />
      ) : (
        <>
          <div className="card">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">Dataset</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">Size</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">Rows × Cols</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">Quality</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">Uploaded</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-text-muted uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {datasets.map((dataset) => {
                    const row = dataset as DatasetRow
                    row.qualityPercent = Math.max(0, Math.round((1 - dataset.missing_values / Math.max(1, dataset.row_count)) * 100))
                    return (
                      <tr key={dataset.id} className="hover:bg-surface-elevated/50 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-primary/15 flex items-center justify-center">
                              <Database className="w-5 h-5 text-primary" />
                            </div>
                            <div>
                              <p className="font-medium text-text-primary truncate max-w-xs">{dataset.name}</p>
                              <p className="text-xs text-text-muted">{dataset.file_type.toUpperCase()}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="badge badge-primary">{dataset.file_type.toUpperCase()}</span>
                        </td>
                        <td className="px-6 py-4 text-text-secondary">{formatSize(dataset.file_size_bytes)}</td>
                        <td className="px-6 py-4 text-text-secondary">{dataset.row_count.toLocaleString()} × {dataset.column_count}</td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <div className="w-24 h-2 bg-surface-elevated rounded-full overflow-hidden">
                              <div
                                className={clsx(
                                  'h-full rounded-full transition-all duration-300',
                                  row.qualityPercent >= 80 ? 'bg-success' : row.qualityPercent >= 60 ? 'bg-warning' : 'bg-error'
                                )}
                                style={{ width: `${row.qualityPercent}%` }}
                              />
                            </div>
                            <span className="text-xs text-text-muted">{row.qualityPercent}%</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-text-secondary">{formatDate(dataset.created_at)}</td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              onClick={() => window.open(`/data-explorer?dataset=${dataset.id}`, '_blank')}
                              className="p-2 rounded-lg hover:bg-surface-hover text-text-secondary transition-colors"
                              aria-label="Explore"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => api.datasets.download(dataset.id)}
                              className="p-2 rounded-lg hover:bg-surface-hover text-text-secondary transition-colors"
                              aria-label="Download"
                            >
                              <Download className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => api.datasets.getProfile(dataset.id)}
                              className="p-2 rounded-lg hover:bg-surface-hover text-text-secondary transition-colors"
                              aria-label="View profile"
                            >
                              <RefreshCw className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => deleteMutation.mutate(dataset.id)}
                              disabled={deleteMutation.isPending}
                              className="p-2 rounded-lg hover:bg-error/10 hover:text-error text-text-secondary transition-colors disabled:opacity-50"
                              aria-label="Delete"
                            >
                              {deleteMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            <Pagination
              page={page}
              pageSize={pageSize}
              total={total}
              onPageChange={setPage}
              onPageSizeChange={setPageSize}
            />
          </div>
        </>
      )}
    </div>
  )
}