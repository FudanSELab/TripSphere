'use client'

import { useState } from 'react'
import type {
  ChatRequest,
  ChatResponse,
  Conversation,
  Message,
  PaginatedResponse,
  ApiResponse,
} from '@/lib/types'

export const useChat = () => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const baseUrl = process.env.NEXT_PUBLIC_CHAT_SERVICE_URL || 'http://localhost:8000'

  /**
   * Create a new conversation
   */
  const createConversation = async (
    userId: string,
    title?: string,
    metadata?: Record<string, unknown>
  ): Promise<Conversation | null> => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${baseUrl}/api/v1/conversations`, {
        method: 'POST',
        headers: {
          'X-User-Id': userId,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title, metadata }),
      })

      if (!response.ok) {
        throw new Error(`Failed to create conversation: ${response.statusText}`)
      }

      const result: ApiResponse<Conversation> = await response.json()
      return result.data
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to create conversation'
      setError(errorMessage)
      return null
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * List user conversations
   */
  const listConversations = async (
    userId: string,
    resultsPerPage: number = 20,
    cursor?: string
  ): Promise<PaginatedResponse<Conversation> | null> => {
    setIsLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams({
        results_per_page: resultsPerPage.toString(),
      })
      if (cursor) {
        params.set('cursor', cursor)
      }

      const response = await fetch(
        `${baseUrl}/api/v1/conversations?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'X-User-Id': userId,
          },
        }
      )

      if (!response.ok) {
        throw new Error(`Failed to list conversations: ${response.statusText}`)
      }

      const result: ApiResponse<PaginatedResponse<Conversation>> = await response.json()
      return result.data
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to list conversations'
      setError(errorMessage)
      return null
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Delete a conversation
   */
  const deleteConversation = async (userId: string, conversationId: string): Promise<boolean> => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${baseUrl}/api/v1/conversations/${conversationId}`, {
        method: 'DELETE',
        headers: {
          'X-User-Id': userId,
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to delete conversation: ${response.statusText}`)
      }

      return true
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to delete conversation'
      setError(errorMessage)
      return false
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Send a chat message and get response
   */
  const sendMessage = async (
    userId: string,
    request: ChatRequest
  ): Promise<ChatResponse | null> => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${baseUrl}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'X-User-Id': userId,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.statusText}`)
      }

      const result: ApiResponse<ChatResponse> = await response.json()
      return result.data
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to send message'
      setError(errorMessage)
      return null
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Send a chat message with streaming response
   */
  const streamMessage = async (
    userId: string,
    request: ChatRequest,
    onChunk: (chunk: string) => void,
    onComplete?: () => void,
    onError?: (error: Error) => void
  ): Promise<void> => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${baseUrl}/api/v1/chat:stream`, {
        method: 'POST',
        headers: {
          'X-User-Id': userId,
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data !== '[DONE]') {
              onChunk(data)
            }
          }
        }
      }

      onComplete?.()
    } catch (e) {
      const err = e instanceof Error ? e : new Error('Stream error')
      setError(err.message)
      onError?.(err)
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * List messages in a conversation
   */
  const listMessages = async (
    userId: string,
    conversationId: string,
    resultsPerPage: number = 50,
    cursor?: string
  ): Promise<PaginatedResponse<Message> | null> => {
    setIsLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams({
        results_per_page: resultsPerPage.toString(),
      })
      if (cursor) {
        params.set('cursor', cursor)
      }

      const response = await fetch(
        `${baseUrl}/api/v1/conversations/${conversationId}/messages?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'X-User-Id': userId,
          },
        }
      )

      if (!response.ok) {
        throw new Error(`Failed to list messages: ${response.statusText}`)
      }

      const result: ApiResponse<PaginatedResponse<Message>> = await response.json()
      return result.data
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to list messages'
      setError(errorMessage)
      return null
    } finally {
      setIsLoading(false)
    }
  }

  return {
    isLoading,
    error,
    createConversation,
    listConversations,
    deleteConversation,
    sendMessage,
    streamMessage,
    listMessages,
  }
}
