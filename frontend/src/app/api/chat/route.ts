import { config, serverConfig } from '@/lib/config'

export const maxDuration = 30

export async function POST(req: Request) {
  try {
    const { question, model, top_k, max_output_tokens } = await req.json()

    // ヘッダーから認証情報を取得
    const embedKey = req.headers.get('x-embed-key')
    const adminSecret = req.headers.get('x-admin-api-secret')

    if (!question.trim()) {
      return Response.json(
        { error: '質問を入力してください。' },
        { status: 400 }
      )
    }

    const url = `${config.apiUrl}${config.apiBasePath}/embed/docs/ask`

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (embedKey) headers['x-embed-key'] = String(embedKey)
    if (adminSecret && serverConfig.adminApiSecret) {
      headers['x-admin-api-secret'] = String(serverConfig.adminApiSecret)
    }

    const askResponse = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        question: question,
        top_k: typeof top_k === 'number' ? top_k : 10,
        model: model || undefined,
        max_output_tokens:
          typeof max_output_tokens === 'number' ? max_output_tokens : undefined,
      }),
    })

    if (!askResponse.ok) {
      const contentType = askResponse.headers.get('content-type')
      let errorMessage = 'Unknown error'

      if (contentType && contentType.includes('application/json')) {
        try {
          const errorData = await askResponse.json()
          errorMessage = errorData.detail || 'Unknown error'
        } catch {
          errorMessage = 'JSON parse error in error response'
        }
      } else {
        errorMessage = await askResponse.text()
      }

      throw new Error(`FastAPI request failed: ${errorMessage}`)
    }

    const data = await askResponse.json()

    return Response.json({
      role: 'assistant',
      content: data.answer,
      question: data.question,
      documents: data.documents,
      llm_model: data.llm_model,
    })
  } catch (error) {
    console.error('Chat API error:', error)
    return Response.json(
      {
        error:
          error instanceof Error
            ? error.message
            : 'チャット処理中にエラーが発生しました。',
      },
      { status: 500 }
    )
  }
}
