"use client";

import { useState } from "react";
import Markdown from "react-markdown";
import type { Itinerary, DayPlan, Activity } from "@/actions/itinerary";

// ── Category metadata ──────────────────────────────────────────────────────

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
    bg: "bg-slate-50",
    text: "text-slate-600",
    dot: "bg-slate-400",
    bar: "bg-slate-300",
  },
  sightseeing: {
    icon: "🏛️",
    label: "观光",
    bg: "bg-blue-50",
    text: "text-blue-600",
    dot: "bg-blue-400",
    bar: "bg-blue-400",
  },
  cultural: {
    icon: "🎭",
    label: "文化",
    bg: "bg-violet-50",
    text: "text-violet-600",
    dot: "bg-violet-400",
    bar: "bg-violet-400",
  },
  shopping: {
    icon: "🛍️",
    label: "购物",
    bg: "bg-pink-50",
    text: "text-pink-600",
    dot: "bg-pink-400",
    bar: "bg-pink-400",
  },
  dining: {
    icon: "🍜",
    label: "美食",
    bg: "bg-orange-50",
    text: "text-orange-600",
    dot: "bg-orange-400",
    bar: "bg-orange-400",
  },
  entertainment: {
    icon: "🎪",
    label: "娱乐",
    bg: "bg-amber-50",
    text: "text-amber-600",
    dot: "bg-amber-400",
    bar: "bg-amber-400",
  },
  nature: {
    icon: "🌿",
    label: "自然",
    bg: "bg-emerald-50",
    text: "text-emerald-600",
    dot: "bg-emerald-400",
    bar: "bg-emerald-400",
  },
  custom: {
    icon: "📍",
    label: "自定义",
    bg: "bg-teal-50",
    text: "text-teal-600",
    dot: "bg-teal-400",
    bar: "bg-teal-400",
  },
};

const DEFAULT_META = {
  icon: "📍",
  label: "活动",
  bg: "bg-gray-50",
  text: "text-gray-600",
  dot: "bg-gray-400",
  bar: "bg-gray-300",
};

function getCategoryMeta(activity: Activity) {
  if (activity.kind === "transport")
    return CATEGORY_META["transportation"] ?? DEFAULT_META;
  if (activity.kind === "hotel_stay")
    return {
      icon: "🛏️",
      label: "住宿",
      bg: "bg-indigo-50",
      text: "text-indigo-600",
      dot: "bg-indigo-400",
      bar: "bg-indigo-400",
    };
  return CATEGORY_META[activity.category] ?? DEFAULT_META;
}

// ── Date helpers ───────────────────────────────────────────────────────────

const WEEKDAYS = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];

function shortDate(dateStr: string): string {
  const [, m, d] = dateStr.split("-");
  return `${parseInt(m, 10)}/${parseInt(d, 10)}`;
}

function fullDateLabel(dateStr: string): { date: string; weekday: string } {
  if (!dateStr) return { date: "", weekday: "" };
  const [, m, d] = dateStr.split("-");
  const month = parseInt(m, 10);
  const day = parseInt(d, 10);
  if (isNaN(month) || isNaN(day)) return { date: dateStr, weekday: "" };
  const dt = new Date(`${dateStr}T12:00:00`);
  const weekday = Number.isFinite(dt.getDay()) ? WEEKDAYS[dt.getDay()] : "";
  return { date: `${month}月${day}日`, weekday };
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

// ── Time period grouping ───────────────────────────────────────────────────

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
  morning: { label: "上午", icon: "🌅", color: "text-amber-600" },
  afternoon: { label: "下午", icon: "☀️", color: "text-orange-500" },
  evening: { label: "傍晚 / 夜间", icon: "🌙", color: "text-indigo-600" },
};

// ── Trip Header ────────────────────────────────────────────────────────────

function TripHeader({ itinerary }: { itinerary: Itinerary }) {
  const totalCost = itinerary.summary?.total_estimated_cost ?? 0;
  const totalActivities = itinerary.summary?.total_activities ?? 0;
  const days = itinerary.day_plans.length;

  return (
    <div className="shrink-0 bg-gradient-to-r from-blue-600 to-blue-500 px-5 py-4 text-white">
      <h1 className="text-lg leading-tight font-bold tracking-wide">
        {itinerary.destination} 旅行行程
      </h1>
      <p className="mt-0.5 text-xs text-blue-100">
        {itinerary.start_date} — {itinerary.end_date}
      </p>
      <div className="mt-3 flex gap-4 text-xs">
        <div className="flex flex-col items-center rounded-lg bg-white/15 px-3 py-1.5">
          <span className="text-base font-bold">{days}</span>
          <span className="text-blue-100">天</span>
        </div>
        <div className="flex flex-col items-center rounded-lg bg-white/15 px-3 py-1.5">
          <span className="text-base font-bold">{totalActivities}</span>
          <span className="text-blue-100">活动</span>
        </div>
        {totalCost > 0 && (
          <div className="flex flex-col items-center rounded-lg bg-white/15 px-3 py-1.5">
            <span className="text-base font-bold">
              ¥{totalCost.toLocaleString()}
            </span>
            <span className="text-blue-100">预算</span>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Day card (overview) ────────────────────────────────────────────────────

function DayCard({ day, onClick }: { day: DayPlan; onClick: () => void }) {
  const { date, weekday } = fullDateLabel(day.date);
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
      className="group w-full rounded-xl border border-gray-100 bg-white text-left shadow-sm transition-all hover:border-blue-200 hover:shadow-md active:scale-[.985]"
    >
      <div className="flex gap-0 overflow-hidden rounded-xl">
        {/* Left color accent */}
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
            <div className="flex-1 bg-gray-200" />
          )}
        </div>

        <div className="flex flex-1 flex-col gap-2 p-3.5">
          {/* Header row */}
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-bold text-gray-900">{date}</span>
                {weekday && (
                  <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-500">
                    {weekday}
                  </span>
                )}
              </div>
              {notes && (
                <p className="mt-0.5 line-clamp-1 text-xs text-gray-400">
                  {notes}
                </p>
              )}
            </div>
            <div className="shrink-0 text-right">
              {dayCost > 0 && (
                <p className="text-xs font-semibold text-orange-500">
                  ¥{dayCost}
                </p>
              )}
              <p className="text-[10px] text-gray-400">
                {day.activities.length} 项活动
              </p>
            </div>
          </div>

          {/* Activity pills */}
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
                      {a.kind === "hotel_stay" ? `住在${a.name || "目的地"}` : a.name}
                    </span>
                  </span>
                );
              })}
              {day.activities.length > 6 && (
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] text-gray-400">
                  +{day.activities.length - 6}
                </span>
              )}
            </div>
          )}

          {day.activities.length === 0 && (
            <p className="text-xs text-gray-400 italic">暂无活动安排</p>
          )}
        </div>
      </div>
    </button>
  );
}

// ── Activity card (timeline) ───────────────────────────────────────────────

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
      {/* Time column */}
      <div className="flex w-14 shrink-0 flex-col items-end pt-3">
        <span className="text-xs font-semibold text-gray-700 tabular-nums">
          {activity.start_time}
        </span>
        {durLabel && (
          <span className="mt-0.5 text-[9px] text-gray-400">{durLabel}</span>
        )}
      </div>

      {/* Timeline spine + dot */}
      <div className="relative flex flex-col items-center">
        <div
          className={`relative z-10 mt-3 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 border-white text-[9px] shadow-sm ${meta.dot}`}
        >
          {meta.icon}
        </div>
        {!isLast && (
          <div
            className="mt-1 w-px flex-1 bg-gray-200"
            style={{ minHeight: "1.5rem" }}
          />
        )}
      </div>

      {/* Card */}
      <div
        className={`mb-3 min-w-0 flex-1 rounded-xl border border-gray-100 ${meta.bg} overflow-hidden shadow-sm`}
      >
        {/* Colored top bar */}
        <div className={`h-0.5 w-full ${meta.bar}`} />
        <div className="p-3">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="truncate text-sm font-semibold text-gray-900">
                  {activity.kind === "hotel_stay"
                    ? `住在 ${activity.name || "目的地"}`
                    : activity.name}
                </span>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${meta.bg} ${meta.text} border border-current/20`}
                >
                  {meta.label}
                </span>
              </div>

              {activity.description && (
                <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-gray-500">
                  {activity.description}
                </p>
              )}

              {(activity.location.address || activity.name) && (
                <p className="mt-1.5 flex items-center gap-1 text-[10px] text-gray-400">
                  <span>📍</span>
                  <span className="truncate">
                    {activity.location.address || activity.name}
                  </span>
                </p>
              )}
            </div>

            <div className="shrink-0 text-right">
              {(activity.estimated_cost?.amount ?? 0) > 0 && (
                <p className="text-sm font-bold text-orange-500">
                  ¥{activity.estimated_cost.amount}
                </p>
              )}
              {(activity.estimated_cost?.amount ?? 0) === 0 && (
                <p className="text-[10px] font-medium text-emerald-500">免费</p>
              )}
              {activity.kind !== "hotel_stay" && (
                <p className="mt-0.5 text-[10px] text-gray-400 whitespace-nowrap">
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

// ── Day detail ─────────────────────────────────────────────────────────────

function DayDetail({ day }: { day: DayPlan }) {
  const { date, weekday } = fullDateLabel(day.date);
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
            <h2 className="text-base font-bold text-gray-900">{date}</h2>
            {weekday && (
              <span className="rounded-md bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-600">
                {weekday}
              </span>
            )}
          </div>
          {notes && <p className="mt-0.5 text-sm text-gray-500">{notes}</p>}
        </div>
        {totalCost > 0 && (
          <div className="shrink-0 rounded-xl bg-orange-50 px-3 py-1.5 text-right">
            <p className="text-[10px] text-gray-400">今日预算</p>
            <p className="text-sm font-bold text-orange-500">¥{totalCost}</p>
          </div>
        )}
      </div>

      {day.activities.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <span className="text-4xl">📅</span>
          <p className="mt-3 text-sm text-gray-400">本天暂无活动安排</p>
          <p className="mt-1 text-xs text-gray-300">
            可以告诉 AI 助手为这天添加活动
          </p>
        </div>
      )}

      {/* Timeline by period */}
      {periods.map((period) => {
        const periodInfo = PERIOD_LABEL[period];
        const acts = grouped[period] ?? [];
        return (
          <div key={period} className="mb-3">
            {/* Period label */}
            <div className="mb-2 flex items-center gap-1.5">
              <span className="text-base">{periodInfo.icon}</span>
              <span className={`text-xs font-semibold ${periodInfo.color}`}>
                {periodInfo.label}
              </span>
              <div className="h-px flex-1 bg-gray-100" />
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

// ── Summary card ───────────────────────────────────────────────────────────

function SummaryCard({ itinerary }: { itinerary: Itinerary }) {
  const { summary } = itinerary;
  if (!summary) return null;

  return (
    <div className="mt-1 rounded-xl border border-blue-100 bg-blue-50 p-4">
      <p className="text-xs font-semibold tracking-wide text-blue-700 uppercase">
        行程概览
      </p>
      <div className="mt-2 flex flex-wrap gap-3 text-xs text-blue-600">
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
              className="rounded-full bg-blue-100 px-2.5 py-0.5 text-[11px] text-blue-700"
            >
              {h}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

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
        <p className="mt-4 text-sm font-medium text-gray-500">暂无行程内容</p>
      </div>
    );
  }

  const currentDay =
    selectedDay !== null
      ? (itinerary.day_plans.find((d) => d.day_number === selectedDay) ?? null)
      : null;

  // If the selected day was deleted, fall back to overview
  if (selectedDay !== null && currentDay === null) {
    setSelectedDay(null);
  }

  return (
    <div className="flex h-full flex-col overflow-hidden bg-gray-50">
      {/* ── Trip header ── */}
      <TripHeader itinerary={itinerary} />

      {/* ── Top tabs ── */}
      <div className="flex shrink-0 border-b border-gray-100 bg-white px-4">
        {(["itinerary", "inspiration"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setTopTab(tab)}
            className={`relative mr-6 py-3 text-sm font-medium transition-colors ${
              topTab === tab
                ? "text-blue-600"
                : "text-gray-400 hover:text-gray-600"
            }`}
          >
            {tab === "itinerary" ? "行程详情" : "旅行灵感"}
            {topTab === tab && (
              <span className="absolute right-0 bottom-0 left-0 h-0.5 rounded-t bg-blue-500" />
            )}
          </button>
        ))}
      </div>

      {/* ── Inspiration tab ── */}
      {topTab === "inspiration" && (
        <div className="flex-1 overflow-y-auto bg-white px-5 py-5">
          {markdownContent ? (
            <article className="prose prose-sm prose-blue max-w-none">
              <Markdown>{markdownContent}</Markdown>
            </article>
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <span className="text-4xl">✨</span>
              <p className="mt-3 text-sm text-gray-400">旅行灵感正在生成中……</p>
            </div>
          )}
        </div>
      )}

      {/* ── Itinerary tab ── */}
      {topTab === "itinerary" && (
        <>
          {/* Day pill selector */}
          <div className="flex shrink-0 items-center gap-2 overflow-x-auto border-b border-gray-100 bg-white px-4 py-2.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            <button
              onClick={() => setSelectedDay(null)}
              className={`shrink-0 rounded-full px-3.5 py-1 text-xs font-medium transition-colors ${
                selectedDay === null
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              总览
            </button>

            {itinerary.day_plans.map((day) => (
              <button
                key={day.day_number}
                onClick={() => setSelectedDay(day.day_number)}
                className={`shrink-0 rounded-full px-3.5 py-1 text-xs font-medium transition-colors ${
                  selectedDay === day.day_number
                    ? "bg-blue-600 text-white shadow-sm"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                第{day.day_number}天
                <span className="ml-1 opacity-60">{shortDate(day.date)}</span>
              </button>
            ))}
          </div>

          {/* Scrollable content */}
          <div className="flex-1 overflow-y-auto px-4 py-4">
            {selectedDay === null ? (
              /* Overview */
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
              /* Day detail */
              <DayDetail day={currentDay} />
            ) : null}
          </div>
        </>
      )}
    </div>
  );
}
