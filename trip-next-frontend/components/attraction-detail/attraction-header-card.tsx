import Image from "next/image";
import Link from "next/link";
import {
  MapPin,
  Clock,
  Tag,
  ExternalLink,
  Ticket,
  AlertCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ImagePlaceholder } from "@/components/image-placeholder";
import { formatMoney } from "@/lib/format";
import type { Attraction } from "@/lib/grpc/generated/tripsphere/attraction/v1/attraction";

interface AttractionHeaderCardProps {
  attraction: Attraction;
}

export function AttractionHeaderCard({
  attraction,
}: AttractionHeaderCardProps) {
  const images = attraction.images.slice(0, 5);
  const price = attraction.ticketInfo?.estimatedPrice
    ? formatMoney(attraction.ticketInfo.estimatedPrice)
    : null;
  const fullAddress = [
    attraction.address?.province,
    attraction.address?.city,
    attraction.address?.district,
    attraction.address?.detailed,
  ]
    .filter(Boolean)
    .join("");

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      {/* Image gallery */}
      <div className="flex-1">
        {images.length === 0 ? (
          <div className="aspect-video w-full overflow-hidden rounded-2xl">
            <ImagePlaceholder className="h-full w-full" />
          </div>
        ) : images.length === 1 ? (
          <div className="relative aspect-video w-full overflow-hidden rounded-2xl">
            <Image
              src={images[0]}
              alt={attraction.name}
              fill
              unoptimized
              className="object-cover"
              priority
            />
          </div>
        ) : (
          <div className="grid h-72 grid-cols-4 grid-rows-2 gap-2 overflow-hidden rounded-2xl lg:h-96">
            {/* Main large image */}
            <div className="relative col-span-2 row-span-2 overflow-hidden">
              <Image
                src={images[0]}
                alt={attraction.name}
                fill
                unoptimized
                className="object-cover"
                priority
              />
            </div>
            {/* Side images */}
            {images.slice(1, 5).map((img, i) => (
              <div key={i} className="relative overflow-hidden">
                <Image
                  src={img}
                  alt={`${attraction.name} ${i + 2}`}
                  fill
                  unoptimized
                  className="object-cover"
                />
              </div>
            ))}
            {/* Fill remaining slots with placeholder */}
            {Array.from({ length: Math.max(0, 4 - (images.length - 1)) }).map(
              (_, i) => (
                <div key={`placeholder-${i}`} className="overflow-hidden">
                  <ImagePlaceholder className="h-full w-full" />
                </div>
              ),
            )}
          </div>
        )}
      </div>

      {/* Info card */}
      <div className="flex w-full flex-col gap-4 lg:w-72">
        <div>
          {/* Temporarily closed alert */}
          {attraction.temporarilyClosed && (
            <div className="mb-3 flex items-center gap-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>该景点暂停开放</span>
            </div>
          )}

          {/* Tags */}
          <div className="mb-2 flex flex-wrap gap-1.5">
            {attraction.tags.map((tag) => (
              <Badge
                key={tag}
                className="bg-teal-50 text-teal-700 hover:bg-teal-100 border-teal-200"
                variant="outline"
              >
                <Tag className="mr-1 h-2.5 w-2.5" />
                {tag}
              </Badge>
            ))}
          </div>

          <h1 className="text-2xl font-bold text-foreground">
            {attraction.name}
          </h1>

          {/* Address */}
          {fullAddress && (
            <div className="mt-2 flex items-start gap-1.5 text-sm text-muted-foreground">
              <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-teal-600" />
              <span className="line-clamp-2">{fullAddress}</span>
            </div>
          )}

          {/* Recommend time */}
          {(attraction.recommendTime?.minHours ||
            attraction.recommendTime?.maxHours) && (
            <div className="mt-2 flex items-center gap-1.5 text-sm">
              <Clock className="h-4 w-4 shrink-0 text-teal-600" />
              <span className="text-teal-700 font-medium">
                建议游览{" "}
                {attraction.recommendTime!.minHours > 0 &&
                attraction.recommendTime!.maxHours > 0
                  ? `${attraction.recommendTime!.minHours}–${attraction.recommendTime!.maxHours} 小时`
                  : `${attraction.recommendTime!.maxHours || attraction.recommendTime!.minHours} 小时`}
              </span>
            </div>
          )}
        </div>

        {/* Ticket price */}
        <div className="rounded-xl border bg-card p-4">
          {price != null ? (
            price > 0 ? (
              <>
                <p className="text-xs text-muted-foreground">参考票价（成人）</p>
                <p className="mt-1 text-3xl font-bold text-orange-500">
                  ¥{price.toLocaleString()}
                </p>
              </>
            ) : (
              <>
                <p className="text-xs text-muted-foreground">门票</p>
                <p className="mt-1 text-2xl font-bold text-emerald-600">免费</p>
              </>
            )
          ) : (
            <>
              <p className="text-xs text-muted-foreground">门票</p>
              <p className="mt-1 text-sm text-muted-foreground">价格待查</p>
            </>
          )}
          <Button
            className="mt-3 w-full bg-teal-600 font-semibold text-white hover:bg-teal-700"
            disabled={attraction.temporarilyClosed}
          >
            <Ticket className="mr-2 h-4 w-4" />
            {attraction.temporarilyClosed ? "暂停开放" : "立即购票"}
          </Button>
        </div>

        {/* Map link */}
        {attraction.location && (
          <Link
            href={`https://maps.google.com/?q=${attraction.location.latitude},${attraction.location.longitude}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-sm text-teal-600 hover:text-teal-800 hover:underline"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            在地图中查看
          </Link>
        )}
      </div>
    </div>
  );
}
