import "server-only";

import { cache } from "react";
import { getAuthMetadata, getReviewService } from "@/lib/grpc/client";
import type {
  ListReviewsByEntityResponse,
  Review,
} from "@/lib/grpc/generated/tripsphere/review/v1/review";
import {
  toReviewEntityType,
  type ReviewOverview,
  type ReviewStats,
  type ReviewTargetType,
} from "@/lib/review/types";

const REVIEW_PAGE_SIZE = 100;

const emptyStats: ReviewStats = {
  averageRating: null,
  reviewCount: 0,
};

function calculateReviewStats(reviews: Review[]): ReviewStats {
  if (reviews.length === 0) {
    return emptyStats;
  }

  const ratingTotal = reviews.reduce((total, review) => total + review.rating, 0);
  return {
    averageRating: ratingTotal / reviews.length,
    reviewCount: reviews.length,
  };
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "加载评论失败";
}

export const getReviewOverview = cache(
  async (
    targetId: string,
    targetType: ReviewTargetType,
  ): Promise<ReviewOverview> => {
    const normalizedTargetId = targetId.trim();
    if (!normalizedTargetId) {
      return {
        reviews: [],
        stats: emptyStats,
        error: "评论目标不能为空",
      };
    }

    try {
      const client = getReviewService();
      const metadata = await getAuthMetadata();
      const entityType = toReviewEntityType(targetType);
      const reviews: Review[] = [];
      const seenPageTokens = new Set<string>();
      let pageToken = "";
      let userReview: Review | undefined;

      while (true) {
        seenPageTokens.add(pageToken);
        const response = await new Promise<ListReviewsByEntityResponse>(
          (resolve, reject) => {
            client.listReviewsByEntity(
              {
                entityType,
                entityId: normalizedTargetId,
                pageSize: REVIEW_PAGE_SIZE,
                pageToken,
                orderBy: "updated_at desc",
              },
              metadata,
              (error, result) => {
                if (error) reject(error);
                else resolve(result);
              },
            );
          },
        );

        reviews.push(...response.reviews);
        userReview ??= response.userReview;

        const nextPageToken = response.nextPageToken;
        if (!nextPageToken) {
          const reviewsForStats = userReview
            ? [...reviews, userReview]
            : reviews;
          return {
            reviews,
            userReview,
            stats: calculateReviewStats(reviewsForStats),
          };
        }
        if (seenPageTokens.has(nextPageToken)) {
          throw new Error("评论分页游标发生循环");
        }
        pageToken = nextPageToken;
      }
    } catch (error) {
      return {
        reviews: [],
        stats: emptyStats,
        error: getErrorMessage(error),
      };
    }
  },
);

export async function getReviewStats(
  targetId: string,
  targetType: ReviewTargetType,
): Promise<ReviewStats> {
  const overview = await getReviewOverview(targetId, targetType);
  if (overview.error) {
    throw new Error(overview.error);
  }
  return overview.stats;
}
