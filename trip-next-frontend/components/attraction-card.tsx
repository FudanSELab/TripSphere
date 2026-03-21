import Image from "next/image";
import Link from "next/link";
import { Clock, MapPin } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { ImagePlaceholder } from "@/components/image-placeholder";
import { formatMoney } from "@/lib/format";
import type { Attraction } from "@/lib/grpc/generated/tripsphere/attraction/v1/attraction";

// Cycle of image heights to create natural masonry variety
const IMAGE_ASPECT_CLASSES = [
  "aspect-[3/4]",
  "aspect-[2/3]",
  "aspect-[3/4]",
  "aspect-[4/5]",
  "aspect-[2/3]",
  "aspect-[3/4]",
] as const;

export interface AttractionCardData {
  id: string;
  name: string;
  image: string | null;
  tags: string[];
  district: string;
  price: number | null;
  minHours: number;
  maxHours: number;
  temporarilyClosed: boolean;
  introduction: string;
}

export function attractionToCardData(a: Attraction): AttractionCardData {
  return {
    id: a.id,
    name: a.name,
    image: a.images[0] ?? null,
    tags: a.tags.slice(0, 3),
    district: a.address?.district ?? a.address?.city ?? "",
    price: a.ticketInfo?.estimatedPrice
      ? formatMoney(a.ticketInfo.estimatedPrice)
      : null,
    minHours: a.recommendTime?.minHours ?? 0,
    maxHours: a.recommendTime?.maxHours ?? 0,
    temporarilyClosed: a.temporarilyClosed,
    introduction: a.introduction,
  };
}

interface AttractionCardProps {
  attraction: AttractionCardData;
  index?: number;
}

export function AttractionCard({ attraction, index = 0 }: AttractionCardProps) {
  const imageClass = IMAGE_ASPECT_CLASSES[index % IMAGE_ASPECT_CLASSES.length];

  return (
    <Link
      href={`/attractions/${attraction.id}`}
      className="group block w-full overflow-hidden rounded-2xl bg-card shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl"
    >
      {/* Image container with variable height */}
      <div className={`relative ${imageClass} w-full overflow-hidden`}>
        {attraction.image ? (
          <Image
            src={attraction.image}
            alt={attraction.name}
            fill
            unoptimized
            className="object-cover transition-transform duration-500 group-hover:scale-105"
            sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
          />
        ) : (
          <ImagePlaceholder className="h-full w-full" />
        )}

        {/* Gradient overlay — stronger at bottom */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/15 to-transparent" />

        {/* Tags — top left */}
        {attraction.tags.length > 0 && (
          <div className="absolute left-2.5 top-2.5 flex flex-wrap gap-1">
            {attraction.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-teal-500/85 px-2 py-0.5 text-[10px] font-semibold text-white backdrop-blur-sm"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Temporarily closed badge — top right */}
        {attraction.temporarilyClosed && (
          <span className="absolute right-2.5 top-2.5 rounded-full bg-red-500/90 px-2 py-0.5 text-[10px] font-semibold text-white backdrop-blur-sm">
            暂停开放
          </span>
        )}

        {/* Name + district on image bottom */}
        <div className="absolute bottom-0 left-0 right-0 p-3">
          <h3 className="line-clamp-2 text-sm font-bold leading-snug text-white drop-shadow-md">
            {attraction.name}
          </h3>
          {attraction.district && (
            <div className="mt-0.5 flex items-center gap-0.5 text-white/80">
              <MapPin className="h-2.5 w-2.5 shrink-0" />
              <span className="text-[11px]">{attraction.district}</span>
            </div>
          )}
        </div>
      </div>

      {/* Footer — visit time + price */}
      <div className="flex items-center justify-between px-3 py-2.5">
        {attraction.minHours > 0 || attraction.maxHours > 0 ? (
          <div className="flex items-center gap-1 text-teal-600">
            <Clock className="h-3 w-3 shrink-0" />
            <span className="text-[11px] font-medium">
              {attraction.minHours > 0 && attraction.maxHours > 0
                ? `${attraction.minHours}–${attraction.maxHours}h`
                : `${attraction.maxHours || attraction.minHours}h`}
            </span>
          </div>
        ) : (
          <span className="text-[11px] text-muted-foreground">景点</span>
        )}

        {attraction.price != null && attraction.price > 0 ? (
          <div className="flex items-baseline gap-0.5">
            <span className="text-[10px] text-muted-foreground">¥</span>
            <span className="text-sm font-bold text-orange-500">
              {attraction.price.toLocaleString()}
            </span>
          </div>
        ) : (
          <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-600">
            免费
          </span>
        )}
      </div>
    </Link>
  );
}

export function AttractionCardSkeleton({ index = 0 }: { index?: number }) {
  const imageClass = IMAGE_ASPECT_CLASSES[index % IMAGE_ASPECT_CLASSES.length];
  return (
    <div className="w-full overflow-hidden rounded-2xl bg-card shadow-sm">
      <Skeleton className={`${imageClass} w-full rounded-none`} />
      <div className="flex items-center justify-between px-3 py-2.5">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-4 w-12" />
      </div>
    </div>
  );
}
