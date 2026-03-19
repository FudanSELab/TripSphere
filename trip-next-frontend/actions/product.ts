"use server";

import { getProductService } from "@/lib/grpc/client";
import { listSpusByRoomType } from "@/lib/data/product";
import type {
  Spu,
  BatchGetSpusResponse,
} from "@/lib/grpc/generated/tripsphere/product/v1/product";

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

export async function getSpusForRoomTypes(
  roomTypeIds: string[],
): Promise<Record<string, Spu[]>> {
  const result: Record<string, Spu[]> = {};

  await Promise.all(
    roomTypeIds.map(async (roomTypeId) => {
      const { spus } = await listSpusByRoomType(roomTypeId);
      result[roomTypeId] = spus;
    }),
  );

  return result;
}
