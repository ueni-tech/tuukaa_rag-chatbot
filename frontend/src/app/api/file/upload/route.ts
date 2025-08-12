import { config } from '@/lib/config'

export async function POST(req: Request) {
  try {
    const formData = await req.formData()

    const ac = new AbortController()
    const t = setTimeout(() => ac.abort(), 55_000)

    let uploadResponse: Response
    try {
      uploadResponse = await fetch(
        `${config.apiUrl}${config.apiBasePath}/pdf/upload`,
        {
          method: 'POST',
          body: formData,
          signal: ac.signal,
          cache: 'no-store'
        }
      )
    } finally {
      clearTimeout(t)
    }

    if (!uploadResponse.ok) {
      let detail = 'Unknown error'
      try {
        const errJson = await uploadResponse.json()
        detail = errJson.detail || detail
      } catch {
        // ignore json parse error
      }
      return Response.json(
        { error: `アップロードエラー: ${detail}` },
        { status: uploadResponse.status }
      )
    }

    const data = await uploadResponse.json()
    return Response.json(data)
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      return Response.json({ error: 'アップロードがタイムアウトしました。' }, { status: 504 })
    }
    console.error('File upload API error:', error)
    return Response.json(
      {
        error:
          error instanceof Error
            ? error.message
            : 'ファイルアップロード中にエラーが発生しました。',
      },
      { status: 500 }
    )
  }
}
