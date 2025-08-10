import { config } from '@/lib/config'

export const maxDuration = 30

export async function POST(req: Request) {
  try {
    const { messages } = await req.json()

    const lastMessage = messages[messages.length - 1]
    const question = lastMessage?.content || ''

    if (!question.trim()) {
      return Response.json(
        { error: '質問を入力してください。' },
        { status: 400 }
      )
    }

    const askResponse = await fetch(
      `${config.apiUrl}${config.apiBasePath}/pdf/ask`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question,
          top_k: 5,
        }),
      }
    )

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
