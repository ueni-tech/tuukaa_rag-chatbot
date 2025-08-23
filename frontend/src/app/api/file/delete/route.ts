import { config } from '@/lib/config'

export async function DELETE(req: Request) {
  try {
    let body: any = {}
    try {
      body = await req.json()
    } catch {
      return Response.json({ error: '不正なJSONです' }, { status: 400 })
    }
    const { fileName } = body
    if (!fileName || typeof fileName !== 'string') {
      return Response.json({ error: 'fileNameは必須です' }, { status: 400 })
    }

    const ac = new AbortController()
    const t = setTimeout(() => ac.abort(), 10000)

    let deleteResponse: Response
    try {
      deleteResponse = await fetch(
        `${config.apiUrl}${config.apiBasePath}/pdf/documents`,
        {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ filename: fileName }),
          signal: ac.signal,
          cache: 'no-store',
        }
      )
    } finally {
      clearTimeout(t)
    }

    if (!deleteResponse.ok) {
      let detail = 'Unknown error'
      try {
        const errJson = await deleteResponse.json()
        detail = errJson.detail || detail
      } catch {
        detail = 'JSON parse error in error response'
      }
      return Response.json(
        { error: `ファイル削除エラー: ${detail}` },
        { status: 400 }
      )
    }

    const data = await deleteResponse.json()
    console.log(data)
    return Response.json({
      status: data.status,
      message: data.message,
      deleted_filename: data.deleted_filename,
      remaining_files: data.remaining_files,
    })
  } catch (error) {
    console.error('File delete API error:', error)
    const msg = error instanceof DOMException && error.name === 'AbortError' ? 'タイムアウトしました。ネットワーク状況を確認してください。' : error instanceof Error ? error.message : 'ファイル削除中にエラーが発生しました。'
    return Response.json({ error: msg }, { status: 500 })
  }
}
