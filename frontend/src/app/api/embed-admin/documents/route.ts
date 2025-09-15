import { config, serverConfig } from '@/lib/config'

export async function GET(req: Request) {
  const key = req.headers.get('x-embed-key') || ''
  const base = serverConfig.internalApiUrl || config.apiUrl
  const res = await fetch(`${base}${config.apiBasePath}/embed/docs/documents`, {
    headers: { 'x-embed-key': key },
    cache: 'no-store',
  })
  let data: unknown = null
  try {
    data = await res.json()
  } catch {
    data = null
  }
  return Response.json(data, { status: res.status })
}

export async function DELETE(req: Request) {
  const key = req.headers.get('x-embed-key') || ''
  let body: unknown = null
  try {
    body = await req.json()
  } catch {
    body = null
  }
  const base = serverConfig.internalApiUrl || config.apiUrl
  const res = await fetch(`${base}${config.apiBasePath}/embed/docs/documents`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      'x-embed-key': key,
    },
    body: body ? JSON.stringify(body) : undefined,
  })
  let data: unknown = null
  try {
    data = await res.json()
  } catch {
    data = null
  }
  return Response.json(data, { status: res.status })
}
