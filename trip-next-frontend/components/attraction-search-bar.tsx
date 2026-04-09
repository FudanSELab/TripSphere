"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { MapPin, Search, Compass, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

const CITIES = ["上海", "广州", "北京", "南京", "成都", "杭州", "西安"];

interface AttractionSearchBarProps {
  defaultCity?: string;
  defaultKeyword?: string;
}

export function AttractionSearchBar({
  defaultCity = "上海",
  defaultKeyword = "",
}: AttractionSearchBarProps) {
  const router = useRouter();
  const [city, setCity] = useState(defaultCity);
  const [keyword, setKeyword] = useState(defaultKeyword);
  const [open, setOpen] = useState(false);

  function handleSearch() {
    const params = new URLSearchParams();
    if (city) params.set("city", city);
    if (keyword.trim()) params.set("keyword", keyword.trim());
    router.push(`/attractions?${params.toString()}`);
  }

  return (
    <div className="from-primary/40 via-primary/20 to-primary/30 relative overflow-hidden rounded-2xl bg-gradient-to-b px-6 py-10 text-white shadow-lg">
      <div
        className="from-primary/50 to-primary/30 absolute inset-0 bg-gradient-to-r"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute -top-8 -right-8 size-48 rounded-full bg-white/5"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute right-20 -bottom-10 size-36 rounded-full bg-white/5"
        aria-hidden="true"
      />
      <Compass
        className="pointer-events-none absolute top-8 right-10 size-24 text-white/10"
        aria-hidden="true"
      />

      <div className="relative z-10 flex flex-col gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">探索景点</h1>
          <p className="mt-1 text-white/80">发现城市里值得一去的每一处精彩</p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
              <button
                type="button"
                aria-label={`选择城市，当前: ${city || "未选择"}`}
                className="flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2.5 text-sm font-medium backdrop-blur-sm transition hover:bg-white/25"
              >
                <MapPin className="size-4 shrink-0" />
                <span>{city || "选择城市"}</span>
                <ChevronDown
                  className={cn(
                    "size-3 transition-transform",
                    open && "rotate-180",
                  )}
                />
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-36 p-1" align="start">
              {CITIES.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => {
                    setCity(c);
                    setOpen(false);
                  }}
                  className={cn(
                    "hover:bg-accent block w-full rounded-md px-3 py-2 text-left text-sm transition",
                    city === c
                      ? "text-primary font-semibold"
                      : "text-foreground",
                  )}
                >
                  {c}
                </button>
              ))}
            </PopoverContent>
          </Popover>

          <div className="flex flex-1 items-center gap-2 rounded-xl bg-white/15 px-4 py-1 backdrop-blur-sm">
            <Search
              className="size-4 shrink-0 text-white/70"
              aria-hidden="true"
            />
            <label htmlFor="attraction-keyword-search" className="sr-only">
              景点关键词搜索
            </label>
            <Input
              id="attraction-keyword-search"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="搜索景点名称、特色..."
              className="h-8 border-0 bg-transparent p-0 text-white placeholder:text-white/60 focus-visible:ring-0"
            />
          </div>

          <Button
            onClick={handleSearch}
            size="lg"
            variant="secondary"
            className="shrink-0 font-semibold shadow-md"
          >
            <Search className="size-4" data-icon="inline-start" />
            搜索
          </Button>
        </div>
      </div>
    </div>
  );
}
