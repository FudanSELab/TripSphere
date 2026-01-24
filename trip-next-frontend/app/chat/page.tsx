"use client";

import { ChatWindow } from "@/components/chat/chat-window";
import { Button } from "@/components/ui/button";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
} from "@/components/ui/sidebar";
import { useAuth } from "@/hooks/use-auth";
import { useChat } from "@/hooks/use-chat";
import type { Conversation } from "@/lib/types";
import { Clock, MessageSquare, Plus, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export default function ChatPage() {
  const auth = useAuth();
  const chat = useChat();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] =
    useState<Conversation | null>(null);
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
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <MessageSquare className="text-muted-foreground mx-auto mb-4 h-16 w-16" />
          <h2 className="text-foreground mb-2 text-xl font-semibold">
            Please log in
          </h2>
          <p className="text-muted-foreground">
            You need to be logged in to access the chat
          </p>
        </div>
      </div>
    );
  }

  return (
    <SidebarProvider>
      <Sidebar>
        <SidebarHeader className="border-sidebar-border border-b p-4">
          <Button className="w-full justify-center" onClick={createNewChat}>
            <Plus className="mr-2 h-4 w-4" />
            New Chat
          </Button>
        </SidebarHeader>

        <SidebarContent>
          {conversations.length > 0 ? (
            <SidebarMenu className="p-2">
              {conversations.map((conversation) => (
                <SidebarMenuItem key={conversation.conversationId}>
                  <SidebarMenuButton
                    isActive={
                      selectedConversation?.conversationId ===
                      conversation.conversationId
                    }
                    onClick={() => selectConversation(conversation)}
                    className="h-auto py-3"
                  >
                    <MessageSquare className="h-5 w-5 shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">
                        {conversation.title || "New Chat"}
                      </p>
                      <p className="mt-1 flex items-center gap-1 text-xs opacity-70">
                        <Clock className="h-3 w-3" />
                        {conversation.createdAt}
                      </p>
                    </div>
                  </SidebarMenuButton>
                  <SidebarMenuAction
                    onClick={(e) => deleteConversation(conversation, e)}
                    className="text-sidebar-foreground/50 hover:bg-destructive/10 hover:text-destructive"
                    showOnHover
                  >
                    <Trash2 className="h-4 w-4" />
                  </SidebarMenuAction>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center p-6 text-center">
              <MessageSquare className="text-sidebar-foreground/30 mb-3 h-12 w-12" />
              <p className="text-sidebar-foreground/70 text-sm">
                No conversations yet
              </p>
              <p className="text-sidebar-foreground/50 mt-1 text-xs">
                Start a new chat to begin
              </p>
            </div>
          )}
        </SidebarContent>
      </Sidebar>

      <SidebarInset>
        <ChatWindow
          conversation={selectedConversation}
          fullScreen={true}
          onConversationCreated={handleConversationCreated}
        />
      </SidebarInset>
    </SidebarProvider>
  );
}
