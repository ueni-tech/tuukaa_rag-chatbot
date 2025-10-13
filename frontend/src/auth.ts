import NextAuth from 'next-auth'
import Google from 'next-auth/providers/google'

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  pages: {
    signIn: '/login',
    error: '/auth/error',
  },
  callbacks: {
    async signIn({ user }) {
      const allowedEmails =
        process.env.ADMIN_EMAILS?.split(',').map(e => e.trim()) || []

      if (allowedEmails.length === 0) {
        console.error('ADMIN_EMAILS is not set in environment variables')
        return false
      }

      if (!allowedEmails.includes(user.email || '')) {
        console.log(`Access denied for email: ${user.email}`)
        return false
      }

      return true
    },
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user
      const isOnProtectedPage =
        nextUrl.pathname === '/' ||
        nextUrl.pathname.startsWith('/embed-admin') ||
        nextUrl.pathname.startsWith('/chat-test')

      if (isOnProtectedPage) {
        if (isLoggedIn) return true
        return false
      }

      return true
    },
    jwt({ token, user }) {
      if (user) {
        token.role = 'admin'
      }
      return token
    },
    session({ session, token }) {
      if (session.user) {
        session.user.role = token.role
      }
      return session
    },
  },
  session: {
    strategy: 'jwt',
    maxAge: 24 * 60 * 60,
  },
  secret: process.env.AUTH_SECRET,
})

// 起動時の必須環境変数チェック
if (!process.env.AUTH_SECRET) {
  throw new Error('AUTH_SECRET is required')
}
if (!process.env.GOOGLE_CLIENT_ID || !process.env.GOOGLE_CLIENT_SECRET) {
  throw new Error('Google OAuth credentials are required')
}
