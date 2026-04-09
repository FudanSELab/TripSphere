import "server-only";

import { cache } from "react";
import { getAttractionService } from "@/lib/grpc/client";
import type {
  Attraction,
  GetAttractionByIdResponse,
  GetAttractionsNearbyResponse,
  ListAttractionsByCityResponse,
} from "@/lib/grpc/generated/tripsphere/attraction/v1/attraction";
import type { GeoPoint } from "@/lib/grpc/generated/tripsphere/common/v1/map";

export interface ListAttractionsByCityResult {
  attractions: Attraction[];
  nextPageToken: string;
}

export const listAttractionsByCity = cache(
  async (
    city: string,
    tags?: string[],
  ): Promise<ListAttractionsByCityResult> => {
    const client = getAttractionService();

    const response = await new Promise<ListAttractionsByCityResponse>(
      (resolve, reject) => {
        client.listAttractionsByCity(
          { city, tags: tags ?? [], pageSize: 50, pageToken: "" },
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
  },
);

export const getAttractionById = cache(
  async (id: string): Promise<Attraction | null> => {
    const client = getAttractionService();

    try {
      const response = await new Promise<GetAttractionByIdResponse>(
        (resolve, reject) => {
          client.getAttractionById({ id }, (error, response) => {
            if (error) reject(error);
            else resolve(response);
          });
        },
      );
      return response.attraction ?? null;
    } catch {
      return null;
    }
  },
);

export const getAttractionsNearby = cache(
  async (location: GeoPoint, radiusMeters: number): Promise<Attraction[]> => {
    const client = getAttractionService();

    try {
      const response = await new Promise<GetAttractionsNearbyResponse>(
        (resolve, reject) => {
          client.getAttractionsNearby(
            { location, radiusMeters, tags: [] },
            (error, response) => {
              if (error) reject(error);
              else resolve(response);
            },
          );
        },
      );
      return response.attractions;
    } catch {
      return [];
    }
  },
);
