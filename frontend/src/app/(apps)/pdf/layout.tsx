import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '../../globals.css'
import { SidebarProvider } from '@/components/ui/sidebar'
import AppSidebar from '@/components/app-sidebar'
import { ThemeProvider } from '@/components/theme-provider'
import { Toaster } from '@/components/ui/sonner'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Tuukaa | RAG Chatbot',
  description: 'Tuukaa is AI-powered chatbot with document understanding',
}

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
