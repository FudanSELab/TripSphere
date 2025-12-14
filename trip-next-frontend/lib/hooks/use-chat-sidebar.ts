'use client'

import { create } from 'zustand'
import type { ChatContext } from '@/lib/types'

interface ChatSidebarState {
  isOpen: boolean
  context: ChatContext | null
  title: string
  
  open: (context?: ChatContext | null, title?: string) => void
  close: () => void
  toggle: () => void
}

export const useChatSidebar = create<ChatSidebarState>((set) => ({
  isOpen: false,
  context: null,
  title: 'AI Assistant',
  
  open: (context = null, title = 'AI Assistant') => {
    set({ isOpen: true, context, title })
  },
  
  close: () => {
    set({ isOpen: false })
  },
  
  toggle: () => {
    set((state) => ({ isOpen: !state.isOpen }))
  },
}))
