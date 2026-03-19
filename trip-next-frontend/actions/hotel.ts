"use server";

import { getHotelService } from "@/lib/grpc/client";
import type {
  Hotel,
  ListHotelsResponse,
} from "@/lib/grpc/generated/tripsphere/hotel/v1/hotel";

export interface ListHotelsResult {
  hotels: Hotel[];
  nextPageToken: string;
}

export async function listHotels(
  city: string,
  pageToken?: string,
): Promise<ListHotelsResult> {
  const client = getHotelService();

  const response = await new Promise<ListHotelsResponse>((resolve, reject) => {
    client.listHotels(
      { province: "", city, pageSize: 12, pageToken: pageToken ?? "" },
      (error, response) => {
        if (error) reject(error);
        else resolve(response);
      },
    );
  });

  return {
    hotels: response.hotels,
    nextPageToken: response.nextPageToken,
  };
}
