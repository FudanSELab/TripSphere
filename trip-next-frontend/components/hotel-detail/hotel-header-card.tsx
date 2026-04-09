import Image from "next/image";
import {
  MapPin,
  Calendar,
  Bed,
  Phone,
  Clock,
  PawPrint,
  Image as ImageIcon,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ImagePlaceholder } from "@/components/image-placeholder";
import { StarIcons } from "@/components/star-icons";
import { AmenityIcon } from "./amenity-icon";
import { getStarCount, getFullAddress, formatTime } from "@/lib/hotel-helpers";
import { formatMoney } from "@/lib/format";
import type { Hotel } from "@/lib/grpc/generated/tripsphere/hotel/v1/hotel";

interface HotelHeaderCardProps {
  hotel: Hotel;
}

export function HotelHeaderCard({ hotel }: HotelHeaderCardProps) {
  const starCount = getStarCount(hotel.tags);
  const address = getFullAddress(hotel);
  const estimatedPrice = formatMoney(hotel.estimatedPrice);
  const hasImages = hotel.images.length > 0;

  return (
    <div className="bg-card rounded-xl border p-6">
      <div className="mb-4 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-foreground text-xl font-bold">{hotel.name}</h1>
            <StarIcons count={starCount} className="size-4" />
          </div>
          <div className="text-muted-foreground mt-1 flex items-center gap-2 text-sm">
            <MapPin className="size-4" />
            <span>{address}</span>
            <Button variant="link" size="sm" className="h-auto p-0 text-sm">
              显示地图
            </Button>
          </div>
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
            <span className="text-price text-2xl font-bold">
              ¥{Math.round(estimatedPrice)}
            </span>
            <span className="text-muted-foreground text-sm">起</span>
          </div>
          <Button className="px-6">选择房间</Button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2">
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

      <div className="mt-6 grid grid-cols-3 gap-8">
        <div className="col-span-2 flex flex-col gap-6">
          {hotel.amenities.length > 0 && (
            <div>
              <h2 className="text-foreground mb-4 text-base font-bold">
                酒店设施
              </h2>
              <div className="grid grid-cols-4 gap-3">
                {hotel.amenities.slice(0, 8).map((amenity) => (
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
              {hotel.amenities.length > 8 && (
                <Button
                  variant="link"
                  size="sm"
                  className="mt-3 h-auto p-0 text-sm"
                >
                  查看全部{hotel.amenities.length}项设施
                </Button>
              )}
            </div>
          )}

          {hotel.information?.introduction && (
            <div>
              <h2 className="text-foreground mb-2 text-base font-bold">
                酒店简介
              </h2>
              <p className="text-muted-foreground line-clamp-3 text-sm leading-relaxed">
                {hotel.information.introduction}
              </p>
              <Button
                variant="link"
                size="sm"
                className="mt-2 h-auto p-0 text-sm"
              >
                查看更多
              </Button>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-4">
          {hotel.information && (
            <div className="bg-card rounded-lg border p-4">
              <h3 className="text-foreground mb-3 font-bold">酒店信息</h3>
              <div className="flex flex-col gap-2 text-sm">
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

          {hotel.policy && (
            <div className="bg-card rounded-lg border p-4">
              <h3 className="text-foreground mb-3 font-bold">入住政策</h3>
              <div className="flex flex-col gap-2 text-sm">
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
  );
}
