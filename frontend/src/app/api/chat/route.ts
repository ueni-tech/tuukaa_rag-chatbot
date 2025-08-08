import { config } from '@/lib/config'

export const maxDuration = 30

export async function POST(req: Request) {
  try {
    const { messages } = await req.json()

    const lastMessage = messages[messages.length - 1]
    const question = lastMessage?.content || ""

    if(!question.trim()){
      return Response.json(
        {error: '質問を入力してください。'},
        {status: 400}
      )
    }

    const askResponse = await fetch(`${config.apiUrl}${config.apiBasePath}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: question,
        top_k: 5
      }),
    })

    if(!askResponse.ok){
      const errorData = await askResponse.json()
      throw new Error(`FastAPI request failed: ${errorData.detail || 'Unknown error'}`)
    }

    const data = await askResponse.json()

    return Response.json({
      role: "assistant",
      content: data.answer,
      question: data.question,
      documents: data.documents,
      context_used: data.context_used
    })
  } catch(error){
    console.error("Chat API error:", error)
    return Response.json(
      { error: error instanceof Error ? error.message : 'チャット処理中にエラーが発生しました。' },
      { status: 500 }
    )
  }
}