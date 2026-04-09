import Image from "next/image";
import Link from "next/link";
import { MapPin, Clock, ExternalLink, Ticket, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ImagePlaceholder } from "@/components/image-placeholder";
import { formatMoney, formatRecommendTime } from "@/lib/format";
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
  const visitTime = formatRecommendTime(
    attraction.recommendTime?.minHours,
    attraction.recommendTime?.maxHours,
    " 小时",
  );

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
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

      <div className="flex w-full flex-col gap-4 lg:w-[300px]">
        <div className="flex flex-col gap-2">
          {attraction.temporarilyClosed && (
            <Alert variant="destructive">
              <AlertCircle className="size-4" />
              <AlertDescription>该景点暂停开放</AlertDescription>
            </Alert>
          )}

          <div className="flex flex-wrap gap-1.5">
            {attraction.tags.map((tag) => (
              <Badge key={tag} variant="secondary">
                {tag}
              </Badge>
            ))}
          </div>

          <h1 className="text-foreground text-2xl font-bold">
            {attraction.name}
          </h1>

          {fullAddress && (
            <div className="text-muted-foreground flex items-start gap-1.5 text-sm">
              <MapPin className="text-primary mt-0.5 size-4 shrink-0" />
              <span className="line-clamp-2">{fullAddress}</span>
            </div>
          )}

          {visitTime && (
            <div className="text-primary flex items-center gap-1.5 text-sm">
              <Clock className="size-4 shrink-0" />
              <span className="font-medium">建议游览 {visitTime}</span>
            </div>
          )}
        </div>

        <div className="bg-card flex flex-col gap-3 rounded-xl border p-4">
          {price != null ? (
            price > 0 ? (
              <>
                <p className="text-muted-foreground text-xs">
                  参考票价（成人）
                </p>
                <p className="text-price mt-1 text-3xl font-bold">
                  ¥{price.toLocaleString()}
                </p>
              </>
            ) : (
              <>
                <p className="text-muted-foreground text-xs">门票</p>
                <p className="text-success mt-1 text-2xl font-bold">免费</p>
              </>
            )
          ) : (
            <>
              <p className="text-muted-foreground text-xs">门票</p>
              <p className="text-muted-foreground mt-1 text-sm">价格待查</p>
            </>
          )}
          <Button
            className="w-full font-semibold"
            disabled={attraction.temporarilyClosed}
          >
            <Ticket className="size-4" data-icon="inline-start" />
            {attraction.temporarilyClosed ? "暂停开放" : "立即购票"}
          </Button>
        </div>

        {attraction.location && (
          <Link
            href={`https://maps.google.com/?q=${attraction.location.latitude},${attraction.location.longitude}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:text-primary/80 flex items-center gap-1.5 text-sm hover:underline"
          >
            <ExternalLink className="size-3.5" />
            在地图中查看
          </Link>
        )}
      </div>
    </div>
  );
}
