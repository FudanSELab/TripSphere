import type { ChatRequest, ChatResponse, Conversation, Message, PaginatedResponse, ApiResponse } from '~/types'

export const useChat = () => {
  const config = useRuntimeConfig()
  const baseUrl = config.public.chatServiceUrl

  const isLoading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Create a new conversation
   */
  const createConversation = async (
    userId: string,
    title?: string,
    metadata?: Record<string, unknown>
  ): Promise<Conversation | null> => {
    isLoading.value = true
    error.value = null

    try {
      const response = await $fetch<ApiResponse<Conversation>>(`${baseUrl}/api/v1/conversations`, {
        method: 'POST',
        headers: {
          'X-User-Id': userId,
          'Content-Type': 'application/json',
        },
        body: { title, metadata },
      })
      return response.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create conversation'
      return null
    } finally {
      isLoading.value = false
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
    isLoading.value = true
    error.value = null

    try {
      const params = new URLSearchParams({
        results_per_page: resultsPerPage.toString(),
      })
      if (cursor) {
        params.set('cursor', cursor)
      }

      const response = await $fetch<ApiResponse<PaginatedResponse<Conversation>>>(
        `${baseUrl}/api/v1/conversations?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'X-User-Id': userId,
          },
        }
      )
      return response.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to list conversations'
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete a conversation
   */
  const deleteConversation = async (userId: string, conversationId: string): Promise<boolean> => {
    isLoading.value = true
    error.value = null

    try {
      await $fetch(`${baseUrl}/api/v1/conversations/${conversationId}`, {
        method: 'DELETE',
        headers: {
          'X-User-Id': userId,
        },
      })
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete conversation'
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Send a chat message and get response
   */
  const sendMessage = async (
    userId: string,
    request: ChatRequest
  ): Promise<ChatResponse | null> => {
    isLoading.value = true
    error.value = null

    try {
      const response = await $fetch<ApiResponse<ChatResponse>>(`${baseUrl}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'X-User-Id': userId,
          'Content-Type': 'application/json',
        },
        body: request,
      })
      return response.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to send message'
      return null
    } finally {
      isLoading.value = false
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
    isLoading.value = true
    error.value = null

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
      error.value = err.message
      onError?.(err)
    } finally {
      isLoading.value = false
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
    isLoading.value = true
    error.value = null

    try {
      const params = new URLSearchParams({
        results_per_page: resultsPerPage.toString(),
      })
      if (cursor) {
        params.set('cursor', cursor)
      }

      const response = await $fetch<ApiResponse<PaginatedResponse<Message>>>(
        `${baseUrl}/api/v1/conversations/${conversationId}/messages?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'X-User-Id': userId,
          },
        }
      )
      return response.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to list messages'
      return null
    } finally {
      isLoading.value = false
    }
  }

  return {
    isLoading: readonly(isLoading),
    error: readonly(error),
    createConversation,
    listConversations,
    deleteConversation,
    sendMessage,
    streamMessage,
    listMessages,
  }
}
