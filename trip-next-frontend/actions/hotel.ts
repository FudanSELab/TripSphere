"use server";

import { getHotelService } from "@/lib/grpc/client";
import type { ListHotelsResponse } from "@/lib/grpc/generated/tripsphere/hotel/v1/hotel";
import type { ListHotelsResult } from "@/lib/data/hotel";

export async function loadMoreHotels(
  city: string,
  pageToken: string,
): Promise<ListHotelsResult> {
  const client = getHotelService();

  const response = await new Promise<ListHotelsResponse>((resolve, reject) => {
    client.listHotels(
      { province: "", city, pageSize: 12, pageToken },
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
