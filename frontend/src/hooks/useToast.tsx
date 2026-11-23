import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { CheckCircle, AlertCircle, X } from 'lucide-react'
import { clsx } from 'clsx'

export interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
}

interface ToastState {
  toasts: Toast[]
  addToast: (_toast: Omit<Toast, 'id'>) => void
  removeToast: (_id: string) => void
}

export const useToastStore = create<ToastState>()(
  persist(
    (set) => ({
      toasts: [],
      addToast: (toast) =>
        set((state) => ({
          toasts: [...state.toasts, { ...toast, id: Math.random().toString(36).slice(2) }],
        })),
      removeToast: (id) =>
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        })),
    }),
    { name: 'insightiq-toasts' }
  )
)

export function useToast() {
  const { addToast, removeToast } = useToastStore()

  return {
    success: (title: string, message?: string, duration = 4000) =>
      addToast({ type: 'success', title, message, duration }),
    error: (title: string, message?: string, duration = 6000) =>
      addToast({ type: 'error', title, message, duration }),
    warning: (title: string, message?: string, duration = 5000) =>
      addToast({ type: 'warning', title, message, duration }),
    info: (title: string, message?: string, duration = 4000) =>
      addToast({ type: 'info', title, message, duration }),
    remove: removeToast,
  }
}

export function ToastContainer() {
  const { toasts, removeToast } = useToastStore()

  if (toasts.length === 0) return null

  const icons = {
    success: <CheckCircle className="w-5 h-5 text-success" />,
    error: <AlertCircle className="w-5 h-5 text-error" />,
    warning: <AlertCircle className="w-5 h-5 text-warning" />,
    info: <AlertCircle className="w-5 h-5 text-primary" />,
  }

  const bgColors = {
    success: 'bg-success/10 border-success/20',
    error: 'bg-error/10 border-error/20',
    warning: 'bg-warning/10 border-warning/20',
    info: 'bg-primary/10 border-primary/20',
  }

  return (
    <div className="fixed bottom-6 right-6 z-toast flex flex-col gap-3 max-w-sm w-full">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={clsx(
            'flex items-start gap-3 p-4 rounded-xl border shadow-xl animate-in slide-in-from-right',
            bgColors[toast.type]
          )}
        >
          <div className="flex-shrink-0 mt-0.5">{icons[toast.type]}</div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-text-primary">{toast.title}</p>
            {toast.message && (
              <p className="text-sm text-text-secondary mt-0.5">{toast.message}</p>
            )}
          </div>
          <button
            onClick={() => removeToast(toast.id)}
            className="flex-shrink-0 p-1 rounded hover:bg-black/10 text-text-muted transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  )
}