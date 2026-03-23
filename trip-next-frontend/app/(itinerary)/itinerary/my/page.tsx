import Link from "next/link";
import { revalidatePath } from "next/cache";
import { listMyItineraries } from "@/lib/data/itinerary";
import {
  deleteItinerary,
  type SavedItinerarySummary,
} from "@/actions/itinerary";
import { formatDateCompact, formatRelative, tripDayCount } from "@/lib/format";
import { Alert, AlertDescription } from "@/components/ui/alert";

async function handleDelete(formData: FormData) {
  "use server";
  const id = formData.get("id") as string;
  await deleteItinerary(id);
  revalidatePath("/itinerary/my");
}

function ItineraryCard({ item }: { item: SavedItinerarySummary }) {
  const days = tripDayCount(item.start_date, item.end_date);

  return (
    <div className="border-border bg-card group hover:border-primary/30 relative flex flex-col overflow-hidden rounded-2xl border shadow-sm transition-all hover:shadow-md">
      <div className="from-primary to-primary/80 text-primary-foreground flex items-start justify-between bg-gradient-to-r p-5">
        <div>
          <h3 className="text-lg leading-snug font-bold">{item.destination}</h3>
          <p className="text-primary-foreground/70 mt-1 text-xs">
            {formatDateCompact(item.start_date)} —{" "}
            {formatDateCompact(item.end_date)}
          </p>
        </div>
        <div className="flex flex-col items-center rounded-xl bg-white/20 px-3 py-2 text-center">
          <span className="text-xl font-bold">{days}</span>
          <span className="text-primary-foreground/70 text-[10px]">天</span>
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="text-muted-foreground flex items-center gap-3 text-xs">
          <span>🎯 {item.day_count} 个活动</span>
          <span>·</span>
          <span>🕐 {formatRelative(item.updated_at)}</span>
        </div>

        <div className="mt-auto flex items-center gap-2 pt-2">
          <Link
            href={`/itinerary/planner?id=${item.id}`}
            className="bg-primary text-primary-foreground hover:bg-primary/90 flex-1 rounded-lg px-3 py-2 text-center text-sm font-medium transition-colors"
          >
            查看 / 继续编辑
          </Link>

          <form action={handleDelete}>
            <input type="hidden" name="id" value={item.id} />
            <button
              type="submit"
              className="border-border text-muted-foreground hover:border-destructive/30 hover:bg-destructive/10 hover:text-destructive rounded-lg border px-3 py-2 text-sm transition-colors"
              title="删除行程"
            >
              删除
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default async function MyItinerariesPage() {
  let itineraries: SavedItinerarySummary[] = [];
  let error: string | null = null;

  try {
    itineraries = await listMyItineraries();
  } catch (err) {
    error = err instanceof Error ? err.message : "加载失败";
  }

  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-8">
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="text-foreground text-2xl font-bold">我的行程</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            {itineraries.length > 0
              ? `共 ${itineraries.length} 份保存的行程`
              : "还没有保存的行程"}
          </p>
        </div>
        <Link
          href="/itinerary"
          className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-xl px-4 py-2 text-sm font-medium transition-colors"
        >
          + 新建行程
        </Link>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {!error && itineraries.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <span className="text-6xl">🗺️</span>
          <p className="text-muted-foreground mt-4 text-base font-medium">
            还没有保存的行程
          </p>
          <p className="text-muted-foreground mt-1 text-sm">
            用 AI 规划你的第一次旅行吧！
          </p>
          <Link
            href="/itinerary"
            className="bg-primary text-primary-foreground hover:bg-primary/90 mt-5 rounded-xl px-5 py-2.5 text-sm font-medium"
          >
            开始规划
          </Link>
        </div>
      )}

      {itineraries.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {itineraries.map((item) => (
            <ItineraryCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
