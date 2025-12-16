import type { 
  Conversation, 
  Message, 
  CursorPagination,
  SendMessageRequest,
  Part,
  Author
} from '~/types'

export const useChat = () => {
  const config = useRuntimeConfig()
  const baseUrl = config.public.chatServiceUrl

  const isLoading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Helper function to convert text content to Part array
   */
  const textToParts = (text: string): Part[] => {
    return [{
      text,
      kind: 'text' as const,
    }]
  }

  /**
   * Helper function to extract text from Part array
   */
  const partsToText = (parts: Part[]): string => {
    return parts
      .filter((part): part is { text: string; kind: 'text' } => part.kind === 'text')
      .map(part => part.text)
      .join('\n\n')
  }

  /**
   * Convert backend message format to frontend message format
   */
  const convertBackendMessage = (backendMsg: any): Message => {
    return {
      id: backendMsg.message_id,
      conversationId: backendMsg.conversation_id,
      role: backendMsg.author.role === 'agent' ? 'assistant' : 'user',
      content: partsToText(backendMsg.content),
      metadata: backendMsg.metadata,
      createdAt: backendMsg.created_at,
    }
  }

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
      const response = await $fetch<any>(`${baseUrl}/api/v1/conversations`, {
        method: 'POST',
        headers: {
          'X-User-Id': userId,
          'Content-Type': 'application/json',
        },
        body: { title, metadata },
      })
      
      // Convert snake_case to camelCase
      return {
        conversationId: response.conversation_id,
        userId: response.user_id,
        title: response.title,
        metadata: response.metadata,
        createdAt: response.created_at,
      }
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
  ): Promise<CursorPagination<Conversation> | null> => {
    isLoading.value = true
    error.value = null

    try {
      const params = new URLSearchParams({
        results_per_page: resultsPerPage.toString(),
      })
      if (cursor) {
        params.set('cursor', cursor)
      }

      const response = await $fetch<any>(
        `${baseUrl}/api/v1/conversations?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'X-User-Id': userId,
          },
        }
      )
      
      // Convert backend response to frontend format
      const items = (response.items || []).map((item: any) => ({
        conversationId: item.conversation_id,
        userId: item.user_id,
        title: item.title,
        metadata: item.metadata,
        createdAt: item.created_at,
      }))
      
      return {
        items,
        resultsPerPage: response.results_per_page || response.resultsPerPage || resultsPerPage,
        cursor: response.cursor,
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to list conversations'
      console.error('List conversations error:', e)
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
   * Send a chat message with streaming response (using /messages:stream)
   */
  const streamMessage = async (
    userId: string,
    conversationId: string,
    content: string,
    metadata?: Record<string, unknown>,
    onEvent?: (event: any) => void,
    onChunk?: (chunk: string) => void,
    onMessage?: (message: Message) => void,
    onComplete?: () => void,
    onError?: (error: Error) => void
  ): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      const requestBody: SendMessageRequest = {
        conversation_id: conversationId,
        content: textToParts(content),
        metadata,
      }

      const response = await fetch(`${baseUrl}/api/v1/messages:stream`, {
        method: 'POST',
        headers: {
          'X-User-Id': userId,
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      let buffer = ''
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        
        // Keep the last incomplete line in buffer
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue

          // Parse SSE format
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            
            try {
              const parsedData = JSON.parse(data)
              
              // Check if it's a final message (has message_id)
              if (parsedData.message_id) {
                const message = convertBackendMessage(parsedData)
                onMessage?.(message)
              } else {
                // It's an ADK event (streaming chunk)
                onEvent?.(parsedData)
                
                // Extract text content if available
                if (parsedData.content?.parts) {
                  for (const part of parsedData.content.parts) {
                    if (part.text) {
                      onChunk?.(part.text)
                    }
                  }
                }
              }
            } catch (e) {
              console.warn('Failed to parse SSE data:', data, e)
            }
          } else if (line.startsWith(': ')) {
            // Comment line - ignore
            continue
          } else if (line.startsWith('id: ') || line.startsWith('event: ')) {
            // Event metadata - can be used if needed
            continue
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
  ): Promise<CursorPagination<Message> | null> => {
    isLoading.value = true
    error.value = null

    try {
      const params = new URLSearchParams({
        conversation_id: conversationId,
        results_per_page: resultsPerPage.toString(),
      })
      if (cursor) {
        params.set('cursor', cursor)
      }

      const response = await $fetch<any>(
        `${baseUrl}/api/v1/messages?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'X-User-Id': userId,
          },
        }
      )
      
      // Convert backend messages to frontend format
      if (response && response.items) {
        const items = response.items.map((item: any) => convertBackendMessage(item))
        return {
          items,
          resultsPerPage: response.results_per_page || response.resultsPerPage || resultsPerPage,
          cursor: response.cursor,
        }
      }
      
      return null
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to list messages'
      console.error('List messages error:', e)
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
    streamMessage,
    listMessages,
  }
}
