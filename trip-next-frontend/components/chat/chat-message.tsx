'use client'

import { User, Bot } from "lucide-react"
import { Message } from "@/lib/types"
import { cn, formatRelativeTime } from "@/lib/utils"

interface ChatMessageProps {
  message: Message
  isStreaming?: boolean
}

export function ChatMessage({ message, isStreaming = false }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={cn(
        'flex gap-3 animate-message-fade-in',
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
            <span className="typing-indicator inline-flex gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.32s]" />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.16s]" />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
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
