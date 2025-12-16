// User related types
export interface User {
  id: string
  username: string
  email: string
  avatar?: string
  createdAt: string
}

// Auth types
export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface AuthResponse {
  token: string
  user: User
}

// Chat types - Part structure for message content
export interface TextPart {
  text: string
  kind: 'text'
  metadata?: Record<string, unknown>
}

export interface FilePart {
  file: {
    uri?: string
    bytes?: string
    mime_type?: string
    name?: string
  }
  kind: 'file'
  metadata?: Record<string, unknown>
}

export interface DataPart {
  data: Record<string, unknown>
  kind: 'data'
  metadata?: Record<string, unknown>
}

export type Part = TextPart | FilePart | DataPart

export interface Author {
  role: 'user' | 'agent'
  name?: string
}

// Frontend message format
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
}

// Request for /messages:stream endpoint
export interface SendMessageRequest {
  conversation_id: string
  content: Part[]
  metadata?: Record<string, unknown>
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

// Chat context for contextual conversations
export interface ChatContext {
  type: 'review-summary' | 'attraction' | 'hotel' | 'itinerary' | 'general'
  targetType?: string
  targetId?: string
  attractionName?: string
  hotelName?: string
  [key: string]: unknown
}

// Pagination types
export interface PaginatedResponse<T> {
  items: T[]
  resultsPerPage: number
  cursor?: string
}

// Hotel types
export interface Room {
  name: string
  totalNumber: number
  remainingNumber: number
  bedWidth: number
  bedNumber: number
  minArea: number
  maxArea: number
  peopleNumber: number
  tags: string[]
}

export interface Address {
  country: string
  province: string
  city: string
  county: string
  district: string
  street: string
}

export interface Location {
  lng: number
  lat: number
}

export interface Hotel {
  id: string
  name: string
  address: Address
  introduction: string
  tags: string[]
  rooms: Room[]
  location: Location
  rating?: number
  priceRange?: string
  images?: string[]
}

export interface HotelPage {
  content: Hotel[]
  totalPages: number
  totalElements: number
  size: number
  number: number
  first: boolean
  last: boolean
  numberOfElements: number
}

// Attraction types
export interface Attraction {
  id: string
  name: string
  description: string
  address: Address
  location: Location
  category: string
  rating?: number
  openingHours?: string
  ticketPrice?: string
  images?: string[]
  tags?: string[]
}

// Itinerary types
export interface Activity {
  id: string
  name: string
  description: string
  startTime: string
  endTime: string
  location: {
    name: string
    latitude: number
    longitude: number
    address: string
  }
  category: string
  cost?: {
    amount: number
    currency: string
  }
}

export interface DayPlan {
  dayNumber: number
  date: string
  activities: Activity[]
  notes?: string
}

export interface Itinerary {
  id: string
  destination: string
  startDate: string
  endDate: string
  dayPlans: DayPlan[]
  summary?: {
    totalEstimatedCost: number
    currency: string
    totalActivities: number
    highlights: string[]
  }
  createdAt: string
  updatedAt: string
}

export interface PlanItineraryRequest {
  userId: string
  destination: string
  startDate: string
  endDate: string
  interests: string[]
  budgetLevel: 'budget' | 'moderate' | 'luxury'
  numTravelers: number
  preferences?: Record<string, string>
}

// Note types
export interface Note {
  id: string
  userId: string
  title: string
  content: string
  coverImage?: string
  tags?: string[]
  likes: number
  createdAt: string
  updatedAt: string
  published: boolean
}

export interface Draft {
  id: string
  userId: string
  noteId?: string
  title: string
  content: string
  coverImage?: string
  tags?: string[]
  createdAt: string
  updatedAt: string
}

// File types
export interface FileResource {
  bucket: 'temp' | 'permanent'
  service: string
  path: string
  url?: string
}

export interface UploadSignedUrlResponse {
  signedUrl: string
  file: FileResource
}

// Review types
export interface Review {
  id: string
  userId: string
  targetType: 'attraction' | 'hotel'
  targetId: string
  rating: number
  text: string
  images: string[]
  createdAt: number
  updatedAt: number
}

export interface CreateReviewRequest {
  userId: string
  targetType: 'attraction' | 'hotel'
  targetId: string
  rating: number
  text: string
  images: string[]
}

export interface UpdateReviewRequest {
  id: string
  rating: number
  text: string
  images: string[]
}

export interface GetReviewsResponse {
  reviews: Review[]
  totalReviews: number
  status: boolean
  nextCursor?: string
}

export interface ReviewStats {
  goodReviewCount: number
  middleReviewCount: number
  badReviewCount: number
  imageReviewCount: number
  averageRating: number
  totalReviews: number
}

// API Response wrapper
export interface ApiResponse<T> {
  data: T
  message?: string
  code?: number
}
