'use client'

import React, { useEffect, useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Card } from '@/components/ui/card'
import { Send, Bot, User, Search, Thermometer } from 'lucide-react'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { toast } from 'sonner'
import { config } from '@/lib/config'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { useSettingsStore } from '@/lib/settings-store'
import dynamic from 'next/dynamic'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
const ReactMarkdown = dynamic(() => import('react-markdown'), { ssr: false })

const unwrapMarkdownFence = (s: string) => {
  if (!s) return s
  const text = s.replace(/\r\n?/g, '\n').trim()
  if (!text.startsWith('```')) return text
  const open = text.match(/^```(?:markdown|md|mdx)?[^\n]*\n?/)
  if (!open) return text
  const body = text.slice(open[0].length)
  return body.replace(/\n?```[\s]*$/, '')
}

const normalizeMarkdown = (s: string) => {
  if (!s) return s
  const parts = s.split(/(```[\s\S]*?```)/g)
  return parts
    .map((p, i) => {
      if (i % 2) return p
      return p
        .replace(/\r\n?/g, '\n')
        .replace(/[\u00A0\u200B\uFEFF]/g, ' ')
        .replace(/(^|\n)(\d+\.)([^\s])/g, '$1$2 $3')
        .replace(/(^|\n)([-*+])([^\s])/g, '$1$2 $3')
        .replace(/([^\n])\n(?=(?:\s*(?:[-*+]\s|\d+\.\s)))/g, '$1\n\n')
    })
    .join('')
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  documents?: Array<{
    content: string
    metadata?: any
  }>
  content_used?: string
  llm_model?: string
}

type TenantInfo = { name: string; key: string }

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isBot, setIsBot] = useState(true)
  const topK = useSettingsStore(s => s.topK)
  const [tenants, setTenants] = useState<TenantInfo[]>([])
  const [selectedTenant, setSelectedTenant] = useState('')
  const [selectedKey, setSelectedKey] = useState('')
  const setTopK = useSettingsStore(s => s.setTopK)

  // テナントの初期ロード
  useEffect(() => {
    ;(async () => {
      try {
        const res = await fetch('/api/embed-admin/tenants', {
          cache: 'no-store',
        })
        const data = await res.json()
        const list = (data?.tenants || []) as TenantInfo[]
        setTenants(list)
        const saveKey =
          typeof window !== 'undefined' ? localStorage.getItem('embed:key') : ''
        const initial = list.find(t => t.key === saveKey) || list[0]
        if (initial) {
          setSelectedTenant(initial.name)
          setSelectedKey(initial.key)
          try {
            localStorage.setItem('embed:key', initial.key)
          } catch {}
        }
      } catch {}
    })()
  }, [])

  // 選択されたキーを常に localStorage と同期
  useEffect(() => {
    if (!selectedKey) return
    try {
      localStorage.setItem('embed:key', selectedKey)
    } catch {}
  }, [selectedKey])

  // LLMのセットアップ
  const MODELS = [
    'gpt-5',
    'gpt-5-mini',
    'gpt-4.1',
    'gpt-4o',
    'gpt-4o-mini',
  ] as const
  type Model = (typeof MODELS)[number]
  const DEFAULT_MODEL: Model = 'gpt-5-mini'
  const [model, setModel] = useState<Model>(DEFAULT_MODEL)
  const mounted = useRef(false)
  const isModel = (v: string): v is Model =>
    (MODELS as readonly string[]).includes(v)

  useEffect(() => {
    try {
      const saved = localStorage.getItem('llm:model')
      if (saved && isModel(saved)) {
        setModel(saved)
      } else {
        setModel(DEFAULT_MODEL)
      }
    } catch {}
    mounted.current = true
  }, [])

  useEffect(() => {
    if (!mounted.current) return
    try {
      localStorage.setItem('llm:model', model)
    } catch {}
  }, [model])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const model =
        typeof window !== 'undefined' ? localStorage.getItem('llm:model') : null

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          askToBot: isBot,
          model: model || undefined,
          top_k: topK,
          admin: true,
          embedKey: selectedKey || undefined,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Network response was not ok')
      }

      const data = await response.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.content,
        documents: data.documents,
        content_used: data.context_used,
        llm_model: data.llm_model,
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `申し訳ありません。エラーが発生しました: ${error instanceof Error ? error.message : 'Unknown error'}`,
      }
      setMessages(prev => [...prev, errorMessage])
      toast.error('エラーが発生しました。もう一度お試しください。')
    } finally {
      setIsLoading(false)
    }
  }

  const onChangeTenant = (name: string) => {
    setSelectedTenant(name)
    const t = tenants.find(x => x.name === name)
    setSelectedKey(t?.key || '')
    try {
      localStorage.setItem('embed:key', t?.key || '')
    } catch {}
  }

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Chat Message */}
      <ScrollArea className="flex-1 min-h-0 p-4">
        <div className="space-y-4 max-w-5xl mx-auto">
          {messages.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">
                Welcome to Tuukaa the RAG Chatbot
              </p>
              <p>
                Upload a PDF document and start asking questions about its
                content.
              </p>
              {config.isDebug && (
                <p className="text-xs mt-2 opacity-75">Debug Mode: ON</p>
              )}
            </div>
          )}

          {messages.map(message => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`flex gap-3 max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
              >
                <div
                  className={`flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full ${message.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}
                >
                  {message.role === 'user' ? (
                    <User className="h-4 w-4" />
                  ) : (
                    <Bot className="h-4 w-4" />
                  )}
                </div>
                <Card className="p-4">
                  {message.content ? (
                    <div className="prose prose-sm max-w-none dark:prose-invert chat-prose">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[rehypeHighlight]}
                      >
                        {normalizeMarkdown(
                          unwrapMarkdownFence(message.content)
                        )}
                      </ReactMarkdown>
                      {message.llm_model ? (
                        <div className="mt-1 text-xs text-muted-foreground">
                          Model: {message.llm_model}
                        </div>
                      ) : (
                        ''
                      )}
                    </div>
                  ) : (
                    ''
                  )}
                  {/* 参照された文書を表示 */}
                  {message.documents && message.documents.length > 0 && (
                    <div className="mt-3 space-y-2 text-xs text-muted-foreground">
                      {message.content ? (
                        <p className="font-semibold">参照元:</p>
                      ) : (
                        <p className="font-semibold">検索結果:</p>
                      )}
                      {message.documents.map((doc, docIndex) => (
                        <div
                          key={docIndex}
                          className="p-2 bg-secondary rounded-md"
                        >
                          <p className="font-medium truncate">
                            {doc.metadata?.souce || `文書 ${docIndex + 1}`}
                          </p>
                          <p className="line-clamp-2">{doc.content}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </Card>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="flex gap-3 max-w-[80%]">
                <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full bg-muted">
                  <Bot className="h-4 w-4" />
                </div>
                <Card className="p-4">
                  <div className="flex items-center gap-2">
                    <div className="flex space-x-1">
                      <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                      <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                      <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce"></div>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      AI thinking...
                    </span>
                  </div>
                </Card>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Form */}
      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <form
          className="flex gap-2 p-4 max-w-5xl mx-auto"
          onSubmit={handleSubmit}
        >
          {/* <div className="flex items-center justify-between gap-1">
            <Search className="h-4 w-4" />
            <Switch checked={isBot} onCheckedChange={setIsBot} />
            <Bot className="h-4 w-4" />
          </div> */}
          <Select value={selectedTenant} onValueChange={onChangeTenant}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="テナント" />
            </SelectTrigger>
            <SelectContent>
              {tenants.map(t => (
                <SelectItem key={t.key} value={t.name}>
                  {t.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="flex items-center gap-2 w-[220px]">
            <Label className="whitespace-nowrap">top_k: {topK}</Label>
            <Slider
              min={1}
              max={10}
              step={1}
              value={[topK]}
              onValueChange={v => setTopK(v[0] ?? 3)}
            />
          </div>
          {/* LLM */}
          <div>
            <Select
              value={MODELS.includes(model) ? model : DEFAULT_MODEL}
              onValueChange={v => {
                if (v && isModel(v)) setModel(v)
              }}
            >
              <SelectTrigger
                className={isBot ? '' : 'cursor-not-allowed'}
                disabled={!isBot}
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gpt-5">gpt-5</SelectItem>
                <SelectItem value="gpt-5-mini">gpt-5-mini</SelectItem>
                <SelectItem value="gpt-4.1">gpt-4.1</SelectItem>
                <SelectItem value="gpt-4o">gpt-4o</SelectItem>
                <SelectItem value="gpt-4o-mini">gpt-4o-mini</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Input
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask a question about your PDF..."
            className="flex-1"
            disabled={isLoading}
          />
          <Button type="submit" size="icon" disabled={isLoading}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  )
}
