// Chat related types

export interface Message {
  id: string
  conversationId: string
  role: 'user' | 'assistant' | 'system'
  content: string
  metadata?: Record<string, unknown>
  createdAt: string
}

export interface Conversation {
  conversationId: string
  userId: string
  title?: string
  metadata?: Record<string, unknown>
  createdAt: string
  updatedAt: string
}

export interface ChatRequest {
  conversationId: string
  taskId?: string
  content: string
  metadata?: Record<string, unknown>
}

export interface ChatResponse {
  queryId: string
  answerId: string
  taskId?: string
}

export interface ChatContext {
  type: 'review-summary' | 'attraction' | 'hotel' | 'itinerary' | 'general'
  targetType?: string
  targetId?: string
  attractionName?: string
  hotelName?: string
  [key: string]: unknown
}
