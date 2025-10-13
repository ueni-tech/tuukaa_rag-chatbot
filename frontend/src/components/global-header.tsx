'use client'

import Link from 'next/link'
import { Bot, LogOut } from 'lucide-react'
import { usePathname } from 'next/navigation'
import { config } from '@/lib/config'
import { Button } from '@/components/ui/button'
import { signOut, useSession } from 'next-auth/react'
import { toast } from 'sonner'

export default function GlobalHeader() {
  const pathname = usePathname()
  const { data: session, status } = useSession()
  const isLoggedIn = status === 'authenticated'

  const handleLogout = async () => {
    try {
      await signOut({
        callbackUrl: '/login',
        redirect: true,
      })
      toast.success('ログアウトしました')
    } catch (error) {
      toast.error('ログアウトに失敗しました')
    }
  }

  if (
    pathname === '/login' ||
    pathname === '/widget-test' ||
    pathname === '/auth/error'
  ) {
    return null
  }

  return (
    <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4">
        <div className="flex items-center gap-2">
          <Bot className="h-6 w-6" />
          <Link href="/" className="font-semibold">
            {config.appName}
          </Link>
        </div>
        <div className="ml-auto flex items-center gap-4">
          <Link
            href="/embed-admin"
            className={`text-sm ${
              pathname?.startsWith('/embed-admin')
                ? 'underline font-semibold'
                : ''
            }`}
          >
            Embed Admin
          </Link>
          <Link
            href="/chat-test"
            className={`text-sm ${
              pathname?.startsWith('/chat-test')
                ? 'underline font-semibold'
                : ''
            }`}
          >
            Chat Test
          </Link>
          {isLoggedIn && (
            <>
              <span className="text-sm text-muted-foreground">
                {session?.user?.name}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="flex items-center gap-2"
              >
                <LogOut className="h-4 w-4" />
                ログアウト
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
