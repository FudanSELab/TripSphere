import type { Review as GrpcReview } from "@/lib/grpc/gen/tripsphere/review/review";
import { del, get, post, put } from "@/lib/requests/base/request";

/**
 * Request type for getting reviews by target
 */
export interface GetReviewsByTargetRequest {
  targetType: "attraction" | "hotel";
  targetId: string;
  pageNumber?: number;
  pageSize?: number;
}

/**
 * Response type for getting reviews
 */
export interface GetReviewsResponse {
  reviews: GrpcReview[];
  totalReviews: number;
}

/**
 * Request type for creating a review
 */
export interface CreateReviewRequest {
  userId: string;
  targetType: "attraction" | "hotel";
  targetId: string;
  rating: number;
  text: string;
  images?: string[];
}

/**
 * Request type for updating a review
 */
export interface UpdateReviewRequest {
  id: string;
  rating: number;
  text: string;
  images?: string[];
}

/**
 * Get reviews for a target (attraction or hotel)
 * @param request - Search parameters
 * @returns List of reviews with total count
 */
export async function getReviewsByTarget(request: GetReviewsByTargetRequest) {
  const params = new URLSearchParams({
    targetType: request.targetType,
    targetId: request.targetId,
    pageNumber: String(request.pageNumber || 1),
    pageSize: String(request.pageSize || 20),
  });
  return get<GetReviewsResponse>(`/api/v1/reviews?${params.toString()}`);
}

/**
 * Create a new review
 * @param request - Review data
 * @returns Created review ID and status
 */
export async function createReview(request: CreateReviewRequest) {
  return post<{ id: string; status: boolean }>("/api/v1/reviews", request);
}

/**
 * Update an existing review
 * @param request - Updated review data
 * @returns Update status
 */
export async function updateReview(request: UpdateReviewRequest) {
  return put<{ status: boolean }>(`/api/v1/reviews/${request.id}`, request);
}

/**
 * Delete a review
 * @param reviewId - Review ID to delete
 * @returns Delete status
 */
export async function deleteReview(reviewId: string) {
  return del<{ status: boolean }>(`/api/v1/reviews/${reviewId}`);
}
