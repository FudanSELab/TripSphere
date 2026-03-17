import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import {
  MapPin,
  Calendar,
  User,
  Phone,
  Clock,
  Bed,
  LayoutGrid,
  Wifi,
  Car,
  Utensils,
  Dumbbell,
  Waves,
  CheckCircle,
  XCircle,
  Zap,
  CreditCard,
  PawPrint,
  Building2,
  Image as ImageIcon,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ImagePlaceholder } from "@/components/image-placeholder";
import { StarIcons } from "@/components/star-icons";
import { getHotelById, getRoomTypesByHotelId } from "@/actions/hotel";
import { listSpusByRoomType } from "@/actions/product";
import { formatDate, formatMoney } from "@/lib/format";
import type {
  Hotel,
  RoomType,
} from "@/lib/grpc/generated/tripsphere/hotel/v1/hotel";
import type {
  Spu,
  Sku,
} from "@/lib/grpc/generated/tripsphere/product/v1/product";

function AmenityIcon({
  name,
  className,
}: {
  name: string;
  className?: string;
}) {
  const key = name.toLowerCase();

  if (key.includes("wifi") || key.includes("网络") || key.includes("宽带")) {
    return <Wifi className={className} />;
  }
  if (key.includes("停车") || key.includes("车")) {
    return <Car className={className} />;
  }
  if (key.includes("餐") || key.includes("厨") || key.includes("早")) {
    return <Utensils className={className} />;
  }
  if (key.includes("健身") || key.includes("运动")) {
    return <Dumbbell className={className} />;
  }
  if (key.includes("泳") || key.includes("池")) {
    return <Waves className={className} />;
  }

  return <CheckCircle className={className} />;
}

function formatTime(
  time: { hours: number; minutes: number } | undefined,
  fallbackHour: number,
): string {
  const h = time?.hours ?? fallbackHour;
  const m = String(time?.minutes ?? 0).padStart(2, "0");
  return `${h}:${m}`;
}

function getDateStrings() {
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  return {
    checkIn: formatDate(today),
    checkOut: formatDate(tomorrow),
  };
}

function getCityFromAddress(hotel: Hotel): string {
  if (hotel.address?.city) return hotel.address.city;
  if (hotel.address?.province) return hotel.address.province;
  return "未知城市";
}

function getFullAddress(hotel: Hotel): string {
  const addr = hotel.address;
  if (!addr) return "地址未知";
  const parts = [addr.province, addr.city, addr.district, addr.detailed].filter(
    Boolean,
  );
  return parts.join("") || "地址未知";
}

function getLowestSkuPrice(spus: Spu[]): number {
  let lowest = Infinity;
  for (const spu of spus) {
    for (const sku of spu.skus) {
      const price = formatMoney(sku.basePrice);
      if (price > 0 && price < lowest) {
        lowest = price;
      }
    }
  }
  return lowest === Infinity ? 0 : lowest;
}

interface RoomTypeWithSpus {
  roomType: RoomType;
  spus: Spu[];
}

function RoomTypeCard({ roomType, spus }: RoomTypeWithSpus) {
  const lowestPrice = getLowestSkuPrice(spus);
  const hasImages = roomType.images.length > 0;

  return (
    <div className="rounded-lg border">
      {/* Room Type Header */}
      <div className="bg-muted border-b px-4 py-3">
        <h3 className="text-foreground text-lg font-bold">{roomType.name}</h3>
      </div>

      <div className="flex">
        {/* Room Image & Info */}
        <div className="w-64 shrink-0 border-r p-4">
          {/* Room Images */}
          <div className="mb-3">
            <div className="relative aspect-[4/3] overflow-hidden rounded-lg">
              {hasImages ? (
                <Image
                  src={roomType.images[0]}
                  alt={roomType.name}
                  fill
                  unoptimized
                  className="object-cover"
                />
              ) : (
                <ImagePlaceholder
                  className="h-full w-full"
                  iconClassName="size-8"
                />
              )}
              {roomType.images.length > 1 && (
                <div className="absolute right-1 bottom-1 rounded bg-black/60 px-1.5 py-0.5 text-xs text-white">
                  {roomType.images.length}
                </div>
              )}
            </div>
          </div>

          {/* Room Details */}
          <div className="text-muted-foreground space-y-1.5 text-sm">
            <div className="flex items-center gap-2">
              <Bed className="size-4" />
              <span>{roomType.bedDescription || "标准床型"}</span>
            </div>
            <div className="flex items-center gap-2">
              <LayoutGrid className="size-4" />
              <span>{roomType.hasWindow ? "有窗" : "无窗"}</span>
            </div>
            <div className="flex items-center gap-2">
              <Building2 className="size-4" />
              <span>{roomType.areaDescription || "标准面积"}</span>
            </div>
            <div className="flex items-center gap-2">
              <User className="size-4" />
              <span>最多{roomType.maxOccupancy}人入住</span>
            </div>
            {roomType.amenities.slice(0, 3).map((amenity, i) => (
              <div key={i} className="flex items-center gap-2">
                <AmenityIcon name={amenity} className="size-4" />
                <span className="text-blue-500">{amenity}</span>
              </div>
            ))}
          </div>
          <button className="mt-3 text-sm text-blue-500 hover:underline">
            房间详情
          </button>
        </div>

        {/* Room Options Table */}
        <div className="flex-1">
          <table className="w-full">
            <thead>
              <tr className="bg-muted text-muted-foreground border-b text-sm">
                <th className="px-4 py-3 text-left font-medium">房型摘要</th>
                <th className="px-4 py-3 text-center font-medium">可住人数</th>
                <th className="px-4 py-3 text-right font-medium">今日价格</th>
              </tr>
            </thead>
            <tbody>
              {spus.length > 0 ? (
                spus.flatMap((spu) =>
                  spu.skus.map((sku, skuIdx) => (
                    <SkuRow
                      key={sku.id}
                      sku={sku}
                      maxOccupancy={roomType.maxOccupancy}
                      isLast={
                        skuIdx === spu.skus.length - 1 &&
                        spu === spus[spus.length - 1]
                      }
                    />
                  )),
                )
              ) : (
                <tr>
                  <td
                    colSpan={3}
                    className="text-muted-foreground px-4 py-8 text-center"
                  >
                    暂无可预订房型
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          {/* Show more prices */}
          {spus.length > 0 && lowestPrice > 0 && (
            <div className="border-t p-3 text-center">
              <button className="text-sm text-blue-500 hover:underline">
                展示更多价格选项
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SkuRow({
  sku,
  maxOccupancy,
  isLast,
}: {
  sku: Sku;
  maxOccupancy: number;
  isLast: boolean;
}) {
  const price = formatMoney(sku.basePrice);
  const attrs = sku.attributes as Record<string, unknown> | undefined;
  const hasBreakfast = attrs?.breakfast === true;
  const cancellable = attrs?.cancellable === true;
  const instantConfirm = attrs?.instant_confirm !== false;

  return (
    <tr className={!isLast ? "border-b" : ""}>
      {/* Room Summary */}
      <td className="px-4 py-4">
        <div className="space-y-1 text-sm">
          <div className="text-foreground font-medium">{sku.name}</div>
          <div className="flex items-center gap-2">
            <Utensils
              className={`size-4 ${hasBreakfast ? "text-green-500" : "text-muted-foreground"}`}
            />
            <span
              className={
                hasBreakfast ? "text-green-600" : "text-muted-foreground"
              }
            >
              {hasBreakfast ? "含早餐" : "无早餐"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {cancellable ? (
              <CheckCircle className="size-4 text-green-500" />
            ) : (
              <XCircle className="text-muted-foreground size-4" />
            )}
            <span
              className={
                cancellable ? "text-green-600" : "text-muted-foreground"
              }
            >
              {cancellable ? "可取消" : "不可取消"}
            </span>
          </div>
          {instantConfirm && (
            <div className="flex items-center gap-2">
              <Zap className="size-4 text-green-500" />
              <span className="text-green-600">立即确认</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <CreditCard className="text-muted-foreground size-4" />
            <span className="text-muted-foreground">在线付</span>
          </div>
        </div>
      </td>

      {/* Occupancy */}
      <td className="px-4 py-4 text-center">
        <div className="flex items-center justify-center gap-0.5">
          {Array.from({ length: maxOccupancy }).map((_, i) => (
            <User key={i} className="text-muted-foreground size-5" />
          ))}
        </div>
      </td>

      {/* Price & Booking */}
      <td className="px-4 py-4">
        <div className="flex flex-col items-end gap-2">
          <div className="flex items-baseline gap-1">
            <span className="text-xl font-bold text-orange-500">
              ¥{Math.round(price)}
            </span>
          </div>
          <Button size="sm" className="bg-blue-500 px-6 hover:bg-blue-600">
            预订
          </Button>
        </div>
      </td>
    </tr>
  );
}

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

  const roomTypes = await getRoomTypesByHotelId(id);

  // Fetch SPUs for each room type
  const roomTypesWithSpus: RoomTypeWithSpus[] = await Promise.all(
    roomTypes.map(async (roomType) => {
      const { spus } = await listSpusByRoomType(roomType.id);
      return { roomType, spus };
    }),
  );

  const dates = getDateStrings();
  const city = getCityFromAddress(hotel);
  const address = getFullAddress(hotel);
  const estimatedPrice = formatMoney(hotel.estimatedPrice);
  const hasImages = hotel.images.length > 0;

  // Calculate star count based on tags or default to 3
  const starCount = hotel.tags.some((t) => t.includes("五星"))
    ? 5
    : hotel.tags.some((t) => t.includes("四星"))
      ? 4
      : hotel.tags.some((t) => t.includes("三星"))
        ? 3
        : 2;

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

      {/* Hotel Header Card */}
      <div className="bg-card rounded-xl border p-6">
        {/* Title Row */}
        <div className="mb-4 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-foreground text-xl font-bold">
                {hotel.name}
              </h1>
              <StarIcons count={starCount} className="size-4" />
            </div>
            <div className="text-muted-foreground mt-1 flex items-center gap-2 text-sm">
              <MapPin className="size-4" />
              <span>{address}</span>
              <button className="text-blue-500 hover:underline">
                显示地图
              </button>
            </div>
            {/* Tags */}
            {hotel.tags.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {hotel.tags.slice(0, 5).map((tag) => (
                  <Badge
                    key={tag}
                    variant="secondary"
                    className="rounded-md text-xs"
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <span className="text-2xl font-bold text-orange-500">
                ¥{Math.round(estimatedPrice)}
              </span>
              <span className="text-muted-foreground text-sm">起</span>
            </div>
            <Button className="bg-blue-500 px-6 hover:bg-blue-600">
              选择房间
            </Button>
          </div>
        </div>

        {/* Image Gallery */}
        <div className="grid grid-cols-4 gap-2">
          {/* Main Image */}
          <div className="relative col-span-2 row-span-2 overflow-hidden rounded-lg">
            {hasImages ? (
              <Image
                src={hotel.images[0]}
                alt={hotel.name}
                fill
                unoptimized
                className="object-cover"
                sizes="(max-width: 768px) 100vw, 50vw"
              />
            ) : (
              <ImagePlaceholder className="aspect-[4/3] h-full w-full rounded-lg" />
            )}
          </div>
          {/* Thumbnail Images */}
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="relative aspect-[4/3] overflow-hidden rounded-lg"
            >
              {hotel.images[i] ? (
                <Image
                  src={hotel.images[i]}
                  alt={`${hotel.name} ${i}`}
                  fill
                  unoptimized
                  className="object-cover"
                  sizes="(max-width: 768px) 50vw, 25vw"
                />
              ) : (
                <ImagePlaceholder
                  className="h-full w-full rounded-lg"
                  iconClassName="size-8"
                />
              )}
              {i === 4 && hotel.images.length > 5 && (
                <div className="absolute inset-0 flex cursor-pointer items-center justify-center bg-black/50 text-white transition-colors hover:bg-black/60">
                  <div className="text-center">
                    <ImageIcon className="mx-auto mb-1 size-6" />
                    <span className="text-sm">
                      查看所有{hotel.images.length}张照片
                    </span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Hotel Info */}
        <div className="mt-6 grid grid-cols-3 gap-8">
          {/* Left: Facilities & Description */}
          <div className="col-span-2 space-y-6">
            {/* Facilities */}
            {hotel.amenities.length > 0 && (
              <div>
                <h2 className="text-foreground mb-4 text-base font-bold">
                  酒店设施
                </h2>
                <div className="grid grid-cols-4 gap-3">
                  {hotel.amenities.slice(0, 8).map((amenity, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-sm">
                      <AmenityIcon
                        name={amenity}
                        className="text-muted-foreground size-5"
                      />
                      <span className="text-foreground">{amenity}</span>
                    </div>
                  ))}
                </div>
                {hotel.amenities.length > 8 && (
                  <button className="mt-3 text-sm text-blue-500 hover:underline">
                    查看全部{hotel.amenities.length}项设施
                  </button>
                )}
              </div>
            )}

            {/* Description */}
            {hotel.information?.introduction && (
              <div>
                <h2 className="text-foreground mb-2 text-base font-bold">
                  酒店简介
                </h2>
                <p className="text-muted-foreground line-clamp-3 text-sm leading-relaxed">
                  {hotel.information.introduction}
                </p>
                <button className="mt-2 text-sm text-blue-500 hover:underline">
                  查看更多
                </button>
              </div>
            )}
          </div>

          {/* Right: Info Cards */}
          <div className="space-y-4">
            {/* Opening & Room Info */}
            {hotel.information && (
              <div className="bg-card rounded-lg border p-4">
                <h3 className="text-foreground mb-3 font-bold">酒店信息</h3>
                <div className="space-y-2 text-sm">
                  {hotel.information.openingSince > 0 && (
                    <div className="text-muted-foreground flex items-center gap-2">
                      <Calendar className="size-4" />
                      <span>开业: {hotel.information.openingSince}年</span>
                    </div>
                  )}
                  {hotel.information.roomCount > 0 && (
                    <div className="text-muted-foreground flex items-center gap-2">
                      <Bed className="size-4" />
                      <span>客房数: {hotel.information.roomCount}间</span>
                    </div>
                  )}
                  {hotel.information.phoneNumber && (
                    <div className="text-muted-foreground flex items-center gap-2">
                      <Phone className="size-4" />
                      <span>{hotel.information.phoneNumber}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Policy */}
            {hotel.policy && (
              <div className="bg-card rounded-lg border p-4">
                <h3 className="text-foreground mb-3 font-bold">入住政策</h3>
                <div className="space-y-2 text-sm">
                  {hotel.policy.checkInTime && (
                    <div className="text-muted-foreground flex items-center gap-2">
                      <Clock className="size-4" />
                      <span>
                        入住: {formatTime(hotel.policy.checkInTime, 14)}
                      </span>
                    </div>
                  )}
                  {hotel.policy.checkOutTime && (
                    <div className="text-muted-foreground flex items-center gap-2">
                      <Clock className="size-4" />
                      <span>
                        退房: {formatTime(hotel.policy.checkOutTime, 12)}
                      </span>
                    </div>
                  )}
                  <div className="text-muted-foreground flex items-center gap-2">
                    <PawPrint className="size-4" />
                    <span>
                      {hotel.policy.petsAllowed
                        ? "允许携带宠物"
                        : "不允许携带宠物"}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Room Selection Section */}
      <div className="bg-card rounded-xl border">
        {/* Tabs Navigation */}
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
              {/* Date & Guest Selector */}
              <div className="bg-muted mb-4 flex items-center gap-4 rounded-lg border p-3">
                <div className="flex items-center gap-2">
                  <Calendar className="text-muted-foreground size-5" />
                  <span className="font-medium">{dates.checkIn}</span>
                  <span className="text-muted-foreground text-sm">1晚</span>
                  <span className="font-medium">{dates.checkOut}</span>
                </div>
                <div className="flex items-center gap-2 border-l pl-4">
                  <User className="text-muted-foreground size-5" />
                  <span>1间, 1成人, 0儿童</span>
                </div>
              </div>

              {/* Room Type List */}
              <div className="space-y-6">
                {roomTypesWithSpus.length > 0 ? (
                  roomTypesWithSpus.map(({ roomType, spus }) => (
                    <RoomTypeCard
                      key={roomType.id}
                      roomType={roomType}
                      spus={spus}
                    />
                  ))
                ) : (
                  <div className="text-muted-foreground py-12 text-center">
                    <Building2 className="text-muted-foreground/50 mx-auto mb-4 size-16" />
                    <p>暂无可预订房型</p>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Other tab contents - placeholders */}
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
                    {hotel.amenities.map((amenity, idx) => (
                      <div
                        key={idx}
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
