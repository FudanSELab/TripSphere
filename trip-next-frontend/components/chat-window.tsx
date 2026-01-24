"use client";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { useChat } from "@/hooks/use-chat";
import { Conversation, Message } from "@/lib/types";
import { Send, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { v7 as uuidv7 } from "uuid";
import { ChatMessage } from "./chat-message";

interface ChatWindowProps {
  conversation?: Conversation | null;
  fullScreen?: boolean;
  onConversationCreated?: (conversation: Conversation) => void;
}

// Suggested prompts for new conversations
const suggestedPrompts = [
  { text: "Plan a weekend trip to Shanghai", icon: "🏙️" },
  { text: "Find hotels near the Bund", icon: "🏨" },
  { text: "What are the must-see attractions in Beijing?", icon: "🏛️" },
  { text: "Create a 3-day itinerary for Hangzhou", icon: "📋" },
];

export function ChatWindow({
  conversation,
  fullScreen = false,
  onConversationCreated,
}: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [currentConversation, setCurrentConversation] =
    useState<Conversation | null>(conversation || null);

  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const chat = useChat();
  const { user } = useAuth();

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop =
        messagesContainerRef.current.scrollHeight;
    }
  };

  // Scroll on messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  // Initialize conversation if prop changes
  useEffect(() => {
    // Only load messages if conversation actually changed
    if (conversation?.conversationId !== currentConversation?.conversationId) {
      if (conversation) {
        setCurrentConversation(conversation);
        loadMessages(conversation);
      } else {
        // Clear messages when conversation is set to null (new chat)
        setCurrentConversation(null);
        setMessages([]);
      }
    }
  }, [conversation]);

  // Load messages for current conversation
  const loadMessages = async (conv?: Conversation) => {
    const targetConversation = conv || currentConversation;
    if (!targetConversation?.conversationId || !user) {
      setMessages([]);
      return;
    }

    const result = await chat.listMessages(
      user.id,
      targetConversation.conversationId,
    );

    if (result) {
      setMessages(result.items.reverse());
    }
  };

  // Create a new conversation if needed
  const ensureConversation = async (): Promise<Conversation | null> => {
    if (currentConversation) return currentConversation;
    if (!user) return null;

    const newConversation = await chat.createConversation(user.id, "New Chat");

    if (newConversation) {
      setCurrentConversation(newConversation);
      onConversationCreated?.(newConversation);
    }

    return newConversation;
  };

  // Send message handler
  const sendMessage = async () => {
    const content = inputMessage.trim();
    if (!content || isStreaming || !user) return;

    // Ensure we have a conversation
    const conv = await ensureConversation();
    if (!conv) return;

    // Add user message locally
    const userMessage: Message = {
      id: uuidv7(),
      conversationId: conv.conversationId,
      role: "user",
      content,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");

    // Start streaming response
    setIsStreaming(true);
    setStreamingContent("");

    try {
      await chat.streamMessage(
        user.id,
        conv.conversationId,
        content,
        undefined,
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
              id: uuidv7(),
              conversationId: conv.conversationId,
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
          id: uuidv7(),
          conversationId: conv.conversationId,
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

  // Handle enter key
  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  // Auto-resize textarea
  const autoResize = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const target = event.target;
    target.style.height = "auto";
    target.style.height = Math.min(target.scrollHeight, 200) + "px";
  };

  // Use suggested prompt
  const handleSuggestedPrompt = (prompt: string) => {
    setInputMessage(prompt);
    inputRef.current?.focus();
  };

  return (
    <div
      className={
        fullScreen
          ? "bg-background flex h-full flex-col"
          : "border-border bg-background flex h-150 flex-col rounded-2xl border shadow-lg"
      }
    >
      {/* Messages area */}
      <div
        ref={messagesContainerRef}
        className="flex-1 space-y-4 overflow-y-auto p-6"
      >
        {/* Empty state with suggestions */}
        {messages.length === 0 && !isStreaming && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="bg-primary/10 mb-6 flex h-20 w-20 items-center justify-center rounded-2xl">
              <Sparkles className="text-primary h-10 w-10" />
            </div>
            <h3 className="text-foreground mb-2 text-xl font-semibold">
              Welcome to TripSphere AI!
            </h3>
            <p className="text-muted-foreground mb-8 max-w-md">
              I&apos;m your intelligent travel assistant. Ask me anything about
              destinations, hotels, attractions, or let me help you plan your
              perfect trip.
            </p>

            {/* Suggested prompts */}
            <div className="grid max-w-lg grid-cols-1 gap-3 sm:grid-cols-2">
              {suggestedPrompts.map((prompt) => (
                <button
                  key={prompt.text}
                  className="bg-muted hover:bg-muted/80 flex items-center gap-3 rounded-xl px-4 py-3 text-left transition-colors"
                  onClick={() => handleSuggestedPrompt(prompt.text)}
                >
                  <span className="text-xl">{prompt.icon}</span>
                  <span className="text-foreground text-sm">{prompt.text}</span>
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

      {/* Input area */}
      <div className="border-border shrink-0 border-t p-4">
        <div className="flex items-end gap-3">
          <textarea
            ref={inputRef}
            value={inputMessage}
            onChange={(e) => {
              setInputMessage(e.target.value);
              autoResize(e);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything about travel..."
            className="scrollbar-hide border-input bg-muted focus:ring-ring flex-1 resize-none overflow-y-auto rounded-xl border px-4 py-3 transition-all focus:border-transparent focus:ring-2 focus:outline-none"
            rows={1}
            disabled={isStreaming}
          />
          <Button
            disabled={!inputMessage.trim() || isStreaming}
            size="sm"
            className="h-12 w-12 shrink-0 p-0!"
            onClick={sendMessage}
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
        <p className="text-muted-foreground mt-2 text-center text-xs">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
