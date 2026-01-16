"use client";

import type {
  Conversation,
  Message,
  PaginatedResponse,
  Part,
  SendMessageRequest,
} from "@/lib/types";
import { useState } from "react";

export const useChat = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const baseUrl =
    process.env.NEXT_PUBLIC_CHAT_SERVICE_URL || "http://localhost:24210";

  /**
   * Helper function to convert text content to Part array
   */
  const textToParts = (text: string): Part[] => {
    return [
      {
        text,
        kind: "text" as const,
      },
    ];
  };

  /**
   * Helper function to extract text from Part array
   */
  const partsToText = (parts: Part[]): string => {
    return parts
      .filter(
        (part): part is { text: string; kind: "text" } => part.kind === "text",
      )
      .map((part) => part.text)
      .join("\n\n");
  };

  /**
   * Backend message format from API
   */
  interface BackendMessage {
    message_id: string;
    conversation_id: string;
    author: { role: "user" | "agent" };
    content: Part[];
    metadata?: Record<string, unknown>;
    created_at: string;
  }

  /**
   * Convert backend message format to frontend message format
   */
  const convertBackendMessage = (backendMsg: BackendMessage): Message => {
    return {
      id: backendMsg.message_id,
      conversationId: backendMsg.conversation_id,
      role: backendMsg.author.role === "agent" ? "assistant" : "user",
      content: partsToText(backendMsg.content),
      metadata: backendMsg.metadata,
      createdAt: backendMsg.created_at,
    };
  };

  /**
   * Create a new conversation
   */
  const createConversation = async (
    userId: string,
    title?: string,
    metadata?: Record<string, unknown>,
  ): Promise<Conversation | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${baseUrl}/api/v1/conversations`, {
        method: "POST",
        headers: {
          "X-User-Id": userId,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ title, metadata }),
      });

      if (!response.ok) {
        throw new Error(
          `Failed to create conversation: ${response.statusText}`,
        );
      }

      const result = (await response.json()) as {
        conversation_id: string;
        user_id: string;
        title?: string;
        metadata?: Record<string, unknown>;
        created_at: string;
      };

      // Convert snake_case to camelCase
      return {
        conversationId: result.conversation_id,
        userId: result.user_id,
        title: result.title,
        metadata: result.metadata,
        createdAt: result.created_at,
      };
    } catch (e) {
      const errorMessage =
        e instanceof Error ? e.message : "Failed to create conversation";
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * List user conversations
   */
  const listConversations = async (
    userId: string,
    resultsPerPage: number = 20,
    cursor?: string,
  ): Promise<PaginatedResponse<Conversation> | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        results_per_page: resultsPerPage.toString(),
      });
      if (cursor) {
        params.set("cursor", cursor);
      }

      const response = await fetch(
        `${baseUrl}/api/v1/conversations?${params.toString()}`,
        {
          method: "GET",
          headers: {
            "X-User-Id": userId,
          },
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to list conversations: ${response.statusText}`);
      }

      interface BackendConversation {
        conversation_id: string;
        user_id: string;
        title?: string;
        metadata?: Record<string, unknown>;
        created_at: string;
      }

      const result = (await response.json()) as {
        items?: BackendConversation[];
        results_per_page?: number;
        resultsPerPage?: number;
        cursor?: string;
      };

      // Convert backend response to frontend format
      const items = (result.items || []).map((item) => ({
        conversationId: item.conversation_id,
        userId: item.user_id,
        title: item.title,
        metadata: item.metadata,
        createdAt: item.created_at,
      }));

      return {
        items,
        resultsPerPage:
          result.results_per_page || result.resultsPerPage || resultsPerPage,
        cursor: result.cursor,
      };
    } catch (e) {
      const errorMessage =
        e instanceof Error ? e.message : "Failed to list conversations";
      setError(errorMessage);
      console.error("List conversations error:", e);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Delete a conversation
   */
  const deleteConversation = async (
    userId: string,
    conversationId: string,
  ): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${baseUrl}/api/v1/conversations/${conversationId}`,
        {
          method: "DELETE",
          headers: {
            "X-User-Id": userId,
          },
        },
      );

      if (!response.ok) {
        throw new Error(
          `Failed to delete conversation: ${response.statusText}`,
        );
      }

      return true;
    } catch (e) {
      const errorMessage =
        e instanceof Error ? e.message : "Failed to delete conversation";
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Send a chat message with streaming response (using /messages:stream)
   */
  const streamMessage = async (
    userId: string,
    conversationId: string,
    content: string,
    metadata?: Record<string, unknown>,
    onEvent?: (event: Record<string, unknown>) => void,
    onChunk?: (chunk: string) => void,
    onMessage?: (message: Message) => void,
    onComplete?: () => void,
    onError?: (error: Error) => void,
  ): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      const requestBody: SendMessageRequest = {
        conversation_id: conversationId,
        content: textToParts(content),
        metadata,
      };

      const response = await fetch(`${baseUrl}/api/v1/messages:stream`, {
        method: "POST",
        headers: {
          "X-User-Id": userId,
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");

        // Keep the last incomplete line in buffer
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.trim()) continue;

          // Parse SSE format
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();

            try {
              const parsedData = JSON.parse(data);

              // Check if it's a final message (has message_id)
              if (parsedData.message_id) {
                const message = convertBackendMessage(parsedData);
                onMessage?.(message);
              } else {
                // It's an ADK event (streaming chunk)
                onEvent?.(parsedData);

                // Extract text content if available
                if (parsedData.content?.parts) {
                  for (const part of parsedData.content.parts) {
                    if (part.text) {
                      onChunk?.(part.text);
                    }
                  }
                }
              }
            } catch (e) {
              console.warn("Failed to parse SSE data:", data, e);
            }
          } else if (line.startsWith(": ")) {
            // Comment line - ignore
            continue;
          } else if (line.startsWith("id: ") || line.startsWith("event: ")) {
            // Event metadata - can be used if needed
            continue;
          }
        }
      }

      onComplete?.();
    } catch (e) {
      const err = e instanceof Error ? e : new Error("Stream error");
      setError(err.message);
      onError?.(err);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * List messages in a conversation
   */
  const listMessages = async (
    userId: string,
    conversationId: string,
    resultsPerPage: number = 50,
    cursor?: string,
  ): Promise<PaginatedResponse<Message> | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        conversation_id: conversationId,
        results_per_page: resultsPerPage.toString(),
      });
      if (cursor) {
        params.set("cursor", cursor);
      }

      const response = await fetch(
        `${baseUrl}/api/v1/messages?${params.toString()}`,
        {
          method: "GET",
          headers: {
            "X-User-Id": userId,
          },
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to list messages: ${response.statusText}`);
      }

      const result = (await response.json()) as {
        items?: BackendMessage[];
        results_per_page?: number;
        resultsPerPage?: number;
        cursor?: string;
      };

      // Convert backend messages to frontend format
      if (result && result.items) {
        const items = result.items.map((item) => convertBackendMessage(item));
        return {
          items,
          resultsPerPage:
            result.results_per_page || result.resultsPerPage || resultsPerPage,
          cursor: result.cursor,
        };
      }

      return null;
    } catch (e) {
      const errorMessage =
        e instanceof Error ? e.message : "Failed to list messages";
      setError(errorMessage);
      console.error("List messages error:", e);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isLoading,
    error,
    createConversation,
    listConversations,
    deleteConversation,
    streamMessage,
    listMessages,
  };
};
