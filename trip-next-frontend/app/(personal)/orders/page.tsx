import { Suspense } from "react";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { listUserOrders } from "@/lib/data/order";
import { OrderTabs } from "@/components/orders/order-tabs";
import { OrderFilters } from "@/components/orders/order-filters";
import { OrderList } from "@/components/orders/order-list";
import { OrderPagination } from "@/components/orders/order-pagination";
import { Skeleton } from "@/components/ui/skeleton";
import { orderToData } from "@/lib/mappers/order";

function OrderListSkeleton() {
  return (
    <div className="flex flex-col gap-4">
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
              <div className="flex flex-col gap-2">
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
  );
}

async function OrderContent({
  userId,
  status,
  type,
  pageToken,
}: {
  userId: string;
  status: number;
  type: number;
  pageToken: string;
}) {
  const { orders, nextPageToken } = await listUserOrders(
    userId,
    status,
    type,
    10,
    pageToken,
  );

  const serialized = orders.map(orderToData);

  return (
    <>
      <OrderList orders={serialized} />
      <OrderPagination nextPageToken={nextPageToken} />
    </>
  );
}

export default async function OrderPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const session = await getSession();
  if (!session) redirect("/signin");

  const params = await searchParams;
  const status = Number(params.status) || 0;
  const type = Number(params.type) || 0;
  const pageToken = typeof params.page === "string" ? params.page : "";

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">我的订单</h1>
      <OrderTabs>
        <div className="mt-4 flex flex-col gap-4">
          <OrderFilters />
          <Suspense fallback={<OrderListSkeleton />}>
            <OrderContent
              userId={session.userId}
              status={status}
              type={type}
              pageToken={pageToken}
            />
          </Suspense>
        </div>
      </OrderTabs>
    </div>
  );
}
