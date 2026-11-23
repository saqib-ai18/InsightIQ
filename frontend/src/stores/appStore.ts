import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  setSidebarCollapsed: (_collapsed: boolean) => void
  activeDatasetId: string | null
  setActiveDatasetId: (_id: string | null) => void
  activeDataset: DatasetInfo | null
  setActiveDataset: (_dataset: DatasetInfo | null) => void
}

interface DatasetInfo {
  id: string
  name: string
  rowCount: number
  columnCount: number
  createdAt: string
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      toggleSidebar: () => set((_state) => ({ sidebarCollapsed: !_state.sidebarCollapsed })),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      activeDatasetId: null,
      setActiveDatasetId: (id) => set({ activeDatasetId: id }),
      activeDataset: null,
      setActiveDataset: (dataset) => set({ activeDataset: dataset, activeDatasetId: dataset?.id ?? null }),
    }),
    {
      name: 'insightiq-app',
      partialize: (_state) => ({ sidebarCollapsed: _state.sidebarCollapsed }),
    }
  )
)