import { useCallback } from "react";
import type { Attraction } from "@/lib/types";
import {
  findAttractionById,
  searchAttractions,
} from "@/lib/requests/attraction/attraction";

export function useAttractions() {
  const fetchAttraction = useCallback(
    async (id: string): Promise<Attraction | null> => {
      try {
        const response = await findAttractionById(id);
        if (response.code === "Success" && response.data) {
          return response.data;
        }
        return null;
      } catch (error) {
        console.error("Error fetching attraction:", error);
        throw error;
      }
    },
    [],
  );

  const fetchAttractions = useCallback(
    async (params?: {
      location?: { lng: number; lat: number };
      radiusKm?: number;
      page?: number;
      pageSize?: number;
      name?: string;
      tags?: string[];
    }): Promise<Attraction[]> => {
      try {
        // Default to Shanghai center if no location provided
        const defaultLocation = { lng: 121.4737, lat: 31.2304 };
        const location = params?.location || defaultLocation;
        const radiusKm = params?.radiusKm || 50; // Default 50km radius

        const response = await searchAttractions({
          location,
          radiusKm,
          page: params?.page ?? 0,
          pageSize: params?.pageSize ?? 20,
          name: params?.name,
          tags: params?.tags,
        });

        if (response.code === "Success" && response.data) {
          return response.data.attractions;
        }
        return [];
      } catch (error) {
        console.error("Error fetching attractions:", error);
        throw error;
      }
    },
    [],
  );

  const searchNearby = useCallback(
    async (params: {
      location: { lng: number; lat: number };
      radiusKm: number;
      page?: number;
      pageSize?: number;
      name?: string;
      tags?: string[];
    }) => {
      try {
        const response = await searchAttractions(params);
        if (response.code === "Success" && response.data) {
          return response.data;
        }
        return {
          attractions: [],
          totalPages: 0,
          totalElements: 0,
          currentPage: 0,
          pageSize: 0,
        };
      } catch (error) {
        console.error("Error searching attractions:", error);
        throw error;
      }
    },
    [],
  );

  return {
    fetchAttraction,
    fetchAttractions,
    searchNearby,
  };
}
