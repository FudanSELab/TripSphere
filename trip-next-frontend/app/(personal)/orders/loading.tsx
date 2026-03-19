import { Skeleton } from "@/components/ui/skeleton";

export default function OrdersLoading() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-32" />
      <div>
        <div className="flex gap-2 border-b pb-2">
          {Array.from({ length: 5 }, (_, i) => (
            <Skeleton key={i} className="h-8 w-20" />
          ))}
        </div>
        <div className="mt-4 space-y-2">
          <Skeleton className="h-7 w-60" />
        </div>
        <div className="mt-4 space-y-4">
          {Array.from({ length: 3 }, (_, i) => (
            <div key={i} className="rounded-xl border">
              <div className="bg-muted/40 flex items-center justify-between px-6 py-3">
                <div className="flex items-center gap-4">
                  <Skeleton className="h-4 w-40" />
                  <Skeleton className="h-4 w-32" />
                </div>
                <Skeleton className="h-5 w-14 rounded-full" />
              </div>
              <div className="px-6 py-4">
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <Skeleton className="h-5 w-48" />
                    <Skeleton className="h-4 w-64" />
                    <Skeleton className="h-4 w-40" />
                  </div>
                  <Skeleton className="h-6 w-16" />
                </div>
              </div>
              <div className="flex justify-end gap-2 px-6 py-3">
                <Skeleton className="h-8 w-20 rounded-md" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
