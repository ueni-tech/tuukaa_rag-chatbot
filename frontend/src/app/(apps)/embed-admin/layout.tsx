import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '../../globals.css'
import { Toaster } from '@/components/ui/sonner'

const inter = Inter({ subsets: ['latin'] })

export default function Layout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <>
      <main className="flex-1 flex flex-col min-h-screen">{children}</main>
      <Toaster />
    </>
  )
}
