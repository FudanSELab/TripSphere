import "server-only";

import { cache } from "react";
import { getHotelService } from "@/lib/grpc/client";
import type {
  Hotel,
  RoomType,
  GetHotelByIdResponse,
  GetRoomTypesByHotelIdResponse,
} from "@/lib/grpc/generated/tripsphere/hotel/v1/hotel";

/**
 * Per-request deduplication via React.cache() — safe to call from both
 * generateMetadata and the page component without triggering duplicate RPCs.
 */
export const getHotelById = cache(async (id: string): Promise<Hotel | null> => {
  const client = getHotelService();
  try {
    const response = await new Promise<GetHotelByIdResponse>(
      (resolve, reject) => {
        client.getHotelById({ id }, (error, response) => {
          if (error) reject(error);
          else resolve(response);
        });
      },
    );
    return response.hotel ?? null;
  } catch {
    return null;
  }
});

export const getRoomTypesByHotelId = cache(
  async (hotelId: string): Promise<RoomType[]> => {
    const client = getHotelService();
    try {
      const response = await new Promise<GetRoomTypesByHotelIdResponse>(
        (resolve, reject) => {
          client.getRoomTypesByHotelId({ hotelId }, (error, response) => {
            if (error) reject(error);
            else resolve(response);
          });
        },
      );
      return response.roomTypes;
    } catch {
      return [];
    }
  },
);
