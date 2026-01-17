/**
 * Unified type definitions for TripSphere frontend
 *
 * This file re-exports types from protobuf-generated code and defines
 * frontend-specific types. This ensures type consistency across the app.
 *
 * ## Type Management Strategy:
 *
 * 1. **Direct Usage**: Types that match exactly between gRPC and frontend are
 *    re-exported directly from generated code (e.g., Review, Address)
 *
 * 2. **Frontend Adaptation**: Types that need UI-specific fields or field name
 *    changes are redefined (e.g., User with avatar, Hotel with rating)
 *
 * 3. **Structural Differences**: Types where gRPC uses flexible metadata but
 *    frontend needs concrete fields (e.g., Activity, Itinerary)
 *
 * ## Guidelines:
 * - Use gRPC types as Single Source of Truth when possible
 * - Document why frontend types differ from gRPC counterparts
 * - Provide conversion functions for complex transformations
 */

// ============================================================================
// GRPC Generated Types (Single Source of Truth)
// ============================================================================

// User types
export type {
  LoginResponse as GrpcLoginResponse,
  User as GrpcUser,
  LoginRequest,
  RegisterRequest,
} from "@/lib/grpc/gen/tripsphere/user/user";

// Hotel types
import type {
  Hotel as GrpcHotel,
  HotelPage,
  Room,
} from "@/lib/grpc/gen/tripsphere/hotel/hotel";

export type { GrpcHotel, HotelPage, Room };

// Attraction types
export type { Attraction as GrpcAttraction } from "@/lib/grpc/gen/tripsphere/attraction/attraction";

// Itinerary types
export type {
  Activity as GrpcActivity,
  DayPlan as GrpcDayPlan,
  Itinerary as GrpcItinerary,
} from "@/lib/grpc/gen/tripsphere/itinerary/itinerary";

// Common types
import type {
  Address,
  Location as GrpcLocation,
} from "@/lib/grpc/gen/tripsphere/common/geo";

export type { Address, GrpcLocation };

// Review types
import type {
  GetReviewByTargetIDWithCursorResponse,
  CreateReviewRequest as GrpcCreateReviewRequest,
  Review as GrpcReview,
  UpdateReviewRequest as GrpcUpdateReviewRequest,
} from "@/lib/grpc/gen/tripsphere/review/review";

export type {
  GetReviewByTargetIDWithCursorResponse,
  GrpcCreateReviewRequest,
  GrpcReview,
  GrpcUpdateReviewRequest,
};

// ============================================================================
// Frontend Adapted Types
// ============================================================================
// These types extend or adapt gRPC types for frontend-specific needs:
// - Adding UI-specific fields (avatar, rating, priceRange, etc.)
// - Converting field names for better DX (lng/lat vs longitude/latitude)
// - Adding computed/derived fields not present in backend

/**
 * User type adapted for frontend use
 * Extends GrpcUser with UI-specific fields:
 * - avatar: User profile picture URL
 * - createdAt: Account creation timestamp
 */
export interface User {
  id: string;
  username: string;
  avatar?: string;
  createdAt?: string;
  roles?: string[];
}

/**
 * LoginResponse adapted for frontend
 * Ensures user field is always present (non-optional)
 */
export interface LoginResponse {
  user: User;
  token: string;
}

/**
 * Location type adapted for frontend
 * - Uses lng/lat instead of longitude/latitude for consistency with map libraries
 */
export interface Location {
  lng: number;
  lat: number;
}

/**
 * Convert grpc Location to frontend Location
 */
export function toLocation(
  grpcLocation?: { longitude: number; latitude: number } | null,
): Location | undefined {
  if (!grpcLocation) return undefined;
  return {
    lng: grpcLocation.longitude,
    lat: grpcLocation.latitude,
  };
}

/**
 * Convert frontend Location to grpc Location
 */
export function toGrpcLocation(
  location?: Location | null,
): { longitude: number; latitude: number } | undefined {
  if (!location) return undefined;
  return {
    longitude: location.lng,
    latitude: location.lat,
  };
}

/**
 * Hotel type adapted for frontend use
 * Extends GrpcHotel with UI-specific fields:
 * - rating: Aggregated user rating (computed from reviews)
 * - priceRange: Price category for display ("$", "$$", "$$$")
 * - images: Hotel photo URLs (string[] instead of File[])
 * - location: Converted to frontend Location format (lng/lat)
 */
export interface Hotel {
  id: string;
  name: string;
  address: Address;
  introduction: string;
  tags: string[];
  rooms: Room[];
  location: Location;
  rating?: number;
  priceRange?: string;
  images?: string[];
}

/**
 * Attraction type adapted for frontend use
 * Differs from GrpcAttraction:
 * - description: Renamed from 'introduction' for clarity
 * - category: Business category for filtering
 * - rating: Aggregated user rating
 * - openingHours: Business hours for display
 * - ticketPrice: Price information string
 * - images: Photo URLs as string[] instead of File[]
 * - location: Converted to frontend Location format
 */
export interface Attraction {
  id: string;
  name: string;
  description: string;
  address: Address;
  location: Location;
  category: string;
  rating?: number;
  openingHours?: string;
  ticketPrice?: string;
  images?: string[];
  tags?: string[];
}

/**
 * Activity type adapted for frontend use
 *
 * NOTE: This differs significantly from GrpcActivity which uses flexible metadata.
 * Frontend needs concrete fields for type safety and better DX.
 *
 * GrpcActivity: { activityId, kind, metadata }
 * Frontend Activity: explicit fields for all properties
 */
export interface Activity {
  id: string;
  name: string;
  description: string;
  startTime: string;
  endTime: string;
  location: {
    name: string;
    latitude: number;
    longitude: number;
    address: string;
  };
  category: string;
  cost?: {
    amount: number;
    currency: string;
  };
}

/**
 * DayPlan type adapted for frontend use
 *
 * NOTE: Differs from GrpcDayPlan structure:
 * - Uses dayNumber + date instead of just title
 * - Uses notes instead of metadata
 * - Activities are frontend Activity type (concrete fields vs metadata)
 */
export interface DayPlan {
  dayNumber: number;
  date: string;
  activities: Activity[];
  notes?: string;
}

/**
 * Itinerary type adapted for frontend use
 *
 * NOTE: Extends GrpcItinerary with frontend-specific fields:
 * - destination: Trip destination (not in gRPC)
 * - summary: Computed summary statistics (not in gRPC metadata)
 * - Uses frontend DayPlan type with concrete fields
 */
export interface Itinerary {
  id: string;
  destination: string;
  startDate: string;
  endDate: string;
  dayPlans: DayPlan[];
  summary?: {
    totalEstimatedCost: number;
    currency: string;
    totalActivities: number;
    highlights: string[];
  };
  createdAt: string;
  updatedAt: string;
}

// ============================================================================
// Frontend-Only Types
// ============================================================================

// Auth types
export interface AuthResponse {
  token: string;
  user: User;
}

// Chat types - Part structure for message content
export interface TextPart {
  text: string;
  kind: "text";
  metadata?: Record<string, unknown>;
}

export interface FilePart {
  file: {
    uri?: string;
    bytes?: string;
    mime_type?: string;
    name?: string;
  };
  kind: "file";
  metadata?: Record<string, unknown>;
}

export interface DataPart {
  data: Record<string, unknown>;
  kind: "data";
  metadata?: Record<string, unknown>;
}

export type Part = TextPart | FilePart | DataPart;

export interface Author {
  role: "user" | "agent";
  name?: string;
}

// Frontend message format
export interface Message {
  id: string;
  conversationId: string;
  role: "user" | "assistant" | "system";
  content: string;
  metadata?: Record<string, unknown>;
  createdAt: string;
}

export interface Conversation {
  conversationId: string;
  userId: string;
  title?: string;
  metadata?: Record<string, unknown>;
  createdAt: string;
}

// Request for /messages:stream endpoint
export interface SendMessageRequest {
  conversation_id: string;
  content: Part[];
  metadata?: Record<string, unknown>;
}

export interface ChatRequest {
  conversationId: string;
  taskId?: string;
  content: string;
  metadata?: Record<string, unknown>;
}

export interface ChatResponse {
  queryId: string;
  answerId: string;
  taskId?: string;
}

// Chat context for contextual conversations
export interface ChatContext {
  type: "review-summary" | "attraction" | "hotel" | "itinerary" | "general";
  targetType?: string;
  targetId?: string;
  attractionName?: string;
  hotelName?: string;
  autoSendQuery?: string;
  autoSendMetadata?: Record<string, unknown>;
  agent?: string;
  [key: string]: unknown;
}

// Pagination types
export interface PaginatedResponse<T> {
  items: T[];
  resultsPerPage: number;
  cursor?: string;
}

export interface PlanItineraryRequest {
  userId: string;
  destination: string;
  startDate: string;
  endDate: string;
  interests: string[];
  budgetLevel: "budget" | "moderate" | "luxury";
  numTravelers: number;
  preferences?: Record<string, string>;
}

// Note types
export interface Note {
  id: string;
  userId: string;
  title: string;
  content: string;
  coverImage?: string;
  tags?: string[];
  likes: number;
  createdAt: string;
  updatedAt: string;
  published: boolean;
}

export interface Draft {
  id: string;
  userId: string;
  noteId?: string;
  title: string;
  content: string;
  coverImage?: string;
  tags?: string[];
  createdAt: string;
  updatedAt: string;
}

// File types
export interface FileResource {
  bucket: "temp" | "permanent";
  service: string;
  path: string;
  url?: string;
}

export interface UploadSignedUrlResponse {
  signedUrl: string;
  file: FileResource;
}

// Review types - using gRPC generated types directly (no adaptation needed)
export type Review = GrpcReview;
export type CreateReviewRequest = GrpcCreateReviewRequest;
export type UpdateReviewRequest = GrpcUpdateReviewRequest;
export type GetReviewsResponse = GetReviewByTargetIDWithCursorResponse;

export interface ReviewStats {
  goodReviewCount: number;
  middleReviewCount: number;
  badReviewCount: number;
  imageReviewCount: number;
  averageRating: number;
  totalReviews: number;
}

// API Response wrapper
export interface ApiResponse<T> {
  data: T;
  message?: string;
  code?: number;
}
