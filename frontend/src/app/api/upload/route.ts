import { config } from '@/lib/config'

export const maxDuration = 30

export async function POST(req: Request) {
  try {
    const formData = await req.formData()

    const uploadRespose = await fetch(
      `${config.apiUrl}${config.apiBasePath}/upload`,
      {
        method: 'POST',
        body: formData,
      }
    )

    if (!uploadRespose.ok) {
      const contentType = uploadRespose.headers.get('content-type')
      let errorMessage = 'Unkown error'

      if (contentType && contentType.includes('application/json')) {
        const errorData = await uploadRespose.json()
        errorMessage = errorData.detail || 'Unknown error'
      } else {
        errorMessage = await uploadRespose.text()
      }
      throw new Error(`FastAPI request failed: ${errorMessage}`)
    }

    const result = await uploadRespose.json()
    console.log('Upload successful:', result)

    return Response.json(result)
  } catch (error) {
    console.error('Upload API error:', error)
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
