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
      {/* Background Image */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage:
            "url('https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=1920&q=80')",
        }}
      />
      {/* Overlay gradient for better text readability */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-600/40 via-blue-500/20 to-blue-400/30" />

      {/* Content */}
      <div className="relative z-10 flex flex-col gap-8 px-10 pt-10 pb-14">
        {/* Title */}
        <h1 className="text-4xl font-bold text-white drop-shadow-md">
          酒店
          <span className="ml-1 inline-block size-2.5 rounded-full bg-amber-400" />
        </h1>

        {/* Search Card */}
        <div className="bg-card flex h-14 items-center rounded-xl p-2 shadow-lg">
          {/* Location */}
          <SearchField className="w-1/6">
            <MapPin className="size-4 shrink-0 text-blue-500" />
            <span className="text-foreground text-sm font-medium">
              {location || "目的地"}
            </span>
            {location && (
              <button
                onClick={() => setLocation("")}
                className="text-muted-foreground hover:bg-accent hover:text-foreground ml-auto rounded-full p-0.5 transition-colors"
              >
                <X className="size-3.5" />
              </button>
            )}
          </SearchField>

          <Separator orientation="vertical" className="mx-1" />

          {/* Date Range */}
          <Popover>
            <PopoverTrigger asChild>
              <button className="hover:bg-accent flex min-w-[220px] cursor-pointer items-center gap-2 rounded-lg px-3 py-2 transition-colors">
                <CalendarDays className="size-4 shrink-0 text-blue-500" />
                <span className="text-foreground text-sm font-medium">
                  {formatDate(checkIn)}
                </span>
                <span className="text-muted-foreground mx-3 text-xs">-</span>
                <span className="text-foreground text-sm font-medium">
                  {formatDate(checkOut)}
                </span>
                <Badge
                  variant="secondary"
                  className="ml-1 rounded-md bg-blue-50 px-1.5 py-0.5 text-xs font-medium text-blue-600"
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

          {/* Rooms & Guests */}
          <Popover>
            <PopoverTrigger asChild>
              <button className="hover:bg-accent flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 transition-colors">
                <Users className="size-4 shrink-0 text-blue-500" />
                <span className="text-foreground text-sm font-medium">
                  {rooms}间, {adults}成人, {children}儿童
                </span>
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-72" align="start">
              <div className="flex flex-col gap-4">
                {/* Constraint: rooms >= 1, rooms <= adults */}
                <GuestCounterRow
                  label="房间"
                  value={rooms}
                  min={1}
                  max={adults}
                  onDecrement={() => setRooms((r) => Math.max(1, r - 1))}
                  onIncrement={() => setRooms((r) => Math.min(adults, r + 1))}
                />
                {/* Constraint: adults >= 1, adults >= rooms */}
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

          {/* Keyword */}
          <div className="hover:bg-accent flex flex-1 items-center rounded-lg px-3">
            <Input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="位置/品牌/酒店（选填）"
              className="placeholder:text-muted-foreground/70 h-9 border-none bg-transparent px-0 text-sm shadow-none focus-visible:ring-0"
            />
          </div>

          {/* Search Button */}
          <Button
            onClick={handleSearch}
            className="ml-2 h-10 cursor-pointer gap-1.5 rounded-lg bg-blue-600 px-6 text-white hover:bg-blue-700"
          >
            <Search className="size-4" />
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
        >
          <Minus className="size-3.5" />
        </Button>
        <span className="w-5 text-center text-sm font-medium">{value}</span>
        <Button
          variant="outline"
          size="icon"
          className="size-8 rounded-full"
          disabled={!canIncrement}
          onClick={onIncrement}
        >
          <Plus className="size-3.5" />
        </Button>
      </div>
    </div>
  );
}
