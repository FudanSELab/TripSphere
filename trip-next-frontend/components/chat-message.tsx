"use client";

import { Message } from "@/lib/types";
import { cn } from "@/lib/utils";
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
          isUser ? "bg-primary" : "bg-secondary",
        )}
      >
        {isUser ? (
          <User className="text-primary-foreground h-5 w-5" />
        ) : (
          <Bot className="text-secondary-foreground h-5 w-5" />
        )}
      </div>

      {/* Message content */}
      <div
        className={cn(
          "max-w-[75%] rounded-2xl px-4 py-3",
          isUser
            ? "bg-primary text-primary-foreground rounded-tr-none"
            : "bg-muted text-foreground rounded-tl-none",
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
                      <code className="bg-muted-foreground/20 rounded px-1.5 py-0.5 font-mono text-xs">
                        {children}
                      </code>
                    );
                  }
                  return (
                    <code className="bg-card text-card-foreground block overflow-x-auto rounded-lg p-3 font-mono text-xs">
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
                  <blockquote className="border-border text-muted-foreground my-2 border-l-4 pl-3 italic last:mb-0">
                    {children}
                  </blockquote>
                ),
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:text-primary/80 underline"
                  >
                    {children}
                  </a>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold">{children}</strong>
                ),
                em: ({ children }) => <em className="italic">{children}</em>,
                hr: () => <hr className="border-border my-3" />,
              }}
            >
              {message.content}
            </Markdown>
          )}
          {/* Typing indicator for streaming */}
          {isStreaming && !message.content && (
            <span className="typing-indicator inline-flex gap-1">
              <span className="bg-muted-foreground h-2 w-2 rounded-full" />
              <span className="bg-muted-foreground h-2 w-2 rounded-full" />
              <span className="bg-muted-foreground h-2 w-2 rounded-full" />
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
            isUser ? "text-primary-foreground/60" : "text-muted-foreground",
          )}
        >
          {message.createdAt}
        </div>
      </div>
    </div>
  );
}
