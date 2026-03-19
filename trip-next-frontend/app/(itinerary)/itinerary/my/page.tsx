import Link from "next/link";
import { revalidatePath } from "next/cache";
import {
  listMyItineraries,
  deleteItinerary,
  type SavedItinerarySummary,
} from "@/actions/itinerary";

// ── Date helpers ───────────────────────────────────────────────────────────

function formatDate(dateStr: string): string {
  if (!dateStr || dateStr.trim() === "") return "—";
  const [, m, d] = dateStr.split("-");
  const month = parseInt(m, 10);
  const day = parseInt(d, 10);
  if (Number.isNaN(month) || Number.isNaN(day)) return "—";
  return `${month}月${day}日`;
}

function formatRelative(dateStr: string): string {
  if (!dateStr || dateStr.trim() === "") return "—";
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return "—";
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "刚刚";
  if (diffMin < 60) return `${diffMin}分钟前`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}小时前`;
  const diffD = Math.floor(diffH / 24);
  if (diffD < 30) return `${diffD}天前`;
  return date.toLocaleDateString("zh-CN");
}

function tripDays(start: string, end: string): number {
  const s = new Date(start);
  const e = new Date(end);
  if (Number.isNaN(s.getTime()) || Number.isNaN(e.getTime())) return 0;
  return Math.max(0, Math.round((e.getTime() - s.getTime()) / 86400000) + 1);
}

// ── Delete button (needs client interaction) ───────────────────────────────

async function handleDelete(formData: FormData) {
  "use server";
  const id = formData.get("id") as string;
  await deleteItinerary(id);
  revalidatePath("/itinerary/my");
}

// ── Card ───────────────────────────────────────────────────────────────────

function ItineraryCard({ item }: { item: SavedItinerarySummary }) {
  const days = tripDays(item.start_date, item.end_date);

  return (
    <div className="group relative flex flex-col overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm transition-all hover:border-blue-200 hover:shadow-md">
      {/* Colored header */}
      <div className="flex items-start justify-between bg-gradient-to-r from-blue-600 to-blue-500 p-5 text-white">
        <div>
          <h3 className="text-lg leading-snug font-bold">{item.destination}</h3>
          <p className="mt-1 text-xs text-blue-100">
            {formatDate(item.start_date)} — {formatDate(item.end_date)}
          </p>
        </div>
        <div className="flex flex-col items-center rounded-xl bg-white/20 px-3 py-2 text-center">
          <span className="text-xl font-bold">{days}</span>
          <span className="text-[10px] text-blue-100">天</span>
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex items-center gap-3 text-xs text-gray-400">
          <span>🎯 {item.day_count} 个活动</span>
          <span>·</span>
          <span>🕐 {formatRelative(item.updated_at)}</span>
        </div>

        {/* Actions */}
        <div className="mt-auto flex items-center gap-2 pt-2">
          <Link
            href={`/itinerary/planner?id=${item.id}`}
            className="flex-1 rounded-lg bg-blue-600 px-3 py-2 text-center text-sm font-medium text-white transition-colors hover:bg-blue-700"
          >
            查看 / 继续编辑
          </Link>

          <form action={handleDelete}>
            <input type="hidden" name="id" value={item.id} />
            <button
              type="submit"
              className="rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-400 transition-colors hover:border-red-200 hover:bg-red-50 hover:text-red-500"
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

// ── Page ───────────────────────────────────────────────────────────────────

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
      {/* Page header */}
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">我的行程</h1>
          <p className="mt-1 text-sm text-gray-400">
            {itineraries.length > 0
              ? `共 ${itineraries.length} 份保存的行程`
              : "还没有保存的行程"}
          </p>
        </div>
        <Link
          href="/itinerary"
          className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
        >
          + 新建行程
        </Link>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-500">
          {error}
        </div>
      )}

      {/* Empty state */}
      {!error && itineraries.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <span className="text-6xl">🗺️</span>
          <p className="mt-4 text-base font-medium text-gray-500">
            还没有保存的行程
          </p>
          <p className="mt-1 text-sm text-gray-400">
            用 AI 规划你的第一次旅行吧！
          </p>
          <Link
            href="/itinerary"
            className="mt-5 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            开始规划
          </Link>
        </div>
      )}

      {/* Grid */}
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
