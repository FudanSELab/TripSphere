import type { Attraction as GrpcAttraction } from "@/lib/grpc/gen/tripsphere/attraction/attraction";
import {
  findAttractionById,
  findAttractionsWithinRadius,
  type FindAttractionsWithinRadiusRequest,
} from "@/lib/requests";
import type { Attraction } from "@/lib/types";

/**
 * Generate mock rating based on attraction ID for consistency
 */
function generateMockRating(id: string): number {
  // Generate a rating between 4.0 and 5.0 based on ID hash
  const hash = id.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return 4.0 + (hash % 11) / 10; // Results in 4.0 to 5.0
}

/**
 * Generate mock opening hours based on category
 */
function generateMockOpeningHours(category: string): string {
  const hoursByCategory: Record<string, string> = {
    Museum: "9:00 AM - 5:00 PM",
    Park: "24 hours",
    Temple: "8:00 AM - 6:00 PM",
    Garden: "8:30 AM - 5:30 PM",
    Landmark: "24 hours",
    Historical: "9:00 AM - 5:00 PM",
    Nature: "24 hours",
  };
  return hoursByCategory[category] || "9:00 AM - 6:00 PM";
}

/**
 * Generate mock ticket price based on category
 */
function generateMockTicketPrice(category: string): string {
  const pricesByCategory: Record<string, string> = {
    Museum: "¥40-60",
    Park: "Free",
    Temple: "¥30",
    Garden: "¥40",
    Landmark: "Free",
    Historical: "¥60",
    Nature: "Free",
  };
  return pricesByCategory[category] || "¥40";
}

/**
 * Convert gRPC Attraction to frontend Attraction type
 */
function convertGrpcAttractionToFrontend(
  grpcAttraction: GrpcAttraction,
): Attraction {
  // Add 47.120.37.103:9000/ prefix to image URLs
  const images =
    grpcAttraction.images?.map((url) =>
      url.startsWith("http")
        ? url
        : `http://47.120.37.103:9000/${url.replace(/^\//, "")}`,
    ) || [];

  const category = grpcAttraction.tags?.[0] || "Attraction";

  return {
    id: grpcAttraction.id,
    name: grpcAttraction.name,
    description: grpcAttraction.introduction,
    address: grpcAttraction.address || {
      country: "",
      province: "",
      city: "",
      county: "",
      district: "",
      street: "",
    },
    location: {
      lng: grpcAttraction.location?.longitude || 0,
      lat: grpcAttraction.location?.latitude || 0,
    },
    category,
    // Mock data for fields not in gRPC Attraction
    rating: generateMockRating(grpcAttraction.id),
    openingHours: generateMockOpeningHours(category),
    ticketPrice: generateMockTicketPrice(category),
    images,
    tags: grpcAttraction.tags || [],
  };
}

export function useAttractions() {
  const fetchAttraction = async (id: string): Promise<Attraction | null> => {
    try {
      const response = await findAttractionById(id);

      if (!response.data) {
        console.error("Failed to fetch attraction:", response.msg);
        return null;
      }

      return convertGrpcAttractionToFrontend(response.data);
    } catch (error) {
      console.error("Error fetching attraction:", error);
      throw error;
    }
  };

  const fetchAttractionsNearby = async (
    request: FindAttractionsWithinRadiusRequest,
  ): Promise<Attraction[]> => {
    try {
      const response = await findAttractionsWithinRadius(request);

      if (!response.data) {
        console.error("Failed to fetch attractions:", response.msg);
        return [];
      }

      return response.data.map(convertGrpcAttractionToFrontend);
    } catch (error) {
      console.error("Error fetching attractions:", error);
      throw error;
    }
  };

  return {
    fetchAttraction,
    fetchAttractionsNearby,
  };
}
