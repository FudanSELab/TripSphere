"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

const STATUS_TABS = [
  { value: "", label: "全部订单" },
  { value: "1", label: "待支付" },
  { value: "2", label: "已付款" },
  { value: "3", label: "已完成" },
  { value: "4", label: "已取消" },
] as const;

export function OrderTabs({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentStatus = searchParams.get("status") ?? "";

  const handleTabChange = useCallback(
    (value: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value) {
        params.set("status", value);
      } else {
        params.delete("status");
      }
      params.delete("page");
      router.push(`/orders?${params.toString()}`);
    },
    [router, searchParams],
  );

  return (
    <Tabs value={currentStatus} onValueChange={handleTabChange}>
      <TabsList variant="line" className="w-full justify-start">
        {STATUS_TABS.map((tab) => (
          <TabsTrigger key={tab.value} value={tab.value} className="text-base">
            {tab.label}
          </TabsTrigger>
        ))}
      </TabsList>
      {children}
    </Tabs>
  );
}
