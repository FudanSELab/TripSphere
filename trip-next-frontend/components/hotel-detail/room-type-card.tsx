import Image from "next/image";
import { Bed, LayoutGrid, Building2, User } from "lucide-react";
import { ImagePlaceholder } from "@/components/image-placeholder";
import { AmenityIcon } from "./amenity-icon";
import { SkuRow } from "./sku-row";
import { getLowestSkuPrice, type RoomTypeWithSpus } from "@/lib/hotel-helpers";

export function RoomTypeCard({ roomType, spus }: RoomTypeWithSpus) {
  const lowestPrice = getLowestSkuPrice(spus);
  const hasImages = roomType.images.length > 0;

  return (
    <div className="rounded-lg border">
      <div className="bg-muted border-b px-4 py-3">
        <h3 className="text-foreground text-lg font-bold">{roomType.name}</h3>
      </div>

      <div className="flex">
        {/* Room Image & Info */}
        <div className="w-64 shrink-0 border-r p-4">
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
            {roomType.amenities.slice(0, 3).map((amenity) => (
              <div key={amenity} className="flex items-center gap-2">
                <AmenityIcon name={amenity} className="size-4" />
                <span className="text-blue-500">{amenity}</span>
              </div>
            ))}
          </div>
          <button className="mt-3 text-sm text-blue-500 hover:underline">
            房间详情
          </button>
        </div>

        {/* SKU Table */}
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
