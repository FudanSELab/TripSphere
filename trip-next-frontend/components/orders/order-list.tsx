import { Package } from "lucide-react";
import { OrderCard } from "@/components/orders/order-card";
import type { OrderData } from "@/lib/order-types";

export function OrderList({ orders }: { orders: OrderData[] }) {
  if (orders.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <Package className="text-muted-foreground/50 mb-4 size-16" />
        <p className="text-muted-foreground text-lg">暂无订单</p>
        <p className="text-muted-foreground/70 mt-1 text-sm">
          您还没有相关订单记录
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {orders.map((order) => (
        <OrderCard key={order.id} order={order} />
      ))}
    </div>
  );
}
