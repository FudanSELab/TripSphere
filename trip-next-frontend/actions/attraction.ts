"use server";

import { getAttractionService } from "@/lib/grpc/client";
import type {
  Attraction,
  ListAttractionsByCityResponse,
} from "@/lib/grpc/generated/tripsphere/attraction/v1/attraction";

export interface ListAttractionsByCityResult {
  attractions: Attraction[];
  nextPageToken: string;
}

export async function listAttractionsByCity(
  city: string,
  tags?: string[],
  pageToken?: string,
): Promise<ListAttractionsByCityResult> {
  const client = getAttractionService();

  const response = await new Promise<ListAttractionsByCityResponse>(
    (resolve, reject) => {
      client.listAttractionsByCity(
        {
          city,
          tags: tags ?? [],
          pageSize: 50,
          pageToken: pageToken ?? "",
        },
        (error, response) => {
          if (error) reject(error);
          else resolve(response);
        },
      );
    },
  );

  return {
    attractions: response.attractions,
    nextPageToken: response.nextPageToken,
  };
}
