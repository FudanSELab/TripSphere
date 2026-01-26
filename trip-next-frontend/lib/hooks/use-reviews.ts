import type { Review as GrpcReview } from "@/lib/grpc/gen/tripsphere/review/review";
import {
  createReview as createReviewApi,
  deleteReview as deleteReviewApi,
  getReviewsByTarget,
  updateReview as updateReviewApi,
  type CreateReviewRequest,
  type GetReviewsResponse,
  type UpdateReviewRequest,
} from "@/lib/requests";
import { useState } from "react";

export function useReviews() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReviews = async (
    targetType: "attraction" | "hotel",
    targetId: string,
    pageNumber: number = 1,
    pageSize: number = 20,
  ): Promise<GetReviewsResponse & { status: boolean }> => {
    setLoading(true);
    setError(null);
    try {
      const response = await getReviewsByTarget({
        targetType,
        targetId,
        pageNumber,
        pageSize,
      });

      if (response.data) {
        return {
          reviews: response.data.reviews || [],
          totalReviews: response.data.totalReviews || 0,
          status: true,
        };
      }

      // If no data, return empty result
      return {
        reviews: [],
        totalReviews: 0,
        status: false,
      };
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to fetch reviews";
      setError(message);
      return {
        reviews: [],
        totalReviews: 0,
        status: false,
      };
    } finally {
      setLoading(false);
    }
  };

  const createReview = async (
    request: CreateReviewRequest,
  ): Promise<{ id: string; status: boolean }> => {
    setLoading(true);
    setError(null);
    try {
      const response = await createReviewApi(request);

      if (response.data) {
        return {
          id: response.data.id,
          status: response.data.status,
        };
      }

      return {
        id: "",
        status: false,
      };
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to create review";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateReview = async (
    request: UpdateReviewRequest,
  ): Promise<{ status: boolean }> => {
    setLoading(true);
    setError(null);
    try {
      const response = await updateReviewApi(request);

      if (response.data) {
        return {
          status: response.data.status,
        };
      }

      return {
        status: false,
      };
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to update review";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteReview = async (
    reviewId: string,
  ): Promise<{ status: boolean }> => {
    setLoading(true);
    setError(null);
    try {
      const response = await deleteReviewApi(reviewId);

      if (response.data) {
        return {
          status: response.data.status,
        };
      }

      return {
        status: false,
      };
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to delete review";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    fetchReviews,
    createReview,
    updateReview,
    deleteReview,
  };
}

// Export GrpcReview type for use in components
export type { GrpcReview };
