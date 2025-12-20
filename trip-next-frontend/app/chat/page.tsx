'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { Plus, MessageSquare, Trash2, Clock } from 'lucide-react'
import type { Conversation } from '@/lib/types'
import { formatRelativeTime } from '@/lib/utils'
import { useAuth } from '@/lib/hooks/use-auth'
import { useChat } from '@/lib/hooks/use-chat'
import { ChatWindow } from '@/components/chat/chat-window'
import { Button } from '@/components/ui/button'

export default function ChatPage() {
  const auth = useAuth()
  const chat = useChat()

  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null)
  const [showSidebar, setShowSidebar] = useState(true)
  const hasLoadedRef = useRef(false)

  // Load conversations on mount
  useEffect(() => {
    if (auth.user && !hasLoadedRef.current) {
      hasLoadedRef.current = true
      
      const loadData = async () => {
        if (!auth.user) return
        const result = await chat.listConversations(auth.user.id)
        if (result) {
          setConversations(result.items)
        }
      }
      
      void loadData()
    }
  }, [auth.user, chat])

  const loadConversations = useCallback(async () => {
    if (!auth.user) return
    
    const result = await chat.listConversations(auth.user.id)
    if (result) {
      setConversations(result.items)
    }
  }, [auth.user, chat])

  const createNewChat = () => {
    setSelectedConversation(null)
  }

  const selectConversation = (conversation: Conversation) => {
    setSelectedConversation(conversation)
  }

  const handleConversationCreated = (conversation: Conversation) => {
    setConversations([conversation, ...conversations])
    setSelectedConversation(conversation)
  }

  const deleteConversation = async (conversation: Conversation, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!auth.user) return
    
    const success = await chat.deleteConversation(auth.user.id, conversation.conversationId)
    if (success) {
      const updatedConversations = conversations.filter(c => c.conversationId !== conversation.conversationId)
      setConversations(updatedConversations)
      if (selectedConversation?.conversationId === conversation.conversationId) {
        // Clear the selected conversation to show the initial state
        setSelectedConversation(null)
      }
    }
  }

  if (!auth.user) {
    return (
      <div className="h-[calc(100vh-64px)] flex items-center justify-center">
        <div className="text-center">
          <MessageSquare className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Please log in</h2>
          <p className="text-gray-500">You need to be logged in to access the chat</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-64px)] flex">
      {/* Sidebar */}
      {showSidebar && (
        <aside className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col transition-all duration-300">
          {/* New chat button */}
          <div className="p-4 border-b border-gray-200">
            <Button
              className="w-full justify-center"
              onClick={createNewChat}
            >
              <Plus className="w-4 h-4 mr-2" />
              New Chat
            </Button>
          </div>

          {/* Conversation list */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-2 space-y-1">
              {conversations.map((conversation) => (
                <button
                  key={conversation.conversationId}
                  type="button"
                  className={`w-full flex items-start gap-3 p-3 rounded-lg text-left transition-colors group cursor-pointer ${
                    selectedConversation?.conversationId === conversation.conversationId
                      ? 'bg-primary-100 text-primary-900'
                      : 'hover:bg-gray-100'
                  }`}
                  onClick={() => selectConversation(conversation)}
                >
                  <MessageSquare className="w-5 h-5 flex-shrink-0 mt-0.5 text-gray-500" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">
                      {conversation.title || 'New Chat'}
                    </p>
                    <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                      <Clock className="w-3 h-3" />
                      {formatRelativeTime(conversation.createdAt)}
                    </p>
                  </div>
                  <span
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-100 text-gray-400 hover:text-red-600 transition-all"
                    onClick={(e) => deleteConversation(conversation, e)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </span>
                </button>
              ))}
            </div>

            {/* Empty state */}
            {conversations.length === 0 && (
              <div className="p-6 text-center">
                <MessageSquare className="w-12 h-12 mx-auto text-gray-300 mb-3" />
                <p className="text-gray-500 text-sm">No conversations yet</p>
                <p className="text-gray-400 text-xs mt-1">Start a new chat to begin</p>
              </div>
            )}
          </div>
        </aside>
      )}

      {/* Main chat area */}
      <main className="flex-1 flex flex-col bg-white">
        <ChatWindow
          conversation={selectedConversation}
          fullScreen={true}
          onConversationCreated={handleConversationCreated}
        />
      </main>
    </div>
  )
}
