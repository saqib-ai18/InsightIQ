import { useEffect, useRef, useMemo } from 'react'
import * as echarts from 'echarts/core'
import {
  BarChart,
  LineChart,
  PieChart,
  ScatterChart,
  HeatmapChart,
  BoxplotChart,
  FunnelChart,
  RadarChart,
  GaugeChart,
  TreemapChart,
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  PolarComponent,
  RadarComponent,
  GeoComponent,
  SingleAxisComponent,
  CalendarComponent,
  GraphicComponent,
  ToolboxComponent,
  DataZoomComponent,
  VisualMapComponent,
  AriaComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  ScatterChart,
  HeatmapChart,
  BoxplotChart,
  FunnelChart,
  RadarChart,
  GaugeChart,
  TreemapChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  PolarComponent,
  RadarComponent,
  GeoComponent,
  SingleAxisComponent,
  CalendarComponent,
  GraphicComponent,
  ToolboxComponent,
  DataZoomComponent,
  VisualMapComponent,
  AriaComponent,
  CanvasRenderer,
])

interface ChartData {
  type: string
  categories?: string[]
  series?: Array<{
    name: string
    type?: string
    data: any[]
    areaStyle?: any
    [key: string]: any
  }>
}

interface ChartWrapperProps {
  data: ChartData
  width?: string
  height?: string
  title?: string
  _onDownload?: (_format: 'png' | 'svg') => void
  _onFullscreen?: () => void
  className?: string
}

const CHART_COLORS = [
  '#6366F1', '#06B6D4', '#22C55E', '#F59E0B', '#EF4444',
  '#8B5CF6', '#EC4899', '#14B8A6', '#F97316', '#84CC16',
  '#A855F7', '#E11D48', '#0891B2', '#16A34A', '#D97706',
]

const DARK_THEME = {
  color: CHART_COLORS,
  backgroundColor: 'transparent',
  textStyle: { color: '#FAFAFA' },
  title: { textStyle: { color: '#FAFAFA' } },
  legend: { textStyle: { color: '#A1A1AA' } },
  grid: { borderColor: '#27272A' },
  xAxis: { axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } },
  yAxis: { axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } },
  tooltip: {
    backgroundColor: '#18181B',
    borderColor: '#27272A',
    borderWidth: 1,
    textStyle: { color: '#FAFAFA' },
  },
}

export function ChartWrapper({
  data,
  width = '100%',
  height = '400px',
  title,
  _onDownload,
  _onFullscreen,
  className = '',
}: ChartWrapperProps) {
  void _onDownload
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)

  const option = useMemo(() => {
    const baseOption: any = {
      color: CHART_COLORS,
      backgroundColor: 'transparent',
      title: title ? { text: title, left: 'center', textStyle: { color: '#FAFAFA', fontSize: 16 } } : undefined,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: '#18181B',
        borderColor: '#27272A',
        borderWidth: 1,
        textStyle: { color: '#FAFAFA' },
        formatter: (params: any) => {
          if (Array.isArray(params)) {
            return params.map(p => `${p.seriesName}: ${p.value}`).join('<br/>')
          }
          return `${params.seriesName}: ${params.value}`
        },
      },
      legend: {
        show: true,
        bottom: 0,
        textStyle: { color: '#A1A1AA' },
        selectedMode: true,
      },
      grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
      toolbox: {
        show: true,
        feature: {
          saveAsImage: { show: true, title: 'Download PNG', pixelRatio: 2 },
          dataView: { show: true, title: 'Data View', readOnly: true },
          restore: { show: true, title: 'Reset' },
        },
      },
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        { type: 'slider', show: false, start: 0, end: 100 },
      ],
    }

    if (data.type === 'pie' || data.type === 'donut') {
      return {
        ...baseOption,
        tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: {c} ({d}%)' },
        legend: { orient: 'vertical', left: 'left', textStyle: { color: '#A1A1AA' } },
        series: [{
          name: data.series?.[0]?.name || 'Distribution',
          type: 'pie',
          radius: data.type === 'donut' ? ['40%', '70%'] : '55%',
          center: ['50%', '50%'],
          data: data.series?.[0]?.data || [],
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' },
          },
        }],
      }
    }

    if (data.type === 'bar' || data.type === 'horizontal_bar') {
      return {
        ...baseOption,
        xAxis: data.type === 'horizontal_bar'
          ? { type: 'value', axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } }
          : { type: 'category', data: data.categories || [], axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } },
        yAxis: data.type === 'horizontal_bar'
          ? { type: 'category', data: data.categories || [], axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } }
          : { type: 'value', axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } },
        series: (data.series || []).map(s => ({
          name: s.name,
          type: 'bar',
          data: s.data,
          barWidth: '60%',
          borderRadius: [4, 4, 0, 0],
        })),
      }
    }

    if (data.type === 'line' || data.type === 'area') {
      return {
        ...baseOption,
        xAxis: { type: 'category', data: data.categories || [], axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } },
        yAxis: { type: 'value', axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } },
        series: (data.series || []).map(s => ({
          name: s.name,
          type: 'line',
          data: s.data,
          smooth: true,
          areaStyle: s.areaStyle || (data.type === 'area' ? { opacity: 0.3 } : undefined),
          symbol: 'circle',
          symbolSize: 6,
        })),
      }
    }

    if (data.type === 'scatter') {
      return {
        ...baseOption,
        xAxis: { type: 'value', axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } },
        yAxis: { type: 'value', axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } },
        series: (data.series || []).map(s => ({
          name: s.name,
          type: 'scatter',
          data: s.data,
          symbolSize: 10,
          itemStyle: { opacity: 0.7 },
        })),
      }
    }

    if (data.type === 'histogram') {
      return {
        ...baseOption,
        xAxis: { type: 'value', axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } },
        yAxis: { type: 'value', axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } },
        series: (data.series || []).map(s => ({
          name: s.name,
          type: 'histogram',
          data: s.data,
          itemStyle: { borderWidth: 1, borderColor: '#27272A' },
        })),
      }
    }

    if (data.type === 'box') {
      return {
        ...baseOption,
        xAxis: { type: 'category', data: data.categories || [], axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } },
        yAxis: { type: 'value', axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } },
        series: (data.series || []).map(s => ({
          name: s.name,
          type: 'boxplot',
          data: s.data,
        })),
      }
    }

    if (data.type === 'heatmap') {
      return {
        ...baseOption,
        tooltip: { position: 'top' },
        xAxis: { type: 'category', data: data.categories || [], axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } },
        yAxis: { type: 'category', data: data.categories || [], axisLine: { lineStyle: { color: '#27272A' } }, axisLabel: { color: '#A1A1AA' } },
        visualMap: { min: -1, max: 1, calculable: true, orient: 'horizontal', left: 'center', bottom: '10%' },
        series: [{
          name: 'Correlation',
          type: 'heatmap',
          data: data.series?.[0]?.data || [],
          label: { show: true, formatter: '{c}', textStyle: { color: '#FAFAFA' } },
          emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' } },
        }],
      }
    }

    return baseOption
  }, [data, title])

  useEffect(() => {
    if (!chartRef.current) return

    chartInstance.current = echarts.init(chartRef.current, DARK_THEME)
    chartInstance.current.setOption(option, true)

    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose()
        chartInstance.current = null
      }
    }
  }, [option])

  const handleDownload = (format: 'png' | 'svg' | 'jpeg') => {
    if (!chartInstance.current) return
    if (_onDownload) {
      _onDownload(format === 'jpeg' ? 'png' : format)
      return
    }
    const content = format === 'png'
      ? chartInstance.current.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#09090B' })
      : format === 'svg'
        ? chartInstance.current.getDataURL({ type: 'svg', backgroundColor: '#09090B' })
        : chartInstance.current.getDataURL({ type: 'jpeg', pixelRatio: 2, backgroundColor: '#09090B' })
    const link = document.createElement('a')
    link.download = `chart.${format}`
    link.href = content
    link.click()
  }

  const handleFullscreen = () => {
    if (_onFullscreen) _onFullscreen()
  }

  return (
    <div className={`relative w-full h-full ${className}`} style={{ width, height }}>
      <div ref={chartRef} className="w-full h-full" />
      <div className="absolute top-2 right-2 flex gap-1 z-10">
        <button
          onClick={() => handleDownload('png')}
          className="p-2 rounded-lg bg-surface/80 hover:bg-surface-hover text-text-secondary transition-colors"
          aria-label="Download PNG"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        </button>
        <button
          onClick={handleFullscreen}
          className="p-2 rounded-lg bg-surface/80 hover:bg-surface-hover text-text-secondary transition-colors"
          aria-label="Fullscreen"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
          </svg>
        </button>
      </div>
    </div>
  )
}

export default ChartWrapper