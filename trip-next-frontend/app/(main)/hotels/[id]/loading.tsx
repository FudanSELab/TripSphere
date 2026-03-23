import { Skeleton } from "@/components/ui/skeleton";
import { RoomListSkeleton } from "@/components/hotel-detail/hotel-room-list";

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
          <div className="flex flex-col gap-2">
            <Skeleton className="h-7 w-64" />
            <Skeleton className="h-4 w-48" />
            <div className="flex gap-2">
              <Skeleton className="h-5 w-16 rounded-md" />
              <Skeleton className="h-5 w-16 rounded-md" />
              <Skeleton className="h-5 w-16 rounded-md" />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex flex-col items-end gap-1">
              <Skeleton className="h-8 w-24" />
              <Skeleton className="h-4 w-8" />
            </div>
            <Skeleton className="h-9 w-28 rounded-md" />
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
      </div>

      <div className="bg-card rounded-xl border">
        <div className="border-b px-6 pt-4">
          <div className="flex gap-6">
            <Skeleton className="h-8 w-14" />
            <Skeleton className="h-8 w-12" />
            <Skeleton className="h-8 w-12" />
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-8 w-12" />
            <Skeleton className="h-8 w-12" />
          </div>
        </div>
        <div className="px-6 py-4">
          <RoomListSkeleton />
        </div>
      </div>
    </div>
  );
}
