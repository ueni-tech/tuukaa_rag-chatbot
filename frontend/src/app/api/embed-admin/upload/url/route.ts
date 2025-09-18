import { config, serverConfig } from '@/lib/config'

export async function POST(req: Request) {
  const key = req.headers.get('x-embed-key') || ''
  const { targetUrl } = await req.json()
  const ac = new AbortController()
  const t = setTimeout(() => ac.abort(), 55_000)
  try {
    const base = serverConfig.internalApiUrl || config.apiUrl
    const res = await fetch(`${base}${config.apiBasePath}/embed/docs/url`, {
      method: 'POST',
      body: JSON.stringify({ url: targetUrl }),
      headers: {
        'Content-Type': 'application/json',
        'x-embed-key': key,
      },
      signal: ac.signal,
      cache: 'no-store',
    })
    let data: unknown = null
    try {
      data = await res.json()
    } catch {
      data = null
    }
    return Response.json(data, { status: res.status })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      return Response.json(
        { error: 'アップロードがタイムアウトしました。' },
        { status: 504 }
      )
    }
    return Response.json(
      { error: 'アップロード中にエラーが発生しました。' },
      { status: 500 }
    )
  } finally {
    clearTimeout(t)
  }
}
