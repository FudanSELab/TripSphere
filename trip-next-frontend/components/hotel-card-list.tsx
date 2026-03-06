"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { Hotel as HotelIcon } from "lucide-react";
import { HotelCard, HotelCardSkeleton } from "@/components/hotel-card";
import { listHotels } from "@/actions/hotel";
import type { Hotel } from "@/lib/grpc/generated/tripsphere/hotel/v1/hotel";

const SKELETON_COUNT = 4;

interface HotelListProps {
  initialHotels: Hotel[];
  initialNextPageToken: string;
  city: string;
}

export function HotelCardList({
  initialHotels,
  initialNextPageToken,
  city,
}: HotelListProps) {
  const [hotels, setHotels] = useState<Hotel[]>(initialHotels);
  const [nextPageToken, setNextPageToken] = useState(initialNextPageToken);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(initialNextPageToken !== "");
  const sentinelRef = useRef<HTMLDivElement>(null);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;
    setLoading(true);
    try {
      const result = await listHotels(city, nextPageToken);
      setHotels((prev) => [...prev, ...result.hotels]);
      setNextPageToken(result.nextPageToken);
      setHasMore(result.nextPageToken !== "");
    } catch {
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  }, [city, nextPageToken, loading, hasMore]);

  // Infinite scroll via IntersectionObserver
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          loadMore();
        }
      },
      { rootMargin: "200px" },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [loadMore]);

  return (
    <>
      <div className="grid grid-cols-4 gap-4">
        {hotels.map((hotel) => (
          <HotelCard
            key={hotel.id}
            hotel={{
              id: hotel.id,
              name: hotel.name,
              image: hotel.images[0] ?? null,
              stars: 4,
              rating: 4.5,
              reviews: 0,
              location: hotel.address
                ? `${hotel.address.city} · ${hotel.address.district}`
                : "",
              price: hotel.estimatedPrice?.units ?? 0,
            }}
          />
        ))}

        {loading &&
          Array.from({ length: SKELETON_COUNT }).map((_, i) => (
            <HotelCardSkeleton key={`skeleton-${i}`} />
          ))}
      </div>

      {hasMore && <div ref={sentinelRef} className="h-1" />}

      {!hasMore && hotels.length > 0 && (
        <p className="text-muted-foreground py-4 text-center text-sm">
          已加载全部酒店
        </p>
      )}

      {!hasMore && hotels.length === 0 && (
        <div className="text-muted-foreground flex flex-col items-center gap-2 py-16">
          <HotelIcon className="size-10 stroke-1" />
          <p className="text-sm">暂无该城市的酒店数据</p>
        </div>
      )}
    </>
  );
}
