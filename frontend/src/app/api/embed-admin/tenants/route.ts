import { config, serverConfig } from '@/lib/config'

export async function GET() {
  const base = serverConfig.internalApiUrl || config.apiUrl
  const res = await fetch(`${base}${config.apiBasePath}/admin/tenants`, {
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
