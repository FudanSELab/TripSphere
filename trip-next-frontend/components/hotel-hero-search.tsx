"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  MapPin,
  CalendarDays,
  Users,
  Search,
  X,
  Minus,
  Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { type DateRange } from "react-day-picker";
import { zhCN } from "date-fns/locale";
import { cn } from "@/lib/utils";
import { formatDate } from "@/lib/format";

function calcNights(checkIn: Date, checkOut: Date): number {
  const diff = checkOut.getTime() - checkIn.getTime();
  return Math.max(1, Math.round(diff / (1000 * 60 * 60 * 24)));
}

interface HotelHeroSearchProps {
  // Pass a stable "today" string (YYYY-MM-DD) from the Server Component
  // so the server and client render the same initial dates (no hydration mismatch).
  today: string;
}

export function HotelHeroSearch({ today: todayStr }: HotelHeroSearchProps) {
  const router = useRouter();

  const today = new Date(todayStr + "T00:00:00");
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  const [location, setLocation] = useState("上海");
  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: today,
    to: tomorrow,
  });
  const [rooms, setRooms] = useState(1);
  const [adults, setAdults] = useState(1);
  const [children, setChildren] = useState(0);
  const [keyword, setKeyword] = useState("");
  const checkIn = dateRange?.from ?? today;
  const checkOut = dateRange?.to ?? tomorrow;
  const nights = calcNights(checkIn, checkOut);

  const handleSearch = () => {
    const params = new URLSearchParams();
    if (location) params.set("city", location);
    if (keyword) params.set("keyword", keyword);
    params.set("checkIn", checkIn.toISOString().split("T")[0]);
    params.set("checkOut", checkOut.toISOString().split("T")[0]);
    params.set("rooms", String(rooms));
    params.set("adults", String(adults));
    params.set("children", String(children));
    router.push(`/hotels?${params.toString()}`);
  };

  return (
    <div className="relative overflow-hidden rounded-2xl">
      <div
        className="absolute inset-0 bg-cover bg-center"
        aria-hidden="true"
        style={{
          backgroundImage:
            "url('https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=1920&q=80')",
        }}
      />
      <div
        className="from-primary/40 via-primary/20 to-primary/30 absolute inset-0 bg-gradient-to-b"
        aria-hidden="true"
      />

      <div className="relative z-10 flex flex-col gap-8 px-10 pt-10 pb-14">
        <h1 className="text-4xl font-bold text-white drop-shadow-md">
          酒店
          <span
            className="bg-price ml-1 inline-block size-2.5 rounded-full"
            aria-hidden="true"
          />
        </h1>

        <div className="bg-card flex h-14 items-center rounded-xl p-2 shadow-lg">
          <SearchField className="w-1/6">
            <MapPin
              className="text-primary size-4 shrink-0"
              aria-hidden="true"
            />
            <span className="text-foreground text-sm font-medium">
              {location || "目的地"}
            </span>
            {location && (
              <button
                onClick={() => setLocation("")}
                aria-label="清除目的地"
                className="text-muted-foreground hover:bg-accent hover:text-foreground ml-auto rounded-full p-0.5 transition-colors"
              >
                <X className="size-3.5" aria-hidden="true" />
              </button>
            )}
          </SearchField>

          <Separator orientation="vertical" className="mx-1" />

          <Popover>
            <PopoverTrigger asChild>
              <button
                aria-label={`入住日期 ${formatDate(checkIn)} 退房日期 ${formatDate(checkOut)} 共 ${nights} 晚`}
                className="hover:bg-accent flex min-w-[220px] cursor-pointer items-center gap-2 rounded-lg px-3 py-2 transition-colors"
              >
                <CalendarDays
                  className="text-primary size-4 shrink-0"
                  aria-hidden="true"
                />
                <span className="text-foreground text-sm font-medium">
                  {formatDate(checkIn)}
                </span>
                <span
                  className="text-muted-foreground mx-3 text-xs"
                  aria-hidden="true"
                >
                  -
                </span>
                <span className="text-foreground text-sm font-medium">
                  {formatDate(checkOut)}
                </span>
                <Badge
                  variant="secondary"
                  className="bg-primary/10 text-primary ml-1 rounded-md px-1.5 py-0.5 text-xs font-medium"
                  aria-hidden="true"
                >
                  {nights}晚
                </Badge>
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="range"
                defaultMonth={checkIn}
                selected={dateRange}
                onSelect={setDateRange}
                numberOfMonths={2}
                disabled={{ before: today }}
                locale={zhCN}
              />
              <p className="text-muted-foreground px-3 pb-3 text-xs">
                所有日期均为当地时间
              </p>
            </PopoverContent>
          </Popover>

          <Separator orientation="vertical" className="mx-1" />

          <Popover>
            <PopoverTrigger asChild>
              <button
                aria-label={`房间和住客：${rooms}间, ${adults}成人, ${children}儿童`}
                className="hover:bg-accent flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 transition-colors"
              >
                <Users
                  className="text-primary size-4 shrink-0"
                  aria-hidden="true"
                />
                <span className="text-foreground text-sm font-medium">
                  {rooms}间, {adults}成人, {children}儿童
                </span>
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-72" align="start">
              <div className="flex flex-col gap-4">
                <GuestCounterRow
                  label="房间"
                  value={rooms}
                  min={1}
                  max={adults}
                  onDecrement={() => setRooms((r) => Math.max(1, r - 1))}
                  onIncrement={() => setRooms((r) => Math.min(adults, r + 1))}
                />
                <GuestCounterRow
                  label="成人"
                  description="18岁及以上"
                  value={adults}
                  min={rooms}
                  max={30}
                  onDecrement={() => setAdults((a) => Math.max(rooms, a - 1))}
                  onIncrement={() => setAdults((a) => a + 1)}
                />
                <GuestCounterRow
                  label="儿童"
                  description="0-17岁"
                  value={children}
                  min={0}
                  max={10}
                  onDecrement={() => setChildren((c) => Math.max(0, c - 1))}
                  onIncrement={() => setChildren((c) => c + 1)}
                />
              </div>
            </PopoverContent>
          </Popover>

          <Separator orientation="vertical" className="mx-1" />

          <div className="hover:bg-accent flex flex-1 items-center rounded-lg px-3">
            <label htmlFor="hotel-keyword-search" className="sr-only">
              酒店关键词搜索
            </label>
            <Input
              id="hotel-keyword-search"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="位置/品牌/酒店（选填）…"
              className="placeholder:text-muted-foreground/70 h-9 border-none bg-transparent px-0 text-sm shadow-none focus-visible:ring-0"
            />
          </div>

          <Button
            onClick={handleSearch}
            className="ml-2 h-10 cursor-pointer gap-1.5 rounded-lg px-6"
          >
            <Search className="size-4" aria-hidden="true" />
            搜索
          </Button>
        </div>
      </div>
    </div>
  );
}

function SearchField({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "hover:bg-accent flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 transition-colors",
        className,
      )}
    >
      {children}
    </div>
  );
}

function GuestCounterRow({
  label,
  description,
  value,
  min,
  max,
  onDecrement,
  onIncrement,
}: {
  label: string;
  description?: string;
  value: number;
  min: number;
  max: number;
  onDecrement: () => void;
  onIncrement: () => void;
}) {
  const canDecrement = value > min;
  const canIncrement = value < max;

  return (
    <div className="flex items-center justify-between">
      <div className="flex flex-col">
        <span className="text-foreground text-sm font-medium">{label}</span>
        {description && (
          <span className="text-muted-foreground text-xs">{description}</span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <Button
          variant="outline"
          size="icon"
          className="size-8 rounded-full"
          disabled={!canDecrement}
          onClick={onDecrement}
          aria-label={`减少${label}`}
        >
          <Minus className="size-3.5" aria-hidden="true" />
        </Button>
        <span
          className="w-5 text-center text-sm font-medium"
          aria-live="polite"
        >
          {value}
        </span>
        <Button
          variant="outline"
          size="icon"
          className="size-8 rounded-full"
          disabled={!canIncrement}
          onClick={onIncrement}
          aria-label={`增加${label}`}
        >
          <Plus className="size-3.5" aria-hidden="true" />
        </Button>
      </div>
    </div>
  );
}
