import { useEffect, useRef, useCallback } from 'react'
import { X } from 'lucide-react'
import { clsx } from 'clsx'
import { createPortal } from 'react-dom'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  description?: string
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  showCloseButton?: boolean
  closeOnOverlayClick?: boolean
  closeOnEscape?: boolean
}

const sizeClasses = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  full: 'max-w-[90vw]',
}

export function Modal({ 
  isOpen, 
  onClose, 
  title, 
  description, 
  children, 
  size = 'md',
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEscape = true,
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null)
  const previousActiveElement = useRef<HTMLElement | null>(null)

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!closeOnEscape) return
    if (event.key === 'Escape') {
      onClose()
    }
    if (event.key === 'Tab' && modalRef.current) {
      const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
      const firstElement = focusableElements[0]
      const lastElement = focusableElements[focusableElements.length - 1]
      
      if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault()
        lastElement?.focus()
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault()
        firstElement?.focus()
      }
    }
  }, [closeOnEscape])

  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement as HTMLElement
      document.addEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'hidden'
      
      // Focus first focusable element
      setTimeout(() => {
        const focusableElement = modalRef.current?.querySelector<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        focusableElement?.focus()
      }, 0)
    }
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
      previousActiveElement.current?.focus()
    }
  }, [isOpen, handleKeyDown])

  if (!isOpen) return null

  const modalContent = (
    <div 
      className="fixed inset-0 z-modal-backdrop flex items-center justify-center p-4 bg-black/50 animate-in"
      onClick={closeOnOverlayClick ? onClose : undefined}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      aria-describedby={description ? 'modal-description' : undefined}
    >
      <div
        ref={modalRef}
        className={clsx(
          'w-full bg-surface border border-border rounded-xl shadow-xl animate-in',
          sizeClasses[size]
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between p-4 border-b border-border">
          <div>
            <h2 id="modal-title" className="text-lg font-semibold text-text-primary">{title}</h2>
            {description && (
              <p id="modal-description" className="text-sm text-text-secondary mt-1">{description}</p>
            )}
          </div>
          {showCloseButton && (
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-surface-hover text-text-secondary transition-colors"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
        <div className="p-4 max-h-[70vh] overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  )

  if (typeof window === 'undefined') return null
  return createPortal(modalContent, document.body)
}

interface ConfirmDialogProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'destructive' | 'primary'
  isLoading?: boolean
}

export function ConfirmDialog({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title, 
  message, 
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'destructive',
  isLoading = false,
}: ConfirmDialogProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
    >
      <div className="space-y-4">
        <p className="text-text-secondary">{message}</p>
        <div className="flex justify-end gap-2 pt-2">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="btn-secondary"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={variant === 'destructive' ? 'btn-destructive' : 'btn-primary'}
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Processing...
              </>
            ) : (
              confirmLabel
            )}
          </button>
        </div>
      </div>
    </Modal>
  )
}