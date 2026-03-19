"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import {
  MapPin,
  CalendarDays,
  Sparkles,
  Gauge,
  MessageSquare,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { type DateRange } from "react-day-picker";
import { zhCN } from "date-fns/locale";
import {
  createItineraryPlan,
  type TravelInterest,
  type TripPace,
} from "@/actions/itinerary";

const INTEREST_OPTIONS: { value: TravelInterest; label: string }[] = [
  { value: "culture", label: "文化体验" },
  { value: "classic", label: "经典打卡" },
  { value: "nature", label: "自然风光" },
  { value: "cityscape", label: "城市漫步" },
  { value: "history", label: "历史人文" },
];

const PACE_OPTIONS: { value: TripPace; label: string; desc: string }[] = [
  { value: "relaxed", label: "悠闲", desc: "每天 2 个活动" },
  { value: "moderate", label: "适中", desc: "每天 3 个活动" },
  { value: "intense", label: "紧凑", desc: "每天 4 个活动" },
];

function formatDateLabel(date: Date): string {
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
  return `${month}月${day}日(${weekdays[date.getDay()]})`;
}

interface ItineraryPlanFormProps {
  today: string;
}

export function ItineraryPlanForm({ today: todayStr }: ItineraryPlanFormProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const today = new Date(todayStr + "T00:00:00");
  const defaultEnd = new Date(today);
  defaultEnd.setDate(defaultEnd.getDate() + 2);

  const [destination, setDestination] = useState("");
  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: today,
    to: defaultEnd,
  });
  const [interests, setInterests] = useState<TravelInterest[]>([]);
  const [pace, setPace] = useState<TripPace>("moderate");
  const [additionalPreferences, setAdditionalPreferences] = useState("");
  const [error, setError] = useState<string | null>(null);

  const startDate = dateRange?.from ?? today;
  const endDate = dateRange?.to ?? defaultEnd;
  const days =
    Math.round(
      (endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24),
    ) + 1;

  function toggleInterest(interest: TravelInterest) {
    setInterests((prev) =>
      prev.includes(interest)
        ? prev.filter((i) => i !== interest)
        : [...prev, interest],
    );
  }

  function handleSubmit() {
    if (!destination.trim()) {
      setError("请输入目的地");
      return;
    }
    setError(null);

    startTransition(async () => {
      try {
        const result = await createItineraryPlan({
          destination: destination.trim(),
          startDate: startDate.toISOString().split("T")[0],
          endDate: endDate.toISOString().split("T")[0],
          interests,
          pace,
          additionalPreferences,
        });

        sessionStorage.setItem("itinerary_plan_result", JSON.stringify(result));
        router.push("/itinerary/planner");
      } catch (err) {
        setError(err instanceof Error ? err.message : "规划失败，请重试");
      }
    });
  }

  return (
    <div className="relative overflow-hidden rounded-2xl">
      {/* Background */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage:
            "url('https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=1920&q=80')",
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-blue-600/50 via-blue-500/30 to-blue-400/40" />

      {/* Content */}
      <div className="relative z-10 flex flex-col gap-8 px-10 pt-10 pb-14">
        <div>
          <h1 className="text-4xl font-bold text-white drop-shadow-md">
            AI 行程规划
            <Sparkles className="ml-2 inline-block size-7 text-amber-300" />
          </h1>
          <p className="mt-2 text-lg text-white/80">
            告诉我你的旅行偏好，AI 为你定制专属行程
          </p>
        </div>

        {/* Form Card */}
        <div className="flex flex-col gap-6 rounded-xl bg-white p-6 shadow-lg">
          {/* Row 1: Destination + Dates */}
          <div className="flex items-end gap-4">
            {/* Destination */}
            <div className="flex flex-1 flex-col gap-2">
              <Label className="flex items-center gap-1.5 text-sm font-medium text-gray-700">
                <MapPin className="size-4 text-blue-500" />
                目的地
              </Label>
              <Input
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="请输入目的地，例如：上海、杭州、北京"
                className="h-11"
              />
            </div>

            {/* Date Range */}
            <div className="flex flex-col gap-2">
              <Label className="flex items-center gap-1.5 text-sm font-medium text-gray-700">
                <CalendarDays className="size-4 text-blue-500" />
                出行日期
              </Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className="h-11 min-w-[260px] justify-start gap-2"
                  >
                    <span className="text-sm">
                      {formatDateLabel(startDate)} - {formatDateLabel(endDate)}
                    </span>
                    <Badge
                      variant="secondary"
                      className="ml-auto rounded-md bg-blue-50 px-1.5 py-0.5 text-xs font-medium text-blue-600"
                    >
                      {days}天
                    </Badge>
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="range"
                    defaultMonth={startDate}
                    selected={dateRange}
                    onSelect={setDateRange}
                    numberOfMonths={2}
                    disabled={{ before: today }}
                    locale={zhCN}
                  />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          {/* Row 2: Interests */}
          <div className="flex flex-col gap-2">
            <Label className="flex items-center gap-1.5 text-sm font-medium text-gray-700">
              <Sparkles className="size-4 text-blue-500" />
              旅行偏好
            </Label>
            <div className="flex flex-wrap gap-2">
              {INTEREST_OPTIONS.map((opt) => {
                const selected = interests.includes(opt.value);
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => toggleInterest(opt.value)}
                    className={`rounded-full border px-4 py-1.5 text-sm font-medium transition-colors ${
                      selected
                        ? "border-blue-500 bg-blue-50 text-blue-700"
                        : "border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Row 3: Pace */}
          <div className="flex flex-col gap-2">
            <Label className="flex items-center gap-1.5 text-sm font-medium text-gray-700">
              <Gauge className="size-4 text-blue-500" />
              行程节奏
            </Label>
            <div className="flex gap-3">
              {PACE_OPTIONS.map((opt) => {
                const selected = pace === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setPace(opt.value)}
                    className={`flex flex-col items-center rounded-lg border px-6 py-3 text-sm transition-colors ${
                      selected
                        ? "border-blue-500 bg-blue-50 text-blue-700"
                        : "border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    <span className="font-medium">{opt.label}</span>
                    <span className="mt-0.5 text-xs opacity-70">
                      {opt.desc}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Row 4: Additional Preferences */}
          <div className="flex flex-col gap-2">
            <Label className="flex items-center gap-1.5 text-sm font-medium text-gray-700">
              <MessageSquare className="size-4 text-blue-500" />
              其他偏好（选填）
            </Label>
            <textarea
              value={additionalPreferences}
              onChange={(e) => setAdditionalPreferences(e.target.value)}
              placeholder="例如：带小孩出行、偏好美食、预算有限……"
              rows={2}
              className="border-input placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 rounded-md border bg-transparent px-3 py-2 text-sm shadow-xs focus-visible:ring-[3px] focus-visible:outline-none"
            />
          </div>

          {/* Error */}
          {error && <p className="text-sm font-medium text-red-500">{error}</p>}

          {/* Submit */}
          <Button
            onClick={handleSubmit}
            disabled={isPending}
            className="h-12 cursor-pointer gap-2 bg-blue-600 text-base font-semibold text-white hover:bg-blue-700"
          >
            {isPending ? (
              <>
                <Loader2 className="size-5 animate-spin" />
                AI 正在规划中……
              </>
            ) : (
              <>
                <Sparkles className="size-5" />
                开始规划行程
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
