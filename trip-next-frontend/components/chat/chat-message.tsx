"use client";

import { Message } from "@/lib/types";
import { cn, formatRelativeTime } from "@/lib/utils";
import { Bot, User } from "lucide-react";

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
}

export function ChatMessage({
  message,
  isStreaming = false,
}: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "animate-message-fade-in flex gap-3",
        isUser ? "flex-row-reverse" : "",
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl",
          isUser
            ? "bg-primary-600"
            : "from-secondary-500 to-accent-500 bg-gradient-to-br",
        )}
      >
        {isUser ? (
          <User className="h-5 w-5 text-white" />
        ) : (
          <Bot className="h-5 w-5 text-white" />
        )}
      </div>

      {/* Message content */}
      <div
        className={cn(
          "max-w-[75%] rounded-2xl px-4 py-3",
          isUser
            ? "bg-primary-600 rounded-tr-none text-white"
            : "rounded-tl-none bg-gray-100 text-gray-900",
        )}
      >
        {/* Message text */}
        <div className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
          {/* Typing indicator for streaming */}
          {isStreaming && !message.content && (
            <span className="typing-indicator inline-flex gap-1">
              <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.32s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.16s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400" />
            </span>
          )}
          {isStreaming && message.content && (
            <span className="ml-0.5 inline-block h-4 w-2 animate-pulse bg-current" />
          )}
        </div>

        {/* Timestamp */}
        <div
          className={cn(
            "mt-1 text-xs",
            isUser ? "text-primary-200" : "text-gray-400",
          )}
        >
          {formatRelativeTime(message.createdAt)}
        </div>
      </div>
    </div>
  );
}
