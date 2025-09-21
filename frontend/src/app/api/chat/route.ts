import { config, serverConfig } from '@/lib/config'

export const maxDuration = 30

export async function POST(req: Request) {
  try {
    const { messages, model, top_k, admin, embedKey } = await req.json()

    const lastMessage = messages[messages.length - 1]
    const question = lastMessage?.content || ''

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
    if (admin && serverConfig.adminApiSecret)
      headers['x-admin-api-secret'] = String(serverConfig.adminApiSecret)

    const askResponse = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        question: question,
        top_k: typeof top_k === 'number' ? top_k : 3,
        model: model || undefined,
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
      context_used: data.context_used,
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
