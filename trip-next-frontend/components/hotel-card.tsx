import Image from "next/image";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ImagePlaceholder } from "@/components/image-placeholder";
import { StarIcons } from "@/components/star-icons";

export interface HotelCardData {
  id: string;
  name: string;
  image: string | null;
  stars: number;
  rating: number | null;
  reviews: number;
  location: string;
  price: number;
}

export function HotelCard({ hotel }: { hotel: HotelCardData }) {
  return (
    <Link
      href={`/hotels/${hotel.id}`}
      className="group bg-card flex w-full flex-col overflow-hidden rounded-xl border"
    >
      {/* Image */}
      <div className="bg-muted relative aspect-[4/3] w-full overflow-hidden">
        {hotel.image ? (
          <Image
            src={hotel.image}
            alt={hotel.name}
            fill
            unoptimized
            className="object-cover transition-transform duration-300 group-hover:scale-105"
            sizes="(max-width: 768px) 100vw, 25vw"
          />
        ) : (
          <ImagePlaceholder className="h-full w-full" />
        )}
        {/* Rating overlay */}
        <div className="absolute bottom-2 left-2 flex items-center gap-1.5">
          {hotel.rating != null ? (
            <>
              <Badge className="rounded-md bg-blue-600 px-1.5 py-0.5 text-xs font-bold text-white">
                {hotel.rating}
              </Badge>
              <span className="text-xs font-medium text-white drop-shadow-md">
                {hotel.reviews}条点评
              </span>
            </>
          ) : (
            <span className="text-xs font-medium text-white drop-shadow-md">
              暂无评分
            </span>
          )}
        </div>
      </div>

      {/* Info */}
      <div className="flex flex-1 flex-col gap-1 p-3">
        <div className="flex items-center gap-1.5">
          <span className="text-foreground line-clamp-1 text-sm font-semibold">
            {hotel.name}
          </span>
          <StarIcons count={hotel.stars} />
        </div>
        <span className="text-muted-foreground line-clamp-1 text-xs">
          {hotel.location}
        </span>
        <div className="mt-auto flex items-baseline justify-end gap-1 pt-2">
          <span className="text-muted-foreground text-xs">最低价</span>
          <span className="text-lg font-bold text-orange-500">
            ¥{hotel.price.toLocaleString()}
          </span>
        </div>
      </div>
    </Link>
  );
}

export function HotelCardSkeleton() {
  return (
    <div className="bg-card flex w-full flex-col overflow-hidden rounded-xl border">
      <Skeleton className="aspect-[4/3] w-full rounded-none" />
      <div className="flex flex-1 flex-col gap-2 p-3">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <div className="mt-auto flex justify-end pt-2">
          <Skeleton className="h-5 w-16" />
        </div>
      </div>
    </div>
  );
}
