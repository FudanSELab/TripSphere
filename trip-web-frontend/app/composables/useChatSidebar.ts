import type { ChatContext } from '~/types'
import { useState } from '#app'
// Global state for the chat sidebar is now managed with useState for SSR safety




export const useChatSidebar = () => {
  const isChatSidebarOpen = useState('isChatSidebarOpen', () => false)
  const chatContext = useState<ChatContext | null>('chatContext', () => null)
  const chatTitle = useState('chatTitle', () => 'AI Assistant')
  const openChatSidebar = (context?: ChatContext | null, title?: string) => {
    chatContext.value = context || null
    chatTitle.value = title || 'AI Assistant'
    isChatSidebarOpen.value = true
  }

  const closeChatSidebar = () => {
    isChatSidebarOpen.value = false
  }

  const toggleChatSidebar = () => {
    isChatSidebarOpen.value = !isChatSidebarOpen.value
  }

  return {
    isChatSidebarOpen: readonly(isChatSidebarOpen),
    chatContext: readonly(chatContext),
    chatTitle: readonly(chatTitle),
    openChatSidebar,
    closeChatSidebar,
    toggleChatSidebar,
  }
}
