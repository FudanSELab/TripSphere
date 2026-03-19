import { Suspense } from "react";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { listUserOrders } from "@/lib/data/order";
import { OrderTabs } from "@/components/orders/order-tabs";
import { OrderFilters } from "@/components/orders/order-filters";
import { OrderList } from "@/components/orders/order-list";
import { OrderPagination } from "@/components/orders/order-pagination";
import { Skeleton } from "@/components/ui/skeleton";
import type { OrderData } from "@/lib/order-types";
import type { Order } from "@/lib/grpc/generated/tripsphere/order/v1/order";

function serializeOrder(order: Order): OrderData {
  const fmtDate = (d: Date | undefined): string | undefined => {
    if (!d) return undefined;
    const date = d instanceof Date ? d : new Date(d as unknown as string);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  };

  return {
    id: order.id,
    orderNo: order.orderNo,
    status: order.status,
    type: order.type,
    resourceId: order.resourceId,
    createdAt: fmtDate(order.createdAt),
    contact: order.contact
      ? {
          name: order.contact.name,
          phone: order.contact.phone,
          email: order.contact.email,
        }
      : undefined,
    totalAmount: order.totalAmount
      ? {
          currency: order.totalAmount.currency,
          units: order.totalAmount.units,
          nanos: order.totalAmount.nanos,
        }
      : undefined,
    items: order.items.map((item) => ({
      id: item.id,
      spuName: item.spuName,
      skuName: item.skuName,
      date: item.date
        ? { year: item.date.year, month: item.date.month, day: item.date.day }
        : undefined,
      endDate: item.endDate
        ? {
            year: item.endDate.year,
            month: item.endDate.month,
            day: item.endDate.day,
          }
        : undefined,
      quantity: item.quantity,
      unitPrice: item.unitPrice
        ? {
            currency: item.unitPrice.currency,
            units: item.unitPrice.units,
            nanos: item.unitPrice.nanos,
          }
        : undefined,
      subtotal: item.subtotal
        ? {
            currency: item.subtotal.currency,
            units: item.subtotal.units,
            nanos: item.subtotal.nanos,
          }
        : undefined,
      spuImage: item.spuImage,
      spuDescription: item.spuDescription,
      resourceId: item.resourceId,
    })),
  };
}

function OrderListSkeleton() {
  return (
    <div className="space-y-4">
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

  const serialized = orders.map(serializeOrder);

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
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">我的订单</h1>
      <OrderTabs>
        <div className="mt-4 space-y-4">
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
