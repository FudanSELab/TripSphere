"use server";

import { revalidatePath } from "next/cache";
import { getAuthMetadata, getOrderService } from "@/lib/grpc/client";
import type { CancelOrderResponse } from "@/lib/grpc/generated/tripsphere/order/v1/order";

export async function cancelOrder(
  orderId: string,
  reason: string,
): Promise<{ success: boolean; error?: string }> {
  const client = getOrderService();
  const metadata = await getAuthMetadata();

  try {
    await new Promise<CancelOrderResponse>((resolve, reject) => {
      client.cancelOrder({ orderId, reason }, metadata, (error, response) => {
        if (error) reject(error);
        else resolve(response);
      });
    });
    revalidatePath("/orders");
    return { success: true };
  } catch (e) {
    const message = e instanceof Error ? e.message : "取消订单失败";
    return { success: false, error: message };
  }
}
