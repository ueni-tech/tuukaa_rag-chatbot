export { auth as middleware } from '@/auth'

export const config = {
  matcher: ['/', '/embed-admin/:path*', '/chat-test/:path*'],
}
