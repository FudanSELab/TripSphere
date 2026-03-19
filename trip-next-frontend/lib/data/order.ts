import "server-only";

import { cache } from "react";
import { getAuthMetadata, getOrderService } from "@/lib/grpc/client";
import type {
  Order,
  ListUserOrdersResponse,
} from "@/lib/grpc/generated/tripsphere/order/v1/order";

export interface ListUserOrdersResult {
  orders: Order[];
  nextPageToken: string;
}

export const listUserOrders = cache(
  async (
    userId: string,
    status = 0,
    type = 0,
    pageSize = 10,
    pageToken = "",
  ): Promise<ListUserOrdersResult> => {
    const client = getOrderService();
    const metadata = await getAuthMetadata();
    try {
      const response = await new Promise<ListUserOrdersResponse>(
        (resolve, reject) => {
          client.listUserOrders(
            { userId, status, type, pageSize, pageToken },
            metadata,
            (error, response) => {
              if (error) reject(error);
              else resolve(response);
            },
          );
        },
      );
      return {
        orders: response.orders,
        nextPageToken: response.nextPageToken,
      };
    } catch {
      return { orders: [], nextPageToken: "" };
    }
  },
);
