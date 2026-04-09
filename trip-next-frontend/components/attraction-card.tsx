import Image from "next/image";
import Link from "next/link";
import { Clock, MapPin } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ImagePlaceholder } from "@/components/image-placeholder";
import { formatMoney, formatRecommendTime } from "@/lib/format";
import type { Attraction } from "@/lib/grpc/generated/tripsphere/attraction/v1/attraction";

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
  const visitTime = formatRecommendTime(
    attraction.minHours,
    attraction.maxHours,
  );

  return (
    <Link
      href={`/attractions/${attraction.id}`}
      className="group bg-card block w-full overflow-hidden rounded-2xl shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl"
    >
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

        <div className="absolute inset-0 bg-gradient-to-t from-black/10 via-black/5 to-transparent" />

        {attraction.tags.length > 0 && (
          <div className="absolute top-2.5 left-2.5 flex flex-wrap gap-1">
            {attraction.tags.map((tag) => (
              <Badge
                key={tag}
                className="bg-primary/85 text-primary-foreground backdrop-blur-sm"
              >
                {tag}
              </Badge>
            ))}
          </div>
        )}

        {attraction.temporarilyClosed && (
          <Badge
            variant="destructive"
            className="absolute top-2.5 right-2.5 backdrop-blur-sm"
          >
            暂停开放
          </Badge>
        )}

        <div className="absolute right-0 bottom-0 left-0 p-3">
          <h3 className="line-clamp-2 text-sm leading-snug font-bold text-white drop-shadow-md">
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

      <div className="flex items-center justify-between px-3 py-2.5">
        {visitTime ? (
          <div className="text-primary flex items-center gap-1">
            <Clock className="h-3 w-3 shrink-0" />
            <span className="text-[11px] font-medium">{visitTime}</span>
          </div>
        ) : (
          <span className="text-muted-foreground text-[11px]">景点</span>
        )}

        {attraction.price != null && attraction.price > 0 ? (
          <div className="flex items-baseline gap-0.5">
            <span className="text-muted-foreground text-[10px]">¥</span>
            <span className="text-price text-sm font-bold">
              {attraction.price.toLocaleString()}
            </span>
          </div>
        ) : (
          <Badge variant="secondary" className="bg-success/10 text-success">
            免费
          </Badge>
        )}
      </div>
    </Link>
  );
}

export function AttractionCardSkeleton({ index = 0 }: { index?: number }) {
  const imageClass = IMAGE_ASPECT_CLASSES[index % IMAGE_ASPECT_CLASSES.length];
  return (
    <div className="bg-card w-full overflow-hidden rounded-2xl shadow-sm">
      <Skeleton className={`${imageClass} w-full rounded-none`} />
      <div className="flex items-center justify-between px-3 py-2.5">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-4 w-12" />
      </div>
    </div>
  );
}
