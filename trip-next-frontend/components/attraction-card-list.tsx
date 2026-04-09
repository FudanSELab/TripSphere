"use client";

import { useState, useMemo, useRef, useEffect, useCallback } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Clock,
  MapPin,
  Flame,
  Ticket,
  LayoutGrid,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ImagePlaceholder } from "@/components/image-placeholder";
import {
  AttractionCard,
  AttractionCardSkeleton,
  attractionToCardData,
} from "@/components/attraction-card";
import { loadMoreAttractionsByCity } from "@/actions/attraction";
import { formatMoney, formatRecommendTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Attraction } from "@/lib/grpc/generated/tripsphere/attraction/v1/attraction";

const CATEGORY_TAGS = [
  "人文景观",
  "体育娱乐",
  "公园",
  "博物馆",
  "历史古迹",
  "商业街区",
  "大学校园",
  "文化旅游区",
  "游乐园",
  "红色景点",
  "纪念馆",
  "美术馆",
  "自然风光",
  "艺术馆",
];

interface AttractionCardListProps {
  initialAttractions: Attraction[];
  initialNextPageToken: string;
  city: string;
}

function HotCarouselCard({ attraction }: { attraction: Attraction }) {
  const price = attraction.ticketInfo?.estimatedPrice
    ? formatMoney(attraction.ticketInfo.estimatedPrice)
    : null;
  const district =
    attraction.address?.district ?? attraction.address?.city ?? "";
  const visitTime = formatRecommendTime(
    attraction.recommendTime?.minHours,
    attraction.recommendTime?.maxHours,
  );

  return (
    <Link
      href={`/attractions/${attraction.id}`}
      className="group relative block aspect-video w-full overflow-hidden rounded-2xl"
    >
      {attraction.images[0] ? (
        <Image
          src={attraction.images[0]}
          alt={attraction.name}
          fill
          unoptimized
          className="object-cover transition-transform duration-700 group-hover:scale-105"
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
        />
      ) : (
        <ImagePlaceholder className="h-full w-full" />
      )}

      <div className="absolute inset-0 bg-gradient-to-t from-black/10 via-black/5 to-transparent" />

      <Badge className="bg-price text-price-foreground absolute top-3 left-3 gap-1">
        <Flame className="size-3" />
        人气热门
      </Badge>

      {attraction.tags.length > 0 && (
        <div className="absolute top-3 right-3 flex flex-wrap justify-end gap-1">
          {attraction.tags.slice(0, 2).map((tag) => (
            <Badge
              key={tag}
              className="bg-background/20 text-white backdrop-blur-sm"
            >
              {tag}
            </Badge>
          ))}
        </div>
      )}

      <div className="absolute right-0 bottom-0 left-0 p-4">
        <h3 className="line-clamp-2 text-base leading-snug font-bold text-white drop-shadow-lg sm:text-lg">
          {attraction.name}
        </h3>
        {district && (
          <div className="mt-1 flex items-center gap-1 text-white/75">
            <MapPin className="h-3 w-3 shrink-0" />
            <span className="text-xs">{district}</span>
          </div>
        )}
        <div className="mt-2 flex items-center gap-3">
          {visitTime && (
            <div className="flex items-center gap-1 text-white/80">
              <Clock className="h-3 w-3" />
              <span className="text-xs">{visitTime}</span>
            </div>
          )}
          {price != null ? (
            <Badge className="bg-price/90 text-price-foreground">
              ¥{price.toLocaleString()}
            </Badge>
          ) : (
            <Badge className="bg-success/90 text-success-foreground">
              免费
            </Badge>
          )}
        </div>
      </div>
    </Link>
  );
}

function FreeAttractionCard({ attraction }: { attraction: Attraction }) {
  const district =
    attraction.address?.district ?? attraction.address?.city ?? "";
  const visitTime = formatRecommendTime(
    attraction.recommendTime?.minHours,
    attraction.recommendTime?.maxHours,
  );

  return (
    <Link
      href={`/attractions/${attraction.id}`}
      className="group bg-card border-success/20 hover:border-success/60 block w-full overflow-hidden rounded-2xl border-2 transition-all duration-300 hover:shadow-lg"
    >
      <div className="relative aspect-video w-full overflow-hidden">
        {attraction.images[0] ? (
          <Image
            src={attraction.images[0]}
            alt={attraction.name}
            fill
            unoptimized
            className="object-cover transition-transform duration-500 group-hover:scale-105"
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
          />
        ) : (
          <ImagePlaceholder className="h-full w-full" />
        )}

        <Badge className="bg-success text-success-foreground absolute top-3 left-3 gap-1">
          <Ticket className="size-3" />
          免费
        </Badge>

        {attraction.tags.length > 0 && (
          <div className="absolute top-3 right-3 flex flex-wrap justify-end gap-1">
            {attraction.tags.slice(0, 2).map((tag) => (
              <Badge
                key={tag}
                className="bg-background/25 text-white backdrop-blur-sm"
              >
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </div>

      <div className="p-3">
        <h3 className="text-foreground group-hover:text-success line-clamp-1 text-sm font-semibold transition-colors">
          {attraction.name}
        </h3>
        <div className="mt-1 flex items-center justify-between">
          {district && (
            <div className="text-muted-foreground flex items-center gap-0.5">
              <MapPin className="h-3 w-3 shrink-0" />
              <span className="line-clamp-1 text-xs">{district}</span>
            </div>
          )}
          {visitTime && (
            <div className="text-success flex shrink-0 items-center gap-1">
              <Clock className="h-3 w-3" />
              <span className="text-xs font-medium">{visitTime}</span>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}

function HorizontalScroll({
  children,
  scrollRef,
}: {
  children: React.ReactNode;
  scrollRef: React.RefObject<HTMLDivElement | null>;
}) {
  return (
    <div
      ref={scrollRef}
      className="flex snap-x snap-mandatory gap-4 overflow-x-auto scroll-smooth pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
    >
      {children}
    </div>
  );
}

function ScrollControls({
  onLeft,
  onRight,
}: {
  onLeft: () => void;
  onRight: () => void;
}) {
  return (
    <div className="flex items-center gap-1">
      <Button
        type="button"
        variant="outline"
        size="icon"
        className="size-8 rounded-full shadow-sm"
        onClick={onLeft}
        aria-label="向左"
      >
        <ChevronLeft className="size-4" />
      </Button>
      <Button
        type="button"
        variant="outline"
        size="icon"
        className="size-8 rounded-full shadow-sm"
        onClick={onRight}
        aria-label="向右"
      >
        <ChevronRight className="size-4" />
      </Button>
    </div>
  );
}

export function AttractionCardList({
  initialAttractions,
  initialNextPageToken,
  city,
}: AttractionCardListProps) {
  const [attractions, setAttractions] =
    useState<Attraction[]>(initialAttractions);
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const nextPageTokenRef = useRef(initialNextPageToken);
  const sentinelRef = useRef<HTMLDivElement>(null);
  const carouselRef = useRef<HTMLDivElement>(null);
  const freeRef = useRef<HTMLDivElement>(null);

  const loadMore = useCallback(async () => {
    if (loading || !nextPageTokenRef.current) return;
    setLoading(true);
    try {
      const result = await loadMoreAttractionsByCity(
        city,
        nextPageTokenRef.current,
      );
      setAttractions((prev) => [...prev, ...result.attractions]);
      nextPageTokenRef.current = result.nextPageToken;
    } finally {
      setLoading(false);
    }
  }, [city, loading]);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) loadMore();
      },
      { rootMargin: "300px" },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [loadMore]);

  const hotAttractions = useMemo(
    () => attractions.filter((a) => !a.temporarilyClosed).slice(0, 9),
    [attractions],
  );

  const freeAttractions = useMemo(
    () =>
      attractions
        .filter((a) => {
          const p = a.ticketInfo?.estimatedPrice
            ? formatMoney(a.ticketInfo.estimatedPrice)
            : null;
          return p === null || p === 0;
        })
        .slice(0, 10),
    [attractions],
  );

  const filteredAttractions = useMemo(() => {
    if (selectedTags.size === 0) return attractions;
    return attractions.filter((a) => a.tags.some((t) => selectedTags.has(t)));
  }, [attractions, selectedTags]);

  const cards = filteredAttractions.map(attractionToCardData);
  const cityShort = city.replace("市", "");

  function scrollSection(
    ref: React.RefObject<HTMLDivElement | null>,
    dir: "left" | "right",
  ) {
    const el = ref.current;
    if (!el) return;
    const cardWidth =
      (el.firstElementChild as HTMLElement)?.offsetWidth ?? el.clientWidth / 2;
    el.scrollBy({
      left: dir === "left" ? -(cardWidth * 2) : cardWidth * 2,
      behavior: "smooth",
    });
  }

  function toggleTag(tag: string) {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) next.delete(tag);
      else next.add(tag);
      return next;
    });
  }

  return (
    <div className="flex flex-col gap-12">
      {hotAttractions.length > 0 && (
        <section className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Flame className="text-price size-5" />
              <h2 className="text-xl font-bold">热门景点</h2>
              <span className="text-muted-foreground text-sm">
                · {cityShort}必去
              </span>
            </div>
            <ScrollControls
              onLeft={() => scrollSection(carouselRef, "left")}
              onRight={() => scrollSection(carouselRef, "right")}
            />
          </div>

          <HorizontalScroll scrollRef={carouselRef}>
            {hotAttractions.map((a) => (
              <div
                key={a.id}
                className="w-full flex-none snap-start sm:w-[calc(50%-8px)] lg:w-[calc(33.333%-11px)]"
              >
                <HotCarouselCard attraction={a} />
              </div>
            ))}
          </HorizontalScroll>
        </section>
      )}

      {freeAttractions.length > 0 && (
        <section className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-success h-6 w-1 rounded-full" />
              <div className="flex items-center gap-2">
                <Ticket className="text-success size-5" />
                <h2 className="text-xl font-bold">免费畅游</h2>
              </div>
              <Badge className="bg-success/10 text-success">Free</Badge>
              <span className="text-muted-foreground hidden text-sm sm:inline">
                · 无需购票，随时出发
              </span>
            </div>
            <ScrollControls
              onLeft={() => scrollSection(freeRef, "left")}
              onRight={() => scrollSection(freeRef, "right")}
            />
          </div>

          <HorizontalScroll scrollRef={freeRef}>
            {freeAttractions.map((a) => (
              <div
                key={a.id}
                className="w-full flex-none snap-start sm:w-[calc(50%-8px)] lg:w-[calc(33.333%-11px)]"
              >
                <FreeAttractionCard attraction={a} />
              </div>
            ))}
          </HorizontalScroll>
        </section>
      )}

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <LayoutGrid className="text-primary size-5" />
            <h2 className="text-xl font-bold">按分类探索</h2>
          </div>
          <p className="text-muted-foreground text-sm">
            筛选你感兴趣的景点类型，发现更多精彩
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setSelectedTags(new Set())}
            className={cn(
              "rounded-full px-4 py-1.5 text-sm font-medium transition",
              selectedTags.size === 0
                ? "bg-primary text-primary-foreground shadow-sm"
                : "bg-muted text-muted-foreground hover:bg-primary/10 hover:text-primary",
            )}
          >
            全部
          </button>
          {CATEGORY_TAGS.map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => toggleTag(tag)}
              className={cn(
                "rounded-full px-4 py-1.5 text-sm font-medium transition",
                selectedTags.has(tag)
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-muted text-muted-foreground hover:bg-primary/10 hover:text-primary",
              )}
            >
              {tag}
            </button>
          ))}
        </div>

        {cards.length === 0 ? (
          <div className="text-muted-foreground flex flex-col items-center gap-3 py-20">
            <MapPin className="size-12 opacity-25" />
            <p className="text-sm">暂无符合条件的景点</p>
          </div>
        ) : (
          <div className="columns-2 gap-4 md:columns-3">
            {cards.map((a, idx) => (
              <div key={a.id} className="mb-4 break-inside-avoid">
                <AttractionCard attraction={a} index={idx} />
              </div>
            ))}
            {loading &&
              Array.from({ length: 3 }).map((_, i) => (
                <div key={`sk-${i}`} className="mb-4 break-inside-avoid">
                  <AttractionCardSkeleton index={cards.length + i} />
                </div>
              ))}
          </div>
        )}

        <div ref={sentinelRef} className="h-1" />

        {loading && cards.length > 0 && (
          <div className="flex justify-center py-6">
            <Loader2 className="text-primary size-5 animate-spin" />
          </div>
        )}
        {!nextPageTokenRef.current && cards.length > 0 && !loading && (
          <p className="text-muted-foreground text-center text-xs">
            已显示全部 {cards.length} 个景点
          </p>
        )}
      </section>
    </div>
  );
}
