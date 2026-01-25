"use client";

import { ChatWindow } from "@/components/chat-window";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
} from "@/components/ui/sidebar";
import { useAuth } from "@/hooks/use-auth";
import { useChat } from "@/hooks/use-chat";
import type { Conversation } from "@/lib/types";
import { MessageSquare, MoreHorizontal, Plus, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

// Header height is h-16 = 4rem = 64px
const HEADER_HEIGHT = "4rem";

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

  const deleteConversation = async (conversation: Conversation) => {
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
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
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
    <SidebarProvider
      style={
        {
          "--header-height": HEADER_HEIGHT,
        } as React.CSSProperties
      }
      className="min-h-[calc(100vh-var(--header-height))]!"
    >
      <Sidebar className="top-(--header-height)! h-[calc(100vh-var(--header-height))]!">
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
                  >
                    <p className="truncate">
                      {conversation.title || "New Chat"}
                    </p>
                  </SidebarMenuButton>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <SidebarMenuAction showOnHover>
                        <MoreHorizontal />
                      </SidebarMenuAction>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent side="right" align="start">
                      <DropdownMenuItem
                        variant="destructive"
                        onClick={() => deleteConversation(conversation)}
                      >
                        <Trash2 />
                        <span>Delete</span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
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

      <main className="flex h-[calc(100vh-var(--header-height))] flex-1 flex-col overflow-hidden">
        <ChatWindow
          conversation={selectedConversation}
          fullScreen={true}
          onConversationCreated={handleConversationCreated}
        />
      </main>
    </SidebarProvider>
  );
}
