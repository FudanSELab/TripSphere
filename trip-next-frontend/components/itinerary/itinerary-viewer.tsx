"use client";

import { useState } from "react";
import Markdown from "react-markdown";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Itinerary, DayPlan, Activity } from "@/actions/itinerary";
import { formatDateMonthDaySlash, formatDateWithWeekday } from "@/lib/format";

const CATEGORY_META: Record<
  string,
  {
    icon: string;
    label: string;
    bg: string;
    text: string;
    dot: string;
    bar: string;
  }
> = {
  transportation: {
    icon: "✈️",
    label: "交通",
    bg: "bg-category-1/10",
    text: "text-category-1",
    dot: "bg-category-1/60",
    bar: "bg-category-1/40",
  },
  sightseeing: {
    icon: "🏛️",
    label: "观光",
    bg: "bg-category-2/10",
    text: "text-category-2",
    dot: "bg-category-2/60",
    bar: "bg-category-2/40",
  },
  cultural: {
    icon: "🎭",
    label: "文化",
    bg: "bg-category-3/10",
    text: "text-category-3",
    dot: "bg-category-3/60",
    bar: "bg-category-3/40",
  },
  shopping: {
    icon: "🛍️",
    label: "购物",
    bg: "bg-category-4/10",
    text: "text-category-4",
    dot: "bg-category-4/60",
    bar: "bg-category-4/40",
  },
  dining: {
    icon: "🍜",
    label: "美食",
    bg: "bg-category-5/10",
    text: "text-category-5",
    dot: "bg-category-5/60",
    bar: "bg-category-5/40",
  },
  entertainment: {
    icon: "🎪",
    label: "娱乐",
    bg: "bg-category-6/10",
    text: "text-category-6",
    dot: "bg-category-6/60",
    bar: "bg-category-6/40",
  },
  nature: {
    icon: "🌿",
    label: "自然",
    bg: "bg-category-7/10",
    text: "text-category-7",
    dot: "bg-category-7/60",
    bar: "bg-category-7/40",
  },
  custom: {
    icon: "📍",
    label: "自定义",
    bg: "bg-category-8/10",
    text: "text-category-8",
    dot: "bg-category-8/60",
    bar: "bg-category-8/40",
  },
};

const DEFAULT_META = {
  icon: "📍",
  label: "活动",
  bg: "bg-muted",
  text: "text-muted-foreground",
  dot: "bg-muted-foreground/60",
  bar: "bg-muted-foreground/40",
};

function getCategoryMeta(activity: Activity) {
  if (activity.kind === "transport")
    return CATEGORY_META["transportation"] ?? DEFAULT_META;
  if (activity.kind === "hotel_stay")
    return {
      icon: "🛏️",
      label: "住宿",
      bg: "bg-category-9/10",
      text: "text-category-9",
      dot: "bg-category-9/60",
      bar: "bg-category-9/40",
    };
  return CATEGORY_META[activity.category] ?? DEFAULT_META;
}

function safeNotes(value: string | null | undefined): string {
  if (!value || value === "undefined" || value === "null") return "";
  return value;
}

function durationMinutes(start: string, end: string): number {
  const [sh, sm] = start.split(":").map(Number);
  const [eh, em] = end.split(":").map(Number);
  return eh * 60 + em - (sh * 60 + sm);
}

function formatDuration(mins: number): string {
  if (mins <= 0) return "";
  if (mins < 60) return `${mins}分钟`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m > 0 ? `${h}小时${m}分` : `${h}小时`;
}

type TimePeriod = "morning" | "afternoon" | "evening";

function getTimePeriod(startTime: string): TimePeriod {
  const hour = parseInt(startTime.split(":")[0], 10);
  if (hour < 12) return "morning";
  if (hour < 18) return "afternoon";
  return "evening";
}

const PERIOD_LABEL: Record<
  TimePeriod,
  { label: string; icon: string; color: string }
> = {
  morning: { label: "上午", icon: "🌅", color: "text-price" },
  afternoon: { label: "下午", icon: "☀️", color: "text-price" },
  evening: { label: "傍晚 / 夜间", icon: "🌙", color: "text-primary" },
};

function TripHeader({ itinerary }: { itinerary: Itinerary }) {
  const totalCost = itinerary.summary?.total_estimated_cost ?? 0;
  const totalActivities = itinerary.summary?.total_activities ?? 0;
  const days = itinerary.day_plans.length;

  return (
    <div className="from-primary to-primary/80 text-primary-foreground shrink-0 bg-gradient-to-r px-5 py-4">
      <h1 className="text-lg leading-tight font-bold tracking-wide">
        {itinerary.destination} 旅行行程
      </h1>
      <p className="text-primary-foreground/70 mt-0.5 text-xs">
        {itinerary.start_date} — {itinerary.end_date}
      </p>
      <div className="mt-3 flex gap-4 text-xs">
        <div className="flex flex-col items-center rounded-lg bg-white/15 px-3 py-1.5">
          <span className="text-base font-bold">{days}</span>
          <span className="text-primary-foreground/70">天</span>
        </div>
        <div className="flex flex-col items-center rounded-lg bg-white/15 px-3 py-1.5">
          <span className="text-base font-bold">{totalActivities}</span>
          <span className="text-primary-foreground/70">活动</span>
        </div>
        {totalCost > 0 && (
          <div className="flex flex-col items-center rounded-lg bg-white/15 px-3 py-1.5">
            <span className="text-base font-bold">
              ¥{totalCost.toLocaleString()}
            </span>
            <span className="text-primary-foreground/70">预算</span>
          </div>
        )}
      </div>
    </div>
  );
}

function DayCard({ day, onClick }: { day: DayPlan; onClick: () => void }) {
  const { date, weekday } = formatDateWithWeekday(day.date);
  const notes = safeNotes(day.notes);
  const dayCost = day.activities.reduce(
    (s, a) => s + (a.estimated_cost?.amount ?? 0),
    0,
  );

  // Take first 3 categories for the color strip
  const categories = [
    ...new Set(
      day.activities.map((a) =>
        a.kind === "hotel_stay"
          ? "hotel"
          : a.kind === "transport"
            ? "transportation"
            : a.category,
      ),
    ),
  ].slice(0, 4);

  return (
    <button
      onClick={onClick}
      className="border-border bg-card group hover:border-primary/30 w-full rounded-xl border text-left shadow-sm transition-all hover:shadow-md active:scale-[.985]"
    >
      <div className="flex gap-0 overflow-hidden rounded-xl">
        <div className="flex w-1.5 shrink-0 flex-col">
          {categories.length > 0 ? (
            categories.map((cat, i) => (
              <div
                key={i}
                className={`flex-1 ${(CATEGORY_META[cat] ?? DEFAULT_META).bar}`}
                style={{ minHeight: "12px" }}
              />
            ))
          ) : (
            <div className="bg-border flex-1" />
          )}
        </div>

        <div className="flex flex-1 flex-col gap-2 p-3.5">
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-foreground text-sm font-bold">
                  {date}
                </span>
                {weekday && (
                  <span className="bg-muted text-muted-foreground rounded px-1.5 py-0.5 text-[10px] font-medium">
                    {weekday}
                  </span>
                )}
              </div>
              {notes && (
                <p className="text-muted-foreground mt-0.5 line-clamp-1 text-xs">
                  {notes}
                </p>
              )}
            </div>
            <div className="shrink-0 text-right">
              {dayCost > 0 && (
                <p className="text-price text-xs font-semibold">¥{dayCost}</p>
              )}
              <p className="text-muted-foreground text-[10px]">
                {day.activities.length} 项活动
              </p>
            </div>
          </div>

          {day.activities.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {day.activities.slice(0, 6).map((a, i) => {
                const meta = getCategoryMeta(a);
                return (
                  <span
                    key={a.id ?? i}
                    className={`inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[10px] font-medium ${meta.bg} ${meta.text}`}
                  >
                    <span>{meta.icon}</span>
                    <span className="max-w-[5rem] truncate">
                      {a.kind === "hotel_stay"
                        ? `${a.name || "目的地"}`
                        : a.name}
                    </span>
                  </span>
                );
              })}
              {day.activities.length > 6 && (
                <span className="bg-muted text-muted-foreground rounded-full px-2 py-0.5 text-[10px]">
                  +{day.activities.length - 6}
                </span>
              )}
            </div>
          )}

          {day.activities.length === 0 && (
            <p className="text-muted-foreground text-xs italic">暂无活动安排</p>
          )}
        </div>
      </div>
    </button>
  );
}

function ActivityCard({
  activity,
  isLast,
}: {
  activity: Activity;
  isLast: boolean;
}) {
  const meta = getCategoryMeta(activity);
  const dur = durationMinutes(activity.start_time, activity.end_time);
  const durLabel = formatDuration(dur);

  return (
    <div className="flex gap-3">
      <div className="flex w-14 shrink-0 flex-col items-end pt-3">
        <span className="text-foreground text-xs font-semibold tabular-nums">
          {activity.start_time}
        </span>
        {durLabel && (
          <span className="text-muted-foreground mt-0.5 text-[9px]">
            {durLabel}
          </span>
        )}
      </div>

      <div className="relative flex flex-col items-center">
        <div
          className={`relative z-10 mt-3 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 border-white text-[9px] shadow-sm ${meta.dot}`}
        >
          {meta.icon}
        </div>
        {!isLast && (
          <div
            className="bg-border mt-1 w-px flex-1"
            style={{ minHeight: "1.5rem" }}
          />
        )}
      </div>

      <div
        className={`border-border mb-3 min-w-0 flex-1 rounded-xl border ${meta.bg} overflow-hidden shadow-sm`}
      >
        <div className={`h-0.5 w-full ${meta.bar}`} />
        <div className="p-3">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-foreground truncate text-sm font-semibold">
                  {activity.kind === "hotel_stay"
                    ? `${activity.name || "目的地"}`
                    : activity.name}
                </span>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${meta.bg} ${meta.text} border border-current/20`}
                >
                  {meta.label}
                </span>
              </div>

              {activity.description && (
                <p className="text-muted-foreground mt-1 line-clamp-2 text-xs leading-relaxed">
                  {activity.description}
                </p>
              )}

              {(activity.location.address || activity.name) && (
                <p className="text-muted-foreground mt-1.5 flex items-center gap-1 text-[10px]">
                  <span>📍</span>
                  <span className="truncate">
                    {activity.location.address || activity.name}
                  </span>
                </p>
              )}
            </div>

            <div className="shrink-0 text-right">
              {(activity.estimated_cost?.amount ?? 0) > 0 && (
                <p className="text-price text-sm font-bold">
                  ¥{activity.estimated_cost.amount}
                </p>
              )}
              {(activity.estimated_cost?.amount ?? 0) === 0 && (
                <p className="text-success text-[10px] font-medium">免费</p>
              )}
              {activity.kind !== "hotel_stay" && (
                <p className="text-muted-foreground mt-0.5 text-[10px] whitespace-nowrap">
                  止 {activity.end_time}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DayDetail({ day }: { day: DayPlan }) {
  const { date, weekday } = formatDateWithWeekday(day.date);
  const notes = safeNotes(day.notes);
  const totalCost = day.activities.reduce(
    (s, a) => s + (a.estimated_cost?.amount ?? 0),
    0,
  );

  // Group activities by time period
  const grouped: Partial<Record<TimePeriod, Activity[]>> = {};
  for (const a of day.activities) {
    const period = getTimePeriod(a.start_time);
    if (!grouped[period]) grouped[period] = [];
    grouped[period]!.push(a);
  }
  const periods = (["morning", "afternoon", "evening"] as TimePeriod[]).filter(
    (p) => (grouped[p]?.length ?? 0) > 0,
  );

  return (
    <div className="pb-4">
      {/* Day header */}
      <div className="mb-4 flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-foreground text-base font-bold">{date}</h2>
            {weekday && (
              <span className="bg-primary/10 text-primary rounded-md px-2 py-0.5 text-xs font-medium">
                {weekday}
              </span>
            )}
          </div>
          {notes && (
            <p className="text-muted-foreground mt-0.5 text-sm">{notes}</p>
          )}
        </div>
        {totalCost > 0 && (
          <div className="bg-price/10 shrink-0 rounded-xl px-3 py-1.5 text-right">
            <p className="text-muted-foreground text-[10px]">今日预算</p>
            <p className="text-price text-sm font-bold">¥{totalCost}</p>
          </div>
        )}
      </div>

      {day.activities.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <span className="text-4xl">📅</span>
          <p className="text-muted-foreground mt-3 text-sm">本天暂无活动安排</p>
          <p className="text-muted-foreground/60 mt-1 text-xs">
            可以告诉 AI 助手为这天添加活动
          </p>
        </div>
      )}

      {periods.map((period) => {
        const periodInfo = PERIOD_LABEL[period];
        const acts = grouped[period] ?? [];
        return (
          <div key={period} className="mb-3">
            <div className="mb-2 flex items-center gap-1.5">
              <span className="text-base">{periodInfo.icon}</span>
              <span className={`text-xs font-semibold ${periodInfo.color}`}>
                {periodInfo.label}
              </span>
              <div className="bg-border h-px flex-1" />
            </div>

            {/* Activities */}
            <div>
              {acts.map((activity, i) => (
                <ActivityCard
                  key={activity.id ?? i}
                  activity={activity}
                  isLast={i === acts.length - 1}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function SummaryCard({ itinerary }: { itinerary: Itinerary }) {
  const { summary } = itinerary;
  if (!summary) return null;

  return (
    <div className="border-primary/20 bg-primary/10 mt-1 rounded-xl border p-4">
      <p className="text-primary/80 text-xs font-semibold tracking-wide uppercase">
        行程概览
      </p>
      <div className="text-primary mt-2 flex flex-wrap gap-3 text-xs">
        <span>🗓️ {itinerary.day_plans.length} 天</span>
        <span>🎯 {summary.total_activities} 个活动</span>
        {summary.total_estimated_cost > 0 && (
          <span>💰 预估 ¥{summary.total_estimated_cost.toLocaleString()}</span>
        )}
      </div>
      {summary.highlights.length > 0 && (
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {summary.highlights.map((h, i) => (
            <span
              key={i}
              className="bg-primary/20 text-primary rounded-full px-2.5 py-0.5 text-[11px]"
            >
              {h}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

interface Props {
  itinerary: Itinerary;
  markdownContent: string;
}

type TopTab = "itinerary" | "inspiration";

export function ItineraryViewer({ itinerary, markdownContent }: Props) {
  const [topTab, setTopTab] = useState<TopTab>("itinerary");
  const [selectedDay, setSelectedDay] = useState<number | null>(null);

  if (!itinerary || itinerary.day_plans.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-center">
        <span className="text-5xl">🗺️</span>
        <p className="text-muted-foreground mt-4 text-sm font-medium">
          暂无行程内容
        </p>
      </div>
    );
  }

  const currentDay =
    selectedDay !== null
      ? (itinerary.day_plans.find((d) => d.day_number === selectedDay) ?? null)
      : null;

  const displayDay = currentDay !== null ? selectedDay : null;

  return (
    <div className="bg-background flex h-full flex-col overflow-hidden">
      <TripHeader itinerary={itinerary} />

      <Tabs
        value={topTab}
        onValueChange={(v) => setTopTab(v as TopTab)}
        className="flex min-h-0 flex-1 flex-col"
      >
        <TabsList
          variant="line"
          className="border-border bg-background shrink-0 justify-start rounded-none border-b px-4"
        >
          <TabsTrigger value="itinerary" className="px-2">
            行程详情
          </TabsTrigger>
          <TabsTrigger value="inspiration" className="px-2">
            旅行灵感
          </TabsTrigger>
        </TabsList>

        <TabsContent
          value="inspiration"
          className="bg-background mt-0 flex-1 overflow-y-auto px-5 py-5"
        >
          {markdownContent ? (
            <article className="prose prose-sm prose-neutral max-w-none">
              <Markdown>{markdownContent}</Markdown>
            </article>
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <span className="text-4xl">✨</span>
              <p className="text-muted-foreground mt-3 text-sm">
                旅行灵感正在生成中…
              </p>
            </div>
          )}
        </TabsContent>

        <TabsContent
          value="itinerary"
          className="mt-0 flex min-h-0 flex-1 flex-col"
        >
          <div className="border-border bg-background flex shrink-0 items-center gap-2 overflow-x-auto border-b px-4 py-2.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            <button
              onClick={() => setSelectedDay(null)}
              className={`shrink-0 rounded-full px-3.5 py-1 text-xs font-medium transition-colors ${
                displayDay === null
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-muted text-muted-foreground hover:bg-muted/70"
              }`}
            >
              总览
            </button>

            {itinerary.day_plans.map((day) => (
              <button
                key={day.day_number}
                onClick={() => setSelectedDay(day.day_number)}
                className={`shrink-0 rounded-full px-3.5 py-1 text-xs font-medium transition-colors ${
                  displayDay === day.day_number
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "bg-muted text-muted-foreground hover:bg-muted/70"
                }`}
              >
                第{day.day_number}天
                <span className="ml-1 opacity-60">
                  {formatDateMonthDaySlash(day.date)}
                </span>
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-4">
            {displayDay === null ? (
              <div className="flex flex-col gap-3">
                {itinerary.day_plans.map((day) => (
                  <DayCard
                    key={day.day_number}
                    day={day}
                    onClick={() => setSelectedDay(day.day_number)}
                  />
                ))}
                <SummaryCard itinerary={itinerary} />
              </div>
            ) : currentDay ? (
              <DayDetail day={currentDay} />
            ) : null}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
