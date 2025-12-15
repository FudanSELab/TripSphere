'use client'

import { User, Bot } from "lucide-react"
import { Message } from "@/types/chat"
import { cn } from "@/lib/utils"

interface ChatMessageProps {
  message: Message
  isStreaming?: boolean
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (diffInSeconds < 60) return 'Just now'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
  return `${Math.floor(diffInSeconds / 86400)}d ago`
}

export function ChatMessage({ message, isStreaming = false }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={cn(
        'flex gap-3 animate-fade-in-up',
        isUser ? 'flex-row-reverse' : ''
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center',
          isUser
            ? 'bg-primary-600'
            : 'bg-gradient-to-br from-secondary-500 to-accent-500'
        )}
      >
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-white" />
        )}
      </div>

      {/* Message content */}
      <div
        className={cn(
          'max-w-[75%] rounded-2xl px-4 py-3',
          isUser
            ? 'bg-primary-600 text-white rounded-tr-none'
            : 'bg-gray-100 text-gray-900 rounded-tl-none'
        )}
      >
        {/* Message text */}
        <div className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
          {/* Typing indicator for streaming */}
          {isStreaming && !message.content && (
            <span className="typing-indicator inline-flex">
              <span className="animate-typing"></span>
              <span className="animate-typing [animation-delay:-0.16s]"></span>
              <span className="animate-typing [animation-delay:-0.32s]"></span>
            </span>
          )}
          {isStreaming && message.content && (
            <span className="inline-block w-2 h-4 ml-0.5 bg-current animate-pulse" />
          )}
        </div>

        {/* Timestamp */}
        <div
          className={cn(
            'text-xs mt-1',
            isUser ? 'text-primary-200' : 'text-gray-400'
          )}
        >
          {formatRelativeTime(message.createdAt)}
        </div>
      </div>
    </div>
  )
}
