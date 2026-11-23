import { useState } from 'react'
import { Link, useLocation, NavLink } from 'react-router-dom'
import { ChevronLeft, ChevronRight, BarChart3, LayoutDashboard, Bot, Database, Search, BarChart2, FileText, History, Settings, Plus, Sparkles } from 'lucide-react'
import { useAppStore } from '@/stores/appStore'
import { clsx } from 'clsx'

const navigation = [
  { name: 'New Analysis', href: '/overview', icon: Plus, badge: null },
  { name: 'Overview', href: '/overview', icon: LayoutDashboard, badge: null },
  { name: 'AI Analyst', href: '/ai-analyst', icon: Bot, badge: null },
  { name: 'Dashboards', href: '/dashboard', icon: BarChart3, badge: null },
  { name: 'Datasets', href: '/datasets', icon: Database, badge: null },
  { name: 'Data Explorer', href: '/data-explorer', icon: Search, badge: null },
  { name: 'Visualizations', href: '/visualizations', icon: BarChart2, badge: null },
  { name: 'Reports', href: '/reports', icon: FileText, badge: null },
  { name: 'History', href: '/history', icon: History, badge: null },
  { name: 'Settings', href: '/settings', icon: Settings, badge: null },
]

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useAppStore()
  const location = useLocation()
  const [hovered, setHovered] = useState(false)

  const isActive = (href: string) => location.pathname === href || (href !== '/overview' && location.pathname.startsWith(href))

  return (
    <aside
      className={clsx(
        'fixed left-0 top-0 z-sticky h-screen bg-surface border-r border-border flex flex-col transition-all duration-fast',
        sidebarCollapsed ? 'w-16' : 'w-64'
      )}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div className="flex h-16 items-center justify-between px-4 border-b border-border">
        {!sidebarCollapsed && (
          <Link to="/overview" className="flex items-center gap-2" aria-label="InsightIQ Home">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-semibold text-lg text-text-primary">InsightIQ</span>
          </Link>
        )}
        <button
          onClick={toggleSidebar}
          className={clsx(
            'p-2 rounded-md transition-colors hover:bg-surface-hover',
            sidebarCollapsed && !hovered ? 'ml-auto' : ''
          )}
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-expanded={!sidebarCollapsed}
        >
          {sidebarCollapsed ? <ChevronRight className="w-5 h-5 text-text-secondary" /> : <ChevronLeft className="w-5 h-5 text-text-secondary" />}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto p-3 space-y-1" role="navigation" aria-label="Main navigation">
        {navigation.map((item) => {
          const active = isActive(item.href)
          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive: navActive }) => clsx(
                'relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-fast',
                navActive
                  ? 'bg-primary/10 text-primary border border-primary/20'
                  : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover',
                sidebarCollapsed && !hovered && 'justify-center px-2'
              )}
              title={sidebarCollapsed && !hovered ? item.name : undefined}
              aria-current={active ? 'page' : undefined}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
              {!sidebarCollapsed && (
                <>
                  <span className="truncate">{item.name}</span>
                  {item.badge && (
                    <span className="ml-auto px-2 py-0.5 text-xs font-medium bg-primary/15 text-primary rounded-full">
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          )
        })}
      </nav>

      <div className="p-3 border-t border-border">
        {!sidebarCollapsed && (
          <div className="space-y-2">
            <div className="px-3 py-2">
              <p className="text-xs font-medium text-text-muted uppercase tracking-wider">Account</p>
            </div>
            <button className={clsx(
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-hover transition-colors',
              sidebarCollapsed && !hovered && 'justify-center px-2'
            )}>
              <div className="w-8 h-8 rounded-full bg-primary/15 flex items-center justify-center flex-shrink-0">
                <span className="text-sm font-medium text-primary">SA</span>
              </div>
              {!sidebarCollapsed && (
                <div className="flex-1 min-w-0 text-left">
                  <p className="truncate font-medium text-text-primary">Saqib Ali</p>
                  <p className="truncate text-xs text-text-muted">saqib@example.com</p>
                </div>
              )}
            </button>
          </div>
        )}
      </div>
    </aside>
  )
}