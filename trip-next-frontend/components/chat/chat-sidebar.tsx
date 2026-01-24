"use client";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/hooks/use-auth";
import { useChat } from "@/lib/hooks/use-chat";
import { useChatSidebar } from "@/lib/hooks/use-chat-sidebar";
import type { ChatContext, Conversation, Message } from "@/lib/types";
import { cn, generateId } from "@/lib/utils";
import { Send, Sparkles, X } from "lucide-react";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ChatMessage } from "./chat-message";

interface ChatSidebarProps {
  conversation?: Conversation | null;
  initialContext?: ChatContext | null;
  title?: string;
  onConversationCreated?: (conversation: Conversation) => void;
}

export function ChatSidebar({
  conversation: propConversation,
  initialContext: propInitialContext,
  title: propTitle,
  onConversationCreated,
}: ChatSidebarProps) {
  const { isOpen, context, title: storeTitle, close } = useChatSidebar();
  const auth = useAuth();
  const chat = useChat();
  const pathname = usePathname();

  // Use props if provided, otherwise use store values
  const initialContext = propInitialContext || context;
  const title = propTitle || storeTitle;

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [currentConversation, setCurrentConversation] =
    useState<Conversation | null>(propConversation || null);

  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  /**
   * Extract backend metadata fields from ChatContext.
   * Only includes fields that should be sent to trip-chat-service.
   */
  const extractBackendMetadata = (
    ctx: ChatContext | null,
  ): Record<string, unknown> | undefined => {
    if (!ctx) return undefined;

    const metadata: Record<string, unknown> = {};

    // Only include backend-relevant fields (snake_case convention)
    if (ctx.agent) metadata.agent = ctx.agent;
    if (ctx.target_id) metadata.target_id = ctx.target_id;
    if (ctx.target_type) metadata.target_type = ctx.target_type;

    return Object.keys(metadata).length > 0 ? metadata : undefined;
  };

  // Auto-close sidebar when navigating to /chat page
  useEffect(() => {
    if (pathname === "/chat" && isOpen) {
      close();
    }
  }, [pathname, isOpen, close]);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    setTimeout(() => {
      if (messagesContainerRef.current) {
        messagesContainerRef.current.scrollTop =
          messagesContainerRef.current.scrollHeight;
      }
    }, 0);
  };

  // Scroll on message changes
  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  // Initialize conversation if prop changes
  useEffect(() => {
    if (propConversation) {
      setCurrentConversation(propConversation);
      loadMessages();
    }
  }, [propConversation]);

  // When sidebar opens with initial context, create conversation
  useEffect(() => {
    if (isOpen && initialContext && !currentConversation) {
      createContextualConversation();
    }
  }, [isOpen, initialContext]);

  // Load messages for current conversation
  const loadMessages = async () => {
    if (!currentConversation || !auth.user) return;

    const result = await chat.listMessages(
      auth.user.id,
      currentConversation.conversationId,
    );

    if (result) {
      setMessages(result.items.reverse());
    }
  };

  // Create a conversation with initial context
  const createContextualConversation = async () => {
    if (!initialContext || !auth.user) return;

    // Extract only backend-relevant metadata for the conversation
    const backendMetadata = extractBackendMetadata(initialContext);

    const conversation = await chat.createConversation(
      auth.user.id,
      title,
      backendMetadata,
    );

    if (conversation) {
      setCurrentConversation(conversation);
      onConversationCreated?.(conversation);

      // Check if we need to auto-send a query
      if (initialContext.autoSendQuery) {
        await sendMessageWithMetadata(
          conversation,
          initialContext.autoSendQuery,
          backendMetadata,
        );
      }
    }
  };

  // Create a new conversation if needed
  const ensureConversation = async (): Promise<Conversation | null> => {
    if (currentConversation) return currentConversation;
    if (!auth.user) return null;

    const conversation = await chat.createConversation(
      auth.user.id,
      title || "New Chat",
    );

    if (conversation) {
      setCurrentConversation(conversation);
      onConversationCreated?.(conversation);
    }

    return conversation;
  };

  // Send message handler with optional custom metadata
  const sendMessageWithMetadata = async (
    conversation: Conversation,
    content: string,
    customMetadata?: Record<string, unknown>,
  ) => {
    if (!content.trim() || isStreaming || !auth.user) return;

    // Add user message locally
    const userMessage: Message = {
      id: generateId(),
      conversationId: conversation.conversationId,
      role: "user",
      content,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");

    // Start streaming response
    setIsStreaming(true);
    setStreamingContent("");

    // Use custom metadata if provided, otherwise extract from initialContext
    const metadata = customMetadata || extractBackendMetadata(initialContext);

    try {
      await chat.streamMessage(
        auth.user.id,
        conversation.conversationId,
        content,
        metadata,
        // onEvent: handle ADK events (tool calls, etc.)
        (event) => {
          console.log("ADK Event:", event);
        },
        // onChunk: accumulate streaming text
        (chunk) => {
          setStreamingContent((prev) => prev + chunk);
        },
        // onMessage: handle final saved message
        (message) => {
          // Replace streaming content with final message
          setStreamingContent("");
          setMessages((prev) => [...prev, message]);
        },
        // onComplete
        () => {
          console.log("Stream completed");
        },
        // onError
        (error) => {
          console.error("Stream error:", error);
          setMessages((prev) => [
            ...prev,
            {
              id: generateId(),
              conversationId: conversation.conversationId,
              role: "assistant",
              content: "Sorry, I encountered an error. Please try again.",
              createdAt: new Date().toISOString(),
            },
          ]);
        },
      );
    } catch (error) {
      console.error("Failed to send message:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          conversationId: conversation.conversationId,
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
          createdAt: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsStreaming(false);
      setStreamingContent("");
    }
  };

  // Send message handler (uses default metadata from initialContext)
  const sendMessage = async () => {
    const content = inputMessage.trim();
    if (!content || isStreaming || !auth.user) return;

    // Ensure we have a conversation
    const conversation = await ensureConversation();
    if (!conversation) return;

    // Use the sendMessageWithMetadata function
    await sendMessageWithMetadata(conversation, content);
  };

  // Handle enter key
  const handleKeydown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  // Auto-resize textarea
  const autoResize = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const target = event.target;
    target.style.height = "auto";
    target.style.height = Math.min(target.scrollHeight, 120) + "px";
  };

  // Reset state when closing
  const handleClose = () => {
    close();
  };

  // Quick prompts based on context
  const quickPrompts =
    initialContext?.type === "review-summary"
      ? [
          "Summarize the reviews",
          "What do visitors like most?",
          "Any negative feedback?",
          "Best time to visit?",
        ]
      : [
          "Tell me more",
          "How to get there?",
          "Nearby attractions",
          "Local tips",
        ];

  const handleQuickPrompt = (prompt: string) => {
    setInputMessage(prompt);
    // Send immediately
    setTimeout(() => sendMessage(), 0);
  };

  return (
    <>
      {/* Backdrop (only on mobile) */}
      <div
        className={cn(
          "fixed inset-0 z-40 bg-black/20 transition-opacity duration-200 lg:hidden",
          isOpen ? "opacity-100" : "pointer-events-none opacity-0",
        )}
        onClick={handleClose}
      />

      {/* Sidebar */}
      <div
        className={cn(
          "fixed top-16 right-0 bottom-0 z-40 flex w-full flex-col border-l border-gray-200 bg-white shadow-2xl transition-transform duration-300 ease-out sm:w-100 lg:w-105",
          isOpen ? "translate-x-0" : "translate-x-full",
        )}
      >
        {/* Header */}
        <div className="from-primary-50 to-secondary-50 flex shrink-0 items-center justify-between border-b border-gray-100 bg-linear-to-r px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="from-primary-500 to-secondary-500 flex h-9 w-9 items-center justify-center rounded-xl bg-linear-to-br">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-gray-900">{title}</h2>
              <p className="text-xs text-gray-500">AI Travel Assistant</p>
            </div>
          </div>
          <button
            className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
            onClick={handleClose}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Messages area */}
        <div
          ref={messagesContainerRef}
          className="scrollbar-hide flex-1 space-y-4 overflow-y-auto p-4"
        >
          {/* Empty state */}
          {messages.length === 0 && !isStreaming && (
            <div className="flex h-full flex-col items-center justify-center px-4 text-center">
              <div className="from-primary-100 to-secondary-100 mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-linear-to-br">
                <Sparkles className="text-primary-600 h-8 w-8" />
              </div>
              <p className="mb-4 text-sm text-gray-500">
                Ask me anything about this attraction or the reviews!
              </p>

              {/* Quick prompts */}
              <div className="flex flex-wrap justify-center gap-2">
                {quickPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    className="rounded-full bg-gray-100 px-3 py-1.5 text-xs text-gray-700 transition-colors hover:bg-gray-200"
                    onClick={() => handleQuickPrompt(prompt)}
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
                id: "streaming",
                conversationId: currentConversation?.conversationId || "",
                role: "assistant",
                content: streamingContent,
                createdAt: new Date().toISOString(),
              }}
              isStreaming={true}
            />
          )}
        </div>

        {/* Quick prompts when conversation is active */}
        {messages.length > 0 && (
          <div className="shrink-0 border-t border-gray-100 bg-gray-50 px-4 py-2">
            <div className="flex gap-2 overflow-x-auto pb-1">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt}
                  className="hover:border-primary-300 hover:bg-primary-50 shrink-0 rounded-full border border-gray-200 bg-white px-3 py-1 text-xs text-gray-600 transition-colors"
                  onClick={() => handleQuickPrompt(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input area */}
        <div className="shrink-0 border-t border-gray-100 bg-white p-4">
          <div className="flex items-end gap-3">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => {
                setInputMessage(e.target.value);
                autoResize(e);
              }}
              onKeyDown={handleKeydown}
              placeholder="Type your question..."
              className="focus:ring-primary-500 scrollbar-hide flex-1 resize-none overflow-y-auto rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm transition-all focus:border-transparent focus:ring-2 focus:outline-none"
              rows={1}
              disabled={isStreaming}
            />
            <Button
              disabled={!inputMessage.trim() || isStreaming}
              loading={isStreaming}
              className="h-11.5 w-11.5 shrink-0 p-0!"
              onClick={sendMessage}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}
