import { config } from '@/lib/config'

export const maxDuration = 60

export async function POST(req: Request) {
  try {
    const formData = await req.formData()

    const uploadResponse = await fetch(
      `${config.apiUrl}${config.apiBasePath}/pdf/upload`,
      {
        method: 'POST',
        body: formData,
      }
    )

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
