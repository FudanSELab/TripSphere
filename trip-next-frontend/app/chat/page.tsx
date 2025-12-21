"use client";

import { ChatWindow } from "@/components/chat/chat-window";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/hooks/use-auth";
import { useChat } from "@/lib/hooks/use-chat";
import type { Conversation } from "@/lib/types";
import { formatRelativeTime } from "@/lib/utils";
import { Clock, MessageSquare, Plus, Trash2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

export default function ChatPage() {
  const auth = useAuth();
  const chat = useChat();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] =
    useState<Conversation | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const hasLoadedRef = useRef(false);

  // Load conversations on mount
  useEffect(() => {
    if (auth.user && !hasLoadedRef.current) {
      hasLoadedRef.current = true;

      const loadData = async () => {
        if (!auth.user) return;
        const result = await chat.listConversations(auth.user.id);
        if (result) {
          setConversations(result.items);
        }
      };

      void loadData();
    }
  }, [auth.user, chat]);

  const loadConversations = useCallback(async () => {
    if (!auth.user) return;

    const result = await chat.listConversations(auth.user.id);
    if (result) {
      setConversations(result.items);
    }
  }, [auth.user, chat]);

  const createNewChat = () => {
    setSelectedConversation(null);
  };

  const selectConversation = (conversation: Conversation) => {
    setSelectedConversation(conversation);
  };

  const handleConversationCreated = (conversation: Conversation) => {
    setConversations([conversation, ...conversations]);
    setSelectedConversation(conversation);
  };

  const deleteConversation = async (
    conversation: Conversation,
    e: React.MouseEvent,
  ) => {
    e.stopPropagation();
    if (!auth.user) return;

    const success = await chat.deleteConversation(
      auth.user.id,
      conversation.conversationId,
    );
    if (success) {
      const updatedConversations = conversations.filter(
        (c) => c.conversationId !== conversation.conversationId,
      );
      setConversations(updatedConversations);
      if (
        selectedConversation?.conversationId === conversation.conversationId
      ) {
        // Clear the selected conversation to show the initial state
        setSelectedConversation(null);
      }
    }
  };

  if (!auth.user) {
    return (
      <div className="flex h-[calc(100vh-64px)] items-center justify-center">
        <div className="text-center">
          <MessageSquare className="mx-auto mb-4 h-16 w-16 text-gray-400" />
          <h2 className="mb-2 text-xl font-semibold text-gray-900">
            Please log in
          </h2>
          <p className="text-gray-500">
            You need to be logged in to access the chat
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-64px)]">
      {/* Sidebar */}
      {showSidebar && (
        <aside className="flex w-80 flex-col border-r border-gray-200 bg-gray-50 transition-all duration-300">
          {/* New chat button */}
          <div className="border-b border-gray-200 p-4">
            <Button className="w-full justify-center" onClick={createNewChat}>
              <Plus className="mr-2 h-4 w-4" />
              New Chat
            </Button>
          </div>

          {/* Conversation list */}
          <div className="flex-1 overflow-y-auto">
            <div className="space-y-1 p-2">
              {conversations.map((conversation) => (
                <button
                  key={conversation.conversationId}
                  type="button"
                  className={`group flex w-full cursor-pointer items-start gap-3 rounded-lg p-3 text-left transition-colors ${
                    selectedConversation?.conversationId ===
                    conversation.conversationId
                      ? "bg-primary-100 text-primary-900"
                      : "hover:bg-gray-100"
                  }`}
                  onClick={() => selectConversation(conversation)}
                >
                  <MessageSquare className="mt-0.5 h-5 w-5 shrink-0 text-gray-500" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">
                      {conversation.title || "New Chat"}
                    </p>
                    <p className="mt-1 flex items-center gap-1 text-xs text-gray-500">
                      <Clock className="h-3 w-3" />
                      {formatRelativeTime(conversation.createdAt)}
                    </p>
                  </div>
                  <span
                    className="rounded-lg p-1.5 text-gray-400 opacity-0 transition-all group-hover:opacity-100 hover:bg-red-100 hover:text-red-600"
                    onClick={(e) => deleteConversation(conversation, e)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </span>
                </button>
              ))}
            </div>

            {/* Empty state */}
            {conversations.length === 0 && (
              <div className="p-6 text-center">
                <MessageSquare className="mx-auto mb-3 h-12 w-12 text-gray-300" />
                <p className="text-sm text-gray-500">No conversations yet</p>
                <p className="mt-1 text-xs text-gray-400">
                  Start a new chat to begin
                </p>
              </div>
            )}
          </div>
        </aside>
      )}

      {/* Main chat area */}
      <main className="flex flex-1 flex-col bg-white">
        <ChatWindow
          conversation={selectedConversation}
          fullScreen={true}
          onConversationCreated={handleConversationCreated}
        />
      </main>
    </div>
  );
}
