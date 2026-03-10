import Image from "next/image";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

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

function StarIcons({ count }: { count: number }) {
  return (
    <span className="inline-flex gap-0.5">
      {Array.from({ length: count }).map((_, i) => (
        <svg
          key={i}
          className="size-3 fill-amber-500"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path d="M12 2L9 9H2l6 5-2.5 8L12 17l6.5 5L16 14l6-5h-7z" />
        </svg>
      ))}
    </span>
  );
}

export function HotelCard({ hotel }: { hotel: HotelCardData }) {
  return (
    <Link
      href={`/hotels/${hotel.id}`}
      className="group flex w-full flex-col overflow-hidden rounded-xl border bg-white"
    >
      {/* Image */}
      <div className="relative aspect-[4/3] w-full overflow-hidden bg-gray-100">
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
          <div className="flex h-full w-full items-center justify-center text-gray-300">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="size-12"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M9 22V12h6v10"
              />
            </svg>
          </div>
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
          <span className="line-clamp-1 text-sm font-semibold text-gray-900">
            {hotel.name}
          </span>
          <StarIcons count={hotel.stars} />
        </div>
        <span className="text-muted-foreground line-clamp-1 text-xs">
          {hotel.location}
        </span>
        <div className="mt-auto flex items-baseline justify-end gap-1 pt-2">
          <span className="text-xs text-gray-500">最低价</span>
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
    <div className="flex w-full flex-col overflow-hidden rounded-xl border bg-white">
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
