import { Upload, Database, BarChart3, Bot, Sparkles, FileText, Search } from 'lucide-react'
import { clsx } from 'clsx'
import { LucideIcon } from 'lucide-react'
import { useAppStore } from '@/stores/appStore'
import { useNavigate } from 'react-router-dom'
import { FileUpload } from '@/components/datasets/FileUpload'
import { useToast } from '@/hooks/useToast'

const features = [
  {
    icon: Upload,
    title: 'Upload Data',
    description: 'Drag and drop CSV, Excel, JSON, or Parquet files. Automatic validation and profiling.',
  },
  {
    icon: Database,
    title: 'Explore & Profile',
    description: 'Comprehensive data profiling with statistics, quality scores, and column analysis.',
  },
  {
    icon: Bot,
    title: 'AI Data Analyst',
    description: 'Ask questions in natural language. Get accurate answers with explanations and SQL.',
  },
  {
    icon: BarChart3,
    title: 'Smart Visualizations',
    description: '18+ chart types with intelligent selection. Interactive exploration and export.',
  },
  {
    icon: FileText,
    title: 'Executive Reports',
    description: 'Generate professional PDF, Excel, and CSV reports with findings and recommendations.',
  },
  {
    icon: Sparkles,
    title: 'Advanced Analytics',
    description: 'Forecasting, anomaly detection, correlation analysis, and customer segmentation.',
  },
]

interface StatItem {
  label: string
  value: string | number
  icon: LucideIcon
  trend?: string
}

const stats: StatItem[] = [
  { label: 'Datasets', value: 0, icon: Database },
  { label: 'Analyses', value: 0, icon: BarChart3 },
  { label: 'Charts', value: 0, icon: FileText },
  { label: 'Reports', value: 0, icon: Sparkles },
]

export function OverviewPage() {
  const { activeDataset } = useAppStore()
  const navigate = useNavigate()
  const { success } = useToast()

  const handleUploadComplete = (datasetId: string) => {
    success('Dataset uploaded successfully')
    navigate(`/data-explorer?dataset=${datasetId}`)
  }

  return (
    <div className="space-y-8 animate-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text-primary">Welcome to InsightIQ</h1>
          <p className="mt-2 text-text-secondary">
            Transform your data into actionable insights with AI-powered analytics
          </p>
        </div>
        <FileUpload onUploadComplete={handleUploadComplete} />
      </div>

      {activeDataset && (
        <div className="card animate-in">
          <div className="card-content">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-primary/15 flex items-center justify-center">
                  <Database className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary">{activeDataset.name}</h3>
                  <p className="text-sm text-text-secondary">
                    {activeDataset.rowCount.toLocaleString()} rows × {activeDataset.columnCount} columns
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button onClick={() => navigate(`/data-explorer?dataset=${activeDataset.id}`)} className="btn-secondary">
                  <Search className="w-4 h-4" />
                  Explore
                </button>
                <button onClick={() => navigate(`/ai-analyst?dataset=${activeDataset.id}`)} className="btn-primary">
                  <Bot className="w-4 h-4" />
                  Ask AI
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-in">
        {stats.map((stat, index) => (
          <div key={stat.label} className="card" style={{ animationDelay: `${index * 50}ms` }}>
            <div className="card-content">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-3xl font-bold text-text-primary">{stat.value}</p>
                  <p className="text-sm text-text-secondary">{stat.label}</p>
                </div>
                <div className="w-12 h-12 rounded-lg bg-primary/15 flex items-center justify-center">
                  <stat.icon className="w-6 h-6 text-primary" />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <section className="animate-in">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-text-primary">Capabilities</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((feature, index) => (
            <div
              key={feature.title}
              className={clsx(
                'card group hover:border-primary/30 transition-all duration-fast',
                'animate-in'
              )}
              style={{ animationDelay: `${index * 30}ms` }}
            >
              <div className="card-content">
                <div className="w-10 h-10 rounded-lg bg-primary/15 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <feature.icon className="w-5 h-5 text-primary" />
                </div>
                <h3 className="font-semibold text-text-primary mb-2">{feature.title}</h3>
                <p className="text-sm text-text-secondary">{feature.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="card animate-in">
        <div className="card-header">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="card-title">Quick Start</h2>
              <p className="card-description">Get started with your first analysis in three steps</p>
            </div>
          </div>
        </div>
        <div className="card-content">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="relative flex flex-col items-center text-center p-4">
              <div className="w-16 h-16 rounded-full bg-primary/15 flex items-center justify-center mb-4">
                <span className="text-2xl font-bold text-primary">1</span>
              </div>
              <h3 className="font-semibold text-text-primary mb-2">Upload Data</h3>
              <p className="text-sm text-text-secondary">Drag and drop your CSV, Excel, or JSON file. We&apos;ll automatically profile and validate it.</p>
            </div>
            <div className="relative flex flex-col items-center text-center p-4">
              <div className="w-16 h-16 rounded-full bg-primary/15 flex items-center justify-center mb-4">
                <span className="text-2xl font-bold text-primary">2</span>
              </div>
              <h3 className="font-semibold text-text-primary mb-2">Ask Questions</h3>
              <p className="text-sm text-text-secondary">Use natural language to ask about trends, comparisons, anomalies, and predictions.</p>
            </div>
            <div className="relative flex flex-col items-center text-center p-4">
              <div className="w-16 h-16 rounded-full bg-primary/15 flex items-center justify-center mb-4">
                <span className="text-2xl font-bold text-primary">3</span>
              </div>
              <h3 className="font-semibold text-text-primary mb-2">Get Insights</h3>
              <p className="text-sm text-text-secondary">Receive accurate answers with visualizations, SQL, and exportable reports.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}