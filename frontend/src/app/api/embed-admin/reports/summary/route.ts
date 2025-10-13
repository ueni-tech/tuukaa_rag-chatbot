import { config, serverConfig } from '@/lib/config'

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const tenant = searchParams.get('tenant')
  const start = searchParams.get('start')
  const end = searchParams.get('end')
  if (!tenant || !start || !end) {
    return Response.json({ error: 'missing params' }, { status: 400 })
  }
  const base = serverConfig.internalApiUrl || config.apiUrl
  const url = `${base}${
    config.apiBasePath
  }/admin/reports/summary?tenant=${encodeURIComponent(
    tenant
  )}&start=${start}&end=${end}`
  const res = await fetch(url, {
    headers: {
      'x-admin-api-secret': serverConfig.adminApiSecret || '',
    },
    cache: 'no-store',
  })
  if (!res.ok) {
    const t = await res.text().catch(() => 'error')
    return Response.json({ error: t }, { status: 500 })
  }
  const data = await res.json()
  return Response.json(data)
}

export async function POST(req: Request) {
  const { tenant, start, end } = await req.json().catch(() => ({}))
  if (!tenant || !start || !end) {
    return Response.json({ error: 'missing params' }, { status: 400 })
  }
  const base = serverConfig.internalApiUrl || config.apiUrl
  const url = `${base}${config.apiBasePath}/admin/reports/summary/evidence?tenant=${encodeURIComponent(tenant)}&start=${start}&end=${end}`
  const res = await fetch(url, {
    headers: { 'x-admin-api-secret': serverConfig.adminApiSecret || '' },
    cache: 'no-store',
  })
  if (!res.ok) {
    const t = await res.text().catch(() => 'error')
    return Response.json({ error: t }, { status: 500 })
  }
  const data = await res.json()
  return Response.json(data)
}
