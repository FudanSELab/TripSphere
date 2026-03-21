"use client";

import {
  useState,
  useMemo,
  useRef,
  useEffect,
  useCallback,
} from "react";
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
import { ImagePlaceholder } from "@/components/image-placeholder";
import {
  AttractionCard,
  AttractionCardSkeleton,
  attractionToCardData,
} from "@/components/attraction-card";
import { listAttractionsByCity } from "@/actions/attraction";
import { formatMoney } from "@/lib/format";
import type { Attraction } from "@/lib/grpc/generated/tripsphere/attraction/v1/attraction";

// Corrected from itinerary.py
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

// ─── Section 1: Cinematic carousel card ─────────────────────────────────────

function HotCarouselCard({ attraction }: { attraction: Attraction }) {
  const price = attraction.ticketInfo?.estimatedPrice
    ? formatMoney(attraction.ticketInfo.estimatedPrice)
    : null;
  const district =
    attraction.address?.district ?? attraction.address?.city ?? "";

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

      {/* Full dark cinematic overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-black/10" />

      {/* Hot badge */}
      <span className="absolute left-3 top-3 flex items-center gap-1 rounded-full bg-orange-500 px-2.5 py-1 text-[11px] font-bold text-white shadow-md">
        <Flame className="h-3 w-3" />
        人气热门
      </span>

      {/* Tags */}
      {attraction.tags.length > 0 && (
        <div className="absolute right-3 top-3 flex flex-wrap justify-end gap-1">
          {attraction.tags.slice(0, 2).map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-white/20 px-2 py-0.5 text-[10px] font-medium text-white backdrop-blur-sm"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Bottom content */}
      <div className="absolute bottom-0 left-0 right-0 p-4">
        <h3 className="line-clamp-2 text-base font-bold leading-snug text-white drop-shadow-lg sm:text-lg">
          {attraction.name}
        </h3>
        {district && (
          <div className="mt-1 flex items-center gap-1 text-white/75">
            <MapPin className="h-3 w-3 shrink-0" />
            <span className="text-xs">{district}</span>
          </div>
        )}
        <div className="mt-2 flex items-center gap-3">
          {(attraction.recommendTime?.minHours || attraction.recommendTime?.maxHours) && (
            <div className="flex items-center gap-1 text-white/80">
              <Clock className="h-3 w-3" />
              <span className="text-xs">
                {attraction.recommendTime!.minHours > 0 &&
                attraction.recommendTime!.maxHours > 0
                  ? `${attraction.recommendTime!.minHours}–${attraction.recommendTime!.maxHours}h`
                  : `${attraction.recommendTime!.maxHours || attraction.recommendTime!.minHours}h`}
              </span>
            </div>
          )}
          {price != null ? (
            <span className="rounded-full bg-orange-500/90 px-2.5 py-0.5 text-xs font-bold text-white">
              ¥{price.toLocaleString()}
            </span>
          ) : (
            <span className="rounded-full bg-emerald-500/90 px-2.5 py-0.5 text-xs font-bold text-white">
              免费
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}

// ─── Section 2: Free row card ────────────────────────────────────────────────

function FreeAttractionCard({ attraction }: { attraction: Attraction }) {
  const district =
    attraction.address?.district ?? attraction.address?.city ?? "";
  const recommendTime = attraction.recommendTime;

  return (
    <Link
      href={`/attractions/${attraction.id}`}
      className="group block w-full overflow-hidden rounded-2xl border-2 border-emerald-100 bg-card transition-all duration-300 hover:border-emerald-400 hover:shadow-lg"
    >
      {/* Image — same aspect-video ratio as hot carousel for visual alignment */}
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
        {/* Light-to-transparent overlay (visually lighter than cinematic hot section) */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-black/5 to-transparent" />

        {/* FREE badge — top left */}
        <span className="absolute left-3 top-3 flex items-center gap-1 rounded-full bg-emerald-500 px-2.5 py-1 text-[11px] font-bold text-white shadow-md">
          <Ticket className="h-3 w-3" />
          免费
        </span>

        {/* Tags — top right */}
        {attraction.tags.length > 0 && (
          <div className="absolute right-3 top-3 flex flex-wrap justify-end gap-1">
            {attraction.tags.slice(0, 2).map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-white/25 px-2 py-0.5 text-[10px] font-medium text-white backdrop-blur-sm"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Footer — name, district, visit time */}
      <div className="p-3">
        <h3 className="line-clamp-1 text-sm font-semibold text-foreground group-hover:text-emerald-700">
          {attraction.name}
        </h3>
        <div className="mt-1 flex items-center justify-between">
          {district && (
            <div className="flex items-center gap-0.5 text-muted-foreground">
              <MapPin className="h-3 w-3 shrink-0" />
              <span className="text-xs line-clamp-1">{district}</span>
            </div>
          )}
          {(recommendTime?.minHours || recommendTime?.maxHours) && (
            <div className="flex shrink-0 items-center gap-1 text-emerald-600">
              <Clock className="h-3 w-3" />
              <span className="text-xs font-medium">
                {recommendTime!.minHours > 0 && recommendTime!.maxHours > 0
                  ? `${recommendTime!.minHours}–${recommendTime!.maxHours}h`
                  : `${recommendTime!.maxHours || recommendTime!.minHours}h`}
              </span>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}

// ─── Main component ──────────────────────────────────────────────────────────

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

  // ── Infinite scroll ──────────────────────────────────────────────────────
  const loadMore = useCallback(async () => {
    if (loading || !nextPageTokenRef.current) return;
    setLoading(true);
    try {
      const result = await listAttractionsByCity(
        city,
        undefined,
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

  // ── Derived data ─────────────────────────────────────────────────────────
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

  // ── Shared scroll helper — advances 2 cards per click ───────────────────
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

  // ── Tag filter ───────────────────────────────────────────────────────────
  function toggleTag(tag: string) {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) next.delete(tag);
      else next.add(tag);
      return next;
    });
  }

  const cityShort = city.replace("市", "");

  return (
    <div className="flex flex-col gap-12">
      {/* ════════════════════════════════════════════════════════════════════
          Section 1 — Hot Attractions Carousel
      ════════════════════════════════════════════════════════════════════ */}
      {hotAttractions.length > 0 && (
        <section className="flex flex-col gap-4">
          {/* Section header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Flame className="h-5 w-5 text-orange-500" />
              <h2 className="text-xl font-bold">热门景点</h2>
              <span className="text-sm text-muted-foreground">
                · {cityShort}必去
              </span>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => scrollSection(carouselRef, "left")}
                className="flex h-8 w-8 items-center justify-center rounded-full border bg-card shadow-sm transition hover:bg-muted"
                aria-label="向左"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => scrollSection(carouselRef, "right")}
                className="flex h-8 w-8 items-center justify-center rounded-full border bg-card shadow-sm transition hover:bg-muted"
                aria-label="向右"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Carousel strip */}
          <div
            ref={carouselRef}
            className="flex gap-4 overflow-x-auto scroll-smooth snap-x snap-mandatory pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          >
            {hotAttractions.map((a) => (
              <div
                key={a.id}
                className="flex-none snap-start w-full sm:w-[calc(50%-8px)] lg:w-[calc(33.333%-11px)]"
              >
                <HotCarouselCard attraction={a} />
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          Section 2 — Free Attractions Row
      ════════════════════════════════════════════════════════════════════ */}
      {freeAttractions.length > 0 && (
        <section className="flex flex-col gap-4">
          {/* Section header with emerald accent + arrows */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-6 w-1 rounded-full bg-emerald-500" />
              <div className="flex items-center gap-2">
                <Ticket className="h-5 w-5 text-emerald-600" />
                <h2 className="text-xl font-bold">免费畅游</h2>
              </div>
              <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
                Free
              </span>
              <span className="hidden text-sm text-muted-foreground sm:inline">
                · 无需购票，随时出发
              </span>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => scrollSection(freeRef, "left")}
                className="flex h-8 w-8 items-center justify-center rounded-full border bg-card shadow-sm transition hover:bg-muted"
                aria-label="向左"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => scrollSection(freeRef, "right")}
                className="flex h-8 w-8 items-center justify-center rounded-full border bg-card shadow-sm transition hover:bg-muted"
                aria-label="向右"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Horizontal snap scroll */}
          <div
            ref={freeRef}
            className="flex gap-4 overflow-x-auto scroll-smooth snap-x snap-mandatory pb-2 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          >
            {freeAttractions.map((a) => (
              <div
                key={a.id}
                className="flex-none snap-start w-full sm:w-[calc(50%-8px)] lg:w-[calc(33.333%-11px)]"
              >
                <FreeAttractionCard attraction={a} />
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          Section 3 — Browse by Category (Masonry)
      ════════════════════════════════════════════════════════════════════ */}
      <section className="flex flex-col gap-4">
        {/* Section header */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <LayoutGrid className="h-5 w-5 text-teal-600" />
            <h2 className="text-xl font-bold">按分类探索</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            筛选你感兴趣的景点类型，发现更多精彩
          </p>
        </div>

        {/* Tag filter chips */}
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setSelectedTags(new Set())}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
              selectedTags.size === 0
                ? "bg-teal-600 text-white shadow-sm"
                : "bg-muted text-muted-foreground hover:bg-teal-50 hover:text-teal-700"
            }`}
          >
            全部
          </button>
          {CATEGORY_TAGS.map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => toggleTag(tag)}
              className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
                selectedTags.has(tag)
                  ? "bg-teal-600 text-white shadow-sm"
                  : "bg-muted text-muted-foreground hover:bg-teal-50 hover:text-teal-700"
              }`}
            >
              {tag}
            </button>
          ))}
        </div>

        {/* Masonry waterfall — 3 columns max */}
        {cards.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-20 text-muted-foreground">
            <MapPin className="h-12 w-12 opacity-25" />
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

        {/* Infinite scroll sentinel */}
        <div ref={sentinelRef} className="h-1" />

        {/* End / loading states */}
        {loading && cards.length > 0 && (
          <div className="flex justify-center py-6">
            <Loader2 className="h-5 w-5 animate-spin text-teal-600" />
          </div>
        )}
        {!nextPageTokenRef.current && cards.length > 0 && !loading && (
          <p className="text-center text-xs text-muted-foreground">
            已显示全部 {cards.length} 个景点
          </p>
        )}
      </section>
    </div>
  );
}
