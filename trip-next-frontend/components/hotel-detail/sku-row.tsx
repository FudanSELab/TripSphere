import {
  User,
  Utensils,
  CheckCircle,
  XCircle,
  Zap,
  CreditCard,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatMoney } from "@/lib/format";
import type { Sku } from "@/lib/grpc/generated/tripsphere/product/v1/product";

interface SkuRowProps {
  sku: Sku;
  maxOccupancy: number;
  isLast: boolean;
}

export function SkuRow({ sku, maxOccupancy, isLast }: SkuRowProps) {
  const price = formatMoney(sku.basePrice);
  const attrs = sku.attributes as Record<string, unknown> | undefined;
  const hasBreakfast = attrs?.breakfast === true;
  const cancellable = attrs?.cancellable === true;
  const instantConfirm = attrs?.instant_confirm !== false;

  return (
    <tr className={!isLast ? "border-b" : ""}>
      <td className="px-4 py-4">
        <div className="flex flex-col gap-1 text-sm">
          <div className="text-foreground font-medium">{sku.name}</div>
          <div className="flex items-center gap-2">
            <Utensils
              className={`size-4 ${hasBreakfast ? "text-success" : "text-muted-foreground"}`}
            />
            <span
              className={
                hasBreakfast ? "text-success" : "text-muted-foreground"
              }
            >
              {hasBreakfast ? "含早餐" : "无早餐"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {cancellable ? (
              <CheckCircle className="text-success size-4" />
            ) : (
              <XCircle className="text-muted-foreground size-4" />
            )}
            <span
              className={cancellable ? "text-success" : "text-muted-foreground"}
            >
              {cancellable ? "可取消" : "不可取消"}
            </span>
          </div>
          {instantConfirm && (
            <div className="flex items-center gap-2">
              <Zap className="text-success size-4" />
              <span className="text-success">立即确认</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <CreditCard className="text-muted-foreground size-4" />
            <span className="text-muted-foreground">在线付</span>
          </div>
        </div>
      </td>

      <td className="px-4 py-4 text-center">
        <div className="flex items-center justify-center gap-0.5">
          {Array.from({ length: maxOccupancy }).map((_, i) => (
            <User key={i} className="text-muted-foreground size-5" />
          ))}
        </div>
      </td>

      <td className="px-4 py-4">
        <div className="flex flex-col items-end gap-2">
          <span className="text-price text-xl font-bold">
            ¥{Math.round(price)}
          </span>
          <Button size="sm" className="px-6">
            预订
          </Button>
        </div>
      </td>
    </tr>
  );
}
