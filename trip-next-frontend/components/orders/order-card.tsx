"use client";

import { useTransition } from "react";
import { Hotel, Plane, TrainFront, Ticket, User, Calendar } from "lucide-react";
import {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { cancelOrder } from "@/actions/order";
import {
  formatMoney,
  formatDateMessage,
  formatOrderStatus,
} from "@/lib/format";
import {
  type OrderData,
  ORDER_STATUS_PENDING_PAYMENT,
  ORDER_STATUS_PAID,
  ORDER_STATUS_COMPLETED,
  ORDER_STATUS_CANCELLED,
  ORDER_TYPE_HOTEL,
  ORDER_TYPE_FLIGHT,
  ORDER_TYPE_TRAIN,
  ORDER_TYPE_ATTRACTION,
} from "@/lib/order-types";

const TYPE_ICON: Record<number, React.ReactNode> = {
  [ORDER_TYPE_HOTEL]: <Hotel className="size-4" />,
  [ORDER_TYPE_FLIGHT]: <Plane className="size-4" />,
  [ORDER_TYPE_TRAIN]: <TrainFront className="size-4" />,
  [ORDER_TYPE_ATTRACTION]: <Ticket className="size-4" />,
};

const STATUS_VARIANT: Record<
  number,
  "default" | "secondary" | "destructive" | "outline"
> = {
  [ORDER_STATUS_PENDING_PAYMENT]: "outline",
  [ORDER_STATUS_PAID]: "default",
  [ORDER_STATUS_COMPLETED]: "secondary",
  [ORDER_STATUS_CANCELLED]: "destructive",
};

export function OrderCard({ order }: { order: OrderData }) {
  const [isPending, startTransition] = useTransition();

  const totalPrice = formatMoney(order.totalAmount);
  const firstItem = order.items[0];
  const statusLabel = formatOrderStatus(order.status);

  const handleCancel = () => {
    startTransition(async () => {
      await cancelOrder(order.id, "用户主动取消");
    });
  };

  return (
    <Card className="gap-0 overflow-hidden py-0">
      <CardHeader className="bg-muted/40 flex-row items-center justify-between gap-4 px-6 py-3">
        <div className="flex items-center gap-4 text-sm">
          <span className="text-muted-foreground flex items-center gap-1.5">
            {TYPE_ICON[order.type]}
            订单号:
            <span className="text-foreground font-mono">{order.orderNo}</span>
          </span>
          {order.createdAt && (
            <span className="text-muted-foreground">
              下单日期: {order.createdAt}
            </span>
          )}
        </div>
        <Badge variant={STATUS_VARIANT[order.status] ?? "outline"}>
          {statusLabel}
        </Badge>
      </CardHeader>

      <Separator />

      <CardContent className="px-6 py-4">
        <div className="flex items-start justify-between gap-6">
          <div className="flex min-w-0 flex-1 flex-col gap-2">
            {firstItem ? (
              <>
                <h3 className="truncate text-base font-semibold">
                  {firstItem.spuName}
                </h3>
                {firstItem.skuName && (
                  <p className="text-muted-foreground text-sm">
                    {firstItem.skuName}
                  </p>
                )}
              </>
            ) : (
              <p className="text-muted-foreground text-sm">暂无商品信息</p>
            )}

            <div className="text-muted-foreground flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
              {firstItem?.date && (
                <span className="flex items-center gap-1">
                  <Calendar className="size-3.5" />
                  {formatDateMessage(firstItem.date)}
                  {firstItem.endDate
                    ? ` 至 ${formatDateMessage(firstItem.endDate)}`
                    : ""}
                </span>
              )}
              {order.contact?.name && (
                <span className="flex items-center gap-1">
                  <User className="size-3.5" />
                  {order.contact.name}
                </span>
              )}
              {order.items.length > 1 && (
                <span>共 {order.items.length} 项</span>
              )}
            </div>
          </div>

          <div className="shrink-0 text-right">
            <p className="text-price text-lg font-bold">
              ¥{totalPrice.toFixed(0)}
            </p>
          </div>
        </div>
      </CardContent>

      <Separator />

      <CardFooter className="justify-end gap-2 px-6 py-3">
        {order.status === ORDER_STATUS_PENDING_PAYMENT && (
          <Button
            variant="outline"
            size="sm"
            disabled={isPending}
            onClick={handleCancel}
          >
            {isPending ? (
              <>
                <Spinner className="mr-1.5 size-3.5" />
                取消中…
              </>
            ) : (
              "取消订单"
            )}
          </Button>
        )}
        {order.status === ORDER_STATUS_PENDING_PAYMENT && (
          <Button size="sm">去支付</Button>
        )}
        {(order.status === ORDER_STATUS_PAID ||
          order.status === ORDER_STATUS_COMPLETED) && (
          <Button variant="outline" size="sm">
            查看详情
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
