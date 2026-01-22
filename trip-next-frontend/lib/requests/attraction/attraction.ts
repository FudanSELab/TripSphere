import { post } from "@/lib/requests/base/request";
import type { Attraction } from "@/lib/types";

/**
 * Find attraction by ID
 */
export async function findAttractionById(id: string) {
  return post<Attraction>("/api/v1/attraction/find-by-id", { id });
}

/**
 * Search attractions within a radius
 */
export async function searchAttractions(params: {
  location: { lng: number; lat: number };
  radiusKm: number;
  page?: number;
  pageSize?: number;
  name?: string;
  tags?: string[];
}) {
  return post<{
    attractions: Attraction[];
    totalPages: number;
    totalElements: number;
    currentPage: number;
    pageSize: number;
  }>("/api/v1/attraction/search", {
    location: params.location,
    radiusKm: params.radiusKm,
    page: params.page ?? 0,
    pageSize: params.pageSize ?? 20,
    name: params.name,
    tags: params.tags,
  });
}
