import { Skeleton } from "@/components/ui/skeleton";

function SkeletonCard() {
  return (
    <div className="border-border overflow-hidden rounded-xl border">
      <Skeleton className="h-[58px] rounded-none" />
      <div className="flex items-center gap-2 px-4 py-2.5">
        <Skeleton className="h-3 flex-1 rounded-full" />
        <Skeleton className="h-6 w-16 rounded-lg" />
        <Skeleton className="h-6 w-10 rounded-lg" />
      </div>
    </div>
  );
}

export function ItineraryListSkeleton() {
  return (
    <div className="flex flex-col gap-2.5">
      {Array.from({ length: 3 }, (_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
