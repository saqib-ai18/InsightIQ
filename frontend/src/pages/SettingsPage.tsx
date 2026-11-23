import { Settings, User, Shield, Bell, Palette, Database, Key, Trash2, Save, Loader2, AlertCircle } from 'lucide-react'
import React, { useState } from 'react'
import { clsx } from 'clsx'
import { useThemeStore } from '@/stores/themeStore'

const settingsSections = [
  { id: 'general', label: 'General', icon: Settings, description: 'Basic application preferences' },
  { id: 'account', label: 'Account', icon: User, description: 'Profile and authentication settings' },
  { id: 'appearance', label: 'Appearance', icon: Palette, description: 'Theme and display options' },
  { id: 'data', label: 'Data & Privacy', icon: Database, description: 'Data handling and privacy controls' },
  { id: 'notifications', label: 'Notifications', icon: Bell, description: 'Notification preferences' },
  { id: 'security', label: 'Security', icon: Shield, description: 'Security and access settings' },
  { id: 'api', label: 'API Keys', icon: Key, description: 'Manage API integrations' },
  { id: 'danger', label: 'Danger Zone', icon: Trash2, description: 'Irreversible destructive actions' },
]

export function SettingsPage() {
  const { theme, setTheme } = useThemeStore()
  const [activeSection, setActiveSection] = useState('general')
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    await new Promise(r => setTimeout(r, 1000))
    setSaving(false)
  }

  return (
    <div className="space-y-6 animate-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            <Settings className="text-primary" />
            Settings
          </h1>
          <p className="mt-2 text-text-secondary">Manage your InsightIQ preferences and configuration</p>
        </div>
        <button onClick={handleSave} disabled={saving} className="btn-primary">
          <Save className="w-4 h-4" />
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save Changes'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <aside className="lg:col-span-1">
          <nav className="card overflow-hidden" aria-label="Settings navigation">
            <div className="p-4 border-b border-border">
              <h3 className="font-semibold text-text-primary">Settings</h3>
            </div>
            <ul className="p-2 space-y-1" role="list">
              {settingsSections.map((section) => (
                <li key={section.id}>
                  <button
                    onClick={() => setActiveSection(section.id)}
                    className={clsx(
                      'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                      activeSection === section.id
                        ? 'bg-primary/10 text-primary border border-primary/20'
                        : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'
                    )}
                    aria-current={activeSection === section.id ? 'page' : undefined}
                  >
                    <section.icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                    <span>{section.label}</span>
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        </aside>

        <div className="lg:col-span-3 space-y-6">
          {activeSection === 'general' && <GeneralSettings />}
          {activeSection === 'account' && <AccountSettings />}
          {activeSection === 'appearance' && <AppearanceSettings _theme={theme} setTheme={setTheme} />}
          {activeSection === 'data' && <DataSettings />}
          {activeSection === 'notifications' && <NotificationSettings />}
          {activeSection === 'security' && <SecuritySettings />}
          {activeSection === 'api' && <ApiSettings />}
          {activeSection === 'danger' && <DangerZone />}
        </div>
      </div>
    </div>
  )
}

function SectionCard({ title, description, children }: { title: string; description: string; children: React.ReactNode }) {
  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{title}</h3>
        <p className="card-description">{description}</p>
      </div>
      <div className="card-content">{children}</div>
    </div>
  )
}

function SettingRow({ label, description, children }: { label: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 py-4 border-b border-border last:border-0">
      <div className="flex-1">
        <label className="font-medium text-text-primary">{label}</label>
        {description && <p className="text-sm text-text-secondary mt-0.5">{description}</p>}
      </div>
      <div className="flex items-center gap-3">{children}</div>
    </div>
  )
}

function Toggle({ _checked, onChange, disabled }: { _checked: boolean; onChange: (_checked: boolean) => void; disabled?: boolean }) {
  return (
    <button
      role="switch"
      aria-checked={_checked}
      onClick={() => !disabled && onChange(!_checked)}
      disabled={disabled}
      className={clsx(
        'relative w-11 h-6 rounded-full transition-colors',
        _checked ? 'bg-primary' : 'bg-border'
      )}
    >
      <span
        className={clsx(
          'absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-md transition-transform',
          _checked && 'translate-x-5'
        )}
      />
    </button>
  )
}

function GeneralSettings() {
  const [language, setLanguage] = useState('en')
  const [dateFormat, setDateFormat] = useState('YYYY-MM-DD')
  const [timezone, setTimezone] = useState('UTC')

  return (
    <SectionCard title="General Preferences" description="Configure basic application behavior">
      <SettingRow
        label="Language"
        description="Application interface language"
      >
        <select value={language} onChange={e => setLanguage(e.target.value)} className="input w-auto">
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="de">German</option>
          <option value="ja">Japanese</option>
        </select>
      </SettingRow>
      <SettingRow
        label="Date Format"
        description="Default date display format"
      >
        <select value={dateFormat} onChange={e => setDateFormat(e.target.value)} className="input w-auto">
          <option value="YYYY-MM-DD">YYYY-MM-DD (2024-01-15)</option>
          <option value="DD/MM/YYYY">DD/MM/YYYY (15/01/2024)</option>
          <option value="MM/DD/YYYY">MM/DD/YYYY (01/15/2024)</option>
          <option value="MMM DD, YYYY">MMM DD, YYYY (Jan 15, 2024)</option>
        </select>
      </SettingRow>
      <SettingRow
        label="Timezone"
        description="Default timezone for date/time values"
      >
        <select value={timezone} onChange={e => setTimezone(e.target.value)} className="input w-auto">
          <option value="UTC">UTC</option>
          <option value="America/New_York">Eastern Time (US)</option>
          <option value="America/Chicago">Central Time (US)</option>
          <option value="America/Denver">Mountain Time (US)</option>
          <option value="America/Los_Angeles">Pacific Time (US)</option>
          <option value="Europe/London">London</option>
          <option value="Europe/Paris">Paris</option>
          <option value="Asia/Tokyo">Tokyo</option>
        </select>
      </SettingRow>
      <SettingRow
        label="Auto-save Analysis"
        description="Automatically save analysis progress"
      >
        <Toggle _checked={true} onChange={() => {}} />
      </SettingRow>
      <SettingRow
        label="Show Tooltips"
        description="Display helpful tooltips throughout the application"
      >
        <Toggle _checked={true} onChange={() => {}} />
      </SettingRow>
    </SectionCard>
  )
}

function AccountSettings() {
  return (
    <SectionCard title="Account Settings" description="Manage your profile and authentication">
      <div className="space-y-6">
        <div className="flex items-center gap-4 p-4 bg-surface-elevated rounded-lg">
          <div className="w-16 h-16 rounded-full bg-primary/15 flex items-center justify-center">
            <span className="text-xl font-bold text-primary">SA</span>
          </div>
          <div>
            <h4 className="font-semibold text-text-primary">Saqib Ali</h4>
            <p className="text-sm text-text-secondary">saqib@example.com</p>
            <p className="text-xs text-text-muted mt-1">Member since January 2024</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Full Name</label>
            <input type="text" defaultValue="Saqib Ali" className="input" />
          </div>
          <div>
            <label className="label">Email</label>
            <input type="email" defaultValue="saqib@example.com" className="input" />
          </div>
        </div>
        <div>
          <label className="label">Current Password</label>
          <input type="password" placeholder="••••••••" className="input" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">New Password</label>
            <input type="password" placeholder="••••••••" className="input" />
          </div>
          <div>
            <label className="label">Confirm Password</label>
            <input type="password" placeholder="••••••••" className="input" />
          </div>
        </div>
        <div className="pt-4">
          <button className="btn-secondary">Update Profile</button>
        </div>
      </div>
    </SectionCard>
  )
}

function AppearanceSettings({ _theme, setTheme }: { _theme: 'light' | 'dark' | 'system'; setTheme: (_theme: 'light' | 'dark') => void }) {
  return (
    <SectionCard title="Appearance" description="Customize how InsightIQ looks">
      <SettingRow
        label="Theme"
        description="Choose your preferred color scheme"
      >
        <div className="flex items-center gap-3">
          <button
            onClick={() => setTheme('dark')}
            className={clsx(
              'flex-1 p-4 rounded-lg border-2 transition-colors flex flex-col items-center gap-2',
              _theme === 'dark' ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'
            )}
          >
            <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-700 flex items-center justify-center" />
            <span className="text-sm font-medium text-text-primary">Dark</span>
          </button>
          <button
            onClick={() => setTheme('light')}
            className={clsx(
              'flex-1 p-4 rounded-lg border-2 transition-colors flex flex-col items-center gap-2',
              _theme === 'light' ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'
            )}
          >
            <div className="w-8 h-8 rounded-lg bg-white border border-zinc-200 flex items-center justify-center" />
            <span className="text-sm font-medium text-text-primary">Light</span>
          </button>
          <button
            className={clsx(
              'flex-1 p-4 rounded-lg border-2 transition-colors flex flex-col items-center gap-2',
              _theme === 'system' ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'
            )}
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-zinc-900 to-white border border-zinc-300 flex items-center justify-center" />
            <span className="text-sm font-medium text-text-primary">System</span>
          </button>
        </div>
      </SettingRow>
      <SettingRow
        label="Compact Mode"
        description="Reduce spacing for denser information display"
      >
        <Toggle _checked={false} onChange={() => {}} />
      </SettingRow>
      <SettingRow
        label="Animations"
        description="Enable smooth transitions and micro-interactions"
      >
        <Toggle _checked={true} onChange={() => {}} />
      </SettingRow>
      <SettingRow
        label="Sidebar Collapsed"
        description="Keep sidebar collapsed by default"
      >
        <Toggle _checked={false} onChange={() => {}} />
      </SettingRow>
    </SectionCard>
  )
}

function DataSettings() {
  return (
    <SectionCard title="Data & Privacy" description="Control how your data is handled and stored">
      <SettingRow
        label="Auto-profile on Upload"
        description="Automatically run data profiling when uploading datasets"
      >
        <Toggle _checked={true} onChange={() => {}} />
      </SettingRow>
      <SettingRow
        label="Sample Large Datasets"
        description="Use sampling for profiling datasets over 100k rows"
      >
        <Toggle _checked={true} onChange={() => {}} />
      </SettingRow>
      <SettingRow
        label="Cache Analysis Results"
        description="Cache analytical query results for faster repeated access"
      >
        <Toggle _checked={true} onChange={() => {}} />
      </SettingRow>
      <SettingRow
        label="Data Retention (days)"
        description="Automatically delete uploaded datasets after this many days"
      >
        <input type="number" defaultValue="30" min="1" max="365" className="input w-24" />
      </SettingRow>
      <SettingRow
        label="Allow Analytics Collection"
        description="Help improve InsightIQ by sharing anonymous usage data"
      >
        <Toggle _checked={false} onChange={() => {}} />
      </SettingRow>
      <div className="pt-4 border-t border-border">
        <button className="btn-secondary">Export All Data</button>
        <button className="btn-secondary ml-2">Delete All Data</button>
      </div>
    </SectionCard>
  )
}

function NotificationSettings() {
  return (
    <SectionCard title="Notifications" description="Configure when and how you receive notifications">
      <SettingRow
        label="Email Notifications"
        description="Receive email updates about analysis completion and reports"
      >
        <Toggle _checked={true} onChange={() => {}} />
      </SettingRow>
      <SettingRow
        label="In-App Notifications"
        description="Show notifications within the application"
      >
        <Toggle _checked={true} onChange={() => {}} />
      </SettingRow>
      <SettingRow
        label="Analysis Complete"
        description="Notify when long-running analyses finish"
      >
        <Toggle _checked={true} onChange={() => {}} />
      </SettingRow>
      <SettingRow
        label="Report Ready"
        description="Notify when generated reports are available for download"
      >
        <Toggle _checked={true} onChange={() => {}} />
      </SettingRow>
      <SettingRow
        label="Weekly Digest"
        description="Receive a weekly summary of your analytics activity"
      >
        <Toggle _checked={false} onChange={() => {}} />
      </SettingRow>
    </SectionCard>
  )
}

function SecuritySettings() {
  return (
    <SectionCard title="Security" description="Manage security settings and access control">
      <SettingRow
        label="Two-Factor Authentication"
        description="Add an extra layer of security to your account"
      >
        <div className="flex items-center gap-3">
          <Toggle _checked={false} onChange={() => {}} />
          <button className="btn-secondary btn-sm">Set Up 2FA</button>
        </div>
      </SettingRow>
      <SettingRow
        label="Session Timeout (minutes)"
        description="Automatically log out after inactivity"
      >
        <input type="number" defaultValue="60" min="15" max="480" className="input w-24" />
      </SettingRow>
      <SettingRow
        label="Active Sessions"
        description="View and manage your active login sessions"
      >
        <button className="btn-secondary btn-sm">View Sessions</button>
      </SettingRow>
      <div className="pt-4 border-t border-border">
        <h4 className="font-medium text-text-primary mb-3">API Access</h4>
        <SettingRow
          label="API Key"
          description="Generate API keys for programmatic access"
        >
          <button className="btn-secondary btn-sm">Generate Key</button>
        </SettingRow>
      </div>
    </SectionCard>
  )
}

function ApiSettings() {
  const [llmProvider, setLlmProvider] = useState('openai-compatible')
  const [llmModel, setLlmModel] = useState('gpt-4o-mini')
  const [llmApiKey, setLlmApiKey] = useState('')

  return (
    <SectionCard title="API Keys & Integrations" description="Configure external service connections">
      <div className="space-y-6">
        <div>
          <h4 className="font-medium text-text-primary mb-4">LLM Provider</h4>
          <SettingRow
            label="Provider"
            description="Select the AI provider for the AI Analyst"
          >
            <select value={llmProvider} onChange={e => setLlmProvider(e.target.value)} className="input w-auto">
              <option value="openai-compatible">OpenAI Compatible</option>
              <option value="nvidia-nim">NVIDIA NIM</option>
              <option value="groq">Groq</option>
            </select>
          </SettingRow>
          <SettingRow
            label="Model"
            description="Select the model to use for analysis"
          >
            <select value={llmModel} onChange={e => setLlmModel(e.target.value)} className="input w-auto">
              <option value="gpt-4o-mini">GPT-4o Mini</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
              <option value="llama-3.1-70b">Llama 3.1 70B</option>
              <option value="llama-3.1-8b">Llama 3.1 8B</option>
            </select>
          </SettingRow>
          <SettingRow
            label="API Key"
            description="Your API key for the selected provider"
          >
            <div className="flex items-center gap-2">
              <input
                type="password"
                value={llmApiKey}
                onChange={e => setLlmApiKey(e.target.value)}
                placeholder="••••••••••••••••"
                className="input flex-1 max-w-md"
              />
              <button className="btn-secondary btn-sm">Test Connection</button>
            </div>
          </SettingRow>
        </div>
        <div className="pt-4 border-t border-border">
          <h4 className="font-medium text-text-primary mb-4">Database</h4>
          <SettingRow
            label="PostgreSQL Connection"
            description="Connection string for persistent data storage"
          >
            <input
              type="text"
              placeholder="postgresql://user:pass@host:port/db"
              className="input flex-1 max-w-xl font-mono text-sm"
            />
          </SettingRow>
        </div>
      </div>
    </SectionCard>
  )
}

function DangerZone() {
  return (
    <SectionCard title="Danger Zone" description="Irreversible actions that permanently delete data">
      <div className="space-y-6">
        <div className="p-4 bg-error/5 border border-error/20 rounded-lg">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-error/15 flex items-center justify-center flex-shrink-0">
              <AlertCircle className="w-5 h-5 text-error" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-error">These actions cannot be undone</h4>
              <p className="text-sm text-text-secondary mt-1">Please be absolutely certain before proceeding. All associated data will be permanently deleted.</p>
            </div>
          </div>
        </div>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-surface-elevated rounded-lg">
            <div>
              <h5 className="font-medium text-text-primary">Delete All Datasets</h5>
              <p className="text-sm text-text-secondary">Permanently remove all uploaded datasets and their profiles</p>
            </div>
            <button className="btn-destructive btn-sm">Delete All Datasets</button>
          </div>
          <div className="flex items-center justify-between p-4 bg-surface-elevated rounded-lg">
            <div>
              <h5 className="font-medium text-text-primary">Delete All Analyses</h5>
              <p className="text-sm text-text-secondary">Remove all analysis history, charts, and generated insights</p>
            </div>
            <button className="btn-destructive btn-sm">Delete All Analyses</button>
          </div>
          <div className="flex items-center justify-between p-4 bg-surface-elevated rounded-lg">
            <div>
              <h5 className="font-medium text-text-primary">Delete Account</h5>
              <p className="text-sm text-text-secondary">Permanently delete your account and all associated data</p>
            </div>
            <button className="btn-destructive btn-sm">Delete Account</button>
          </div>
        </div>
      </div>
    </SectionCard>
  )
}