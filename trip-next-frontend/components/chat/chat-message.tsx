"use client";

import { Message } from "@/lib/types";
import { cn, formatRelativeTime } from "@/lib/utils";
import { Bot, User } from "lucide-react";
import Markdown from "react-markdown";

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
    <div className={cn("flex gap-3", isUser ? "flex-row-reverse" : "")}>
      {/* Avatar */}
      <div
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl",
          isUser
            ? "bg-primary-600"
            : "from-secondary-500 to-accent-500 bg-linear-to-br",
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
        <div className="text-sm leading-relaxed">
          {isUser ? (
            <span className="whitespace-pre-wrap">{message.content}</span>
          ) : (
            <Markdown
              components={{
                p: ({ children }) => (
                  <p className="mb-2 last:mb-0">{children}</p>
                ),
                h1: ({ children }) => (
                  <h1 className="mb-2 text-lg font-bold">{children}</h1>
                ),
                h2: ({ children }) => (
                  <h2 className="mb-2 text-base font-bold">{children}</h2>
                ),
                h3: ({ children }) => (
                  <h3 className="mb-2 text-sm font-bold">{children}</h3>
                ),
                ul: ({ children }) => (
                  <ul className="mb-2 ml-4 list-disc space-y-1 last:mb-0">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="mb-2 ml-4 list-decimal space-y-1 last:mb-0">
                    {children}
                  </ol>
                ),
                li: ({ children }) => <li className="pl-1">{children}</li>,
                code: ({ className, children }) => {
                  const isInline = !className;
                  if (isInline) {
                    return (
                      <code className="rounded bg-gray-200 px-1.5 py-0.5 font-mono text-xs text-gray-800">
                        {children}
                      </code>
                    );
                  }
                  return (
                    <code className="block overflow-x-auto rounded-lg bg-gray-800 p-3 font-mono text-xs text-gray-100">
                      {children}
                    </code>
                  );
                },
                pre: ({ children }) => (
                  <pre className="my-2 overflow-hidden rounded-lg last:mb-0">
                    {children}
                  </pre>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="my-2 border-l-4 border-gray-300 pl-3 text-gray-600 italic last:mb-0">
                    {children}
                  </blockquote>
                ),
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-600 hover:text-primary-700 underline"
                  >
                    {children}
                  </a>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold">{children}</strong>
                ),
                em: ({ children }) => <em className="italic">{children}</em>,
                hr: () => <hr className="my-3 border-gray-300" />,
              }}
            >
              {message.content}
            </Markdown>
          )}
          {/* Typing indicator for streaming */}
          {isStreaming && !message.content && (
            <span className="typing-indicator inline-flex gap-1">
              <span className="h-2 w-2 rounded-full bg-gray-400" />
              <span className="h-2 w-2 rounded-full bg-gray-400" />
              <span className="h-2 w-2 rounded-full bg-gray-400" />
            </span>
          )}
          {isStreaming && message.content && (
            <span className="ml-0.5 inline-block h-4 w-2 bg-current" />
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
