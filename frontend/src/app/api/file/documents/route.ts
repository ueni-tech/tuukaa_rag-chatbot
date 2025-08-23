import { config } from "@/lib/config";

export async function GET() {
  try {
    const ac = new AbortController()
    const t = setTimeout(() => ac.abort(), 10000)

    let documentsResponse: Response
    try {
      documentsResponse = await fetch(`${config.apiUrl}${config.apiBasePath}/pdf/documents`, {
        method: 'GET',
        signal: ac.signal,
        cache: 'no-store'
      })
    } finally {
      clearTimeout(t)
    }

    if (!documentsResponse.ok) {
      let detail = 'Unknown error'
      try {
        const result = await documentsResponse.json()
        detail = result.detail || detail
      } catch {
        detail = 'JSON parse error in error response'
      }
      return Response.json({ error: `ドキュメント一覧取得エラー: ${detail}` }, { status: 400 })
    }

    const data = await documentsResponse.json()
    return Response.json({
      files: data.files,
      total_files: data.total_files,
      total_chunks: data.total_chunks,
    })
  } catch (error) {
    console.error('File delete API error:', error)
    const msg = error instanceof DOMException && error.name === 'AbortError' ? 'タイムアウトしました。ネットワーク状況を確認してください。' : error instanceof Error ? error.message : 'ドキュメント一覧取得中にエラーが発生しました。'
    return Response.json({ error: msg }, { status: 500 })
  }
}