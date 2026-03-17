import { Skeleton } from "@/components/ui/skeleton";

export default function HotelDetailLoading() {
  return (
    <div className="flex flex-col gap-6">
      {/* Breadcrumb skeleton */}
      <div className="flex items-center gap-2">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-4" />
        <Skeleton className="h-4 w-12" />
        <Skeleton className="h-4 w-4" />
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-4" />
        <Skeleton className="h-4 w-32" />
      </div>

      {/* Hotel Header Card skeleton */}
      <div className="bg-card rounded-xl border p-6">
        {/* Title Row */}
        <div className="mb-4 flex items-start justify-between">
          <div className="space-y-2">
            <Skeleton className="h-7 w-64" />
            <Skeleton className="h-4 w-48" />
            <div className="flex gap-2">
              <Skeleton className="h-5 w-16 rounded-md" />
              <Skeleton className="h-5 w-16 rounded-md" />
              <Skeleton className="h-5 w-16 rounded-md" />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-9 w-24 rounded-md" />
          </div>
        </div>

        {/* Image Gallery skeleton */}
        <div className="grid grid-cols-4 gap-2">
          <Skeleton className="col-span-2 row-span-2 aspect-[4/3] rounded-lg" />
          <Skeleton className="aspect-[4/3] rounded-lg" />
          <Skeleton className="aspect-[4/3] rounded-lg" />
          <Skeleton className="aspect-[4/3] rounded-lg" />
          <Skeleton className="aspect-[4/3] rounded-lg" />
        </div>

        {/* Hotel Info skeleton */}
        <div className="mt-6 grid grid-cols-3 gap-8">
          <div className="col-span-2 space-y-6">
            <div className="space-y-3">
              <Skeleton className="h-5 w-24" />
              <div className="grid grid-cols-4 gap-3">
                {Array.from({ length: 8 }).map((_, i) => (
                  <Skeleton key={i} className="h-5 w-full" />
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <Skeleton className="h-5 w-24" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          </div>
          <div className="space-y-4">
            <Skeleton className="h-40 w-full rounded-lg" />
            <Skeleton className="h-32 w-full rounded-lg" />
          </div>
        </div>
      </div>

      {/* Room Selection Section skeleton */}
      <div className="bg-card rounded-xl border">
        <div className="border-b px-6 pt-4 pb-3">
          <div className="flex gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-16" />
            ))}
          </div>
        </div>
        <div className="space-y-6 p-6">
          {Array.from({ length: 2 }).map((_, i) => (
            <Skeleton key={i} className="h-64 w-full rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}
