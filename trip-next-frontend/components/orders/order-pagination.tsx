"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { Button } from "@/components/ui/button";

export function OrderPagination({ nextPageToken }: { nextPageToken: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleLoadMore = useCallback(() => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", nextPageToken);
    router.push(`/orders?${params.toString()}`);
  }, [router, searchParams, nextPageToken]);

  if (!nextPageToken) return null;

  return (
    <div className="flex justify-center pt-4">
      <Button variant="outline" onClick={handleLoadMore}>
        加载更多
      </Button>
    </div>
  );
}
