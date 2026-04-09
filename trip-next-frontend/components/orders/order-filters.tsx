"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const TYPE_OPTIONS = [
  { value: "", label: "全部类型" },
  { value: "1", label: "景点门票" },
  { value: "2", label: "酒店住宿" },
  { value: "3", label: "机票" },
  { value: "4", label: "火车票" },
] as const;

export function OrderFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentType = searchParams.get("type") ?? "";

  const handleTypeChange = useCallback(
    (value: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value) {
        params.set("type", value);
      } else {
        params.delete("type");
      }
      params.delete("page");
      router.push(`/orders?${params.toString()}`);
    },
    [router, searchParams],
  );

  return (
    <div className="flex items-center gap-2">
      <span className="text-muted-foreground text-sm">订单类型</span>
      <div className="flex gap-1">
        {TYPE_OPTIONS.map((opt) => (
          <Button
            key={opt.value}
            variant={currentType === opt.value ? "default" : "ghost"}
            size="sm"
            className={cn(
              "h-7 text-xs",
              currentType === opt.value && "pointer-events-none",
            )}
            onClick={() => handleTypeChange(opt.value)}
          >
            {opt.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
