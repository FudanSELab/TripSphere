"use server";

import { getProductService } from "@/lib/grpc/client";
import type {
  Spu,
  ListSpusByResourceResponse,
  BatchGetSpusResponse,
} from "@/lib/grpc/generated/tripsphere/product/v1/product";
import { ResourceType } from "@/lib/grpc/generated/tripsphere/product/v1/product";

export interface ListSpusResult {
  spus: Spu[];
  nextPageToken: string;
}

/**
 * List SPUs by room type ID (resourceId)
 */
export async function listSpusByRoomType(
  roomTypeId: string,
  pageSize = 20,
  pageToken = "",
): Promise<ListSpusResult> {
  const client = getProductService();

  try {
    const response = await new Promise<ListSpusByResourceResponse>(
      (resolve, reject) => {
        client.listSpusByResource(
          {
            resourceType: ResourceType.RESOURCE_TYPE_HOTEL_ROOM,
            resourceId: roomTypeId,
            pageSize,
            pageToken,
          },
          (error, response) => {
            if (error) reject(error);
            else resolve(response);
          },
        );
      },
    );

    return {
      spus: response.spus,
      nextPageToken: response.nextPageToken,
    };
  } catch {
    return { spus: [], nextPageToken: "" };
  }
}

/**
 * Batch get SPUs by their IDs
 */
export async function batchGetSpus(ids: string[]): Promise<Spu[]> {
  if (ids.length === 0) return [];

  const client = getProductService();

  try {
    const response = await new Promise<BatchGetSpusResponse>(
      (resolve, reject) => {
        client.batchGetSpus({ ids }, (error, response) => {
          if (error) reject(error);
          else resolve(response);
        });
      },
    );

    return response.spus;
  } catch {
    return [];
  }
}

/**
 * Get all SPUs for multiple room types
 */
export async function getSpusForRoomTypes(
  roomTypeIds: string[],
): Promise<Map<string, Spu[]>> {
  const result = new Map<string, Spu[]>();

  await Promise.all(
    roomTypeIds.map(async (roomTypeId) => {
      const { spus } = await listSpusByRoomType(roomTypeId);
      result.set(roomTypeId, spus);
    }),
  );

  return result;
}
