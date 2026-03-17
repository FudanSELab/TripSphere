import { Skeleton } from "@/components/ui/skeleton";
import { HotelCardSkeleton } from "@/components/hotel-card";

export default function HotelPageLoading() {
  return (
    <div className="flex flex-col gap-10">
      {/* Hero Search Skeleton */}
      <Skeleton className="h-[220px] w-full rounded-2xl" />

      {/* Hotel Recommendations Skeleton */}
      <section className="flex flex-col gap-4">
        <Skeleton className="h-8 w-32" />

        {/* Tabs skeleton */}
        <div className="mb-2 flex gap-4">
          <Skeleton className="h-8 w-14" />
          <Skeleton className="h-8 w-14" />
          <Skeleton className="h-8 w-14" />
        </div>

        {/* Hotel card grid skeleton */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <HotelCardSkeleton key={i} />
          ))}
        </div>
      </section>
    </div>
  );
}
