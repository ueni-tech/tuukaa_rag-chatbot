'use client'
import { useState } from 'react'
import { postFormData, postJson, getJson } from '@/lib/api'

type UploadResponse = {
  status: string
  message: string
  file_info?: any
  vectorstore_info?: any
}

export default function PdfAppStub() {
  const [status, setStatus] = useState<string>('')
  const [info, setInfo] = useState<any>(null)
  const [busy, setBusy] = useState(false)

  const onUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const fileInput = e.currentTarget.elements.namedItem(
      'file'
    ) as HTMLInputElement
    const file = fileInput?.files?.[0]
    if (!file) return
    setBusy(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await postFormData<UploadResponse>('pdf/upload', fd)
      setStatus(res.message)
    } catch (err: any) {
      setStatus(`アップロード失敗: ${err?.message ?? err}`)
    } finally {
      setBusy(false)
    }
  }

  const onInfo = async () => {
    setBusy(true)
    try {
      const res = await getJson<any>('pdf/system/info')
      setInfo(res)
    } catch (err: any) {
      setStatus(`情報取得失敗: ${err?.message ?? err}`)
    } finally {
      setBusy(false)
    }
  }

  const onSearch = async () => {
    setBusy(true)
    try {
      const res = await postJson<any>('pdf/search', {
        question: 'テスト',
        top_k: 1,
      })
      setInfo(res)
    } catch (err: any) {
      setStatus(`検索失敗: ${err?.message ?? err}`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">PDF アプリ（雛形）</h1>
      <form onSubmit={onUpload} className="flex items-center gap-2">
        <input type="file" name="file" accept="application/pdf" />
        <button
          className="px-3 py-1 rounded bg-black text-white disabled:opacity-50"
          disabled={busy}
        >
          アップロード
        </button>
      </form>
      <div className="flex gap-2">
        <button
          onClick={onInfo}
          className="px-3 py-1 rounded bg-gray-200 disabled:opacity-50"
          disabled={busy}
        >
          system/info
        </button>
        <button
          onClick={onSearch}
          className="px-3 py-1 rounded bg-gray-200 disabled:opacity-50"
          disabled={busy}
        >
          search
        </button>
      </div>
      {status && <p className="text-sm text-gray-700">{status}</p>}
      {info && (
        <pre className="p-3 bg-gray-50 border rounded text-xs overflow-auto max-h-[50vh]">
          {JSON.stringify(info, null, 2)}
        </pre>
      )}
    </main>
  )
}
