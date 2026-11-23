import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import {
  BarChart2, Plus, Download, PieChart, LineChart,
  AreaChart, ScatterChart, BarChart, FileBarChart, Zap,
  GitBranch, Layout, Trash2,
  Eye, RotateCcw, Sparkles, X, Loader2
} from 'lucide-react'
import { clsx } from 'clsx'
import { api } from '@/services/api'
import { ChartWrapper } from '@/components/charts/ChartWrapper'
import { useToast } from '@/hooks/useToast'
import { EmptyState, Modal } from '@/components/ui'

const CHART_TYPES = [
  { name: 'Bar Chart', icon: BarChart2, type: 'bar', description: 'Compare categories' },
  { name: 'Line Chart', icon: LineChart, type: 'line', description: 'Show trends over time' },
  { name: 'Area Chart', icon: AreaChart, type: 'area', description: 'Show volume trends' },
  { name: 'Pie Chart', icon: PieChart, type: 'pie', description: 'Show composition' },
  { name: 'Donut Chart', icon: PieChart, type: 'donut', description: 'Show proportions' },
  { name: 'Scatter Plot', icon: ScatterChart, type: 'scatter', description: 'Show relationships' },
  { name: 'Histogram', icon: BarChart, type: 'histogram', description: 'Show distribution' },
  { name: 'Box Plot', icon: FileBarChart, type: 'box', description: 'Show outliers' },
  { name: 'Heatmap', icon: Zap, type: 'heatmap', description: 'Show correlations' },
  { name: 'Funnel', icon: GitBranch, type: 'funnel', description: 'Show conversion' },
  { name: 'Radar', icon: Layout, type: 'radar', description: 'Multi-variable' },
]

interface SavedChart {
  id: string
  title: string
  chart_type: string
  config: any
  dataset_id: string
  created_at: string
}

export function VisualizationsPage() {
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const { error: showError, success: showSuccess } = useToast()

  const datasetId = searchParams.get('dataset')
  const [activeTab, setActiveTab] = useState<'builder' | 'saved'>('builder')
  const [selectedChartType, setSelectedChartType] = useState<string>('bar')
  const [xColumn, setXColumn] = useState('')
  const [yColumns, setYColumns] = useState<string[]>([])
  const [groupBy, setGroupBy] = useState('')
  const [aggregation, setAggregation] = useState('mean')
  const [_filters, _setFilters] = useState<Array<{column: string, operator: string, value: string}>>([])
  const [limit, setLimit] = useState(1000)
  const [chartTitle, setChartTitle] = useState('')
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [chartPreview, setChartPreview] = useState<any>(null)

  const { data: columnsData } = useQuery<{ columns: any[] }>({
    queryKey: ['dataset-columns', datasetId],
    queryFn: () => api.datasets.getColumns(datasetId!),
    enabled: !!datasetId,
    staleTime: 60000,
  })

  const { data: suggestionsData } = useQuery<{ suggestions: any[] }>({
    queryKey: ['viz-suggestions', datasetId],
    queryFn: () => api.visualizations.suggest(datasetId!),
    enabled: !!datasetId,
    staleTime: 60000,
  })

  const { data: savedChartsData } = useQuery<{ charts: SavedChart[] }>({
    queryKey: ['saved-charts', datasetId],
    queryFn: () => api.visualizations.list(datasetId!),
    enabled: !!datasetId && activeTab === 'saved',
    staleTime: 30000,
  })

  const columns = columnsData?.columns || []
  const numericColumns = columns.filter(c => ['integer', 'float'].includes(c.type))
  const categoricalColumns = columns.filter(c => ['string', 'category'].includes(c.type))
  const dateColumns = columns.filter(c => ['datetime', 'date'].includes(c.type))

  const generateMutation = useMutation({
    mutationFn: (params: any) => api.visualizations.generateChart(params),
    onSuccess: (data) => {
      setIsGenerating(false)
      if (data.chart_config) {
        setChartPreview(data.chart_config)
        showSuccess('Chart generated successfully')
      }
    },
    onError: (error: Error) => {
      setIsGenerating(false)
      showError(error.message || 'Failed to generate chart')
    },
  })

  const saveMutation = useMutation({
    mutationFn: (params: any) => api.visualizations.save(params),
    onSuccess: () => {
      showSuccess('Chart saved')
      setShowSaveModal(false)
      queryClient.invalidateQueries({ queryKey: ['saved-charts', datasetId] })
    },
    onError: (error: Error) => {
      showError(error.message || 'Failed to save chart')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.visualizations.delete(id),
    onSuccess: () => {
      showSuccess('Chart deleted')
      queryClient.invalidateQueries({ queryKey: ['saved-charts', datasetId] })
    },
    onError: (error: Error) => {
      showError(error.message || 'Failed to delete chart')
    },
  })

  const handleGenerate = () => {
    if (!datasetId || !selectedChartType) return
    if (!xColumn && selectedChartType !== 'pie' && selectedChartType !== 'donut' && selectedChartType !== 'histogram') {
      showError('Please select an X column')
      return
    }
    if (yColumns.length === 0 && selectedChartType !== 'pie' && selectedChartType !== 'donut') {
      showError('Please select at least one Y column')
      return
    }

    setIsGenerating(true)
    generateMutation.mutate({
      dataset_id: datasetId,
      chart_type: selectedChartType,
      x_column: xColumn,
      y_columns: yColumns,
      group_by: groupBy || undefined,
      aggregation,
      limit,
    })
  }

  const handleDelete = (id: string) => {
    if (confirm('Delete this chart?')) {
      deleteMutation.mutate(id)
    }
  }

  const handleSaveChart = () => {
    if (!chartPreview || !chartTitle) {
      showError('Please generate a chart and enter a title first')
      return
    }
    saveMutation.mutate({
      dataset_id: datasetId!,
      title: chartTitle,
      chart_type: selectedChartType,
      config: chartPreview,
    })
  }

  // Auto-generate preview when selections change (debounced)
  useEffect(() => {
    if (!datasetId || !selectedChartType) return
    if (!xColumn && selectedChartType !== 'pie' && selectedChartType !== 'donut' && selectedChartType !== 'histogram') return
    if (yColumns.length === 0 && selectedChartType !== 'pie' && selectedChartType !== 'donut') return

    const timer = setTimeout(() => {
      generateMutation.mutate({
        dataset_id: datasetId,
        chart_type: selectedChartType,
        x_column: xColumn,
        y_columns: yColumns,
        group_by: groupBy || undefined,
        aggregation,
        limit,
      })
    }, 500)

    return () => clearTimeout(timer)
  }, [datasetId, selectedChartType, xColumn, yColumns, groupBy, aggregation, limit])

  if (!datasetId) {
    return (
      <div className="space-y-6 animate-in">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
              <BarChart2 className="text-primary" />
              Visualizations
            </h1>
            <p className="mt-2 text-text-secondary">Select a dataset to create visualizations</p>
          </div>
        </div>
        <EmptyState
          icon={BarChart2}
          title="No Dataset Selected"
          description="Navigate to the Datasets page and select a dataset"
          action={{ label: 'Browse Datasets', onClick: () => window.location.href = '/datasets' }}
        />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            <BarChart2 className="text-primary" />
            Visualizations
          </h1>
          <p className="mt-2 text-text-secondary">Create and manage charts from your data</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setActiveTab('builder')} className={clsx(
            'btn-sm px-4 py-2',
            activeTab === 'builder' ? 'btn-primary' : 'btn-secondary'
          )}>
            <Sparkles className="w-4 h-4 mr-2" />
            Chart Builder
          </button>
          <button onClick={() => setActiveTab('saved')} className={clsx(
            'btn-sm px-4 py-2',
            activeTab === 'saved' ? 'btn-primary' : 'btn-secondary'
          )}>
            <Download className="w-4 h-4 mr-2" />
            Saved Charts
          </button>
        </div>
      </div>

      {activeTab === 'builder' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-4 space-y-6">
            <ChartTypePanel
              selectedChartType={selectedChartType}
              setSelectedChartType={setSelectedChartType}
            />

            <DataMappingPanel
              selectedChartType={selectedChartType}
              xColumn={xColumn}
              setXColumn={setXColumn}
              yColumns={yColumns}
              setYColumns={setYColumns}
              groupBy={groupBy}
              setGroupBy={setGroupBy}
              aggregation={aggregation}
              setAggregation={setAggregation}
              limit={limit}
              setLimit={setLimit}
              numericColumns={numericColumns}
              categoricalColumns={categoricalColumns}
              dateColumns={dateColumns}
            />

            <SuggestionsPanel
              suggestions={suggestionsData?.suggestions || []}
              setSelectedChartType={setSelectedChartType}
              setXColumn={setXColumn}
              setYColumns={setYColumns}
            />
          </div>

          <div className="lg:col-span-8 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex items-center gap-3">
                <input
                  type="text"
                  value={chartTitle}
                  onChange={(e) => setChartTitle(e.target.value)}
                  placeholder="Chart title (optional)"
                  className="input flex-1 max-w-md"
                />
              </div>
              <div className="flex items-center gap-2">
                <button onClick={handleGenerate} disabled={isGenerating} className="btn-primary">
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Generate Chart
                    </>
                  )}
                </button>
                <button onClick={() => setShowSaveModal(true)} className="btn-secondary" disabled={!chartPreview}>
                  <Download className="w-4 h-4 mr-2" />
                  Save Chart
                </button>
              </div>
            </div>

            <div className="card" style={{ minHeight: '500px' }}>
              <div className="card-content p-0 relative">
                {chartPreview ? (
                  <ChartWrapper
                    data={chartPreview}
                    height="500px"
                  />
                ) : (
                  <div className="w-full h-[500px] flex items-center justify-center bg-surface-elevated">
                    <EmptyState
                      icon={BarChart2}
                      title="No Chart Yet"
                      description="Configure your chart and click Generate Chart to see a preview"
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'saved' && (
        <SavedChartsTab
          savedCharts={savedChartsData?.charts || []}
          onDelete={handleDelete}
        />
      )}

      {showSaveModal && (
        <SaveChartModal
          isOpen={showSaveModal}
          onClose={() => setShowSaveModal(false)}
          onSave={handleSaveChart}
          chartTitle={chartTitle}
          setChartTitle={setChartTitle}
          isLoading={saveMutation.isPending}
        />
      )}
    </div>
  )
}

function ChartTypePanel({ selectedChartType, setSelectedChartType }: { 
  selectedChartType: string; 
  setSelectedChartType: React.Dispatch<React.SetStateAction<string>>;
}) {
  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Chart Type</h3>
      </div>
      <div className="card-content">
        <div className="grid grid-cols-2 gap-3">
          {CHART_TYPES.map((chart) => (
            <button
              key={chart.type}
              onClick={() => setSelectedChartType(chart.type as any)}
              className={clsx(
                'p-4 rounded-xl border border-border bg-surface-elevated hover:border-primary/30 hover:bg-surface-hover transition-all duration-fast text-left group',
                selectedChartType === chart.type && 'border-primary bg-primary/5'
              )}
            >
              <div className="w-10 h-10 rounded-lg bg-primary/15 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <chart.icon className="w-5 h-5 text-primary" />
              </div>
              <h4 className="font-medium text-text-primary text-sm">{chart.name}</h4>
              <p className="text-xs text-text-secondary mt-1">{chart.description}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

function DataMappingPanel({ 
  selectedChartType, xColumn, setXColumn, yColumns, setYColumns, 
  groupBy, setGroupBy, aggregation, setAggregation, limit, setLimit,
  numericColumns, categoricalColumns, dateColumns
}: { 
  selectedChartType: string; 
  xColumn: string; 
  setXColumn: (v: string) => void;
  yColumns: string[]; 
  setYColumns: (v: string[]) => void;
  groupBy: string; 
  setGroupBy: (v: string) => void;
  aggregation: string; 
  setAggregation: (v: string) => void;
  limit: number; 
  setLimit: (v: number) => void;
  numericColumns: any[]; 
  categoricalColumns: any[]; 
  dateColumns: any[];
}) {
  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Data Mapping</h3>
      </div>
      <div className="card-content space-y-4">
        {selectedChartType !== 'pie' && selectedChartType !== 'donut' && selectedChartType !== 'histogram' && (
          <div>
            <label className="label">X Axis</label>
            <select
              value={xColumn}
              onChange={(e) => setXColumn(e.target.value)}
              className="input"
            >
              <option value="">Select column...</option>
              {dateColumns.map(c => <option key={c.name} value={c.name}>{c.name} (date)</option>)}
              {categoricalColumns.map(c => <option key={c.name} value={c.name}>{c.name} (category)</option>)}
              {numericColumns.map(c => <option key={c.name} value={c.name}>{c.name} (numeric)</option>)}
            </select>
          </div>
        )}

        <div>
          <label className="label">Y Axis (Metrics)</label>
          <div className="space-y-2">
            {yColumns.map((col, index) => (
              <div key={index} className="flex items-center gap-2">
                <select
                  value={col}
                  onChange={(e) => {
                    const newCols = [...yColumns]
                    newCols[index] = e.target.value
                    setYColumns(newCols)
                  }}
                  className="input flex-1"
                >
                  <option value="">Select column...</option>
                  {numericColumns.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
                </select>
                {yColumns.length > 1 && (
                  <button
                    onClick={() => setYColumns(yColumns.filter((_, i) => i !== index))}
                    className="p-2 rounded-lg hover:bg-surface-hover text-text-muted transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
            <button
              onClick={() => setYColumns([...yColumns, ''])}
              className="btn-secondary btn-sm w-full"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Metric
            </button>
          </div>
        </div>

        {selectedChartType !== 'pie' && selectedChartType !== 'donut' && selectedChartType !== 'histogram' && (
          <div>
            <label className="label">Group By (Optional)</label>
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value)}
              className="input"
            >
              <option value="">None</option>
              {categoricalColumns.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
            </select>
          </div>
        )}

        <div>
          <label className="label">Aggregation</label>
          <select
            value={aggregation}
            onChange={(e) => setAggregation(e.target.value)}
            className="input"
          >
            <option value="mean">Mean</option>
            <option value="sum">Sum</option>
            <option value="median">Median</option>
            <option value="min">Min</option>
            <option value="max">Max</option>
            <option value="count">Count</option>
          </select>
        </div>

        <div>
          <label className="label">Limit Rows</label>
          <input
            type="number"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            min="1"
            max="10000"
            className="input"
          />
        </div>
      </div>
    </div>
  )
}

function SuggestionsPanel({ 
  suggestions, setSelectedChartType, 
  setXColumn, setYColumns 
}: { 
  suggestions: any[]; 
  setSelectedChartType: React.Dispatch<React.SetStateAction<string>>;
  setXColumn: (v: string) => void;
  setYColumns: (v: string[]) => void;
}) {
  if (!suggestions.length) return null

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Smart Suggestions</h3>
      </div>
      <div className="card-content">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => {
              setSelectedChartType(suggestion.chart_type)
              if (suggestion.x_column) setXColumn(suggestion.x_column)
              if (suggestion.y_columns?.length) setYColumns(suggestion.y_columns)
            }}
            className="w-full p-3 rounded-lg border border-border bg-surface-elevated hover:border-primary/30 hover:bg-surface-hover transition-all duration-fast text-left"
          >
            <h4 className="font-medium text-text-primary text-sm capitalize">{suggestion.chart_type} chart</h4>
            <p className="text-xs text-text-secondary mt-1">{suggestion.reason}</p>
          </button>
        ))}
      </div>
    </div>
  )
}

function SavedChartsTab({ 
  savedCharts, onDelete 
}: { 
  savedCharts: SavedChart[]; 
  onDelete: (id: string) => void; 
}) {
  return (
    <div className="space-y-6">
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <div>
            <h3 className="card-title">Saved Charts</h3>
            <p className="card-description">Your saved visualizations for this dataset</p>
          </div>
        </div>
        <div className="card-content">
          {savedCharts.length === 0 ? (
            <EmptyState
              icon={BarChart2}
              title="No Saved Charts"
              description="Create and save charts using the Chart Builder"
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {savedCharts.map((chart) => (
                <div key={chart.id} className="group relative card hover:border-primary/30 transition-colors">
                  <div className="aspect-video bg-surface-elevated rounded-lg border border-border flex items-center justify-center relative overflow-hidden">
                    <div className="text-center p-4">
                      <div className="w-12 h-12 rounded-lg bg-primary/15 flex items-center justify-center mx-auto mb-2">
                        {chart.chart_type === 'bar' && <BarChart2 className="w-6 h-6 text-primary" />}
                        {chart.chart_type === 'line' && <LineChart className="w-6 h-6 text-primary" />}
                        {chart.chart_type === 'pie' && <PieChart className="w-6 h-6 text-primary" />}
                        {chart.chart_type === 'donut' && <PieChart className="w-6 h-6 text-primary" />}
                        {chart.chart_type === 'scatter' && <ScatterChart className="w-6 h-6 text-primary" />}
                        {chart.chart_type === 'area' && <AreaChart className="w-6 h-6 text-primary" />}
                        {chart.chart_type === 'histogram' && <BarChart className="w-6 h-6 text-primary" />}
                        {chart.chart_type === 'box' && <FileBarChart className="w-6 h-6 text-primary" />}
                        {chart.chart_type === 'heatmap' && <Zap className="w-6 h-6 text-primary" />}
                        {chart.chart_type === 'funnel' && <GitBranch className="w-6 h-6 text-primary" />}
                        {chart.chart_type === 'radar' && <Layout className="w-6 h-6 text-primary" />}
                      </div>
                      <p className="text-sm font-medium text-text-primary truncate">{chart.title}</p>
                      <p className="text-xs text-text-muted capitalize">{chart.chart_type} chart</p>
                    </div>
                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                      <button className="p-2 rounded-lg bg-surface/80 hover:bg-surface-hover text-text-secondary transition-colors" aria-label="View">
                        <Eye className="w-4 h-4" />
                      </button>
                      <button className="p-2 rounded-lg bg-surface/80 hover:bg-surface-hover text-text-secondary transition-colors" aria-label="Duplicate">
                        <RotateCcw className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => onDelete(chart.id)}
                        className="p-2 rounded-lg bg-error/10 hover:bg-error/20 text-error transition-colors"
                        aria-label="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-xs text-text-muted">
                    <span>Created {new Date(chart.created_at).toLocaleDateString()}</span>
                    <span className="badge badge-default">{chart.chart_type}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function SaveChartModal({ isOpen, onClose, onSave, chartTitle, setChartTitle, isLoading }: { 
  isOpen: boolean; 
  onClose: () => void; 
  onSave: () => void; 
  chartTitle: string; 
  setChartTitle: (v: string) => void; 
  isLoading: boolean;
}) {
  if (!isOpen) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Save Chart"
      size="md"
    >
      <div className="space-y-4">
        <div>
          <label className="label">Chart Title</label>
          <input
            type="text"
            value={chartTitle}
            onChange={(e) => setChartTitle(e.target.value)}
            placeholder="e.g., Sales by Region"
            className="input"
            autoFocus
          />
        </div>
      </div>
      <div className="flex justify-end gap-2 mt-6 pt-4 border-t border-border">
        <button onClick={onClose} className="btn-secondary" disabled={isLoading}>Cancel</button>
        <button onClick={onSave} disabled={isLoading || !chartTitle} className="btn-primary">
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save Chart'}
        </button>
      </div>
    </Modal>
  )
}