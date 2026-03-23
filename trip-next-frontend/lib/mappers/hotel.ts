import type { Hotel } from "@/lib/grpc/generated/tripsphere/hotel/v1/hotel";
import type { HotelCardData } from "@/components/hotel-card";
import { getStarCount } from "@/lib/hotel-helpers";

export function hotelToCardData(hotel: Hotel): HotelCardData {
  return {
    id: hotel.id,
    name: hotel.name,
    image: hotel.images[0] ?? null,
    stars: getStarCount(hotel.tags),
    rating: null,
    reviews: 0,
    location: hotel.address
      ? `${hotel.address.city} · ${hotel.address.district}`
      : "",
    price: hotel.estimatedPrice?.units ?? 0,
  };
}
