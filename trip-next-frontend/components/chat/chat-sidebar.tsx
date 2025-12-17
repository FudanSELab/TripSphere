'use client'

import { useState, useRef, useEffect } from 'react'
import { X, Send, Sparkles } from 'lucide-react'
import { ChatMessage } from './chat-message'
import { Button } from '@/components/ui/button'
import { useChatSidebar } from '@/lib/hooks/use-chat-sidebar'
import { useAuth } from '@/lib/hooks/use-auth'
import { useChat } from '@/lib/hooks/use-chat'
import type { Message, Conversation, ChatContext } from '@/lib/types'
import { cn, generateId } from '@/lib/utils'

interface ChatSidebarProps {
  conversation?: Conversation | null
  initialContext?: ChatContext | null
  title?: string
  onConversationCreated?: (conversation: Conversation) => void
}

export function ChatSidebar({
  conversation: propConversation,
  initialContext: propInitialContext,
  title: propTitle,
  onConversationCreated,
}: ChatSidebarProps) {
  const { isOpen, context, title: storeTitle, close } = useChatSidebar()
  const auth = useAuth()
  const chat = useChat()

  // Use props if provided, otherwise use store values
  const initialContext = propInitialContext || context
  const title = propTitle || storeTitle

  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(
    propConversation || null
  )

  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    setTimeout(() => {
      if (messagesContainerRef.current) {
        messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
      }
    }, 0)
  }

  // Scroll on message changes
  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent])

  // Initialize conversation if prop changes
  useEffect(() => {
    if (propConversation) {
      setCurrentConversation(propConversation)
      loadMessages()
    }
  }, [propConversation])

  // When sidebar opens with initial context, create conversation
  useEffect(() => {
    if (isOpen && initialContext && !currentConversation) {
      createContextualConversation()
    }
  }, [isOpen, initialContext])

  // Load messages for current conversation
  const loadMessages = async () => {
    if (!currentConversation || !auth.user) return

    const result = await chat.listMessages(auth.user.id, currentConversation.conversationId)

    if (result) {
      setMessages(result.items.reverse())
    }
  }

  // Create a conversation with initial context
  const createContextualConversation = async () => {
    if (!initialContext || !auth.user) return

    const conversation = await chat.createConversation(
      auth.user.id,
      title,
      initialContext as Record<string, unknown>
    )

    if (conversation) {
      setCurrentConversation(conversation)
      onConversationCreated?.(conversation)

      // Check if we need to auto-send a query
      if (initialContext.autoSendQuery) {
        // Use autoSendMetadata if provided
        const metadata = initialContext.autoSendMetadata || initialContext
        await sendMessageWithMetadata(conversation, initialContext.autoSendQuery, metadata)
      }
    }
  }

  // Get initial message based on context type
  const getInitialMessage = (): string => {
    if (!initialContext) return ''

    switch (initialContext.type) {
      case 'review-summary':
        return `Hi! I'm here to help you understand the reviews for **${initialContext.attractionName}**. I can summarize what visitors are saying, highlight common themes, or answer specific questions about the reviews. What would you like to know?`
      case 'attraction':
        return `Hello! I'd be happy to tell you more about **${initialContext.attractionName}**. Feel free to ask me anything about this attraction - opening hours, best times to visit, nearby restaurants, or travel tips!`
      default:
        return 'Hello! How can I help you today?'
    }
  }

  // Create a new conversation if needed
  const ensureConversation = async (): Promise<Conversation | null> => {
    if (currentConversation) return currentConversation
    if (!auth.user) return null

    const conversation = await chat.createConversation(
      auth.user.id,
      title || 'New Chat'
    )

    if (conversation) {
      setCurrentConversation(conversation)
      onConversationCreated?.(conversation)
    }

    return conversation
  }

  // Send message handler with optional custom metadata
  const sendMessageWithMetadata = async (
    conversation: Conversation,
    content: string,
    customMetadata?: Record<string, unknown>
  ) => {
    if (!content.trim() || isStreaming || !auth.user) return

    // Add user message locally
    const userMessage: Message = {
      id: generateId(),
      conversationId: conversation.conversationId,
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])
    setInputMessage('')

    // Start streaming response
    setIsStreaming(true)
    setStreamingContent('')

    // Use custom metadata if provided, otherwise use initialContext
    const metadata = customMetadata || (initialContext as Record<string, unknown> | undefined)

    try {
      await chat.streamMessage(
        auth.user.id,
        conversation.conversationId,
        content,
        metadata,
        // onEvent: handle ADK events (tool calls, etc.)
        (event) => {
          console.log('ADK Event:', event)
        },
        // onChunk: accumulate streaming text
        (chunk) => {
          setStreamingContent((prev) => prev + chunk)
        },
        // onMessage: handle final saved message
        (message) => {
          // Replace streaming content with final message
          setStreamingContent('')
          setMessages((prev) => [...prev, message])
        },
        // onComplete
        () => {
          console.log('Stream completed')
        },
        // onError
        (error) => {
          console.error('Stream error:', error)
          setMessages((prev) => [
            ...prev,
            {
              id: generateId(),
              conversationId: conversation.conversationId,
              role: 'assistant',
              content: 'Sorry, I encountered an error. Please try again.',
              createdAt: new Date().toISOString(),
            },
          ])
        }
      )
    } catch (error) {
      console.error('Failed to send message:', error)
      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          conversationId: conversation.conversationId,
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          createdAt: new Date().toISOString(),
        },
      ])
    } finally {
      setIsStreaming(false)
      setStreamingContent('')
    }
  }

  // Send message handler (uses default metadata from initialContext)
  const sendMessage = async () => {
    const content = inputMessage.trim()
    if (!content || isStreaming || !auth.user) return

    // Ensure we have a conversation
    const conversation = await ensureConversation()
    if (!conversation) return

    // Use the sendMessageWithMetadata function
    await sendMessageWithMetadata(conversation, content)
  }

  // Handle enter key
  const handleKeydown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  }

  // Auto-resize textarea
  const autoResize = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const target = event.target
    target.style.height = 'auto'
    target.style.height = Math.min(target.scrollHeight, 120) + 'px'
  }

  // Reset state when closing
  const handleClose = () => {
    close()
  }

  // Quick prompts based on context
  const quickPrompts =
    initialContext?.type === 'review-summary'
      ? [
          'Summarize the reviews',
          'What do visitors like most?',
          'Any negative feedback?',
          'Best time to visit?',
        ]
      : ['Tell me more', 'How to get there?', 'Nearby attractions', 'Local tips']

  const useQuickPrompt = (prompt: string) => {
    setInputMessage(prompt)
    // Send immediately
    setTimeout(() => sendMessage(), 0)
  }

  return (
    <>
      {/* Backdrop (only on mobile) */}
      <div
        className={cn(
          'fixed inset-0 bg-black/20 z-40 lg:hidden transition-opacity duration-200',
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        onClick={handleClose}
      />

      {/* Sidebar */}
      <div
        className={cn(
          'fixed right-0 top-16 bottom-0 w-full sm:w-[400px] lg:w-[420px] bg-white shadow-2xl z-40 flex flex-col border-l border-gray-200 transition-transform duration-300 ease-out',
          isOpen ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {/* Header */}
        <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gradient-to-r from-primary-50 to-secondary-50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900 text-sm">{title}</h2>
              <p className="text-xs text-gray-500">AI Travel Assistant</p>
            </div>
          </div>
          <button
            className="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center text-gray-500 hover:text-gray-700 transition-colors"
            onClick={handleClose}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Messages area */}
        <div
          ref={messagesContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-4"
        >
          {/* Empty state */}
          {messages.length === 0 && !isStreaming && (
            <div className="h-full flex flex-col items-center justify-center text-center px-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-100 to-secondary-100 flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8 text-primary-600" />
              </div>
              <p className="text-sm text-gray-500 mb-4">
                Ask me anything about this attraction or the reviews!
              </p>

              {/* Quick prompts */}
              <div className="flex flex-wrap gap-2 justify-center">
                {quickPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    className="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
                    onClick={() => useQuickPrompt(prompt)}
                  >
                    {prompt}
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

        {/* Quick prompts when conversation is active */}
        {messages.length > 0 && (
          <div className="flex-shrink-0 px-4 py-2 border-t border-gray-100 bg-gray-50">
            <div className="flex gap-2 overflow-x-auto pb-1">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt}
                  className="flex-shrink-0 px-3 py-1 text-xs bg-white border border-gray-200 hover:border-primary-300 hover:bg-primary-50 rounded-full text-gray-600 transition-colors"
                  onClick={() => useQuickPrompt(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input area */}
        <div className="flex-shrink-0 p-4 border-t border-gray-100 bg-white">
          <div className="flex items-end gap-3">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => {
                setInputMessage(e.target.value)
                autoResize(e)
              }}
              onKeyDown={handleKeydown}
              placeholder="Type your question..."
              className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl resize-none text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all scrollbar-hide overflow-y-auto"
              rows={1}
              disabled={isStreaming}
            />
            <Button
              disabled={!inputMessage.trim() || isStreaming}
              loading={isStreaming}
              className="flex-shrink-0 h-[46px] w-[46px] !p-0"
              onClick={sendMessage}
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </>
  )
}
