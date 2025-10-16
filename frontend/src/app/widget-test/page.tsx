'use client'

import { useSearchParams } from 'next/navigation'
import { Suspense, useEffect } from 'react'
import { AlertCircle, Copy, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useState } from 'react'
import { toast } from 'sonner'
import { config } from '@/lib/config'

function WidgetTestContent() {
  const searchParams = useSearchParams()
  const embedKey = searchParams.get('key')
  const [copied, setCopied] = useState(false)
  const [origin, setOrigin] = useState('')

  useEffect(() => {
    setOrigin(window.location.origin)
  }, [])

  const apiBaseUrl = `${config.apiUrl}`

  useEffect(() => {
    if (!embedKey || !origin) {
      return
    }

    const existingWidget = document.querySelector('div[data-embed-key]')
    if (existingWidget) {
      existingWidget.remove()
    }

    let existingScript = document.querySelector(
      'script[src="/embed.js"]'
    ) as HTMLScriptElement

    const initializeWidget = () => {
      const triggerScript = document.createElement('script')
      triggerScript.setAttribute('data-embed-key', embedKey)
      triggerScript.setAttribute('data-api-base', apiBaseUrl)
      triggerScript.setAttribute('data-is-test', 'true')
      document.body.appendChild(triggerScript)

      const event = new Event('DOMContentLoaded', { bubbles: true })
      window.dispatchEvent(event)
    }

    if (existingScript) {
      initializeWidget()
    } else {
      const script = document.createElement('script')
      script.src = '/embed.js'
      script.onload = () => {
        initializeWidget()
      }
      document.body.appendChild(script)
      existingScript = script
    }

    return () => {
      const triggerScript = document.querySelector('script[data-embed-key]')
      if (triggerScript) {
        triggerScript.remove()
      }
      const widget = document.querySelector('div[data-embed-key]')
      if (widget) {
        widget.remove()
      }
    }
  }, [embedKey, origin, apiBaseUrl])

  const handleCopyCode = () => {
    // クライアント向けコードには data-is-test は含めない
    const code = `<script 
  src="${origin || 'https://yourdomain.com'}/embed.js"
  data-embed-key="${embedKey}"
  data-api-base="${apiBaseUrl}"
></script>`

    navigator.clipboard.writeText(code).then(() => {
      setCopied(true)
      toast.success('コードをコピーしました')
      setTimeout(() => setCopied(false), 2000)
    })
  }

  if (!embedKey) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <Card className="max-w-md p-8">
          <div className="flex items-center gap-3 mb-4">
            <AlertCircle className="h-8 w-8 text-red-500 dark:text-red-400" />
            <h1 className="text-2xl font-bold text-red-600 dark:text-red-400">
              エラー
            </h1>
          </div>
          <p className="text-gray-700 dark:text-gray-300 mb-4">
            埋め込みキーが指定されていません。
          </p>
          <div className="bg-gray-50 dark:bg-gray-800 rounded p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              <strong>正しいURL形式:</strong>
            </p>
            <code className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded block break-all">
              /widget-test?key=YOUR_EMBED_KEY
            </code>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-8">
      <div className="max-w-4xl mx-auto">
        <Card className="p-8 mb-8">
          <div className="flex items-center gap-3 mb-1">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="45"
              height="45"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 8V4H8"></path>
              <rect width="16" height="12" x="4" y="8" rx="2"></rect>
              <path d="M2 14h2"></path>
              <path d="M20 14h2"></path>
              <path d="M15 13v2"></path>
              <path d="M9 13v2"></path>
            </svg>
            <h1 className="text-3xl font-bold">AIチャット テストページ</h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            このページでは実際のウィジェットでチャットテストを行っていただくことができます
          </p>
        </Card>

        <Card className="p-8 mb-8">
          <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
            <span className="text-2xl">✨</span>
            使い方
          </h2>
          <ol className="space-y-4">
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold">
                1
              </span>
              <div className="flex-1">
                <p className="flex item-center font-medium text-gray-900 dark:text-gray-100">
                  <span>右下の</span>
                  <span className="mx-1">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M12 8V4H8"></path>
                      <rect width="16" height="12" x="4" y="8" rx="2"></rect>
                      <path d="M2 14h2"></path>
                      <path d="M20 14h2"></path>
                      <path d="M15 13v2"></path>
                      <path d="M9 13v2"></path>
                    </svg>
                  </span>
                  <span>アイコンをクリック</span>
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  画面右下に表示されているボタンをクリックするとウィジェットが開きます
                </p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold">
                2
              </span>
              <div className="flex-1">
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  質問を入力してください
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  テキストエリアに質問を入力し、Enterキーを押すか送信ボタンをクリック
                </p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold">
                3
              </span>
              <div className="flex-1">
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  AIが回答を生成
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  アップロードした文書に基づいて、AIが自動的に回答を生成します
                </p>
              </div>
            </li>
          </ol>
        </Card>

        <Card className="p-8">
          <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
            <span className="text-2xl">💻</span>
            あなたのサイトへの埋め込みコード
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            以下のコードをあなたのウェブサイトの{' '}
            <code className="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
              &lt;body&gt;
            </code>{' '}
            タグ内に貼り付けるだけで、 同じウィジェットが表示されます：
          </p>
          <div className="bg-gray-900 dark:bg-gray-950 rounded-lg p-6 overflow-x-auto relative">
            <pre className="text-gray-100 dark:text-gray-200 text-sm font-mono">
              {origin
                ? `<script 
  src="${origin}/embed.js"
  data-embed-key="${embedKey}"
  data-api-base="${apiBaseUrl}"
></script>
`
                : '読み込み中...'}
            </pre>
            <Button
              variant="ghost"
              size="sm"
              className="absolute top-4 right-4 bg-white hover:bg-gray-200 dark:text-gray-950 dark:hover:bg-gray-200"
              onClick={handleCopyCode}
            >
              {copied ? (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  コピー済み
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-2" />
                  コードをコピー
                </>
              )}
            </Button>
          </div>
        </Card>
      </div>
    </div>
  )
}

export default function WidgetTestPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">読み込み中...</p>
          </div>
        </div>
      }
    >
      <WidgetTestContent />
    </Suspense>
  )
}
