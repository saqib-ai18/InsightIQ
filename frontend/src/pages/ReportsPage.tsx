import { FileText, Plus, Download, Calendar, Clock, CheckCircle, XCircle, Loader2, Trash2, RefreshCw, Users, TrendingUp, Search, Zap } from 'lucide-react'
import { useState } from 'react'
import { clsx } from 'clsx'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import { useToast } from '@/hooks/useToast'
import { EmptyState, LoadingState, ErrorState, Pagination, Modal } from '@/components/ui'
import { LucideIcon } from 'lucide-react'

interface Report {
  id: string
  title: string
  type: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  createdAt: string
  size: string
  dataset_id: string
  description: string | null
  template: string
  format: string
  file_path: string | null
  file_size: number | null
  error_message: string | null
}

interface ReportListResponse {
  reports: Report[]
  total: number
  page: number
  page_size: number
}

export function ReportsPage() {
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newReportTitle, setNewReportTitle] = useState('')
  const [newReportDataset, setNewReportDataset] = useState('')
  const [newReportTemplate, setNewReportTemplate] = useState('custom')
  const [newReportFormat, setNewReportFormat] = useState('pdf')

  const { data: reportsResponse, isLoading, error, refetch } = useQuery<ReportListResponse>({
    queryKey: ['reports', page, pageSize],
    queryFn: () => api.reports.list(page, pageSize),
  })

  const { data: datasetsResponse } = useQuery({
    queryKey: ['datasets', 1, 100, ''],
    queryFn: () => api.datasets.list(1, 100, ''),
  })

  const { data: templatesResponse } = useQuery({
    queryKey: ['report-templates'],
    queryFn: () => api.reports.templates(),
    staleTime: 60000,
  })

  const createMutation = useMutation({
    mutationFn: (report: { title: string; dataset_id: string; template: string; format: string }) =>
      api.reports.create(report),
    onSuccess: (report) => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      setShowCreateModal(false)
      setNewReportTitle('')
      setNewReportDataset('')
      success('Report created')
      api.reports.generate(report.id)
    },
    onError: (error: Error) => {
      toastError(error.message)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.reports.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      success('Report deleted')
    },
    onError: (error: Error) => {
      toastError(error.message)
    },
  })

  const generateMutation = useMutation({
    mutationFn: (id: string) => api.reports.generate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      success('Report generation started')
    },
    onError: (error: Error) => {
      toastError(error.message)
    },
  })

  const reports = reportsResponse?.reports || []
  const total = reportsResponse?.total || 0
  const datasets = datasetsResponse?.datasets || []
  const templates = templatesResponse?.templates || []

  const formatDateTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getStatusConfig = (status: string) => {
    const configs = {
      completed: { className: 'bg-success/15 text-success', icon: <CheckCircle className="w-3 h-3" />, label: 'Completed' },
      processing: { className: 'bg-warning/15 text-warning', icon: <Clock className="w-3 h-3 animate-spin" />, label: 'Processing' },
      failed: { className: 'bg-error/15 text-error', icon: <XCircle className="w-3 h-3" />, label: 'Failed' },
      pending: { className: 'bg-text-muted/15 text-text-muted', icon: <Clock className="w-3 h-3" />, label: 'Pending' },
    }
    return configs[status as keyof typeof configs] || configs.pending
  }

  const templateConfigs: Record<string, { icon: LucideIcon; color: string }> = {
    executive_summary: { icon: FileText, color: 'text-primary' },
    sales_analysis: { icon: TrendingUp, color: 'text-success' },
    customer_report: { icon: Users, color: 'text-warning' },
    forecast_report: { icon: Search, color: 'text-primary' },
    data_quality: { icon: Zap, color: 'text-error' },
    custom: { icon: FileText, color: 'text-text-muted' },
  }

  return (
    <div className="space-y-6 animate-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            <FileText className="text-primary" />
            Reports
          </h1>
          <p className="mt-2 text-text-secondary">Generate and manage analytical reports</p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn-primary">
          <Plus className="w-4 h-4" />
          Generate Report
        </button>
      </div>

      {isLoading && <LoadingState message="Loading reports..." size="lg" />}

      {error && (
        <ErrorState
          title="Failed to load reports"
          message={error.message}
          onRetry={() => refetch()}
        />
      )}

      {!isLoading && !error && reports.length === 0 && (
        <EmptyState
          icon={FileText}
          title="No Reports Yet"
          description="Generate your first analytical report from a dataset"
          action={{ label: 'Generate Report', onClick: () => setShowCreateModal(true) }}
        />
      )}

      {!isLoading && !error && reports.length > 0 && (
        <div className="card">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">Report</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">Format</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">Template</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">Created</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">Size</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-text-muted uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {reports.map((report) => {
                  const statusConfig = getStatusConfig(report.status)
                  const templateConfig = templateConfigs[report.template] || templateConfigs.custom

                  const deleteButton = (
                    <button
                      onClick={() => deleteMutation.mutate(report.id)}
                      disabled={deleteMutation.isPending}
                      className="p-2 rounded-lg hover:bg-error/10 hover:text-error text-text-secondary transition-colors disabled:opacity-50"
                      aria-label="Delete"
                    >
                      {deleteMutation.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  )

                  const downloadButton = report.status === 'completed' && report.file_path ? (
                    <button
                      onClick={() => api.reports.download(report.id)}
                      className="p-2 rounded-lg hover:bg-surface-hover text-text-secondary transition-colors"
                      aria-label="Download"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                  ) : null

                  const generateButton = report.status !== 'completed' ? (
                    <button
                      onClick={() => generateMutation.mutate(report.id)}
                      disabled={generateMutation.isPending}
                      className="p-2 rounded-lg hover:bg-surface-hover text-text-secondary transition-colors disabled:opacity-50"
                      aria-label="Generate"
                    >
                      {generateMutation.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <RefreshCw className="w-4 h-4" />
                      )}
                    </button>
                  ) : null

                  return (
                    <tr key={report.id} className="hover:bg-surface-elevated/50 transition-colors">
                      <td className="px-6 py-4">
                        <p className="font-medium text-text-primary">{report.title}</p>
                        {report.description && <p className="text-sm text-text-muted truncate max-w-xs">{report.description}</p>}
                      </td>
                      <td className="px-6 py-4">
                        <span className="badge badge-primary">{report.format.toUpperCase()}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={clsx(
                          'flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
                          statusConfig.className
                        )}>
                          {statusConfig.icon}
                          {statusConfig.label}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="flex items-center gap-2">
                          <templateConfig.icon className={`w-4 h-4 ${templateConfig.color}`} />
                          <span className="capitalize">{report.template.replace('_', ' ')}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 text-text-secondary">
                        <div className="flex items-center gap-1.5">
                          <Calendar className="w-3 h-3 text-text-muted" />
                          {formatDateTime(report.createdAt)}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-text-secondary">{report.size}</td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          {downloadButton}
                          {generateButton}
                          {deleteButton}
                        </div>
                      </td>
                    </tr>
                  )}
                )}
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
      )}

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Report Templates</h3>
          <p className="card-description">Quick-start templates for common analytical reports</p>
        </div>
        <div className="card-content">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { id: 'executive_summary', title: 'Executive Summary', desc: 'High-level KPIs and key findings', icon: FileText },
              { id: 'sales_analysis', title: 'Sales Analysis', desc: 'Revenue trends and product performance', icon: TrendingUp },
              { id: 'customer_report', title: 'Customer Report', desc: 'Segmentation and behavior analysis', icon: Users },
              { id: 'forecast_report', title: 'Forecast Report', desc: 'Predictions with confidence intervals', icon: Search },
              { id: 'data_quality', title: 'Data Quality', desc: 'Profiling and quality assessment', icon: Zap },
            ].map((template) => (
              <button
                key={template.id}
                onClick={() => {
                  setNewReportTemplate(template.id)
                  setShowCreateModal(true)
                }}
                className="p-4 rounded-xl border border-border bg-surface-elevated hover:border-primary/30 hover:bg-surface-hover transition-all duration-fast text-left group"
              >
                <div className="w-10 h-10 rounded-lg bg-primary/15 flex items-center justify-center mb-3">
                  <template.icon className="w-5 h-5 text-primary" />
                </div>
                <h4 className="font-medium text-text-primary">{template.title}</h4>
                <p className="text-sm text-text-secondary mt-1">{template.desc}</p>
              </button>
            ))}
          </div>
        </div>
      </div>

      {showCreateModal && (
        <CreateReportModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSubmit={(title, datasetId, template, format) => 
            createMutation.mutate({ title, dataset_id: datasetId, template, format })
          }
          isLoading={createMutation.isPending}
          datasets={datasets}
          templates={templates}
          selectedDataset={newReportDataset}
          setSelectedDataset={setNewReportDataset}
          selectedTemplate={newReportTemplate}
          setSelectedTemplate={setNewReportTemplate}
          selectedFormat={newReportFormat}
          setSelectedFormat={setNewReportFormat}
          title={newReportTitle}
          setTitle={setNewReportTitle}
        />
      )}
    </div>
  )
}

function CreateReportModal({ isOpen, onClose, onSubmit, isLoading, datasets, templates, selectedDataset, setSelectedDataset, selectedTemplate, setSelectedTemplate, selectedFormat, setSelectedFormat, title, setTitle }: {
  isOpen: boolean
  onClose: () => void
  onSubmit: (title: string, datasetId: string, template: string, format: string) => void
  isLoading: boolean
  datasets: any[]
  templates: any[]
  selectedDataset: string
  setSelectedDataset: (id: string) => void
  selectedTemplate: string
  setSelectedTemplate: (id: string) => void
  selectedFormat: string
  setSelectedFormat: (id: string) => void
  title: string
  setTitle: (title: string) => void
}) {
  if (!isOpen) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Generate Report"
      size="md"
    >
      <div className="space-y-4">
        <div>
          <label className="label">Report Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Q4 2024 Sales Report"
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
        <div>
          <label className="label">Template</label>
          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="input"
          >
            <option value="custom">Custom</option>
            {templates.map((t: any) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Format</label>
          <select
            value={selectedFormat}
            onChange={(e) => setSelectedFormat(e.target.value)}
            className="input"
          >
            <option value="pdf">PDF</option>
            <option value="xlsx">Excel (XLSX)</option>
            <option value="csv">CSV</option>
          </select>
        </div>
      </div>
      <div className="flex justify-end gap-2 mt-6 pt-4 border-t border-border">
        <button onClick={onClose} className="btn-secondary">Cancel</button>
        <button onClick={() => onSubmit(title, selectedDataset, selectedTemplate, selectedFormat)} disabled={isLoading || !title || !selectedDataset} className="btn-primary">
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Generate Report'}
        </button>
      </div>
    </Modal>
  )
}