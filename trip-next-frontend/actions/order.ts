"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { getAuthMetadata, getOrderService } from "@/lib/grpc/client";
import type {
  CancelOrderResponse,
  ConfirmPaymentResponse,
  CreateOrderResponse,
} from "@/lib/grpc/generated/tripsphere/order/v1/order";
import { getSession } from "@/lib/session";

const isoDateSchema = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "日期格式无效")
  .refine(isValidIsoDate, "日期无效");

const createOrderSchema = z
  .object({
    requestId: z.uuid({ error: "请求标识无效" }),
    skuId: z.string().trim().min(1, "SKU 不能为空"),
    checkInDate: isoDateSchema,
    checkOutDate: isoDateSchema,
    quantity: z.number().int().positive("预订数量必须大于零"),
    contact: z.object({
      name: z.string().trim().min(1, "联系人姓名不能为空"),
      phone: z.string().trim().min(1, "联系电话不能为空"),
      email: z.email({ error: "联系邮箱格式无效" }).trim(),
    }),
  })
  .refine(({ checkInDate, checkOutDate }) => checkOutDate > checkInDate, {
    message: "退房日期必须晚于入住日期",
    path: ["checkOutDate"],
  });

const orderMutationSchema = z.object({
  orderId: z.string().trim().min(1, "订单 ID 不能为空"),
});

export interface CreateOrderInput {
  requestId: string;
  skuId: string;
  checkInDate: string;
  checkOutDate: string;
  quantity: number;
  contact: {
    name: string;
    phone: string;
    email: string;
  };
}

export type OrderActionResult =
  | { success: true; orderId: string }
  | { success: false; error: string };

function isValidIsoDate(value: string): boolean {
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return (
    date.getUTCFullYear() === year &&
    date.getUTCMonth() + 1 === month &&
    date.getUTCDate() === day
  );
}

function toDateMessage(value: string) {
  const [year, month, day] = value.split("-").map(Number);
  return { year, month, day };
}

function getErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

function formatLocalDate(date: Date): string {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
  ].join("-");
}

export async function createOrder(
  input: CreateOrderInput,
): Promise<OrderActionResult> {
  const parsed = createOrderSchema.safeParse(input);
  if (!parsed.success) {
    return {
      success: false,
      error: parsed.error.issues[0]?.message ?? "订单参数无效",
    };
  }
  if (parsed.data.checkInDate < formatLocalDate(new Date())) {
    return { success: false, error: "入住日期不能早于今天" };
  }

  const session = await getSession();
  if (!session?.userId) {
    return { success: false, error: "请先登录后再预订" };
  }

  try {
    const metadata = await getAuthMetadata();
    metadata.set("x-user-id", session.userId);
    const client = getOrderService();
    const response = await new Promise<CreateOrderResponse>(
      (resolve, reject) => {
        client.createOrder(
          {
            userId: session.userId,
            requestId: parsed.data.requestId,
            items: [
              {
                skuId: parsed.data.skuId,
                date: toDateMessage(parsed.data.checkInDate),
                endDate: toDateMessage(parsed.data.checkOutDate),
                quantity: parsed.data.quantity,
              },
            ],
            contact: parsed.data.contact,
            source: { channel: "web", agentId: "", sessionId: "" },
          },
          metadata,
          (error, result) => {
            if (error) reject(error);
            else resolve(result);
          },
        );
      },
    );
    if (!response.order) {
      return { success: false, error: "订单服务未返回新订单" };
    }

    revalidatePath("/orders");
    return { success: true, orderId: response.order.id };
  } catch (error) {
    return {
      success: false,
      error: getErrorMessage(error, "创建订单失败"),
    };
  }
}

export async function cancelOrder(
  orderId: string,
  reason: string,
): Promise<OrderActionResult> {
  const parsed = orderMutationSchema.safeParse({ orderId });
  if (!parsed.success) {
    return { success: false, error: "订单 ID 无效" };
  }
  const session = await getSession();
  if (!session?.userId) {
    return { success: false, error: "请先登录后再取消订单" };
  }

  try {
    const metadata = await getAuthMetadata();
    metadata.set("x-user-id", session.userId);
    const client = getOrderService();
    const response = await new Promise<CancelOrderResponse>(
      (resolve, reject) => {
        client.cancelOrder(
          { orderId: parsed.data.orderId, reason: reason.trim() },
          metadata,
          (error, result) => {
            if (error) reject(error);
            else resolve(result);
          },
        );
      },
    );
    if (!response.order) {
      return { success: false, error: "订单服务未返回取消结果" };
    }

    revalidatePath("/orders");
    return { success: true, orderId: response.order.id };
  } catch (error) {
    return {
      success: false,
      error: getErrorMessage(error, "取消订单失败"),
    };
  }
}

export async function confirmPayment(
  orderId: string,
): Promise<OrderActionResult> {
  const parsed = orderMutationSchema.safeParse({ orderId });
  if (!parsed.success) {
    return { success: false, error: "订单 ID 无效" };
  }
  const session = await getSession();
  if (!session?.userId) {
    return { success: false, error: "请先登录后再支付" };
  }

  try {
    const metadata = await getAuthMetadata();
    metadata.set("x-user-id", session.userId);
    const client = getOrderService();
    const response = await new Promise<ConfirmPaymentResponse>(
      (resolve, reject) => {
        client.confirmPayment(
          { orderId: parsed.data.orderId, paymentMethod: "mock" },
          metadata,
          (error, result) => {
            if (error) reject(error);
            else resolve(result);
          },
        );
      },
    );
    if (!response.order) {
      return { success: false, error: "订单服务未返回支付结果" };
    }

    revalidatePath("/orders");
    return { success: true, orderId: response.order.id };
  } catch (error) {
    return {
      success: false,
      error: getErrorMessage(error, "支付失败"),
    };
  }
}
