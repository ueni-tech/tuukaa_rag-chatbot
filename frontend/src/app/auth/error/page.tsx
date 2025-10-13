'use client'

import { useSearchParams } from 'next/navigation'
import { Card } from '@/components/ui/card'
import { AlertCircle } from 'lucide-react'

export default function AuthError() {
  const searchParams = useSearchParams()
  const error = searchParams.get('error')

  return (
    <div className="flex items-center justify-center min-h-screen">
      <Card className="p-8 max-w-md">
        <div className="flex items-center gap-3 mb-4">
          <AlertCircle className="h-8 w-8 text-red-500" />
          <h1 className="text-2xl font-bold">アクセス拒否</h1>
        </div>
        <p className="text-muted-foreground mb-4">
          {error === 'AccessDenied'
            ? 'このメールアドレスは許可されていません。管理者にお問い合わせください。'
            : 'ログインに失敗しました。'}
        </p>
        <a
          href="/login"
          className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 w-full"
        >
          ログイン画面に戻る
        </a>
      </Card>
    </div>
  )
}
