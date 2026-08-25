/** Default locale for date/time formatting (UI copy is mostly Chinese). */
export const APP_DATE_LOCALE = "zh-CN";
export const APP_TIME_ZONE = "Asia/Shanghai";

const ISO_DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/;

/**
 * Parse a calendar "YYYY-MM-DD" into a local Date at noon (avoids UTC midnight
 * shifting the displayed day in some timezones).
 */
export function parseDateOnly(iso: string): Date | null {
  const trimmed = iso?.trim();
  if (!trimmed) return null;
  const m = ISO_DATE_ONLY.exec(trimmed);
  if (!m) return null;
  const y = Number(m[1]);
  const mo = Number(m[2]);
  const d = Number(m[3]);
  if (y < 1 || mo < 1 || mo > 12 || d < 1 || d > 31) return null;
  const dt = new Date(`${trimmed}T12:00:00`);
  if (
    Number.isNaN(dt.getTime()) ||
    dt.getFullYear() !== y ||
    dt.getMonth() + 1 !== mo ||
    dt.getDate() !== d
  ) {
    return null;
  }
  return dt;
}

/**
 * Format a Date like "3月14日(周六)" using the app locale.
 */
export function formatDate(date: Date): string {
  const datePart = new Intl.DateTimeFormat(APP_DATE_LOCALE, {
    month: "long",
    day: "numeric",
  }).format(date);
  const wd = new Intl.DateTimeFormat(APP_DATE_LOCALE, {
    weekday: "short",
  }).format(date);
  return `${datePart}(${wd})`;
}

/** Serialize a local calendar date without applying a UTC timezone shift. */
export function formatDateOnly(date: Date): string {
  const year = date.getFullYear().toString().padStart(4, "0");
  const month = (date.getMonth() + 1).toString().padStart(2, "0");
  const day = date.getDate().toString().padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/** Format a date using the application's explicit business timezone. */
export function formatDateInTimeZone(
  date: Date,
  timeZone = APP_TIME_ZONE,
): string {
  const parts = new Intl.DateTimeFormat("en", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const year = parts.find((part) => part.type === "year")?.value;
  const month = parts.find((part) => part.type === "month")?.value;
  const day = parts.find((part) => part.type === "day")?.value;
  if (!year || !month || !day) {
    throw new Error("Unable to format date in application timezone");
  }
  return `${year}-${month}-${day}`;
}

/**
 * Format a "YYYY-MM-DD" string to compact locale form like "3月14日".
 * Returns "—" for empty or invalid input.
 */
export function formatDateCompact(dateStr: string): string {
  if (!dateStr?.trim()) return "—";
  const dt = parseDateOnly(dateStr.trim());
  if (!dt) return "—";
  return new Intl.DateTimeFormat(APP_DATE_LOCALE, {
    month: "long",
    day: "numeric",
  }).format(dt);
}

/** Month/day only for itinerary side labels, e.g. "3/22" from locale numeric parts. */
export function formatDateMonthDaySlash(iso: string): string {
  const dt = parseDateOnly((iso ?? "").trim());
  if (!dt) return "";
  const parts = new Intl.DateTimeFormat(APP_DATE_LOCALE, {
    month: "numeric",
    day: "numeric",
  }).formatToParts(dt);
  const month = parts.find((p) => p.type === "month")?.value ?? "";
  const day = parts.find((p) => p.type === "day")?.value ?? "";
  return month && day ? `${month}/${day}` : "";
}

/** Full date line + short weekday for itinerary headers. */
export function formatDateWithWeekday(iso: string): {
  date: string;
  weekday: string;
} {
  if (!iso?.trim()) return { date: "", weekday: "" };
  const dt = parseDateOnly(iso.trim());
  if (!dt) return { date: iso.trim(), weekday: "" };
  return {
    date: new Intl.DateTimeFormat(APP_DATE_LOCALE, {
      month: "long",
      day: "numeric",
    }).format(dt),
    weekday: new Intl.DateTimeFormat(APP_DATE_LOCALE, {
      weekday: "short",
    }).format(dt),
  };
}

/**
 * Format an ISO datetime string as relative time in Chinese (e.g. "5分钟前").
 * Returns "—" for empty or invalid input.
 */
export function formatRelative(dateStr: string): string {
  if (!dateStr?.trim()) return "—";
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return "—";
  const diffMin = Math.floor((Date.now() - date.getTime()) / 60_000);
  if (diffMin < 1) return "刚刚";
  if (diffMin < 60) return `${diffMin}分钟前`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}小时前`;
  const diffD = Math.floor(diffH / 24);
  if (diffD < 30) return `${diffD}天前`;
  return new Intl.DateTimeFormat(APP_DATE_LOCALE, {
    dateStyle: "medium",
  }).format(date);
}

/**
 * Calculate number of trip days between two "YYYY-MM-DD" strings (inclusive).
 * Returns 0 for invalid input.
 */
export function tripDayCount(startStr: string, endStr: string): number {
  const s = parseDateOnly(startStr);
  const e = parseDateOnly(endStr);
  if (!s || !e) return 0;
  return Math.max(0, Math.round((e.getTime() - s.getTime()) / 86_400_000) + 1);
}

/**
 * Convert a Money object (currency + units + nanos) to a numeric amount
 */
export function formatMoney(
  money: { currency: string; units: number; nanos: number } | undefined,
): number {
  if (!money) return 0;
  return money.units + money.nanos / 1_000_000_000;
}

/**
 * Convert a DateMessage { year, month, day } to "YYYY-MM-DD" display string
 */
export function formatDateMessage(
  date: { year: number; month: number; day: number } | undefined,
): string {
  if (!date) return "";
  const y = String(date.year);
  const m = String(date.month).padStart(2, "0");
  const d = String(date.day).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/**
 * Format a recommend time range like "1–3 小时" or "2 小时".
 * Returns null when both values are 0/undefined.
 */
export function formatRecommendTime(
  minHours: number | undefined,
  maxHours: number | undefined,
  unit = "h",
): string | null {
  const min = minHours ?? 0;
  const max = maxHours ?? 0;
  if (min <= 0 && max <= 0) return null;
  if (min > 0 && max > 0 && min !== max) return `${min}–${max}${unit}`;
  return `${max || min}${unit}`;
}

const ORDER_STATUS_LABELS: Record<number, string> = {
  0: "全部",
  1: "待支付",
  2: "已付款",
  3: "已完成",
  4: "已取消",
};

export function formatOrderStatus(status: number): string {
  return ORDER_STATUS_LABELS[status] ?? "未知";
}

const ORDER_TYPE_LABELS: Record<number, string> = {
  0: "全部类型",
  1: "景点门票",
  2: "酒店住宿",
};

export function formatOrderType(type: number): string {
  return ORDER_TYPE_LABELS[type] ?? "未知";
}
