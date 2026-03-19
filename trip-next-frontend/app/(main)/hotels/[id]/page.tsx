import { Suspense } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { HotelHeaderCard } from "@/components/hotel-detail/hotel-header-card";
import {
  HotelRoomList,
  RoomListSkeleton,
} from "@/components/hotel-detail/hotel-room-list";
import { AmenityIcon } from "@/components/hotel-detail/amenity-icon";
import { getHotelById } from "@/lib/data/hotel";
import {
  getCityFromAddress,
  getFullAddress,
  formatTime,
} from "@/lib/hotel-helpers";

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { id } = await params;
  const hotel = await getHotelById(id);

  if (!hotel) {
    return { title: "酒店未找到" };
  }

  return {
    title: hotel.name,
    description:
      hotel.information?.introduction?.slice(0, 160) ??
      `查看${hotel.name}的详情、房型和价格`,
  };
}

export default async function HotelDetailPage({ params }: PageProps) {
  const { id } = await params;
  const hotel = await getHotelById(id);

  if (!hotel) {
    notFound();
  }

  const city = getCityFromAddress(hotel);
  const address = getFullAddress(hotel);

  return (
    <div className="flex flex-col gap-6">
      {/* Breadcrumb */}
      <nav className="text-muted-foreground text-sm">
        <ol className="flex items-center gap-1">
          <li>
            <Link href="/" className="text-blue-500 hover:underline">
              TripSphere
            </Link>
          </li>
          <li className="mx-1">&gt;</li>
          <li>
            <Link href="/hotels" className="text-blue-500 hover:underline">
              酒店
            </Link>
          </li>
          <li className="mx-1">&gt;</li>
          <li>
            <Link href="/hotels" className="text-blue-500 hover:underline">
              {city}酒店
            </Link>
          </li>
          <li className="mx-1">&gt;</li>
          <li className="text-foreground">{hotel.name}</li>
        </ol>
      </nav>

      <HotelHeaderCard hotel={hotel} />

      {/* Tabs Section */}
      <div className="bg-card rounded-xl border">
        <div className="border-b px-6 pt-4">
          <Tabs defaultValue="rooms">
            <TabsList variant="line" className="gap-6">
              <TabsTrigger value="overview" className="px-2 text-base">
                概览
              </TabsTrigger>
              <TabsTrigger value="rooms" className="px-2 text-base">
                房间
              </TabsTrigger>
              <TabsTrigger value="reviews" className="px-2 text-base">
                点评
              </TabsTrigger>
              <TabsTrigger value="facilities" className="px-2 text-base">
                服务及设施
              </TabsTrigger>
              <TabsTrigger value="policy" className="px-2 text-base">
                政策
              </TabsTrigger>
              <TabsTrigger value="location" className="px-2 text-base">
                地点
              </TabsTrigger>
            </TabsList>

            <TabsContent value="rooms" className="py-4">
              <Suspense fallback={<RoomListSkeleton />}>
                <HotelRoomList hotel={hotel} />
              </Suspense>
            </TabsContent>

            <TabsContent value="overview" className="p-6">
              <div className="space-y-4">
                <h3 className="text-lg font-bold">酒店概览</h3>
                <p className="text-muted-foreground">
                  {hotel.information?.introduction || "暂无酒店介绍信息"}
                </p>
              </div>
            </TabsContent>

            <TabsContent value="reviews" className="p-6">
              <p className="text-muted-foreground">用户点评内容...</p>
            </TabsContent>

            <TabsContent value="facilities" className="p-6">
              <div className="space-y-4">
                <h3 className="text-lg font-bold">服务及设施</h3>
                {hotel.amenities.length > 0 ? (
                  <div className="grid grid-cols-4 gap-4">
                    {hotel.amenities.map((amenity) => (
                      <div
                        key={amenity}
                        className="flex items-center gap-2 text-sm"
                      >
                        <AmenityIcon
                          name={amenity}
                          className="text-muted-foreground size-5"
                        />
                        <span className="text-foreground">{amenity}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground">暂无设施信息</p>
                )}
              </div>
            </TabsContent>

            <TabsContent value="policy" className="p-6">
              <div className="space-y-4">
                <h3 className="text-lg font-bold">酒店政策</h3>
                {hotel.policy ? (
                  <div className="text-muted-foreground space-y-2 text-sm">
                    <p>入住时间: {formatTime(hotel.policy.checkInTime, 14)}</p>
                    <p>退房时间: {formatTime(hotel.policy.checkOutTime, 12)}</p>
                    <p>
                      宠物政策:{" "}
                      {hotel.policy.petsAllowed
                        ? "允许携带宠物"
                        : "不允许携带宠物"}
                    </p>
                  </div>
                ) : (
                  <p className="text-muted-foreground">暂无政策信息</p>
                )}
              </div>
            </TabsContent>

            <TabsContent value="location" className="p-6">
              <div className="space-y-4">
                <h3 className="text-lg font-bold">地图与周边位置</h3>
                <p className="text-muted-foreground">地址: {address}</p>
                {hotel.location && (
                  <p className="text-muted-foreground text-sm">
                    坐标: {hotel.location.latitude?.toFixed(6)},{" "}
                    {hotel.location.longitude?.toFixed(6)}
                  </p>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
