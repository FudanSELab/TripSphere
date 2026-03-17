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
