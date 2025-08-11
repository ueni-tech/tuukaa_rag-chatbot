import { config } from '@/lib/config'

export async function DELETE(req: Request) {
  try {
    const { fileName } = await req.json()

    const deleteResponse = await fetch(
      `${config.apiUrl}${config.apiBasePath}/pdf/documents`,
      {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: fileName,
        }),
      }
    )

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
        { status: deleteResponse.status }
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
    return Response.json(
      {
        error:
          error instanceof Error
            ? error.message
            : 'ファイル削除中にエラーが発生しました。',
      },
      { status: 500 }
    )
  }
}
