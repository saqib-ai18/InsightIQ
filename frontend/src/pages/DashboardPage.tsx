import { BarChart3, Plus, LayoutGrid, Trash2, RefreshCw, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import { ChartWrapper } from '@/components/charts/ChartWrapper'
import { useToast } from '@/hooks/useToast'
import { EmptyState, LoadingState, ErrorState, Pagination, Modal } from '@/components/ui'

interface DashboardWidget {
  id: string
  title: string
  chart_type: string
  config: any
  dataset_id: string
  x: number
  y: number
  w: number
  h: number
}

interface Dashboard {
  id: string
  name: string
  description: string | null
  dataset_id: string
  widgets: DashboardWidget[]
  created_at: string
  updated_at: string
}

interface DashboardListResponse {
  dashboards: Dashboard[]
  total: number
  page: number
  page_size: number
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function DashboardPage() {
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(6)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newDashboardName, setNewDashboardName] = useState('')
  const [newDashboardDataset, setNewDashboardDataset] = useState('')
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)

  const { data: dashboardsResponse, isLoading, error, refetch } = useQuery<DashboardListResponse>({
    queryKey: ['dashboards', page, pageSize],
    queryFn: () => api.dashboards.list(page, pageSize),
  })

  const { data: datasetsResponse } = useQuery({
    queryKey: ['datasets', 1, 100, ''],
    queryFn: () => api.datasets.list(1, 100, ''),
  })

  const createMutation = useMutation({
    mutationFn: (dashboard: { name: string; dataset_id: string }) => api.dashboards.create(dashboard),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] })
      setShowCreateModal(false)
      setNewDashboardName('')
      setNewDashboardDataset('')
      success('Dashboard created')
    },
    onError: (error: Error) => {
      toastError(error.message)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.dashboards.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] })
      setDeleteConfirmId(null)
      success('Dashboard deleted')
    },
    onError: (error: Error) => {
      toastError(error.message)
    },
  })

  const refreshMutation = useMutation({
    mutationFn: (id: string) => api.dashboards.refresh(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] })
      success('Dashboard refreshed')
    },
    onError: (error: Error) => {
      toastError(error.message)
    },
  })

  const dashboards = dashboardsResponse?.dashboards || []
  const total = dashboardsResponse?.total || 0
  const datasets = datasetsResponse?.datasets || []

  const handleDeleteConfirm = (id: string) => {
    setDeleteConfirmId(id)
  }

  const handleDeleteConfirmYes = () => {
    if (deleteConfirmId) {
      deleteMutation.mutate(deleteConfirmId)
    }
  }

  return (
    <div className="space-y-6 animate-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            <BarChart3 className="text-primary" />
            Dashboards
          </h1>
          <p className="mt-2 text-text-secondary">Create and manage analytical dashboards for your datasets</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowCreateModal(true)} className="btn-primary">
            <Plus className="w-4 h-4" />
            New Dashboard
          </button>
        </div>
      </div>

      {isLoading && <LoadingState message="Loading dashboards..." size="lg" />}

      {error && (
        <ErrorState
          title="Failed to load dashboards"
          message={error.message}
          onRetry={() => refetch()}
        />
      )}

      {!isLoading && !error && dashboards.length === 0 && (
        <EmptyState
          icon={BarChart3}
          title="No Dashboards Yet"
          description="Create your first dashboard to visualize key metrics and trends from your data. Dashboards automatically adapt to your dataset's structure."
          action={{
            label: 'Create Dashboard',
            onClick: () => setShowCreateModal(true),
          }}
        />
      )}

      {!isLoading && !error && dashboards.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {dashboards.map((dashboard) => (
            <DashboardCard
              key={dashboard.id}
              dashboard={dashboard}
              onDelete={() => handleDeleteConfirm(dashboard.id)}
              onRefresh={() => refreshMutation.mutate(dashboard.id)}
              isRefreshing={refreshMutation.isPending}
              isDeleting={deleteMutation.isPending}
            />
          ))}
        </div>
      )}

      <Pagination
        page={page}
        pageSize={pageSize}
        total={total}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />

      {showCreateModal && (
        <CreateDashboardModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSubmit={(name, datasetId) => createMutation.mutate({ name, dataset_id: datasetId })}
          isLoading={createMutation.isPending}
          datasets={datasets}
          selectedDataset={newDashboardDataset}
          setSelectedDataset={setNewDashboardDataset}
          name={newDashboardName}
          setName={setNewDashboardName}
        />
      )}

      {deleteConfirmId && (
        <Modal
          isOpen={true}
          onClose={() => setDeleteConfirmId(null)}
          title="Delete Dashboard"
          size="sm"
        >
          <p className="text-text-secondary">Are you sure you want to delete this dashboard? This action cannot be undone.</p>
          <div className="flex justify-end gap-2 mt-4">
            <button onClick={() => setDeleteConfirmId(null)} className="btn-secondary" disabled={deleteMutation.isPending}>
              Cancel
            </button>
            <button onClick={handleDeleteConfirmYes} className="btn-destructive" disabled={deleteMutation.isPending}>
              {deleteMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Delete'}
            </button>
          </div>
        </Modal>
      )}
    </div>
  )
}

function DashboardCard({ dashboard, onDelete, onRefresh, isRefreshing, isDeleting }: {
  dashboard: Dashboard
  onDelete: () => void
  onRefresh: () => void
  isRefreshing: boolean
  isDeleting: boolean
}) {
  return (
    <div className="card group hover:border-primary/30 transition-colors">
      <div className="card-header flex items-center justify-between">
        <h3 className="card-title">{dashboard.name}</h3>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button onClick={onRefresh} disabled={isRefreshing} className="p-2 rounded hover:bg-surface-hover transition-colors" aria-label="Refresh">
            {isRefreshing ? <Loader2 className="w-4 h-4 animate-spin text-text-muted" /> : <RefreshCw className="w-4 h-4 text-text-muted" />}
          </button>
          <button onClick={() => window.open(`/dashboard/${dashboard.id}`, '_blank')} className="p-2 rounded hover:bg-surface-hover transition-colors" aria-label="View">
            <LayoutGrid className="w-4 h-4 text-text-muted" />
          </button>
          <button onClick={onDelete} disabled={isDeleting} className="p-2 rounded hover:bg-error/10 hover:text-error text-text-secondary transition-colors disabled:opacity-50" aria-label="Delete">
            {isDeleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
          </button>
        </div>
      </div>
      <div className="card-content">
        {dashboard.widgets.length > 0 ? (
          <div className="grid grid-cols-2 gap-2">
            {dashboard.widgets.slice(0, 4).map((widget) => (
              <div key={widget.id} className="aspect-video bg-surface-elevated rounded-lg border border-border relative overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center">
                  <WidgetPreview widget={widget} />
                </div>
              </div>
            ))}
            {dashboard.widgets.length > 4 && (
              <div className="aspect-video bg-surface-elevated rounded-lg border border-border flex items-center justify-center">
                <span className="text-text-muted text-sm">+{dashboard.widgets.length - 4} more widgets</span>
              </div>
            )}
          </div>
        ) : (
          <div className="aspect-video bg-surface-elevated rounded-lg flex items-center justify-center border border-border">
            <span className="text-text-muted">No widgets</span>
          </div>
        )}
      </div>
      <div className="card-footer text-sm text-text-secondary flex items-center justify-between">
        <span>{dashboard.widgets.length} widgets</span>
        <span>Updated {formatDate(dashboard.updated_at)}</span>
      </div>
    </div>
  )
}

function WidgetPreview({ widget }: { widget: DashboardWidget }) {
  const chartType = widget.chart_type
  
  if (chartType === 'pie' || chartType === 'donut') {
    return (
      <ChartWrapper
        data={{
          type: chartType,
          categories: ['A', 'B', 'C', 'D', 'E'],
          series: [{
            name: 'Distribution',
            data: [
              { value: 30, name: 'A' },
              { value: 25, name: 'B' },
              { value: 20, name: 'C' },
              { value: 15, name: 'D' },
              { value: 10, name: 'E' },
            ],
          }],
        }}
        height="100%"
      />
    )
  }
  
  if (chartType === 'histogram') {
    return (
      <ChartWrapper
        data={{
          type: chartType,
          series: [{
            name: 'Values',
            data: Array.from({ length: 50 }, () => Math.random() * 100),
          }],
        }}
        height="100%"
      />
    )
  }
  
  if (chartType === 'scatter') {
    return (
      <ChartWrapper
        data={{
          type: chartType,
          series: [{
            name: 'Scatter',
            data: Array.from({ length: 30 }, () => ({
              value: [Math.random() * 100, Math.random() * 100],
            })),
          }],
        }}
        height="100%"
      />
    )
  }
  
  if (chartType === 'heatmap') {
    return (
      <ChartWrapper
        data={{
          type: chartType,
          categories: ['A', 'B', 'C', 'D', 'E'],
          series: [{
            name: 'Correlation',
            data: Array.from({ length: 25 }, (_, i) => [
              i % 5,
              Math.floor(i / 5),
              (Math.random() * 2 - 1).toFixed(2),
            ]),
          }],
        }}
        height="100%"
      />
    )
  }
  
  return (
    <ChartWrapper
      data={{
        type: chartType === 'area' ? 'area' : 'bar',
        categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        series: [{
          name: 'Series 1',
          data: [120, 132, 101, 134, 90, 230, 210],
        }],
      }}
      height="100%"
    />
  )
}

function CreateDashboardModal({ isOpen, onClose, onSubmit, isLoading, datasets, selectedDataset, setSelectedDataset, name, setName }: {
  isOpen: boolean
  onClose: () => void
  onSubmit: (name: string, datasetId: string) => void
  isLoading: boolean
  datasets: any[]
  selectedDataset: string
  setSelectedDataset: (id: string) => void
  name: string
  setName: (name: string) => void
}) {
  if (!isOpen) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create Dashboard"
      size="md"
    >
      <div className="space-y-4">
        <div>
          <label className="label">Dashboard Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Sales Overview"
            className="input"
            autoFocus
          />
        </div>
        <div>
          <label className="label">Dataset</label>
          <select
            value={selectedDataset}
            onChange={(e) => setSelectedDataset(e.target.value)}
            className="input"
          >
            <option value="">Select a dataset...</option>
            {datasets.map((ds: any) => (
              <option key={ds.id} value={ds.id}>{ds.name} ({ds.row_count} rows)</option>
            ))}
          </select>
        </div>
      </div>
      <div className="flex justify-end gap-2 mt-6 pt-4 border-t border-border">
        <button onClick={onClose} className="btn-secondary" disabled={isLoading}>Cancel</button>
        <button onClick={() => onSubmit(name, selectedDataset)} disabled={isLoading || !name || !selectedDataset} className="btn-primary">
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create Dashboard'}
        </button>
      </div>
    </Modal>
  )
}