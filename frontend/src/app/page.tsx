'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Card } from '@/components/ui/card'
import { Send, Bot, User } from 'lucide-react'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { toast } from 'sonner'
import { config } from '@/lib/config'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  documents?: Array<{
    content: string
    metadata?: any
  }>
  content_used: string
}

export default function ChatPage() {
  return <div>page</div>
}
