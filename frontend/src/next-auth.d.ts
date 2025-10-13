import { DefaultSession } from 'next-auth'

declare module 'next-auth' {
  interface User {
    role?: string
  }

  interface Session {
    user: {
      role?: string
    } & DefaultSession['user']
  }
}

declare module '@auth/core/jwt' {
  interface JWT {
    role?: string
  }
}
