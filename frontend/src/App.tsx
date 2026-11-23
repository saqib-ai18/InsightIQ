import { Routes, Route, Navigate, Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { DashboardPage } from '@/pages/DashboardPage'
import { AIAnalystPage } from '@/pages/AIAnalystPage'
import { DatasetsPage } from '@/pages/DatasetsPage'
import { DataExplorerPage } from '@/pages/DataExplorerPage'
import { VisualizationsPage } from '@/pages/VisualizationsPage'
import { ReportsPage } from '@/pages/ReportsPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { OverviewPage } from '@/pages/OverviewPage'
import { LoginPage } from '@/pages/LoginPage'
import { useAppStore } from '@/stores/appStore'

function Layout() {
  const { sidebarCollapsed } = useAppStore()
  
  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar />
      <div className={`flex-1 flex flex-col transition-all duration-fast ${sidebarCollapsed ? 'ml-16' : 'ml-64'}`}>
        <Header />
        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function ProtectedRoute() {
  const token = localStorage.getItem('access_token')
  const location = useLocation()
  
  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  
  return <Outlet />
}

function PublicRoute() {
  const token = localStorage.getItem('access_token')
  
  if (token) {
    return <Navigate to="/overview" replace />
  }
  
  return <Outlet />
}

function App() {
  return (
    <Routes>
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>
      
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/overview" replace />} />
          <Route path="overview" element={<OverviewPage />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="ai-analyst" element={<AIAnalystPage />} />
          <Route path="datasets" element={<DatasetsPage />} />
          <Route path="data-explorer" element={<DataExplorerPage />} />
          <Route path="visualizations" element={<VisualizationsPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Route>
      
      <Route path="*" element={<Navigate to="/overview" replace />} />
    </Routes>
  )
}

export default App