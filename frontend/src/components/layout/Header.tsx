import { useState, useRef, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Bell, ChevronDown, User, LogOut, Moon, Sun, HelpCircle, Command, Search } from 'lucide-react'
import { clsx } from 'clsx'
import { useThemeStore } from '@/stores/themeStore'

export function Header() {
  const location = useLocation()
  const { theme, toggleTheme } = useThemeStore()
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const notificationsRef = useRef<HTMLDivElement>(null)
  const userMenuRef = useRef<HTMLDivElement>(null)
  const searchRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (notificationsRef.current && !notificationsRef.current.contains(event.target as Node)) {
        setNotificationsOpen(false)
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false)
      }
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setSearchOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const getPageTitle = () => {
    const path = location.pathname
    if (path === '/overview') return 'Overview'
    if (path === '/dashboard') return 'Dashboards'
    if (path === '/ai-analyst') return 'AI Analyst'
    if (path === '/datasets') return 'Datasets'
    if (path === '/data-explorer') return 'Data Explorer'
    if (path === '/visualizations') return 'Visualizations'
    if (path === '/reports') return 'Reports'
    if (path === '/settings') return 'Settings'
    return 'InsightIQ'
  }

  return (
    <header className="h-16 bg-surface/80 backdrop-blur-sm border-b border-border sticky top-0 z-fixed flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-semibold text-text-primary hidden sm:block">
          {getPageTitle()}
        </h1>
        
        <div className="relative" ref={searchRef}>
          <button
            onClick={() => setSearchOpen(!searchOpen)}
            className={clsx(
              'flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-elevated border border-border text-text-secondary placeholder:text-text-muted transition-all duration-fast',
              searchOpen && 'border-primary/50 bg-surface ring-1 ring-primary/20'
            )}
            aria-label="Search"
            aria-expanded={searchOpen}
          >
            <Search className="w-4 h-4" />
            <span className="hidden md:inline">Search...</span>
            <kbd className="hidden lg:inline-flex items-center gap-1 px-1.5 py-0.5 text-xs bg-border rounded text-text-muted">
              <Command className="w-3 h-3" />
              K
            </kbd>
          </button>
          
          {searchOpen && (
            <div className="absolute right-0 top-full mt-2 w-80 bg-surface border border-border rounded-xl shadow-xl p-3 animate-in">
              <div className="flex items-center gap-2 px-2 py-2">
                <Search className="w-4 h-4 text-text-muted" />
                <input
                  type="text"
                  placeholder="Search datasets, analyses, reports..."
                  className="flex-1 bg-transparent text-text-primary placeholder:text-text-muted outline-none text-sm"
                  autoFocus
                />
              </div>
              <div className="border-t border-border mt-2 pt-2">
                <p className="text-xs text-text-muted px-2 py-1">Recent searches</p>
                <div className="space-y-1 px-1">
                  <button className="w-full text-left px-3 py-2 rounded-lg text-sm text-text-secondary hover:bg-surface-hover hover:text-text-primary transition-colors">
                    Monthly revenue analysis
                  </button>
                  <button className="w-full text-left px-3 py-2 rounded-lg text-sm text-text-secondary hover:bg-surface-hover hover:text-text-primary transition-colors">
                    Customer segmentation
                  </button>
                  <button className="w-full text-left px-3 py-2 rounded-lg text-sm text-text-secondary hover:bg-surface-hover hover:text-text-primary transition-colors">
                    Q3 forecast report
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="relative" ref={notificationsRef}>
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className={clsx(
              'relative p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-hover transition-colors',
              notificationsOpen && 'bg-surface-elevated'
            )}
            aria-label="Notifications"
            aria-expanded={notificationsOpen}
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-error rounded-full" />
          </button>
          
          {notificationsOpen && (
            <div className="absolute right-0 top-full mt-2 w-80 bg-surface border border-border rounded-xl shadow-xl overflow-hidden animate-in">
              <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                <h3 className="font-medium text-text-primary">Notifications</h3>
                <button className="text-sm text-text-muted hover:text-text-primary">Mark all read</button>
              </div>
              <div className="max-h-96 overflow-y-auto">
                <div className="p-4 text-center text-text-muted text-sm">
                  No new notifications
                </div>
              </div>
            </div>
          )}
        </div>

        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-hover transition-colors"
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        <div className="relative" ref={userMenuRef}>
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className={clsx(
              'flex items-center gap-2 p-1.5 rounded-lg hover:bg-surface-hover transition-colors',
              userMenuOpen && 'bg-surface-elevated'
            )}
            aria-label="User menu"
            aria-expanded={userMenuOpen}
            aria-haspopup="true"
          >
            <div className="w-8 h-8 rounded-full bg-primary/15 flex items-center justify-center">
              <span className="text-sm font-medium text-primary">SA</span>
            </div>
            <ChevronDown className="w-4 h-4 text-text-muted" />
          </button>

          {userMenuOpen && (
            <div className="absolute right-0 top-full mt-2 w-56 bg-surface border border-border rounded-xl shadow-xl overflow-hidden animate-in">
              <div className="px-4 py-3 border-b border-border">
                <p className="font-medium text-text-primary">Saqib Ali</p>
                <p className="text-sm text-text-muted truncate">saqib@example.com</p>
              </div>
              <nav className="py-1">
                <Link
                  to="/settings"
                  className="flex items-center gap-3 px-4 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-surface-hover transition-colors"
                  onClick={() => setUserMenuOpen(false)}
                >
                  <User className="w-4 h-4" />
                  Profile
                </Link>
                <Link
                  to="/settings"
                  className="flex items-center gap-3 px-4 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-surface-hover transition-colors"
                  onClick={() => setUserMenuOpen(false)}
                >
                  <HelpCircle className="w-4 h-4" />
                  Help & Docs
                </Link>
              </nav>
              <div className="border-t border-border px-4 py-1">
                <button className="flex items-center gap-3 w-full px-4 py-2 text-sm text-error hover:bg-surface-hover rounded-lg transition-colors">
                  <LogOut className="w-4 h-4" />
                  Sign out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}