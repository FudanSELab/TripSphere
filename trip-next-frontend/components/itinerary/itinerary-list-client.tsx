"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { Loader2 } from "lucide-react";

import type { SavedItinerarySummary } from "@/actions/itinerary";
import { formatDateCompact, formatRelative, tripDayCount } from "@/lib/format";

const BATCH_SIZE = 5;

interface CardProps {
  item: SavedItinerarySummary;
  onDelete: (formData: FormData) => Promise<void>;
}

function ItineraryCard({ item, onDelete }: CardProps) {
  const days = tripDayCount(item.start_date, item.end_date);

  return (
    <div className="border-border bg-card hover:border-primary/30 flex flex-col overflow-hidden rounded-xl border shadow-sm transition-all hover:shadow-md">
      <div className="from-primary to-primary/80 text-primary-foreground flex items-center justify-between bg-gradient-to-r px-4 py-3">
        <div className="min-w-0">
          <h3 className="truncate text-sm leading-snug font-bold">
            {item.destination}
          </h3>
          <p className="text-primary-foreground/70 mt-0.5 text-xs">
            {formatDateCompact(item.start_date)} —{" "}
            {formatDateCompact(item.end_date)}
          </p>
        </div>
        <div className="ml-3 flex shrink-0 flex-col items-center rounded-lg bg-white/20 px-2.5 py-1.5 text-center">
          <span className="text-lg leading-none font-bold">{days}</span>
          <span className="text-primary-foreground/70 text-[10px]">天</span>
        </div>
      </div>

      <div className="flex items-center gap-2 px-4 py-2.5">
        <span className="text-muted-foreground flex-1 text-xs">
          🎯 {item.day_count} 个活动 · 🕐 {formatRelative(item.updated_at)}
        </span>
        <Link
          href={`/itinerary/planner?id=${item.id}`}
          className="bg-primary text-primary-foreground hover:bg-primary/90 shrink-0 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
        >
          查看 / 编辑
        </Link>
        <form action={onDelete}>
          <input type="hidden" name="id" value={item.id} />
          <button
            type="submit"
            className="border-border text-muted-foreground hover:border-destructive/30 hover:bg-destructive/10 hover:text-destructive rounded-lg border px-3 py-1.5 text-xs transition-colors"
          >
            删除
          </button>
        </form>
      </div>
    </div>
  );
}

interface Props {
  items: SavedItinerarySummary[];
  onDelete: (formData: FormData) => Promise<void>;
}

export function ItineraryListClient({ items, onDelete }: Props) {
  const [visibleCount, setVisibleCount] = useState(BATCH_SIZE);
  const sentinelRef = useRef<HTMLDivElement>(null);
  const hasMore = visibleCount < items.length;

  useEffect(() => {
    if (!hasMore) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisibleCount((prev) => Math.min(prev + BATCH_SIZE, items.length));
        }
      },
      { threshold: 0.1 },
    );
    const sentinel = sentinelRef.current;
    if (sentinel) observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, items.length]);

  return (
    <div className="flex flex-col gap-2.5">
      {items.slice(0, visibleCount).map((item) => (
        <ItineraryCard key={item.id} item={item} onDelete={onDelete} />
      ))}
      {hasMore && (
        <div
          ref={sentinelRef}
          aria-hidden
          className="text-muted-foreground/50 flex items-center justify-center py-3"
        >
          <Loader2 className="size-4 animate-spin" />
        </div>
      )}
    </div>
  );
}
