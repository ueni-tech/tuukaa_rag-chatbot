export const config = {
  // クライアントサイドで使用可能
  // 段階移行: NEXT_PUBLIC_API_BASE を優先し、未設定時は API_URL + BASE_PATH で後方互換
  apiUrl:
    process.env.NEXT_PUBLIC_API_BASE ||
    process.env.NEXT_PUBLIC_API_URL ||
    'http://localhost:8000',
  apiBasePath: process.env.NEXT_PUBLIC_API_BASE_PATH || '/api/v1',
  appName: process.env.NEXT_PUBLIC_APP_NAME || 'tuukaa',
  isDebug: process.env.NEXT_PUBLIC_DEBUG === 'true',
}

// サーバーサイドのみで使用
export const serverConfig = {
  adminApiSecret: process.env.ADMIN_API_SECRET,
  internalApiUrl: process.env.INTERNAL_API_URL,
}
