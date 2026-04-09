import "server-only";

import { cache } from "react";
import { getProductService } from "@/lib/grpc/client";
import type {
  Spu,
  ListSpusByResourceResponse,
} from "@/lib/grpc/generated/tripsphere/product/v1/product";
import { ResourceType } from "@/lib/grpc/generated/tripsphere/product/v1/product";

export interface ListSpusResult {
  spus: Spu[];
  nextPageToken: string;
}

export const listSpusByRoomType = cache(
  async (roomTypeId: string): Promise<ListSpusResult> => {
    const client = getProductService();
    try {
      const response = await new Promise<ListSpusByResourceResponse>(
        (resolve, reject) => {
          client.listSpusByResource(
            {
              resourceType: ResourceType.RESOURCE_TYPE_HOTEL_ROOM,
              resourceId: roomTypeId,
              pageSize: 20,
              pageToken: "",
            },
            (error, response) => {
              if (error) reject(error);
              else resolve(response);
            },
          );
        },
      );
      return { spus: response.spus, nextPageToken: response.nextPageToken };
    } catch {
      return { spus: [], nextPageToken: "" };
    }
  },
);
