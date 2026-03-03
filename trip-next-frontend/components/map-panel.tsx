"use client";

import { Map } from "lucide-react";

export function MapPanel() {
  return (
    <div className="flex h-full flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50">
      <Map className="size-12 text-gray-300" />
      <p className="mt-3 text-sm font-medium text-gray-400">地图视图</p>
      <p className="mt-1 text-xs text-gray-300">即将上线</p>
    </div>
  );
}
