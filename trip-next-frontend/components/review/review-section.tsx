"use client";

import { useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { CircleAlert, MessageSquareText, Trash2 } from "lucide-react";
import { deleteReview } from "@/actions/review";
import { ReviewForm } from "@/components/review/review-form";
import { ReviewRating } from "@/components/review/review-rating";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import type { Review } from "@/lib/grpc/generated/tripsphere/review/v1/review";
import type {
  ReviewOverview,
  ReviewTargetType,
} from "@/lib/review/types";

interface ReviewSectionProps {
  targetId: string;
  targetType: ReviewTargetType;
  overview: ReviewOverview;
  isAuthenticated: boolean;
}

function formatReviewDate(date: Date | undefined): string {
  if (!date) return "";

  const parsedDate = date instanceof Date ? date : new Date(date);
  if (Number.isNaN(parsedDate.getTime())) return "";

  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(parsedDate);
}

function ReviewCard({ review }: { review: Review }) {
  const date = formatReviewDate(review.updatedAt ?? review.createdAt);

  return (
    <article className="flex gap-3 py-5">
      <Avatar aria-hidden="true">
        <AvatarFallback>旅</AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-sm font-medium">TripSphere 用户</span>
          {date && (
            <time className="text-muted-foreground text-xs">{date}</time>
          )}
        </div>
        <ReviewRating value={review.rating} label="用户评分" className="mt-1" />
        <p className="mt-3 text-sm leading-relaxed whitespace-pre-wrap">
          {review.content}
        </p>
      </div>
    </article>
  );
}

export function ReviewSection({
  targetId,
  targetType,
  overview,
  isAuthenticated,
}: ReviewSectionProps) {
  const router = useRouter();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteError, setDeleteError] = useState<string>();
  const [isDeleting, startDeleteTransition] = useTransition();

  function handleDelete() {
    if (!overview.userReview) return;

    setDeleteError(undefined);
    startDeleteTransition(async () => {
      const result = await deleteReview({
        reviewId: overview.userReview!.id,
        targetId,
        targetType,
      });
      if (!result.success) {
        setDeleteError(result.error ?? "删除评论失败");
        return;
      }

      setDeleteDialogOpen(false);
      router.refresh();
    });
  }

  if (overview.error) {
    return (
      <Alert variant="destructive">
        <CircleAlert />
        <AlertTitle>评论暂时无法加载</AlertTitle>
        <AlertDescription>{overview.error}</AlertDescription>
      </Alert>
    );
  }

  const { stats } = overview;

  return (
    <section aria-labelledby="review-section-title" className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 id="review-section-title" className="text-lg font-bold">
            用户评论
          </h2>
          <p className="text-muted-foreground mt-1 text-sm">
            来自真实旅行者的体验分享
          </p>
        </div>
        <div className="flex items-center gap-3" aria-live="polite">
          <ReviewRating value={stats.averageRating ?? 0} label="综合评分" />
          <span className="font-semibold">
            {stats.averageRating == null
              ? "暂无评分"
              : `${stats.averageRating.toFixed(1)} 分`}
          </span>
          <span className="text-muted-foreground text-sm">
            {stats.reviewCount} 条评论
          </span>
        </div>
      </div>

      {isAuthenticated ? (
        <Card>
          <CardHeader className="flex-row items-center justify-between gap-4">
            <CardTitle>
              {overview.userReview ? "我的评论" : "写下你的评论"}
            </CardTitle>
            {overview.userReview && (
              <Dialog
                open={deleteDialogOpen}
                onOpenChange={(open) => {
                  setDeleteDialogOpen(open);
                  if (!open) setDeleteError(undefined);
                }}
              >
                <DialogTrigger asChild>
                  <Button variant="ghost" size="sm">
                    <Trash2 />
                    删除
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>删除这条评论？</DialogTitle>
                    <DialogDescription>
                      删除后无法恢复，评分统计也会随之更新。
                    </DialogDescription>
                  </DialogHeader>
                  {deleteError && (
                    <p role="alert" className="text-destructive text-sm">
                      {deleteError}
                    </p>
                  )}
                  <DialogFooter>
                    <DialogClose asChild>
                      <Button variant="outline" disabled={isDeleting}>
                        取消
                      </Button>
                    </DialogClose>
                    <Button
                      variant="destructive"
                      disabled={isDeleting}
                      onClick={handleDelete}
                    >
                      {isDeleting && <Spinner />}
                      {isDeleting ? "删除中…" : "确认删除"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            )}
          </CardHeader>
          <CardContent>
            <ReviewForm
              targetId={targetId}
              targetType={targetType}
              initialReview={overview.userReview}
            />
          </CardContent>
        </Card>
      ) : (
        <Alert>
          <MessageSquareText />
          <AlertTitle>分享你的旅行体验</AlertTitle>
          <AlertDescription>
            <Link href="/signin" className="text-primary underline">
              登录
            </Link>
            后即可评分并发表评论。
          </AlertDescription>
        </Alert>
      )}

      <div>
        <h3 className="font-semibold">
          {overview.userReview ? "其他评论" : "全部评论"}
        </h3>
        {overview.reviews.length === 0 ? (
          <Empty className="mt-4 border">
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <MessageSquareText />
              </EmptyMedia>
              <EmptyTitle>
                {overview.userReview ? "还没有其他评论" : "还没有评论"}
              </EmptyTitle>
              <EmptyDescription>
                成为第一位分享体验的旅行者吧。
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        ) : (
          <div className="mt-2 divide-y">
            {overview.reviews.map((review) => (
              <ReviewCard key={review.id} review={review} />
            ))}
          </div>
        )}
      </div>

      <Separator />
    </section>
  );
}
