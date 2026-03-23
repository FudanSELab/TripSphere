import { Calendar, User, Building2 } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { RoomTypeCard } from "./room-type-card";
import { HotelAgentStateSync } from "@/components/context/hotel-context";
import { getRoomTypesByHotelId } from "@/lib/data/hotel";
import { listSpusByRoomType } from "@/lib/data/product";
import {
  buildHotelContext,
  getStarCount,
  type RoomTypeWithSpus,
} from "@/lib/hotel-helpers";
import { formatDate } from "@/lib/format";
import type { Hotel } from "@/lib/grpc/generated/tripsphere/hotel/v1/hotel";

interface HotelRoomListProps {
  hotel: Hotel;
}

export async function HotelRoomList({ hotel }: HotelRoomListProps) {
  const roomTypes = await getRoomTypesByHotelId(hotel.id);

  const roomTypesWithSpus: RoomTypeWithSpus[] = await Promise.all(
    roomTypes.map(async (roomType) => {
      const { spus } = await listSpusByRoomType(roomType.id);
      return { roomType, spus };
    }),
  );

  const starCount = getStarCount(hotel.tags);
  const hotelContext = buildHotelContext(hotel, roomTypesWithSpus, starCount);

  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  return (
    <>
      <HotelAgentStateSync hotelContext={hotelContext} />

      <div className="bg-muted mb-4 flex items-center gap-4 rounded-lg border p-3">
        <div className="flex items-center gap-2">
          <Calendar className="text-muted-foreground size-5" />
          <span className="font-medium">{formatDate(today)}</span>
          <span className="text-muted-foreground text-sm">1晚</span>
          <span className="font-medium">{formatDate(tomorrow)}</span>
        </div>
        <div className="flex items-center gap-2 border-l pl-4">
          <User className="text-muted-foreground size-5" />
          <span>1间, 1成人, 0儿童</span>
        </div>
      </div>

      <div className="flex flex-col gap-6">
        {roomTypesWithSpus.length > 0 ? (
          roomTypesWithSpus.map(({ roomType, spus }) => (
            <RoomTypeCard key={roomType.id} roomType={roomType} spus={spus} />
          ))
        ) : (
          <div className="text-muted-foreground py-12 text-center">
            <Building2 className="text-muted-foreground/50 mx-auto mb-4 size-16" />
            <p>暂无可预订房型</p>
          </div>
        )}
      </div>
    </>
  );
}

export function RoomListSkeleton() {
  return (
    <div className="flex flex-col gap-6 py-4">
      <Skeleton className="h-12 w-full rounded-lg" />
      {Array.from({ length: 2 }).map((_, i) => (
        <Skeleton key={i} className="h-64 w-full rounded-lg" />
      ))}
    </div>
  );
}
