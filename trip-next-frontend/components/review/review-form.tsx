"use client";

import { useState, useTransition, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { createReview, updateReview } from "@/actions/review";
import { ReviewRating } from "@/components/review/review-rating";
import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import type { Review } from "@/lib/grpc/generated/tripsphere/review/v1/review";
import type { ReviewTargetType } from "@/lib/review/types";

const MAX_REVIEW_CONTENT_LENGTH = 2_000;

interface ReviewFormProps {
  targetId: string;
  targetType: ReviewTargetType;
  initialReview?: Review;
}

export function ReviewForm({
  targetId,
  targetType,
  initialReview,
}: ReviewFormProps) {
  const router = useRouter();
  const [rating, setRating] = useState(initialReview?.rating ?? 5);
  const [content, setContent] = useState(initialReview?.content ?? "");
  const [error, setError] = useState<string>();
  const [isPending, startTransition] = useTransition();
  const isEditing = Boolean(initialReview);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(undefined);

    startTransition(async () => {
      const result = initialReview
        ? await updateReview({
            reviewId: initialReview.id,
            targetId,
            targetType,
            rating,
            content,
          })
        : await createReview({ targetId, targetType, rating, content });

      if (!result.success) {
        setError(result.error ?? "保存评论失败");
        return;
      }

      router.refresh();
    });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Field>
        <FieldLabel>评分</FieldLabel>
        <ReviewRating
          value={rating}
          onChange={setRating}
          disabled={isPending}
          name={initialReview ? `rating-${initialReview.id}` : "rating-new"}
        />
      </Field>

      <Field data-invalid={Boolean(error)}>
        <div className="flex items-center justify-between gap-4">
          <FieldLabel htmlFor="review-content">评论内容</FieldLabel>
          <span className="text-muted-foreground text-xs" aria-live="polite">
            {content.length}/{MAX_REVIEW_CONTENT_LENGTH}
          </span>
        </div>
        <Textarea
          id="review-content"
          value={content}
          onChange={(event) => setContent(event.target.value)}
          maxLength={MAX_REVIEW_CONTENT_LENGTH}
          rows={5}
          disabled={isPending}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? "review-form-error" : undefined}
          placeholder="分享你的真实体验，帮助其他旅行者做出选择"
        />
        {error && <FieldError id="review-form-error">{error}</FieldError>}
      </Field>

      <div className="flex justify-end">
        <Button type="submit" disabled={isPending}>
          {isPending && <Spinner />}
          {isPending ? "保存中…" : isEditing ? "更新评论" : "发表评论"}
        </Button>
      </div>
    </form>
  );
}
