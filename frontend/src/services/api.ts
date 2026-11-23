const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

type ReferrerPolicy = '' | 'no-referrer' | 'no-referrer-when-downgrade' | 'origin' | 'origin-when-cross-origin' | 'same-origin' | 'strict-origin' | 'strict-origin-when-cross-origin' | 'unsafe-url'

interface RequestOptions {
  method?: string
  headers?: Record<string, string>
  body?: string | FormData | null
  redirect?: 'follow' | 'error' | 'manual'
  credentials?: 'omit' | 'same-origin' | 'include'
  cache?: 'default' | 'no-store' | 'reload' | 'no-cache' | 'force-cache' | 'only-if-cached'
  referrer?: string
  referrerPolicy?: ReferrerPolicy
  integrity?: string
  keepalive?: boolean
  signal?: AbortSignal
  mode?: 'cors' | 'no-cors' | 'same-origin' | 'navigate'
  params?: Record<string, string | number | boolean | undefined>
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, ...fetchOptions } = options

  const url = new URL(`${API_BASE}${endpoint}`, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value))
      }
    })
  }

  const token = localStorage.getItem('access_token')
  
  const response = await fetch(url.toString(), {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...fetchOptions.headers,
    },
    ...fetchOptions,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

export const api = {
  datasets: {
    list: (page = 1, pageSize = 20, search = '') =>
      request<{ datasets: any[]; total: number; page: number; page_size: number }>(
        '/datasets',
        { params: { page, page_size: pageSize, search } }
      ),

    get: (id: string) =>
      request<any>(`/datasets/${id}`),

    upload: (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      return request<{ dataset_id: string; status: string; message: string }>('/datasets/upload', {
        method: 'POST',
        body: formData,
        headers: {},
      })
    },

    preview: (id: string, page = 1, pageSize = 50) =>
      request<any>(`/datasets/${id}/preview`, { params: { page, page_size: pageSize } }),

    getProfile: (id: string) =>
      request<any>(`/datasets/${id}/profile`),

    getColumns: (id: string) =>
      request<{ columns: any[] }>(`/datasets/${id}/columns`),

    update: (id: string, data: { name?: string }) =>
      request<any>(`/datasets/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),

    delete: (id: string) =>
      request<void>(`/datasets/${id}`, { method: 'DELETE' }),

    download: (id: string) => {
      window.open(`${API_BASE}/datasets/${id}/download`, '_blank')
    },
  },

  analytics: {
    execute: (datasetId: string, operation: any) =>
      request<any>(`/analytics/execute`, {
        method: 'POST',
        body: JSON.stringify({ dataset_id: datasetId, operation }),
      }),

    query: (datasetId: string, sql: string) =>
      request<any>(`/analytics/query`, {
        method: 'POST',
        body: JSON.stringify({ dataset_id: datasetId, sql }),
      }),

    correlation: (datasetId: string, columns: string[]) =>
      request<any>(`/analytics/correlation`, {
        method: 'POST',
        body: JSON.stringify({ dataset_id: datasetId, columns }),
      }),

    trend: (datasetId: string, dateColumn: string, valueColumn: string) =>
      request<any>(`/analytics/trend`, {
        method: 'POST',
        body: JSON.stringify({ dataset_id: datasetId, date_column: dateColumn, value_column: valueColumn }),
      }),

    forecast: (datasetId: string, dateColumn: string, valueColumn: string, horizon: number) =>
      request<any>(`/analytics/forecast`, {
        method: 'POST',
        body: JSON.stringify({ dataset_id: datasetId, date_column: dateColumn, value_column: valueColumn, horizon }),
      }),

    outliers: (datasetId: string, column: string, method = 'iqr') =>
      request<any>(`/analytics/outliers`, {
        method: 'POST',
        body: JSON.stringify({ dataset_id: datasetId, column, method }),
      }),
  },

  ai: {
    ask: (datasetId: string, question: string, history: any[] = []) =>
      request<any>(`/ai/ask`, {
        method: 'POST',
        body: JSON.stringify({ dataset_id: datasetId, question, history }),
      }),

    stream: (datasetId: string, question: string, history: any[] = [], onChunk: (_chunk: string) => void) => {
      return fetch(`${API_BASE}/ai/ask/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_id: datasetId, question, history }),
      }).then(async (response) => {
        const reader = response.body?.getReader()
        const decoder = new TextDecoder()
        if (!reader) return

        let done = false
        while (!done) {
          const result = await reader.read()
          done = result.done
          if (done) break
          const chunk = decoder.decode(result.value, { stream: true })
          onChunk(chunk)
        }
      })
    },
  },

  visualizations: {
    suggest: (datasetId: string) =>
      request<any>(`/visualizations/suggest`, {
        method: 'POST',
        body: JSON.stringify({ dataset_id: datasetId }),
      }),

    generateChart: (params: {
      dataset_id: string
      chart_type: string
      x_column?: string
      y_columns?: string[]
      group_by?: string
      aggregation?: string
      limit?: number
    }) =>
      request<any>(`/visualizations/generate`, {
        method: 'POST',
        body: JSON.stringify(params),
      }),

    getData: (datasetId: string, chartConfig: any) =>
      request<any>(`/visualizations/data`, {
        method: 'POST',
        body: JSON.stringify({ dataset_id: datasetId, ...chartConfig }),
      }),

    save: (params: {
      dataset_id: string
      title: string
      chart_type: string
      config: any
    }) =>
      request<any>(`/visualizations`, {
        method: 'POST',
        body: JSON.stringify(params),
      }),

    list: (datasetId: string) =>
      request<any>(`/visualizations/list?dataset_id=${datasetId}`),

    delete: (chartId: string) =>
      request<void>(`/visualizations/${chartId}`, { method: 'DELETE' }),
  },

  reports: {
    list: (page = 1, pageSize = 20, datasetId?: string) =>
      request<{ reports: any[]; total: number; page: number; page_size: number }>(
        '/reports',
        { params: { page, page_size: pageSize, dataset_id: datasetId } }
      ),

    get: (id: string) =>
      request<any>(`/reports/${id}`),

    create: (report: {
      title: string
      dataset_id: string
      description?: string
      template?: string
      format?: string
      config?: any
    }) =>
      request<any>('/reports', {
        method: 'POST',
        body: JSON.stringify(report),
      }),

    generate: (reportId: string) =>
      request<any>(`/reports/${reportId}/generate`, { method: 'POST' }),

    download: (reportId: string) => {
      window.open(`${API_BASE}/reports/${reportId}/download`, '_blank')
    },

    update: (id: string, data: any) =>
      request<any>(`/reports/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),

    delete: (id: string) =>
      request<void>(`/reports/${id}`, { method: 'DELETE' }),

    templates: () =>
      request<any>(`/reports/templates/list`),
  },

  health: () =>
    request<{ status: string; version: string }>('/health'),

  dashboards: {
    list: (page = 1, pageSize = 6, datasetId?: string) =>
      request<{ dashboards: any[]; total: number; page: number; page_size: number }>(
        '/dashboards',
        { params: { page, page_size: pageSize, dataset_id: datasetId } }
      ),

    get: (id: string) =>
      request<any>(`/dashboards/${id}`),

    create: (dashboard: { name: string; dataset_id: string }) =>
      request<any>('/dashboards', {
        method: 'POST',
        body: JSON.stringify(dashboard),
      }),

    update: (id: string, data: any) =>
      request<any>(`/dashboards/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),

    delete: (id: string) =>
      request<void>(`/dashboards/${id}`, { method: 'DELETE' }),

    refresh: (id: string) =>
      request<any>(`/dashboards/${id}/refresh`, { method: 'POST' }),
  },

  auth: {
    login: (email: string, password: string) =>
      request<{ access_token: string; token_type: string; expires_in: number }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username: email, password }),
      }),

    register: (email: string, username: string, password: string, fullName?: string) =>
      request<any>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, username, password, full_name: fullName }),
      }),

    getCurrentUser: () =>
      request<any>('/auth/me'),

    createApiKey: (name: string, expiresDays?: number) =>
      request<any>('/auth/api-keys', {
        method: 'POST',
        body: JSON.stringify({ name, expires_days: expiresDays }),
      }),

    listApiKeys: () =>
      request<any[]>('/auth/api-keys'),

    revokeApiKey: (keyId: string) =>
      request<void>(`/auth/api-keys/${keyId}`, { method: 'DELETE' }),
  },
}