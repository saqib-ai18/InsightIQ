import { Bot, Send, Mic, RotateCcw, Code, Sparkles, Loader2, Copy, Check } from 'lucide-react'
import React, { useState, useRef, useEffect, useCallback } from 'react'
import { clsx } from 'clsx'
import { useSearchParams } from 'react-router-dom'
import { api } from '@/services/api'
import { useToast } from '@/hooks/useToast'
import { ChartWrapper } from '@/components/charts/ChartWrapper'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  metadata?: {
    sql?: string
    chart?: { type: string; data: unknown[] }
    citations?: string[]
    operations?: Array<{ operation: string; parameters: Record<string, unknown>; description: string }>
  }
}

interface ChartConfig {
  type: string
  categories?: string[]
  series?: Array<{ name: string; data: unknown[]; type?: string }>
}

export function AIAnalystPage() {
  const [searchParams] = useSearchParams()
  const { error: showError, success: showSuccess } = useToast()

  const datasetId = searchParams.get('dataset')
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hello! I'm your AI Data Analyst. Upload a dataset and ask me anything about your data - trends, comparisons, anomalies, forecasts, and more.",
      timestamp: new Date(),
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationHistory, setConversationHistory] = useState<Array<{ role: string; content: string }>>([])
  const [showSuggestions, setShowSuggestions] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const [expandedMetadata, setExpandedMetadata] = useState<Record<string, boolean>>({})

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleNewChat = useCallback(() => {
    setMessages([{
      id: '1',
      role: 'assistant',
      content: "Hello! I'm your AI Data Analyst. Upload a dataset and ask me anything about your data - trends, comparisons, anomalies, forecasts, and more.",
      timestamp: new Date(),
    }])
    setConversationHistory([])
    setShowSuggestions(true)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    if (!datasetId) {
      showError('Please select a dataset first from the Datasets page')
      return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    const currentInput = input
    setInput('')
    setIsLoading(true)
    setShowSuggestions(false)

    abortControllerRef.current = new AbortController()

    try {
      const response = await api.ai.ask(datasetId, currentInput, conversationHistory)
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        metadata: {
          sql: response.data?.sql,
          chart: response.chart_config,
          citations: response.citations,
          operations: response.operations,
        }
      }

      setMessages(prev => [...prev, assistantMessage])
      setConversationHistory(prev => [
        ...prev,
        { role: 'user', content: currentInput },
        { role: 'assistant', content: response.answer }
      ].slice(-10))
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${err instanceof Error ? err.message : 'Failed to get response'}`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
      showError(err instanceof Error ? err.message : 'Failed to get response')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuggestedClick = (question: string) => {
    setInput(question)
    textareaRef.current?.focus()
  }

  const copyToClipboard = async (text: string, label: string) => {
    await navigator.clipboard.writeText(text)
    showSuccess(`${label} copied to clipboard`)
  }

  const toggleMetadata = (key: string) => {
    setExpandedMetadata(prev => ({ ...prev, [key]: !prev[key] }))
  }

  return (
    <div className="h-full flex flex-col animate-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            <Bot className="text-primary" />
            AI Analyst
          </h1>
          <p className="mt-2 text-text-secondary">Ask questions about your data in natural language</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleNewChat} className="btn-secondary" aria-label="New conversation">
            <RotateCcw className="w-4 h-4" />
            New Chat
          </button>
        </div>
      </div>

      {datasetId && (
        <div className="mb-4 p-3 bg-primary/5 border border-primary/20 rounded-lg flex items-center gap-3">
          <Sparkles className="w-5 h-5 text-primary" />
          <span className="text-sm text-text-secondary">
            Analyzing dataset: <span className="font-medium text-text-primary">{datasetId}</span>
          </span>
        </div>
      )}

      <div className="flex-1 flex flex-col overflow-hidden card">
        <div className="flex-1 overflow-y-auto p-6 space-y-6" role="log" aria-live="polite">
          {messages.map((message) => (
            <MessageBubble 
              key={message.id} 
              message={message} 
              onCopy={copyToClipboard}
              expanded={expandedMetadata[message.id]}
              onToggleExpanded={() => toggleMetadata(message.id)}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {showSuggestions && !isLoading && (
          <div className="border-t border-border px-6 py-4 bg-surface-elevated/50">
            <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">Suggested questions</p>
            <div className="flex flex-wrap gap-2">
              {[
                "What are the key insights in this dataset?",
                "Show me the top 5 categories by value",
                "Calculate month-over-month growth",
                "Identify outliers in the data",
                "Generate an executive summary",
                "Forecast the next 6 months",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => handleSuggestedClick(q)}
                  className="btn-secondary btn-sm text-xs px-3 py-1.5"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="border-t border-border p-4">
          <div className="relative flex items-end gap-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={datasetId ? "Ask a question about your data..." : "Select a dataset first to enable AI analysis"}
              className="flex-1 min-h-[52px] max-h-48 px-4 py-3 bg-surface-elevated border border-border rounded-xl text-text-primary placeholder:text-text-muted resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:opacity-50"
              disabled={isLoading || !datasetId}
              rows={1}
              style={{ height: '52px' }}
            />
            <div className="flex items-center gap-1 mb-1">
              <button
                type="button"
                className="p-2 rounded-lg hover:bg-surface-hover text-text-secondary transition-colors"
                aria-label="Voice input"
                disabled
              >
                <Mic className="w-4 h-4" />
              </button>
              <button
                type="submit"
                disabled={!input.trim() || isLoading || !datasetId}
                className={clsx(
                  'p-2.5 rounded-lg transition-colors',
                  isLoading || !input.trim() || !datasetId
                    ? 'bg-surface-hover text-text-muted cursor-not-allowed'
                    : 'bg-primary text-primary-foreground hover:bg-primary-hover'
                )}
                aria-label="Send message"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
          <p className="text-xs text-text-muted mt-2 text-center">
            Press Enter to send • Shift+Enter for new line • AI responses are generated from your data
          </p>
        </form>
      </div>
    </div>
  )
}

function MessageBubble({ message, onCopy, expanded, onToggleExpanded }: { 
  message: Message; 
  onCopy: (text: string, label: string) => Promise<void>;
  expanded: boolean;
  onToggleExpanded: () => void;
}) {
  const [copiedItem, setCopiedItem] = useState<string | null>(null)

  const handleCopy = async (text: string, label: string) => {
    await onCopy(text, label)
    setCopiedItem(label.toLowerCase())
    setTimeout(() => setCopiedItem(null), 2000)
  }

  return (
    <div className={clsx('flex gap-3 animate-in', message.role === 'user' && 'flex-row-reverse')}>
      <div
        className={clsx(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          message.role === 'user'
            ? 'bg-surface-elevated border border-border'
            : 'bg-primary/15'
        )}
      >
        {message.role === 'user' ? (
          <span className="text-xs font-medium text-text-secondary">You</span>
        ) : (
          <Bot className="w-4 h-4 text-primary" />
        )}
      </div>
      <div className={clsx('flex-1 max-w-3xl', message.role === 'user' && 'text-right')}>
        <div
          className={clsx(
            'inline-block max-w-[85%] px-4 py-3 rounded-2xl',
            message.role === 'user'
              ? 'bg-primary text-primary-foreground rounded-tr-sm'
              : 'bg-surface-elevated border border-border rounded-tl-sm'
          )}
        >
          <div className="prose prose-invert max-w-none text-sm">
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 mt-2 justify-end">
          <span className="text-xs text-text-muted">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
        {message.metadata?.sql && (
          <MetadataSection
            title="SQL Query"
            icon={<Code className="w-3 h-3" />}
            expanded={expanded}
            onToggle={onToggleExpanded}
            content={message.metadata.sql}
            onCopy={handleCopy}
            copiedItem={copiedItem}
          />
        )}
        {message.metadata?.citations && message.metadata.citations.length > 0 && (
          <MetadataSection
            title="Sources"
            icon={<Sparkles className="w-3 h-3" />}
            expanded={true}
            onToggle={() => {}}
            content={message.metadata.citations.map((c, i) => `${i + 1}. ${c}`).join('\n')}
          />
        )}
        {message.metadata?.operations && message.metadata.operations.length > 0 && (
          <MetadataSection
            title="Operations performed"
            icon={<Code className="w-3 h-3" />}
            expanded={true}
            onToggle={() => {}}
            content={message.metadata.operations.map((op, i) => `${i + 1}. ${op.description}`).join('\n')}
          />
        )}
        {message.metadata?.chart && (
          <div className="mt-3 border-t border-border pt-3">
            <p className="text-xs font-medium text-text-muted mb-2">Chart Preview</p>
            <div className="aspect-video bg-surface rounded-lg overflow-hidden">
              <ChartWrapper
                data={message.metadata.chart as ChartConfig}
                height="100%"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function MetadataSection({ title, icon: Icon, expanded, onToggle, content, onCopy, copiedItem }: { 
  title: string;
  icon: React.ReactNode;
  expanded: boolean;
  onToggle: () => void;
  content: string;
  onCopy?: (text: string, label: string) => Promise<void>;
  copiedItem?: string | null;
}) {
  return (
    <div className="mt-3 border-t border-border pt-3">
      <button
        onClick={onToggle}
        className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors"
      >
        <span className={clsx('w-3 h-3 flex items-center justify-center', expanded && 'rotate-90')}>{Icon}</span>
        {expanded ? 'Hide' : 'Show'} {title}
      </button>
      {expanded && (
        <div className="mt-2 p-3 bg-surface rounded-lg overflow-x-auto">
          <div className="flex items-center justify-between mb-2">
            <pre className="text-xs text-text-secondary font-mono flex-1 whitespace-pre-wrap">{content}</pre>
            {onCopy && (
              <button
                onClick={() => onCopy!(content, title)}
                className={clsx(
                  'p-1.5 rounded text-xs text-text-muted hover:text-text-primary transition-colors',
                  copiedItem === title.toLowerCase() && 'text-success'
                )}
              >
                {copiedItem === title.toLowerCase() ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}