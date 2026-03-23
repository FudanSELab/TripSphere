import type { Order } from "@/lib/grpc/generated/tripsphere/order/v1/order";
import type { OrderData } from "@/lib/order-types";

function formatDate(d: Date | undefined): string | undefined {
  if (!d) return undefined;
  const date = d instanceof Date ? d : new Date(d as unknown as string);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

export function orderToData(order: Order): OrderData {
  return {
    id: order.id,
    orderNo: order.orderNo,
    status: order.status,
    type: order.type,
    resourceId: order.resourceId,
    createdAt: formatDate(order.createdAt),
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
