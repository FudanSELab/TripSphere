import Image from "next/image";
import Link from "next/link";
import { MapPin, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ImagePlaceholder } from "@/components/image-placeholder";
import { getAttractionsNearby } from "@/lib/data/attraction";
import { formatMoney } from "@/lib/format";
import type { GeoPoint } from "@/lib/grpc/generated/tripsphere/common/v1/map";

interface NearbyAttractionsProps {
  currentId: string;
  location: GeoPoint;
  radiusMeters?: number;
}

export async function NearbyAttractions({
  currentId,
  location,
  radiusMeters = 5000,
}: NearbyAttractionsProps) {
  const attractions = await getAttractionsNearby(location, radiusMeters);
  const nearby = attractions.filter((a) => a.id !== currentId).slice(0, 6);

  if (nearby.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <MapPin className="h-4 w-4 text-teal-600" />
          周边景点推荐
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {nearby.map((a) => {
          const price = a.ticketInfo?.estimatedPrice
            ? formatMoney(a.ticketInfo.estimatedPrice)
            : null;
          return (
            <Link
              key={a.id}
              href={`/attractions/${a.id}`}
              className="group flex items-center gap-3"
            >
              <div className="relative h-14 w-14 shrink-0 overflow-hidden rounded-lg bg-muted">
                {a.images[0] ? (
                  <Image
                    src={a.images[0]}
                    alt={a.name}
                    fill
                    unoptimized
                    className="object-cover transition-transform duration-200 group-hover:scale-105"
                  />
                ) : (
                  <ImagePlaceholder
                    className="h-full w-full"
                    iconClassName="h-5 w-5"
                  />
                )}
              </div>
              <div className="flex flex-1 flex-col gap-0.5 overflow-hidden">
                <span className="line-clamp-1 text-xs font-semibold text-foreground group-hover:text-teal-700">
                  {a.name}
                </span>
                <span className="line-clamp-1 text-[10px] text-muted-foreground">
                  {a.address?.district || a.address?.city}
                </span>
                <div className="flex items-center gap-2">
                  {(a.recommendTime?.minHours || a.recommendTime?.maxHours) ? (
                    <span className="flex items-center gap-0.5 text-[10px] text-teal-600">
                      <Clock className="h-2.5 w-2.5" />
                      {a.recommendTime!.minHours > 0 &&
                      a.recommendTime!.maxHours > 0
                        ? `${a.recommendTime!.minHours}–${a.recommendTime!.maxHours}h`
                        : `${a.recommendTime!.maxHours || a.recommendTime!.minHours}h`}
                    </span>
                  ) : null}
                  {price != null && (
                    <span className="text-[10px] font-bold text-orange-500">
                      {price > 0 ? `¥${price}` : "免费"}
                    </span>
                  )}
                </div>
              </div>
            </Link>
          );
        })}
      </CardContent>
    </Card>
  );
}

export function NearbyAttractionsSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <MapPin className="h-4 w-4 text-teal-600" />
          周边景点推荐
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-14 w-14 rounded-lg" />
            <div className="flex flex-1 flex-col gap-1.5">
              <Skeleton className="h-3 w-3/4" />
              <Skeleton className="h-2.5 w-1/2" />
              <Skeleton className="h-2.5 w-1/3" />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
