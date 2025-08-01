export const config = {
  // クライアントサイドで使用可能
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  apiBasePath: process.env.NEXT_PUBLIC_API_BASE_PATH || '/api/v1',
  appName: process.env.NEXT_PUBLIC_APP_NAME || 'LPナレッジ検索',
  isDebug: process.env.NEXT_PUBLIC_DEBUG === 'true',
}

// サーバーサイドのみで使用
export const serverConfig = {
  apiSecret: process.env.API_SECRET_KEY,
  internalApiUrl: process.env.INTERNAL_API_URL,
}
