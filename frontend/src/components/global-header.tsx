'use client'

import Link from 'next/link'
import { Bot } from 'lucide-react'
import { usePathname } from 'next/navigation'
import { config } from '@/lib/config'

export default function GlobalHeader() {
  const pathname = usePathname()

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
            className={`text-sm ${pathname?.startsWith('/embed-admin') ? 'underline font-medium' : 'underline'}`}
          >
            Embed Admin
          </Link>
          <Link
            href="/pdf"
            className={`text-sm ${pathname?.startsWith('/pdf') ? 'underline font-medium' : 'underline'}`}
          >
            PDF
          </Link>
        </div>
      </div>
    </div>
  )
}
