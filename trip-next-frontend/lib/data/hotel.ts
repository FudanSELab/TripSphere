import "server-only";

import { cache } from "react";
import { getHotelService } from "@/lib/grpc/client";
import type {
  Hotel,
  RoomType,
  ListHotelsResponse,
  GetHotelByIdResponse,
  GetRoomTypesByHotelIdResponse,
} from "@/lib/grpc/generated/tripsphere/hotel/v1/hotel";

export interface ListHotelsResult {
  hotels: Hotel[];
  nextPageToken: string;
}

export const listHotelsByCity = cache(
  async (city: string): Promise<ListHotelsResult> => {
    const client = getHotelService();
    try {
      const response = await new Promise<ListHotelsResponse>(
        (resolve, reject) => {
          client.listHotels(
            { province: "", city, pageSize: 12, pageToken: "" },
            (error, response) => {
              if (error) reject(error);
              else resolve(response);
            },
          );
        },
      );
      return {
        hotels: response.hotels,
        nextPageToken: response.nextPageToken,
      };
    } catch {
      return { hotels: [], nextPageToken: "" };
    }
  },
);

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
