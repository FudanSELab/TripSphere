"use server";

import type { Metadata } from "@grpc/grpc-js";
import { revalidatePath } from "next/cache";
import { getAuthMetadata, getReviewService } from "@/lib/grpc/client";
import type {
  CreateReviewResponse,
  ListReviewsByEntityResponse,
  Review,
  ReviewServiceClient,
  UpdateReviewResponse,
} from "@/lib/grpc/generated/tripsphere/review/v1/review";
import {
  toReviewEntityType,
  type CreateReviewInput,
  type DeleteReviewInput,
  type ReviewActionResult,
  type ReviewTargetType,
  type UpdateReviewInput,
} from "@/lib/review/types";
import { getSession } from "@/lib/session";

const MAX_REVIEW_CONTENT_LENGTH = 2_000;

function validateTarget(
  targetId: unknown,
  targetType: unknown,
): string | undefined {
  if (typeof targetId !== "string" || !targetId.trim()) {
    return "评论目标不能为空";
  }
  if (targetType !== "hotel" && targetType !== "attraction") {
    return "不支持的评论目标类型";
  }
}

function validateRatingAndContent(
  rating: unknown,
  content: unknown,
): string | undefined {
  if (
    typeof rating !== "number" ||
    !Number.isInteger(rating) ||
    rating < 1 ||
    rating > 5
  ) {
    return "评分必须是 1 到 5 之间的整数";
  }

  if (typeof content !== "string") {
    return "评论内容不能为空";
  }
  const normalizedContent = content.trim();
  if (!normalizedContent) {
    return "评论内容不能为空";
  }
  if (normalizedContent.length > MAX_REVIEW_CONTENT_LENGTH) {
    return `评论内容不能超过 ${MAX_REVIEW_CONTENT_LENGTH} 个字符`;
  }
}

function revalidateReviewTarget(
  targetId: string,
  targetType: ReviewTargetType,
): void {
  revalidatePath(
    targetType === "hotel"
      ? `/hotels/${targetId}`
      : `/attractions/${targetId}`,
  );
  if (targetType === "hotel") {
    revalidatePath("/hotels");
  }
}

function getErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

async function getUserReviewForTarget(
  client: ReviewServiceClient,
  metadata: Metadata,
  targetId: string,
  targetType: ReviewTargetType,
): Promise<Review | undefined> {
  return new Promise<ListReviewsByEntityResponse>((resolve, reject) => {
    client.listReviewsByEntity(
      {
        entityType: toReviewEntityType(targetType),
        entityId: targetId,
        pageSize: 1,
        pageToken: "",
        orderBy: "updated_at desc",
      },
      metadata,
      (error, result) => {
        if (error) reject(error);
        else resolve(result);
      },
    );
  }).then((response) => response.userReview);
}

export async function createReview(
  input: CreateReviewInput,
): Promise<ReviewActionResult> {
  if (!input || typeof input !== "object") {
    return { success: false, error: "评论参数无效" };
  }

  const targetError = validateTarget(input.targetId, input.targetType);
  const contentError = validateRatingAndContent(input.rating, input.content);
  if (targetError || contentError) {
    return { success: false, error: targetError ?? contentError };
  }

  const session = await getSession();
  if (!session?.userId) {
    return { success: false, error: "请先登录后再发表评论" };
  }

  try {
    const client = getReviewService();
    const metadata = await getAuthMetadata();
    metadata.set("x-user-id", session.userId);
    const targetId = input.targetId.trim();
    const response = await new Promise<CreateReviewResponse>(
      (resolve, reject) => {
        client.createReview(
          {
            review: {
              id: "",
              userId: session.userId,
              entityType: toReviewEntityType(input.targetType),
              entityId: targetId,
              rating: input.rating,
              content: input.content.trim(),
              images: [],
              dimensions: {},
              createdAt: undefined,
              updatedAt: undefined,
            },
          },
          metadata,
          (error, result) => {
            if (error) reject(error);
            else resolve(result);
          },
        );
      },
    );
    if (!response.review) {
      return { success: false, error: "评论服务未返回新评论" };
    }

    revalidateReviewTarget(targetId, input.targetType);
    return { success: true, review: response.review };
  } catch (error) {
    return {
      success: false,
      error: getErrorMessage(error, "发表评论失败"),
    };
  }
}

export async function updateReview(
  input: UpdateReviewInput,
): Promise<ReviewActionResult> {
  if (!input || typeof input !== "object") {
    return { success: false, error: "评论参数无效" };
  }

  const targetError = validateTarget(input.targetId, input.targetType);
  const contentError = validateRatingAndContent(input.rating, input.content);
  if (typeof input.reviewId !== "string" || !input.reviewId.trim()) {
    return { success: false, error: "评论 ID 不能为空" };
  }
  if (targetError || contentError) {
    return { success: false, error: targetError ?? contentError };
  }

  const session = await getSession();
  if (!session?.userId) {
    return { success: false, error: "请先登录后再修改评论" };
  }

  try {
    const client = getReviewService();
    const metadata = await getAuthMetadata();
    metadata.set("x-user-id", session.userId);
    const targetId = input.targetId.trim();
    const reviewId = input.reviewId.trim();
    const existingReview = await getUserReviewForTarget(
      client,
      metadata,
      targetId,
      input.targetType,
    );
    if (!existingReview || existingReview.id !== reviewId) {
      return {
        success: false,
        error: "评论不存在或不属于当前目标",
      };
    }

    const response = await new Promise<UpdateReviewResponse>(
      (resolve, reject) => {
        client.updateReview(
          {
            review: {
              ...existingReview,
              id: reviewId,
              userId: session.userId,
              entityType: toReviewEntityType(input.targetType),
              entityId: targetId,
              rating: input.rating,
              content: input.content.trim(),
            },
          },
          metadata,
          (error, result) => {
            if (error) reject(error);
            else resolve(result);
          },
        );
      },
    );
    if (!response.review) {
      return { success: false, error: "评论服务未返回修改结果" };
    }

    revalidateReviewTarget(targetId, input.targetType);
    return { success: true, review: response.review };
  } catch (error) {
    return {
      success: false,
      error: getErrorMessage(error, "修改评论失败"),
    };
  }
}

export async function deleteReview(
  input: DeleteReviewInput,
): Promise<ReviewActionResult> {
  if (!input || typeof input !== "object") {
    return { success: false, error: "评论参数无效" };
  }

  const targetError = validateTarget(input.targetId, input.targetType);
  if (typeof input.reviewId !== "string" || !input.reviewId.trim()) {
    return { success: false, error: "评论 ID 不能为空" };
  }
  if (targetError) {
    return { success: false, error: targetError };
  }

  const session = await getSession();
  if (!session?.userId) {
    return { success: false, error: "请先登录后再删除评论" };
  }

  try {
    const client = getReviewService();
    const metadata = await getAuthMetadata();
    metadata.set("x-user-id", session.userId);
    const targetId = input.targetId.trim();
    const reviewId = input.reviewId.trim();
    const existingReview = await getUserReviewForTarget(
      client,
      metadata,
      targetId,
      input.targetType,
    );
    if (!existingReview || existingReview.id !== reviewId) {
      return {
        success: false,
        error: "评论不存在或不属于当前目标",
      };
    }

    await new Promise<void>((resolve, reject) => {
      client.deleteReview(
        { id: reviewId },
        metadata,
        (error) => {
          if (error) reject(error);
          else resolve();
        },
      );
    });

    revalidateReviewTarget(targetId, input.targetType);
    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: getErrorMessage(error, "删除评论失败"),
    };
  }
}
