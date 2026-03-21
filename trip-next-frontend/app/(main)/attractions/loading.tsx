import { Skeleton } from "@/components/ui/skeleton";
import { AttractionCardSkeleton } from "@/components/attraction-card";

export default function AttractionLoading() {
  return (
    <div className="flex flex-col gap-10">
      {/* Hero skeleton */}
      <Skeleton className="h-48 w-full rounded-2xl" />

      <div className="flex flex-col gap-4">
        <Skeleton className="h-8 w-32" />

        {/* Tab list skeleton */}
        <div className="flex gap-4 border-b pb-2">
          <Skeleton className="h-6 w-12" />
          <Skeleton className="h-6 w-12" />
          <Skeleton className="h-6 w-12" />
        </div>

        {/* Filter chips skeleton */}
        <div className="flex gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-7 w-16 rounded-full" />
          ))}
        </div>

        {/* Masonry skeleton */}
        <div className="columns-2 gap-4 md:columns-3 lg:columns-3 xl:columns-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="mb-4 break-inside-avoid">
              <AttractionCardSkeleton index={i} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
