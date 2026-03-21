"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { MapPin, Search, Compass } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const CITIES = ["上海", "南京", "北京", "成都", "杭州", "广州", "西安"];

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
  const [cityOpen, setCityOpen] = useState(false);

  function handleSearch() {
    const params = new URLSearchParams();
    if (city) params.set("city", city);
    if (keyword.trim()) params.set("keyword", keyword.trim());
    router.push(`/attractions?${params.toString()}`);
  }

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-teal-700 via-teal-600 to-emerald-600 px-6 py-10 text-white shadow-lg">
      {/* Decorative background elements */}
      <div className="pointer-events-none absolute -right-8 -top-8 h-48 w-48 rounded-full bg-white/5" />
      <div className="pointer-events-none absolute -bottom-10 right-20 h-36 w-36 rounded-full bg-white/5" />
      <Compass className="pointer-events-none absolute right-10 top-8 h-24 w-24 text-white/10" />

      <div className="relative z-10 flex flex-col gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">探索景点</h1>
          <p className="mt-1 text-teal-100">发现城市里值得一去的每一处精彩</p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          {/* City selector */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setCityOpen((o) => !o)}
              className="flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2.5 text-sm font-medium backdrop-blur-sm transition hover:bg-white/25"
            >
              <MapPin className="h-4 w-4 shrink-0" />
              <span>{city || "选择城市"}</span>
              <svg
                className={`h-3 w-3 transition-transform ${cityOpen ? "rotate-180" : ""}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>
            {cityOpen && (
              <div className="absolute left-0 top-full z-20 mt-1 min-w-[140px] overflow-hidden rounded-xl bg-white shadow-xl">
                {CITIES.map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => {
                      setCity(c);
                      setCityOpen(false);
                    }}
                    className={`block w-full px-4 py-2 text-left text-sm transition hover:bg-teal-50 ${
                      city === c
                        ? "font-semibold text-teal-700"
                        : "text-gray-700"
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Keyword search */}
          <div className="flex flex-1 items-center gap-2 rounded-xl bg-white/15 px-4 py-1 backdrop-blur-sm">
            <Search className="h-4 w-4 shrink-0 text-white/70" />
            <Input
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
            className="shrink-0 bg-white font-semibold text-teal-700 shadow-md hover:bg-teal-50 hover:text-teal-800"
          >
            <Search className="mr-1.5 h-4 w-4" />
            搜索
          </Button>
        </div>
      </div>
    </div>
  );
}
