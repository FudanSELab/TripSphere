import { Skeleton } from "@/components/ui/skeleton";

export default function AttractionDetailLoading() {
  return (
    <div className="flex flex-col gap-6">
      {/* Breadcrumb skeleton */}
      <Skeleton className="h-4 w-64" />

      {/* Header card skeleton - match attraction-header-card image area */}
      <div className="flex flex-col gap-6 lg:flex-row">
        <div className="min-w-0 flex-1">
          <Skeleton className="aspect-video w-full rounded-2xl" />
        </div>
        <div className="flex w-full flex-col gap-4 lg:w-[300px]">
          <div className="flex flex-col gap-2">
            <div className="flex gap-2">
              <Skeleton className="h-6 w-16 rounded-full" />
              <Skeleton className="h-6 w-16 rounded-full" />
            </div>
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-1/2" />
          </div>
          <div className="flex flex-col gap-3 rounded-xl border p-4">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-9 w-32" />
            <Skeleton className="h-10 w-full rounded-lg" />
          </div>
          <Skeleton className="h-4 w-32" />
        </div>
      </div>

      {/* Two-column section skeleton */}
      <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
        <div className="flex flex-col gap-4 rounded-xl border p-6">
          {/* Tabs skeleton */}
          <div className="flex gap-6 border-b pb-4">
            {["简介", "开放时间", "交通", "政策"].map((t) => (
              <Skeleton key={t} className="h-6 w-16" />
            ))}
          </div>
          <Skeleton className="h-6 w-24" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-4/6" />
        </div>

        <aside>
          <div className="flex flex-col gap-3 rounded-xl border p-4">
            <Skeleton className="h-5 w-32" />
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-14 w-14 rounded-lg" />
                <div className="flex flex-1 flex-col gap-1.5">
                  <Skeleton className="h-3 w-3/4" />
                  <Skeleton className="h-2.5 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}
