export interface ColumnInfo {
  name: string
  type: 'integer' | 'float' | 'string' | 'boolean' | 'datetime' | 'date' | 'category'
  nullable: boolean
  unique: boolean
  sample_values: any[]
  stats?: Record<string, any>
}

export interface DatasetMetadata {
  id: string
  name: string
  original_filename: string
  file_type: 'csv' | 'xlsx' | 'xls' | 'json' | 'parquet'
  file_size_bytes: number
  row_count: number
  column_count: number
  columns: ColumnInfo[]
  missing_values: number
  duplicate_rows: number
  quality_score: number
  status: 'uploading' | 'processing' | 'profiling' | 'ready' | 'error'
  created_at: string
  updated_at: string
  sheet_name?: string
  encoding?: string
  delimiter?: string
}

export interface DatasetListResponse {
  datasets: DatasetMetadata[]
  total: number
  page: number
  page_size: number
}

export interface UploadResponse {
  dataset_id: string
  status: string
  message: string
}

export interface DataPreview {
  columns: ColumnInfo[]
  rows: any[][]
  total_rows: number
  page: number
  page_size: number
}

export interface DatasetProfile {
  dataset_id: string
  dataset_name: string
  row_count: number
  column_count: number
  memory_usage_mb: number
  columns: ColumnProfile[]
  quality_score: number
  quality_issues: DataQualityIssue[]
  recommendations: string[]
  profiled_at: string
}

export interface ColumnProfile {
  name: string
  type: string
  stats: NumericalStats | CategoricalStats | DateTimeStats | Record<string, any>
  quality_issues: DataQualityIssue[]
  sample_values: any[]
}

export type DataQualityIssueType =
  | 'missing_values'
  | 'duplicate_rows'
  | 'invalid_format'
  | 'outlier'
  | 'high_cardinality'
  | 'constant_column'
  | 'type_inconsistency'

export interface DataQualityIssue {
  type: DataQualityIssueType
  column?: string
  severity: 'high' | 'medium' | 'low'
  message: string
  count: number
  recommendation?: string
}

export interface NumericalStats {
  count: number
  mean?: number
  median?: number
  mode?: number
  std?: number
  variance?: number
  min?: number
  max?: number
  range?: number
  q25?: number
  q50?: number
  q75?: number
  iqr?: number
  skewness?: number
  kurtosis?: number
  missing: number
  zeros: number
  negative: number
  positive: number
}

export interface CategoricalStats {
  count: number
  unique: number
  top?: string
  freq?: number
  distribution: Record<string, number>
  missing: number
  cardinality_ratio: number
}

export interface DateTimeStats {
  count: number
  min?: string
  max?: string
  range_days?: number
  missing: number
  frequency?: string
}

export interface AnalyticalOperation {
  operation: 'filter' | 'sort' | 'group_by' | 'aggregate' | 'join' | 'calculate' | 'rank' | 'percentage' | 'growth' | 'statistical_summary' | 'correlation' | 'trend' | 'outlier' | 'time_series' | 'forecast' | 'anomaly_detection' | 'segmentation' | 'rfm' | 'cohort'
  parameters: Record<string, any>
  description: string
}

export interface AIResponse {
  answer: string
  operations: AnalyticalOperation[]
  sql?: string
  data?: any
  chart_config?: ChartConfig
  citations: string[]
  follow_up_suggestions: string[]
  metadata: Record<string, any>
}

export interface ChartConfig {
  type: string
  title?: string
  subtitle?: string
  x_axis: AxisConfig
  y_axis: AxisConfig
  series: SeriesConfig[]
  legend: boolean
  tooltip: boolean
  colors: string[]
  width?: number
  height?: number
}

export interface AxisConfig {
  name?: string
  type: string
  show: boolean
  show_grid: boolean
  min?: number
  max?: number
}

export interface SeriesConfig {
  name: string
  data: any[]
  type?: string
  color?: string
  y_axis_index: number
}