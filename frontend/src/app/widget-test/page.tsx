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

  // クライアントサイドでのみoriginを設定
  useEffect(() => {
    setOrigin(window.location.origin)
  }, [])

  // バックエンドAPIのURLを取得
  const apiBaseUrl = `${config.apiUrl}`

  useEffect(() => {
    if (!embedKey || !origin) {
      return
    }

    // 既存のウィジェットを削除
    const existingWidget = document.querySelector('div[data-embed-key]')
    if (existingWidget) {
      existingWidget.remove()
    }

    // 既存のスクリプトがあるか確認
    let existingScript = document.querySelector(
      'script[src="/embed.js"]'
    ) as HTMLScriptElement

    const initializeWidget = () => {
      // スクリプトタグを作成（ウィジェット初期化のトリガー用）
      const triggerScript = document.createElement('script')
      triggerScript.setAttribute('data-embed-key', embedKey)
      triggerScript.setAttribute('data-api-base', apiBaseUrl)
      triggerScript.setAttribute('data-is-test', 'true')
      document.body.appendChild(triggerScript)

      // DOMContentLoaded イベントを強制的に発火
      const event = new Event('DOMContentLoaded', { bubbles: true })
      window.dispatchEvent(event)
    }

    if (existingScript) {
      // スクリプトが既に存在する場合は直接初期化
      initializeWidget()
    } else {
      // スクリプトを新規追加
      const script = document.createElement('script')
      script.src = '/embed.js'
      script.onload = () => {
        initializeWidget()
      }
      document.body.appendChild(script)
      existingScript = script
    }

    return () => {
      // クリーンアップ（スクリプトタグとウィジェット）
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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md p-8">
          <div className="flex items-center gap-3 mb-4">
            <AlertCircle className="h-8 w-8 text-red-500" />
            <h1 className="text-2xl font-bold text-red-600">エラー</h1>
          </div>
          <p className="text-gray-700 mb-4">
            埋め込みキーが指定されていません。
          </p>
          <div className="bg-gray-50 rounded p-4">
            <p className="text-sm text-gray-600 mb-2">
              <strong>正しいURL形式:</strong>
            </p>
            <code className="text-xs bg-gray-100 px-2 py-1 rounded block break-all">
              /widget-test?key=YOUR_EMBED_KEY
            </code>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        {/* ヘッダーセクション */}
        <Card className="p-8 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="text-4xl">🤖</div>
            <div>
              <h1 className="text-3xl font-bold">
                埋め込みウィジェット テスト環境
              </h1>
              <p className="text-gray-600 mt-1">
                実際のウィジェットの動作をご確認いただけます
              </p>
            </div>
          </div>

          <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4 mt-6">
            <div className="flex items-start gap-3">
              <div className="text-2xl">👉</div>
              <div>
                <p className="font-semibold text-blue-900 mb-1">
                  右下のチャットアイコンをクリック
                </p>
                <p className="text-sm text-blue-800">
                  ウィジェットが開き、質問できるようになります
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-2">
              <strong>使用中の埋め込みキー:</strong>
            </p>
            <code className="text-sm bg-white px-3 py-2 rounded border border-gray-200 block font-mono break-all">
              {embedKey}
            </code>
          </div>
        </Card>

        {/* 使い方セクション */}
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
                <p className="font-medium text-gray-900">
                  右下のチャットアイコンをクリック
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  画面右下に表示されているボタンをクリックするとウィジェットが開きます
                </p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold">
                2
              </span>
              <div className="flex-1">
                <p className="font-medium text-gray-900">
                  質問を入力してください
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  テキストエリアに質問を入力し、Enterキーを押すか送信ボタンをクリック
                </p>
              </div>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold">
                3
              </span>
              <div className="flex-1">
                <p className="font-medium text-gray-900">AIが回答を生成</p>
                <p className="text-sm text-gray-600 mt-1">
                  アップロードした文書に基づいて、AIが自動的に回答を生成します
                </p>
              </div>
            </li>
          </ol>
        </Card>

        {/* 質問例セクション */}
        <Card className="p-8 mb-8">
          <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
            <span className="text-2xl">💡</span>
            質問例
          </h2>
          <div className="grid gap-3">
            {[
              'この文書は何について書かれていますか？',
              '主なポイントを3つ教えてください',
              '具体的な手順を教えてください',
              '注意点はありますか？',
            ].map((question, index) => (
              <div
                key={index}
                className="bg-gray-50 border border-gray-200 rounded-lg p-3 hover:bg-gray-100 transition-colors"
              >
                <p className="text-gray-700">
                  <span className="text-gray-400 mr-2">Q{index + 1}.</span>
                  {question}
                </p>
              </div>
            ))}
          </div>
        </Card>

        {/* 埋め込みコードセクション */}
        <Card className="p-8">
          <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
            <span className="text-2xl">💻</span>
            あなたのサイトへの埋め込みコード
          </h2>
          <p className="text-gray-600 mb-4">
            以下のコードをあなたのウェブサイトの{' '}
            <code className="bg-gray-100 px-2 py-1 rounded">&lt;body&gt;</code>{' '}
            タグ内に貼り付けるだけで、 同じウィジェットが表示されます：
          </p>
          <div className="bg-gray-900 rounded-lg p-6 overflow-x-auto relative">
            <pre className="text-gray-100 text-sm font-mono">
              {origin
                ? `<script 
  src="${origin}/embed.js"
  data-embed-key="${embedKey}"
  data-api-base="${apiBaseUrl}"
></script>
<!-- 本番環境ではこのコードを使用してください -->`
                : '読み込み中...'}
            </pre>
            <Button
              variant="ghost"
              size="sm"
              className="absolute top-4 right-4 bg-gray-800 hover:bg-gray-700"
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
          <div className="mt-4 bg-yellow-50 border-l-4 border-yellow-500 rounded-r-lg p-4">
            <p className="text-sm text-yellow-800">
              <strong>注意:</strong> 本番環境では{' '}
              <code className="bg-yellow-100 px-2 py-1 rounded">
                window.location.origin
              </code>{' '}
              を 実際のドメインに置き換えてください。
            </p>
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
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary mx-auto mb-4"></div>
            <p className="text-gray-600">読み込み中...</p>
          </div>
        </div>
      }
    >
      <WidgetTestContent />
    </Suspense>
  )
}
