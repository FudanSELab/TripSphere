"use client";

import { useAgentContext } from "@copilotkit/react-core/v2";

export interface HotelContext {
  hotel: {
    id: string;
    name: string;
    address: string;
    city: string;
    stars: number;
    tags: string[];
    amenities: string[];
    estimatedPrice: number;
    introduction?: string;
    roomCount?: number;
    checkInTime?: string;
    checkOutTime?: string;
    petsAllowed?: boolean;
  };
  roomTypes: Array<{
    id: string;
    name: string;
    bedDescription: string;
    areaDescription: string;
    maxOccupancy: number;
    hasWindow: boolean;
    amenities: string[];
    spus: Array<{
      id: string;
      name: string;
      skus: Array<{
        id: string;
        name: string;
        price: number;
        breakfast: boolean;
        cancellable: boolean;
      }>;
    }>;
  }>;
}

interface Props {
  hotelContext: HotelContext;
}

export function HotelAgentStateSync({ hotelContext }: Props) {
  useAgentContext({
    description: "hotel context",
    value: JSON.stringify(hotelContext),
  });

  return null;
}
