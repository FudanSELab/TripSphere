import type { Hotel } from "@/lib/grpc/generated/tripsphere/hotel/v1/hotel";
import type { RoomType } from "@/lib/grpc/generated/tripsphere/hotel/v1/hotel";
import type { Spu } from "@/lib/grpc/generated/tripsphere/product/v1/product";
import type { HotelContext } from "@/components/context/hotel-context";
import { formatMoney } from "@/lib/format";

export interface RoomTypeWithSpus {
  roomType: RoomType;
  spus: Spu[];
}

export function formatTime(
  time: { hours: number; minutes: number } | undefined,
  fallbackHour: number,
): string {
  const h = time?.hours ?? fallbackHour;
  const m = String(time?.minutes ?? 0).padStart(2, "0");
  return `${h}:${m}`;
}

export function getCityFromAddress(hotel: Hotel): string {
  return hotel.address?.city || hotel.address?.province || "未知城市";
}

export function getFullAddress(hotel: Hotel): string {
  const addr = hotel.address;
  if (!addr) return "地址未知";
  const parts = [addr.province, addr.city, addr.district, addr.detailed].filter(
    Boolean,
  );
  return parts.join("") || "地址未知";
}

export function getLowestSkuPrice(spus: Spu[]): number {
  let lowest = Infinity;
  for (const spu of spus) {
    for (const sku of spu.skus) {
      const price = formatMoney(sku.basePrice);
      if (price > 0 && price < lowest) lowest = price;
    }
  }
  return lowest === Infinity ? 0 : lowest;
}

export function getStarCount(tags: string[]): number {
  if (tags.some((t) => t.includes("五星"))) return 5;
  if (tags.some((t) => t.includes("四星"))) return 4;
  if (tags.some((t) => t.includes("三星"))) return 3;
  return 2;
}

export function buildHotelContext(
  hotel: Hotel,
  roomTypesWithSpus: RoomTypeWithSpus[],
  starCount: number,
): HotelContext {
  return {
    hotel: {
      id: hotel.id,
      name: hotel.name,
      address: getFullAddress(hotel),
      city: getCityFromAddress(hotel),
      stars: starCount,
      tags: hotel.tags,
      amenities: hotel.amenities,
      estimatedPrice: formatMoney(hotel.estimatedPrice),
      introduction: hotel.information?.introduction,
      roomCount: hotel.information?.roomCount,
      checkInTime: hotel.policy?.checkInTime
        ? formatTime(hotel.policy.checkInTime, 14)
        : undefined,
      checkOutTime: hotel.policy?.checkOutTime
        ? formatTime(hotel.policy.checkOutTime, 12)
        : undefined,
      petsAllowed: hotel.policy?.petsAllowed,
    },
    roomTypes: roomTypesWithSpus.map(({ roomType, spus }) => ({
      id: roomType.id,
      name: roomType.name,
      bedDescription: roomType.bedDescription || "标准床型",
      areaDescription: roomType.areaDescription || "标准面积",
      maxOccupancy: roomType.maxOccupancy,
      hasWindow: roomType.hasWindow,
      amenities: roomType.amenities,
      spus: spus.map((spu) => ({
        id: spu.id,
        name: spu.name,
        skus: spu.skus.map((sku) => ({
          id: sku.id,
          name: sku.name,
          price: formatMoney(sku.basePrice),
          breakfast:
            (sku.attributes as Record<string, unknown>)?.breakfast === true,
          cancellable:
            (sku.attributes as Record<string, unknown>)?.cancellable === true,
        })),
      })),
    })),
  };
}
