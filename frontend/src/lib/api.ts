import { config } from './config'

function joinPath(base: string, ...parts: string[]): string {
  const full = [
    base.replace(/\/$/, ''),
    ...parts.map(p => p.replace(/^\//, '')),
  ].join('/')
  return full
}

export function getApiUrl(path: string): string {
  return joinPath(config.apiUrl, config.apiBasePath, path)
}

export async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(getApiUrl(path), { cache: 'no-store' })
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`)
  return (await res.json()) as T
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(getApiUrl(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body ?? {}),
  })
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`)
  return (await res.json()) as T
}

export async function postFormData<T>(
  path: string,
  formData: FormData
): Promise<T> {
  const res = await fetch(getApiUrl(path), { method: 'POST', body: formData })
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`)
  return (await res.json()) as T
}
