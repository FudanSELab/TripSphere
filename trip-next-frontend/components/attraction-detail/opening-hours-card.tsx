import { Clock, CheckCircle, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { DayOfWeek } from "@/lib/grpc/generated/tripsphere/common/v1/dayofweek";
import type {
  OpeningHours,
  OpenRule,
  TimeRange,
} from "@/lib/grpc/generated/tripsphere/attraction/v1/attraction";
import type { TimeOfDay } from "@/lib/grpc/generated/tripsphere/common/v1/timeofday";

const DAY_LABELS: Record<DayOfWeek, string> = {
  [DayOfWeek.DAY_OF_WEEK_UNSPECIFIED]: "未知",
  [DayOfWeek.DAY_OF_WEEK_MONDAY]: "周一",
  [DayOfWeek.DAY_OF_WEEK_TUESDAY]: "周二",
  [DayOfWeek.DAY_OF_WEEK_WEDNESDAY]: "周三",
  [DayOfWeek.DAY_OF_WEEK_THURSDAY]: "周四",
  [DayOfWeek.DAY_OF_WEEK_FRIDAY]: "周五",
  [DayOfWeek.DAY_OF_WEEK_SATURDAY]: "周六",
  [DayOfWeek.DAY_OF_WEEK_SUNDAY]: "周日",
  [DayOfWeek.UNRECOGNIZED]: "未知",
};

function formatTimeOfDay(t: TimeOfDay | undefined): string {
  if (!t) return "--:--";
  const h = String(t.hours ?? 0).padStart(2, "0");
  const m = String(t.minutes ?? 0).padStart(2, "0");
  return `${h}:${m}`;
}

function formatTimeRange(tr: TimeRange): string {
  const open = formatTimeOfDay(tr.openTime);
  const close = formatTimeOfDay(tr.closeTime);
  const lastEntry = tr.lastEntryTime
    ? `（最晚入场 ${formatTimeOfDay(tr.lastEntryTime)}）`
    : "";
  return `${open} – ${close}${lastEntry}`;
}

function formatDays(days: DayOfWeek[]): string {
  if (days.length === 0) return "每天";
  if (days.length === 7) return "全周";
  return days.map((d) => DAY_LABELS[d] ?? "").join("、");
}

function isCurrentlyOpen(openingHours: OpeningHours): boolean {
  const now = new Date();
  const todayDow = now.getDay();
  const protoDow =
    todayDow === 0 ? DayOfWeek.DAY_OF_WEEK_SUNDAY : (todayDow as DayOfWeek);
  const currentMinutes = now.getHours() * 60 + now.getMinutes();

  for (const rule of openingHours.rules) {
    const days =
      rule.days.length === 0
        ? (Object.values(DayOfWeek).filter(
            (v) => typeof v === "number",
          ) as DayOfWeek[])
        : rule.days;

    if (!days.includes(protoDow)) continue;

    for (const tr of rule.timeRanges) {
      const open = (tr.openTime?.hours ?? 0) * 60 + (tr.openTime?.minutes ?? 0);
      const close =
        (tr.closeTime?.hours ?? 0) * 60 + (tr.closeTime?.minutes ?? 0);
      if (currentMinutes >= open && currentMinutes < close) return true;
    }
  }
  return false;
}

interface OpeningHoursCardProps {
  openingHours: OpeningHours | undefined;
  temporarilyClosed: boolean;
}

export function OpeningHoursCard({
  openingHours,
  temporarilyClosed,
}: OpeningHoursCardProps) {
  if (!openingHours) return null;

  const open = !temporarilyClosed && isCurrentlyOpen(openingHours);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center gap-2">
            <Clock className="text-primary size-4" />
            开放时间
          </div>
          {temporarilyClosed ? (
            <span className="text-destructive flex items-center gap-1 text-xs font-normal">
              <XCircle className="size-3.5" />
              暂停开放
            </span>
          ) : (
            <span
              className={`flex items-center gap-1 text-xs font-normal ${
                open ? "text-success" : "text-muted-foreground"
              }`}
            >
              {open ? (
                <>
                  <CheckCircle className="size-3.5" />
                  开放中
                </>
              ) : (
                <>
                  <XCircle className="size-3.5" />
                  已关闭
                </>
              )}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {openingHours.rules.map((rule: OpenRule, rIdx: number) => (
          <div key={rIdx} className="flex flex-col gap-1.5">
            <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
              {formatDays(rule.days)}
            </p>
            <div className="flex flex-col gap-1">
              {rule.timeRanges.map((tr: TimeRange, tIdx: number) => (
                <p key={tIdx} className="text-foreground text-sm">
                  {formatTimeRange(tr)}
                </p>
              ))}
              {rule.timeRanges.length === 0 && (
                <p className="text-muted-foreground text-sm">全天开放</p>
              )}
            </div>
            {rule.note && (
              <p className="text-muted-foreground text-xs italic">
                {rule.note}
              </p>
            )}
          </div>
        ))}

        {openingHours.rules.length === 0 && (
          <p className="text-muted-foreground text-sm">暂无开放时间信息</p>
        )}

        {openingHours.specialTips && (
          <Alert>
            <AlertDescription className="text-xs">
              💡 {openingHours.specialTips}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
