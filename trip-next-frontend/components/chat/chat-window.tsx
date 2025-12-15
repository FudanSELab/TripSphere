'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles } from 'lucide-react'
import { Message, Conversation } from '@/types/chat'
import { ChatMessage } from './chat-message'

interface ChatWindowProps {
  conversation?: Conversation | null
  fullScreen?: boolean
  onConversationCreated?: (conversation: Conversation) => void
}

// Generate a simple ID
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

// Suggested prompts for new conversations
const suggestedPrompts = [
  { text: 'Plan a weekend trip to Shanghai', icon: '🏙️' },
  { text: 'Find hotels near the Bund', icon: '🏨' },
  { text: 'What are the must-see attractions in Beijing?', icon: '🏛️' },
  { text: 'Create a 3-day itinerary for Hangzhou', icon: '📋' },
]

export function ChatWindow({ 
  conversation, 
  fullScreen = false,
  onConversationCreated 
}: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(
    conversation || null
  )
  
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
    }
  }

  // Scroll on messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent])

  // Update conversation when prop changes
  useEffect(() => {
    if (conversation) {
      setCurrentConversation(conversation)
      // Load messages for this conversation
      // TODO: Implement loadMessages()
    }
  }, [conversation])

  // Create a new conversation if needed
  const ensureConversation = async (): Promise<Conversation | null> => {
    if (currentConversation) return currentConversation

    // TODO: Implement API call to create conversation
    // For now, create a mock conversation
    const newConversation: Conversation = {
      conversationId: generateId(),
      userId: 'mock-user-id',
      title: 'New Chat',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }

    setCurrentConversation(newConversation)
    onConversationCreated?.(newConversation)

    return newConversation
  }

  // Send message handler
  const sendMessage = async () => {
    const content = inputMessage.trim()
    if (!content || isStreaming) return

    // Ensure we have a conversation
    const conv = await ensureConversation()
    if (!conv) return

    // Add user message locally
    const userMessage: Message = {
      id: generateId(),
      conversationId: conv.conversationId,
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])
    setInputMessage('')

    // Reset textarea height
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
    }

    // Start streaming response
    setIsStreaming(true)
    setStreamingContent('')

    try {
      // TODO: Implement actual API call
      // For now, simulate a response
      await new Promise((resolve) => setTimeout(resolve, 1000))

      const assistantMessage: Message = {
        id: generateId(),
        conversationId: conv.conversationId,
        role: 'assistant',
        content:
          "I'm your AI travel assistant! I can help you discover amazing attractions, find the perfect hotels, plan your itinerary, and much more. What would you like to explore today?",
        createdAt: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('Failed to send message:', error)
      // Add error message
      const errorMessage: Message = {
        id: generateId(),
        conversationId: conv.conversationId,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        createdAt: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsStreaming(false)
      setStreamingContent('')
    }
  }

  // Handle enter key
  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  }

  // Auto-resize textarea
  const handleInput = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const target = event.target
    target.style.height = 'auto'
    target.style.height = Math.min(target.scrollHeight, 200) + 'px'
    setInputMessage(target.value)
  }

  // Use suggested prompt
  const useSuggestedPrompt = (prompt: string) => {
    setInputMessage(prompt)
    inputRef.current?.focus()
  }

  return (
    <div
      className={`flex flex-col bg-white ${
        fullScreen ? 'h-screen' : 'h-[600px] rounded-2xl shadow-lg border border-gray-100'
      }`}
    >
      {/* Header */}
      <div className="flex-shrink-0 flex items-center gap-3 px-6 py-4 border-b border-gray-100">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="font-semibold text-gray-900">AI Travel Assistant</h2>
          <p className="text-sm text-gray-500">Powered by TripSphere</p>
        </div>
      </div>

      {/* Messages area */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-6 space-y-4"
      >
        {/* Empty state with suggestions */}
        {messages.length === 0 && !isStreaming && (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-100 to-secondary-100 flex items-center justify-center mb-6 animate-float">
              <Sparkles className="w-10 h-10 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Welcome to TripSphere AI!
            </h3>
            <p className="text-gray-500 mb-8 max-w-md">
              I&apos;m your intelligent travel assistant. Ask me anything about
              destinations, hotels, attractions, or let me help you plan your perfect
              trip.
            </p>

            {/* Suggested prompts */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg">
              {suggestedPrompts.map((prompt) => (
                <button
                  key={prompt.text}
                  className="flex items-center gap-3 px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-xl text-left transition-colors"
                  onClick={() => useSuggestedPrompt(prompt.text)}
                >
                  <span className="text-xl">{prompt.icon}</span>
                  <span className="text-sm text-gray-700">{prompt.text}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message list */}
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {/* Streaming message */}
        {isStreaming && (
          <ChatMessage
            message={{
              id: 'streaming',
              conversationId: currentConversation?.conversationId || '',
              role: 'assistant',
              content: streamingContent,
              createdAt: new Date().toISOString(),
            }}
            isStreaming={true}
          />
        )}
      </div>

      {/* Input area */}
      <div className="flex-shrink-0 p-4 border-t border-gray-100">
        <div className="flex items-start gap-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything about travel..."
              className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all min-h-[48px] [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
              rows={1}
              disabled={isStreaming}
            />
          </div>
          <button
            disabled={!inputMessage.trim() || isStreaming}
            className="flex-shrink-0 h-[48px] w-[48px] bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-xl flex items-center justify-center transition-colors"
            onClick={sendMessage}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2 text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
