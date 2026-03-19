/**
 * Format a date to Chinese locale string like "3月14日(周六)"
 */
export function formatDate(date: Date): string {
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
  const weekday = weekdays[date.getDay()];
  return `${month}月${day}日(${weekday})`;
}

/**
 * Convert a Money object (units + nanos) to a numeric amount
 */
export function formatMoney(
  money: { units: number; nanos: number } | undefined,
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
  3: "机票",
  4: "火车票",
};

export function formatOrderType(type: number): string {
  return ORDER_TYPE_LABELS[type] ?? "未知";
}
