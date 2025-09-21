import Link from 'next/link'
import React from 'react'

export default function home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-full p-8">
      <div className="max-w-md w-full space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-2">Tuukaa</h1>
          <p className="text-muted-foreground">AI-powered Applications</p>
        </div>

        <div className="space-y-4">
          <Link
            href="/embed-admin"
            className="block w-full p-4 text-center bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            QAウィジェット ダッシュボード
          </Link>
          <Link
            href="/chat-test"
            className="block w-full p-4 text-center bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            チャットテスト
          </Link>
        </div>
      </div>
    </div>
  )
}
