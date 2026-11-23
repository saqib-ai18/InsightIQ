import React, { useState, useRef, useCallback } from 'react'
import { Upload, X, AlertCircle, Loader2, FileText, ChevronDown } from 'lucide-react'
import { clsx } from 'clsx'
import { useToast } from '@/hooks/useToast'

interface FileUploadProps {
  onUploadComplete?: (_datasetId: string) => void
  maxSizeMB?: number
  acceptedTypes?: string[]
}

const ACCEPTED_TYPES = ['.csv', '.xlsx', '.xls', '.json', '.parquet']
const MAX_SIZE_MB = 100

export function FileUpload({ onUploadComplete, maxSizeMB = MAX_SIZE_MB, acceptedTypes = ACCEPTED_TYPES }: FileUploadProps) {
  const [isDragActive, setIsDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [showFileInfo, setShowFileInfo] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { success, error: toastError } = useToast()

  const handleFileSelect = useCallback((file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!acceptedTypes.includes(ext)) {
      const msg = `File type ${ext} not supported. Accepted: ${acceptedTypes.join(', ')}`
      setError(msg)
      toastError(msg)
      return
    }
    if (file.size > maxSizeMB * 1024 * 1024) {
      const msg = `File size ${(file.size / (1024 * 1024)).toFixed(1)}MB exceeds ${maxSizeMB}MB limit`
      setError(msg)
      toastError(msg)
      return
    }
    setSelectedFile(file)
    setError(null)
    setShowFileInfo(true)
  }, [acceptedTypes, maxSizeMB, toastError])

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true)
    } else if (e.type === 'dragleave') {
      setIsDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFileSelect(file)
  }, [handleFileSelect])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFileSelect(file)
    e.target.value = ''
  }

  const removeFile = () => {
    setSelectedFile(null)
    setShowFileInfo(false)
    setError(null)
  }

  const uploadFile = async () => {
    if (!selectedFile) return

    setUploading(true)
    setProgress(0)
    setError(null)

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const response = await fetch('/api/datasets/upload', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed')
      }

      setProgress(100)
      success('Dataset uploaded successfully')
      onUploadComplete?.(data.dataset_id)
      removeFile()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed'
      setError(message)
      toastError(message)
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="w-full">
      <div
        className={clsx(
          'relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200',
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/50'
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedTypes.join(',')}
          onChange={handleInputChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={uploading}
        />

        {selectedFile && showFileInfo ? (
          <div className="space-y-4 text-left max-w-md mx-auto">
            <div className="flex items-center gap-3 p-3 bg-surface-elevated rounded-lg border border-border">
              <div className="w-10 h-10 rounded-lg bg-primary/15 flex items-center justify-center flex-shrink-0">
                <FileText className="w-5 h-5 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-text-primary truncate">{selectedFile.name}</p>
                <p className="text-sm text-text-secondary">{formatSize(selectedFile.size)}</p>
              </div>
              <button
                onClick={removeFile}
                className="p-2 rounded-lg hover:bg-surface-hover text-text-muted transition-colors"
                aria-label="Remove file"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {error && (
              <div className="p-3 bg-error/10 border border-error/20 rounded-lg flex items-center gap-2 text-error text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={uploadFile}
                disabled={uploading}
                className={clsx(
                  'flex-1 btn-primary',
                  uploading && 'opacity-50'
                )}
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Upload Dataset
                  </>
                )}
              </button>
              <button
                onClick={removeFile}
                disabled={uploading}
                className="btn-secondary"
              >
                <X className="w-4 h-4" />
                Cancel
              </button>
            </div>

            {uploading && (
              <div className="w-full bg-surface-elevated rounded-full h-2 overflow-hidden">
                <div
                  className="bg-primary h-full rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="w-16 h-16 rounded-full bg-primary/15 flex items-center justify-center mx-auto">
              <Upload className="w-8 h-8 text-primary" />
            </div>
            <div>
              <p className="text-lg font-medium text-text-primary">Drop your dataset here</p>
              <p className="text-sm text-text-secondary mt-1">or click to browse</p>
            </div>
            <p className="text-xs text-text-muted">
              Supports: {acceptedTypes.join(', ')} • Max size: {maxSizeMB}MB
            </p>
          </div>
        )}
      </div>

      {selectedFile && !showFileInfo && (
        <button
          onClick={() => setShowFileInfo(true)}
          className="mt-4 w-full btn-secondary"
        >
          <ChevronDown className="w-4 h-4" />
          Show file details
        </button>
      )}
    </div>
  )
}