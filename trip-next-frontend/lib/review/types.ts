import {
  EntityType,
  type Review,
} from "@/lib/grpc/generated/tripsphere/review/v1/review";

export type ReviewTargetType = "hotel" | "attraction";

export interface ReviewStats {
  averageRating: number | null;
  reviewCount: number;
}

export interface ReviewOverview {
  reviews: Review[];
  userReview?: Review;
  stats: ReviewStats;
  error?: string;
}

export interface CreateReviewInput {
  targetId: string;
  targetType: ReviewTargetType;
  rating: number;
  content: string;
}

export interface UpdateReviewInput extends CreateReviewInput {
  reviewId: string;
}

export interface DeleteReviewInput {
  reviewId: string;
  targetId: string;
  targetType: ReviewTargetType;
}

export interface ReviewActionResult {
  success: boolean;
  review?: Review;
  error?: string;
}

export function toReviewEntityType(targetType: ReviewTargetType): EntityType {
  switch (targetType) {
    case "hotel":
      return EntityType.ENTITY_TYPE_HOTEL;
    case "attraction":
      return EntityType.ENTITY_TYPE_ATTRACTION;
    default:
      throw new Error("Unsupported review target type");
  }
}
