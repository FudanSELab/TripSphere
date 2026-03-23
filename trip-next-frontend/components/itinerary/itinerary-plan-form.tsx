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
import { Textarea } from "@/components/ui/textarea";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { type DateRange } from "react-day-picker";
import { zhCN } from "date-fns/locale";
import { cn } from "@/lib/utils";
import { formatDate } from "@/lib/format";
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
    <div className="bg-card flex flex-col gap-6 rounded-xl border p-6 shadow-lg">
      <div className="flex items-end gap-4">
        <div className="flex flex-1 flex-col gap-2">
          <Label className="flex items-center gap-1.5">
            <MapPin className="text-primary size-4" />
            目的地
          </Label>
          <Input
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="请输入目的地，例如：上海、杭州、北京…"
            className="h-11"
          />
        </div>

        <div className="flex flex-col gap-2">
          <Label className="flex items-center gap-1.5">
            <CalendarDays className="text-primary size-4" />
            出行日期
          </Label>
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className="h-11 min-w-[260px] justify-start gap-2"
              >
                <span className="text-sm">
                  {formatDate(startDate)} - {formatDate(endDate)}
                </span>
                <Badge
                  variant="secondary"
                  className="bg-primary/10 text-primary ml-auto rounded-md px-1.5 py-0.5 text-xs font-medium"
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

      <div className="flex flex-col gap-2">
        <Label className="flex items-center gap-1.5">
          <Sparkles className="text-primary size-4" />
          旅行偏好
        </Label>
        <ToggleGroup
          type="multiple"
          value={interests}
          onValueChange={(v) => setInterests(v as TravelInterest[])}
          className="flex flex-wrap justify-start gap-2"
        >
          {INTEREST_OPTIONS.map((opt) => (
            <ToggleGroupItem
              key={opt.value}
              value={opt.value}
              className={cn(
                "rounded-full border px-4 py-1.5 text-sm font-medium",
                "data-[state=on]:bg-primary/10 data-[state=on]:text-primary data-[state=on]:border-primary/40",
              )}
            >
              {opt.label}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>

      <div className="flex flex-col gap-2">
        <Label className="flex items-center gap-1.5">
          <Gauge className="text-primary size-4" />
          行程节奏
        </Label>
        <ToggleGroup
          type="single"
          value={pace}
          onValueChange={(v) => v && setPace(v as TripPace)}
          className="flex justify-start gap-3"
        >
          {PACE_OPTIONS.map((opt) => (
            <ToggleGroupItem
              key={opt.value}
              value={opt.value}
              className={cn(
                "flex h-auto min-h-0 flex-col items-center justify-center gap-0.5 rounded-lg border px-6 py-3 text-sm",
                "data-[state=on]:bg-primary/10 data-[state=on]:text-primary data-[state=on]:border-primary/40",
              )}
            >
              <span className="font-medium">{opt.label}</span>
              <span className="text-xs opacity-70">{opt.desc}</span>
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>

      <div className="flex flex-col gap-2">
        <Label className="flex items-center gap-1.5">
          <MessageSquare className="text-primary size-4" />
          其他偏好（选填）
        </Label>
        <Textarea
          value={additionalPreferences}
          onChange={(e) => setAdditionalPreferences(e.target.value)}
          placeholder="例如：带小孩出行、偏好美食、预算有限…"
          rows={2}
        />
      </div>

      {error && <p className="text-destructive text-sm font-medium">{error}</p>}

      <Button
        onClick={handleSubmit}
        disabled={isPending}
        className="h-12 cursor-pointer gap-2 text-base font-semibold"
      >
        {isPending ? (
          <>
            <Loader2 className="size-5 animate-spin" />
            AI正在规划中…
          </>
        ) : (
          <>
            <Sparkles className="size-5" />
            开始规划行程
          </>
        )}
      </Button>
    </div>
  );
}
