import "server-only";

import { cache } from "react";
import { headers } from "next/headers";
import { getAuthMetadata, getItineraryService } from "@/lib/grpc/client";
import { formatDateMessage } from "@/lib/format";
import type { Timestamp } from "@/lib/grpc/generated/google/protobuf/timestamp";
import type {
  ListUserItinerariesRequest,
  ListUserItinerariesResponse,
} from "@/lib/grpc/generated/tripsphere/itinerary/v1/itinerary";

export interface SavedItinerarySummary {
  id: string;
  destination: string;
  start_date: string;
  end_date: string;
  day_count: number;
  created_at: string;
  updated_at: string;
}

function toIsoString(value: Date | Timestamp | undefined): string {
  if (!value) return new Date().toISOString();
  if (value instanceof Date) return value.toISOString();
  const ms = Number(value.seconds) * 1000 + value.nanos / 1_000_000;
  const date = new Date(ms);
  return Number.isNaN(date.getTime())
    ? new Date().toISOString()
    : date.toISOString();
}

export const listMyItineraries = cache(
  async (): Promise<SavedItinerarySummary[]> => {
    const reqHeaders = await headers();
    const userId = reqHeaders.get("x-user-id") ?? "";
    if (!userId) return [];

    const client = getItineraryService();
    const metadata = await getAuthMetadata();

    try {
      const response = await new Promise<ListUserItinerariesResponse>(
        (resolve, reject) => {
          const request: ListUserItinerariesRequest = {
            userId,
            pageSize: 50,
            pageToken: "",
          };
          client.listUserItineraries(request, metadata, (error, result) => {
            if (error) reject(error);
            else resolve(result);
          });
        },
      );

      return response.itineraries.map((itinerary) => ({
        id: itinerary.id,
        destination: itinerary.destinationName || itinerary.title,
        start_date: formatDateMessage(itinerary.startDate),
        end_date: formatDateMessage(itinerary.endDate),
        day_count: itinerary.dayPlans.length,
        created_at: toIsoString(itinerary.createdAt),
        updated_at: toIsoString(itinerary.updatedAt),
      }));
    } catch {
      return [];
    }
  },
);
