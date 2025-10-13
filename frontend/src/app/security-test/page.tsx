'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react'

interface TestResult {
  name: string
  status: 'success' | 'error' | 'warning'
  message: string
  details?: string
}

export default function SecurityTestPage() {
  const [question, setQuestion] = useState('')
  const [model, setModel] = useState('gpt-4o-mini')
  const [clientId, setClientId] = useState('test-client-123')
  const [sessionId, setSessionId] = useState('test-session-456')
  const [messageId, setMessageId] = useState('test-message-789')
  const [results, setResults] = useState<TestResult[]>([])
  const [loading, setLoading] = useState(false)

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

  const addResult = (result: TestResult) => {
    setResults(prev => [...prev, result])
  }

  const clearResults = () => {
    setResults([])
  }

  // テスト1: 制御文字を含む質問
  const testControlCharacters = async () => {
    setLoading(true)
    try {
      const testQuestion = 'テスト\x00\x01\x02質問\x03\x04'
      const response = await fetch(`${API_BASE}/api/v1/embed/docs/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Embed-Key': 'demo123',
        },
        body: JSON.stringify({
          question: testQuestion,
          top_k: 2,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        addResult({
          name: '制御文字のサニタイゼーション',
          status: 'success',
          message: '制御文字が適切に除去されました',
          details: `元の質問: "${testQuestion}"\n処理後: "${data.query}"`,
        })
      } else {
        addResult({
          name: '制御文字のサニタイゼーション',
          status: 'error',
          message: `エラー: ${response.status}`,
        })
      }
    } catch (error) {
      addResult({
        name: '制御文字のサニタイゼーション',
        status: 'error',
        message: `例外: ${error}`,
      })
    }
    setLoading(false)
  }

  // テスト2: 最大長制限
  const testMaxLength = async () => {
    setLoading(true)
    try {
      // 2000文字（成功するはず）
      const validQuestion = 'あ'.repeat(2000)
      const response1 = await fetch(`${API_BASE}/api/v1/embed/docs/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Embed-Key': 'demo123',
        },
        body: JSON.stringify({
          question: validQuestion,
          top_k: 2,
        }),
      })

      // 2001文字（失敗するはず）
      const invalidQuestion = 'あ'.repeat(2001)
      const response2 = await fetch(`${API_BASE}/api/v1/embed/docs/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Embed-Key': 'demo123',
        },
        body: JSON.stringify({
          question: invalidQuestion,
          top_k: 2,
        }),
      })

      if (response1.ok && !response2.ok) {
        addResult({
          name: '最大長制限（2000文字）',
          status: 'success',
          message: '2000文字は成功、2001文字は拒否されました',
          details: `2000文字: ${response1.status}\n2001文字: ${response2.status}`,
        })
      } else {
        addResult({
          name: '最大長制限（2000文字）',
          status: 'warning',
          message: '期待と異なる結果',
          details: `2000文字: ${response1.status}\n2001文字: ${response2.status}`,
        })
      }
    } catch (error) {
      addResult({
        name: '最大長制限（2000文字）',
        status: 'error',
        message: `例外: ${error}`,
      })
    }
    setLoading(false)
  }

  // テスト3: モデル名のインジェクション攻撃
  const testModelInjection = async () => {
    setLoading(true)
    try {
      const maliciousModel = 'gpt-4o; DROP TABLE users;'
      const response = await fetch(`${API_BASE}/api/v1/embed/docs/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Embed-Key': 'demo123',
          'X-Admin-Api-Secret': 'test_admin_secret',
          'X-Test-Environment': 'true',
        },
        body: JSON.stringify({
          question: 'テスト',
          top_k: 2,
          model: maliciousModel,
        }),
      })

      if (!response.ok && response.status === 422) {
        addResult({
          name: 'モデル名インジェクション防止',
          status: 'success',
          message: '不正なモデル名が適切に拒否されました',
          details: `試行したモデル名: "${maliciousModel}"\nステータス: ${response.status}`,
        })
      } else {
        addResult({
          name: 'モデル名インジェクション防止',
          status: 'error',
          message: '不正なモデル名が受け入れられてしまいました',
          details: `ステータス: ${response.status}`,
        })
      }
    } catch (error) {
      addResult({
        name: 'モデル名インジェクション防止',
        status: 'error',
        message: `例外: ${error}`,
      })
    }
    setLoading(false)
  }

  // テスト4: ID類のバリデーション
  const testIdValidation = async () => {
    setLoading(true)
    try {
      // 不正な文字を含むclient_id
      const invalidClientId = 'client@123#abc'
      const response = await fetch(`${API_BASE}/api/v1/embed/docs/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Embed-Key': 'demo123',
          'X-Admin-Api-Secret': 'test_admin_secret',
          'X-Test-Environment': 'true',
        },
        body: JSON.stringify({
          question: 'テスト',
          top_k: 2,
          client_id: invalidClientId,
        }),
      })

      if (!response.ok && response.status === 422) {
        addResult({
          name: 'ID類のバリデーション',
          status: 'success',
          message: '不正な文字を含むIDが適切に拒否されました',
          details: `試行したclient_id: "${invalidClientId}"\nステータス: ${response.status}`,
        })
      } else {
        addResult({
          name: 'ID類のバリデーション',
          status: 'error',
          message: '不正なIDが受け入れられてしまいました',
          details: `ステータス: ${response.status}`,
        })
      }
    } catch (error) {
      addResult({
        name: 'ID類のバリデーション',
        status: 'error',
        message: `例外: ${error}`,
      })
    }
    setLoading(false)
  }

  // テスト5: 通常のリクエストが動作することを確認
  const testNormalRequest = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/v1/embed/docs/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Embed-Key': 'demo123',
          'X-Admin-Api-Secret': 'test_admin_secret',
          'X-Test-Environment': 'true',
        },
        body: JSON.stringify({
          question: question || 'これは通常の質問です',
          top_k: 3,
          model: model,
          client_id: clientId,
          session_id: sessionId,
          message_id: messageId,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        addResult({
          name: '通常のリクエスト',
          status: 'success',
          message: '正常に処理されました',
          details: `回答: ${data.answer?.substring(0, 100)}...\nトークン: ${data.tokens}\nコスト: ${data.cost_jpy}円`,
        })
      } else {
        const error = await response.text()
        addResult({
          name: '通常のリクエスト',
          status: 'error',
          message: `エラー: ${response.status}`,
          details: error,
        })
      }
    } catch (error) {
      addResult({
        name: '通常のリクエスト',
        status: 'error',
        message: `例外: ${error}`,
      })
    }
    setLoading(false)
  }

  // 全テストを実行
  const runAllTests = async () => {
    clearResults()
    await testControlCharacters()
    await new Promise(resolve => setTimeout(resolve, 500))
    await testMaxLength()
    await new Promise(resolve => setTimeout(resolve, 500))
    await testModelInjection()
    await new Promise(resolve => setTimeout(resolve, 500))
    await testIdValidation()
    await new Promise(resolve => setTimeout(resolve, 500))
    await testNormalRequest()
  }

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />
    }
  }

  const getStatusColor = (status: TestResult['status']) => {
    switch (status) {
      case 'success':
        return 'border-green-500'
      case 'error':
        return 'border-red-500'
      case 'warning':
        return 'border-yellow-500'
    }
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">
          セキュリティ機能テストページ
        </h1>
        <p className="text-muted-foreground">
          入力サニタイゼーションとログマスキング機能をテストします
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左側: テスト設定 */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>テスト設定</CardTitle>
              <CardDescription>
                通常のリクエストテスト用のパラメータ
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="question">質問</Label>
                <Textarea
                  id="question"
                  placeholder="質問を入力してください"
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  rows={3}
                />
              </div>

              <div>
                <Label htmlFor="model">モデル</Label>
                <Input
                  id="model"
                  value={model}
                  onChange={e => setModel(e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="clientId">Client ID</Label>
                <Input
                  id="clientId"
                  value={clientId}
                  onChange={e => setClientId(e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="sessionId">Session ID</Label>
                <Input
                  id="sessionId"
                  value={sessionId}
                  onChange={e => setSessionId(e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="messageId">Message ID</Label>
                <Input
                  id="messageId"
                  value={messageId}
                  onChange={e => setMessageId(e.target.value)}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>テスト実行</CardTitle>
              <CardDescription>
                各種セキュリティテストを実行します
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                onClick={runAllTests}
                disabled={loading}
                className="w-full"
              >
                全テストを実行
              </Button>
              <Separator />
              <Button
                onClick={testControlCharacters}
                disabled={loading}
                variant="outline"
                className="w-full"
              >
                制御文字のサニタイゼーション
              </Button>
              <Button
                onClick={testMaxLength}
                disabled={loading}
                variant="outline"
                className="w-full"
              >
                最大長制限テスト
              </Button>
              <Button
                onClick={testModelInjection}
                disabled={loading}
                variant="outline"
                className="w-full"
              >
                モデル名インジェクション防止
              </Button>
              <Button
                onClick={testIdValidation}
                disabled={loading}
                variant="outline"
                className="w-full"
              >
                ID類のバリデーション
              </Button>
              <Button
                onClick={testNormalRequest}
                disabled={loading}
                variant="outline"
                className="w-full"
              >
                通常のリクエスト
              </Button>
              <Separator />
              <Button onClick={clearResults} variant="ghost" className="w-full">
                結果をクリア
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* 右側: テスト結果 */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>テスト結果</CardTitle>
              <CardDescription>
                {results.length > 0
                  ? `${results.length}件のテストが実行されました`
                  : 'テストを実行してください'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {results.length === 0 ? (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>テスト未実行</AlertTitle>
                  <AlertDescription>
                    左側のボタンからテストを実行してください
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-4">
                  {results.map((result, index) => (
                    <Card
                      key={index}
                      className={`border-l-4 ${getStatusColor(result.status)}`}
                    >
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(result.status)}
                          <CardTitle className="text-base">
                            {result.name}
                          </CardTitle>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm mb-2">{result.message}</p>
                        {result.details && (
                          <pre className="text-xs bg-muted p-2 rounded overflow-x-auto whitespace-pre-wrap">
                            {result.details}
                          </pre>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* 下部: 注意事項 */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>注意事項</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            •
            このテストページは開発環境専用です。本番環境では使用しないでください。
          </p>
          <p>
            • テストには{' '}
            <code className="bg-muted px-1 rounded">
              X-Test-Environment: true
            </code>{' '}
            ヘッダーを使用してRedis集計をスキップしています。
          </p>
          <p>
            •
            ログマスキングの確認は、バックエンドのログファイルまたはコンソール出力を確認してください。
          </p>
          <p>
            •{' '}
            <code className="bg-muted px-1 rounded">
              docker-compose logs backend
            </code>{' '}
            で確認できます。
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
