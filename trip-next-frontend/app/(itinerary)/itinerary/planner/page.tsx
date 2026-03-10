"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useCopilotAction, useCopilotReadable } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-core/v2";
import { MapPanel } from "@/components/map-panel";
import { ItineraryViewer } from "@/components/itinerary-viewer";
import {
  getItinerary,
  updateSavedItinerary,
  type Itinerary,
  type PlanItineraryResult,
  type DayPlan,
  type Activity,
} from "@/actions/itinerary";

// ── Summary recomputation ──────────────────────────────────────────────────
// Called after every mutation so the overview (total cost, activity count)
// stays in sync with the actual day plans.

function recomputeSummary(it: Itinerary): Itinerary {
  const allActivities = it.day_plans.flatMap((dp) => dp.activities);
  const totalActivities = allActivities.length;
  const totalCost = allActivities.reduce(
    (sum, a) => sum + (a.estimated_cost?.amount ?? 0),
    0,
  );
  if (!it.summary) return it;
  return {
    ...it,
    summary: {
      ...it.summary,
      total_activities: totalActivities,
      total_estimated_cost: Math.round(totalCost),
    },
  };
}

// ── Sync status badge ──────────────────────────────────────────────────────

type SyncStatus = "saved" | "saving" | "unsaved" | "error";

function SyncBadge({ status }: { status: SyncStatus }) {
  const cfg: Record<SyncStatus, { label: string; cls: string }> = {
    saved:   { label: "✓ 已保存",  cls: "bg-emerald-50 text-emerald-600 border-emerald-200" },
    saving:  { label: "⟳ 保存中…", cls: "bg-blue-50 text-blue-500 border-blue-200 animate-pulse" },
    unsaved: { label: "● 未保存",  cls: "bg-amber-50 text-amber-600 border-amber-200" },
    error:   { label: "✕ 保存失败", cls: "bg-red-50 text-red-500 border-red-200" },
  };
  const { label, cls } = cfg[status];
  return (
    <span className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${cls}`}>
      {label}
    </span>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

function PlannerContent() {
  const [loaded, setLoaded] = useState(false);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [markdownContent, setMarkdownContent] = useState("");
  const [itineraryId, setItineraryId] = useState<string | null>(null);
  const [syncStatus, setSyncStatus] = useState<SyncStatus>("saved");

  // Ref kept in sync with itinerary state — used in tool handlers to avoid
  // stale closure issues when the agent calls tools like regenerateDay.
  const itineraryRef = useRef<Itinerary | null>(null);

  // Track whether itinerary has been mutated since last sync
  const isFirstLoad = useRef(true);
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Load itinerary ───────────────────────────────────────────────────────

  useEffect(() => {
    async function load() {
      const params = new URLSearchParams(window.location.search);
      const idParam = params.get("id");

      if (idParam) {
        // Load from persisted backend storage
        try {
          const data = await getItinerary(idParam);
          // Reset isFirstLoad so the debounce effect skips this state update
          isFirstLoad.current = true;
          setItinerary(data.itinerary);
          setMarkdownContent(data.markdown_content);
          setItineraryId(idParam);
        } catch (err) {
          console.error("Failed to load itinerary:", err);
        }
      } else {
        // Load fresh plan from sessionStorage
        const raw = sessionStorage.getItem("itinerary_plan_result");
        if (raw) {
          try {
            const data = JSON.parse(raw) as PlanItineraryResult;
            // Update URL to ?id= so future reloads/refreshes load from MongoDB
            // (sessionStorage is never updated after AI mutations)
            const url = new URL(window.location.href);
            url.searchParams.set("id", data.itinerary.id);
            window.history.replaceState({}, "", url.toString());
            // Reset isFirstLoad so the debounce effect skips this state update
            isFirstLoad.current = true;
            setItinerary(data.itinerary);
            setMarkdownContent(data.markdown_content);
            setItineraryId(data.itinerary.id);
          } catch {
            /* ignore parse errors */
          }
        }
      }
      setLoaded(true);
    }
    load();
  }, []);

  // ── Debounced persistence sync ───────────────────────────────────────────

  const syncToBackend = useCallback(
    async (current: Itinerary, markdown: string, id: string) => {
      setSyncStatus("saving");
      try {
        await updateSavedItinerary(id, current, markdown);
        setSyncStatus("saved");
      } catch (err) {
        console.error("Sync failed:", err);
        setSyncStatus("error");
      }
    },
    [],
  );

  // Keep itineraryRef up to date on every render so tool handlers always
  // access the latest state without stale closure issues.
  useEffect(() => {
    itineraryRef.current = itinerary;
  }, [itinerary]);

  useEffect(() => {
    // Skip the initial population — only sync on actual mutations
    if (isFirstLoad.current) {
      isFirstLoad.current = false;
      return;
    }
    if (!itinerary || !itineraryId) return;

    setSyncStatus("unsaved");

    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      syncToBackend(itinerary, markdownContent, itineraryId);
    }, 1500);

    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
    };
  }, [itinerary, markdownContent, itineraryId, syncToBackend]);

  // ── CopilotKit Context ───────────────────────────────────────────────────

  useCopilotReadable({
    description:
      "Current travel itinerary in structured JSON format. MANDATORY: Before any action, extract 'destination' (the travel city) and 'day_plans' (list of days with activities) from this value. Every activity you generate MUST be located in this destination city.",
    value: itinerary,
  });

  useCopilotReadable({
    description:
      "Current travel itinerary in Markdown format. Use this to understand the narrative context of the trip.",
    value: markdownContent,
  });

  useCopilotReadable({
    description:
      "Trip summary: destination, dates, and key info. Use 'destination' as the ONLY valid city for generating activities.",
    value: itinerary
      ? {
          destination: itinerary.destination,
          start_date: itinerary.start_date,
          end_date: itinerary.end_date,
          total_days: itinerary.day_plans.length,
          days: itinerary.day_plans.map((d) => ({
            day_number: d.day_number,
            date: d.date,
            activity_count: d.activities.length,
            activity_names: d.activities.map((a) => a.name),
          })),
        }
      : null,
  });

  // ── CopilotKit Actions (Tools) ───────────────────────────────────────────

  useCopilotAction({
    name: "updateItinerary",
    description:
      "Replace ALL activities for a specific day with a new list. Use this ONLY when regenerating an entire day. Do NOT use this to add a single activity — use addActivity instead. Only the specified day is modified; all other days remain unchanged.",
    parameters: [
      {
        name: "day",
        type: "number",
        description: "Day number to update (1-indexed)",
        required: true,
      },
      {
        name: "activities",
        type: "object[]",
        description:
          "Complete replacement activities array for the day. Each activity must include id, name, description, start_time, end_time, location (name/longitude/latitude/address), category, estimated_cost (amount/currency), kind, attraction_id, hotel_id.",
        required: true,
      },
      {
        name: "notes",
        type: "string",
        description: "Optional theme/notes for the day",
      },
    ],
    handler: async ({
      day,
      activities,
      notes,
    }: {
      day: number;
      activities: Activity[];
      notes?: string;
    }) => {
      const dayNum = Number(day);
      setItinerary((prev) => {
        if (!prev) return prev;
        const cleanNotes =
          notes !== undefined && notes !== "undefined" && notes !== "null"
            ? notes
            : undefined;
        const updated = {
          ...prev,
          day_plans: prev.day_plans.map((dp: DayPlan) =>
            dp.day_number === dayNum
              ? {
                  ...dp,
                  activities: activities.map((a) => ({
                    ...a,
                    estimated_cost: {
                      amount: Number(a.estimated_cost?.amount ?? 0),
                      currency: a.estimated_cost?.currency ?? "CNY",
                    },
                  })),
                  ...(cleanNotes !== undefined ? { notes: cleanNotes } : {}),
                }
              : dp,
          ),
        };
        return recomputeSummary(updated);
      });
      return `Day ${dayNum} updated successfully`;
    },
  });

  useCopilotAction({
    name: "removeSpot",
    description:
      "Remove a single spot/activity from a specific day by name. Only that one activity is removed; all other activities and all other days are unchanged.",
    parameters: [
      {
        name: "day",
        type: "number",
        description: "Day number (1-indexed)",
        required: true,
      },
      {
        name: "spotName",
        type: "string",
        description: "Name of the spot/activity to remove",
        required: true,
      },
    ],
    handler: async ({ day, spotName }: { day: number; spotName: string }) => {
      const dayNum = Number(day);
      let removed = false;
      setItinerary((prev) => {
        if (!prev) return prev;
        const updated = {
          ...prev,
          day_plans: prev.day_plans.map((dp: DayPlan) => {
            if (dp.day_number !== dayNum) return dp;
            const filtered = dp.activities.filter((a: Activity) => {
              const match =
                a.name === spotName ||
                a.name.includes(spotName) ||
                spotName.includes(a.name);
              if (match) removed = true;
              return !match;
            });
            return { ...dp, activities: filtered };
          }),
        };
        return recomputeSummary(updated);
      });
      return removed
        ? `Removed "${spotName}" from Day ${dayNum}`
        : `Could not find "${spotName}" in Day ${dayNum}`;
    },
  });

  useCopilotAction({
    name: "regenerateDay",
    description:
      "Signal intent to regenerate all activities for a specific day. After calling this, you MUST immediately generate the new activity list and call updateItinerary to apply it. Do NOT modify any other day.",
    parameters: [
      {
        name: "day",
        type: "number",
        description: "Day number to regenerate (1-indexed)",
        required: true,
      },
      {
        name: "preference",
        type: "string",
        description:
          "Style or theme for the day (e.g. relaxed, food-focused, cultural)",
        required: true,
      },
    ],
    handler: async ({ day, preference }: { day: number; preference: string }) => {
      const dayNum = Number(day);
      const current = itineraryRef.current;
      if (!current) {
        return `Day ${dayNum} regeneration requested (preference: "${preference}"). WARNING: Cannot read current itinerary state. Proceed with caution and ask the user for the destination city.`;
      }
      const targetDay = current.day_plans.find((d) => d.day_number === dayNum);
      // Pass explicit itinerary context so the model cannot ignore the destination
      const ctx = {
        目的地: current.destination,
        起止日期: `${current.start_date} ~ ${current.end_date}`,
        操作目标: `第${dayNum}天（${targetDay?.date ?? ""}）`,
        偏好: preference,
        参考坐标: current.day_plans
          .flatMap((d) => d.activities)
          .slice(0, 5)
          .map((a) => ({
            景点: a.name,
            经度: a.location?.longitude,
            纬度: a.location?.latitude,
          })),
      };
      return (
        `已确认：重新规划第${dayNum}天，偏好「${preference}」。` +
        `行程上下文：${JSON.stringify(ctx, null, 0)}。` +
        `请立即调用 updateItinerary(day=${dayNum}, activities=[...])，` +
        `在【${current.destination}】内生成3-5个新活动，禁止使用其他城市的景点。`
      );
    },
  });

  useCopilotAction({
    name: "addActivity",
    description:
      "Add a SINGLE new activity to a specific day WITHOUT replacing existing activities. Use this whenever the user asks to add or insert one activity. The activity object must strictly follow the Activity schema: {id, name, description, start_time, end_time, location:{name,longitude,latitude,address}, category, estimated_cost:{amount,currency}, kind, attraction_id, hotel_id}. Only the specified day is affected.",
    parameters: [
      {
        name: "day",
        type: "number",
        description: "Day number (1-indexed)",
        required: true,
      },
      {
        name: "activity",
        type: "object",
        description:
          "Activity object with all required fields: id (string), name (string), description (string), start_time (HH:MM), end_time (HH:MM), location ({name, longitude, latitude, address}), category (sightseeing|cultural|shopping|dining|entertainment|transportation|nature), estimated_cost ({amount: number, currency: 'CNY'}), kind (attraction_visit|hotel_stay|transport|custom), attraction_id (null), hotel_id (null)",
        required: true,
      },
    ],
    handler: async ({ day, activity }: { day: number; activity: object }) => {
      const dayNum = Number(day);
      const act = activity as Activity;
      setItinerary((prev) => {
        if (!prev) return prev;
        const updated = {
          ...prev,
          day_plans: prev.day_plans.map((dp: DayPlan) =>
            dp.day_number === dayNum
              ? {
                  ...dp,
                  activities: [
                    ...dp.activities,
                    {
                      ...act,
                      id:
                        act.id ||
                        `activity-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
                      estimated_cost: {
                        amount: Number(act.estimated_cost?.amount ?? 0),
                        currency: act.estimated_cost?.currency ?? "CNY",
                      },
                    },
                  ],
                }
              : dp,
          ),
        };
        return recomputeSummary(updated);
      });
      return `Added "${act.name}" to Day ${dayNum}`;
    },
  });

  useCopilotAction({
    name: "deleteDay",
    description:
      "Completely remove a day from the itinerary. All activities for that day are deleted. Subsequent days are renumbered to stay consecutive.",
    parameters: [
      {
        name: "day",
        type: "number",
        description: "Day number to delete (1-indexed)",
        required: true,
      },
    ],
    handler: async ({ day }: { day: number }) => {
      const dayNum = Number(day);
      setItinerary((prev) => {
        if (!prev) return prev;
        const filtered = prev.day_plans.filter(
          (dp: DayPlan) => dp.day_number !== dayNum,
        );
        const renumbered = filtered.map((dp: DayPlan, idx: number) => ({
          ...dp,
          day_number: idx + 1,
        }));
        return recomputeSummary({ ...prev, day_plans: renumbered });
      });
      setMarkdownContent("");
      return `Day ${dayNum} has been completely removed and remaining days renumbered`;
    },
  });

  useCopilotAction({
    name: "addDay",
    description:
      "Add a brand-new day to the itinerary, extending the trip. Use when the user asks to add another day, extend the trip, or add a Nth day that does not yet exist. The day is appended after the last existing day. All activities must be in the same destination city as the rest of the itinerary.",
    parameters: [
      {
        name: "date",
        type: "string",
        description: "Date for the new day in YYYY-MM-DD format",
        required: true,
      },
      {
        name: "activities",
        type: "object[]",
        description:
          "Full activities list for the new day. Each activity must include id, name, description, start_time, end_time, location (name/longitude/latitude/address), category, estimated_cost (amount/currency), kind, attraction_id, hotel_id.",
        required: true,
      },
      {
        name: "notes",
        type: "string",
        description: "Optional theme or notes for the new day",
      },
    ],
    handler: async ({
      date,
      activities,
      notes,
    }: {
      date: string;
      activities: Activity[];
      notes?: string;
    }) => {
      setItinerary((prev) => {
        if (!prev) return prev;
        const newDayNumber = prev.day_plans.length + 1;
        const cleanNotes =
          notes !== undefined && notes !== "undefined" && notes !== "null"
            ? notes
            : "";
        const newDay: DayPlan = {
          day_number: newDayNumber,
          date,
          activities: activities.map((a) => ({
            ...a,
            estimated_cost: {
              amount: Number(a.estimated_cost?.amount ?? 0),
              currency: a.estimated_cost?.currency ?? "CNY",
            },
          })),
          notes: cleanNotes,
        };
        return recomputeSummary({ ...prev, day_plans: [...prev.day_plans, newDay] });
      });
      return `第${(itineraryRef.current?.day_plans.length ?? 0) + 1}天（${date}）已成功添加到行程`;
    },
  });

  useCopilotAction({
    name: "updateMarkdown",
    description:
      "Update the Markdown content displayed in the itinerary viewer after modifications",
    parameters: [
      {
        name: "markdown",
        type: "string",
        description: "Updated Markdown content for the itinerary",
        required: true,
      },
    ],
    handler: async ({ markdown }: { markdown: string }) => {
      setMarkdownContent(markdown);
      return "Markdown updated";
    },
  });

  // ── Render ───────────────────────────────────────────────────────────────

  if (!loaded) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <p className="text-gray-400">加载中……</p>
      </div>
    );
  }

  if (!itinerary) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-medium text-gray-500">暂无行程数据</p>
          <a
            href="/itinerary"
            className="mt-2 inline-block text-sm text-blue-600 hover:underline"
          >
            返回规划页面
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      {/* Top bar with sync status */}
      <div className="flex shrink-0 items-center justify-between border-b border-gray-100 bg-white px-4 py-2">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span className="font-medium text-gray-700">{itinerary.destination}</span>
          <span>·</span>
          <span>{itinerary.start_date} ~ {itinerary.end_date}</span>
        </div>
        <div className="flex items-center gap-3">
          <SyncBadge status={syncStatus} />
          <a
            href="/itinerary/my"
            className="text-xs text-blue-500 hover:underline"
          >
            我的行程
          </a>
        </div>
      </div>

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Map Panel */}
        <div className="hidden w-[300px] shrink-0 border-r p-3 lg:block">
          <MapPanel />
        </div>

        {/* Center: Itinerary Viewer */}
        <div className="min-w-0 flex-1 overflow-hidden">
          <ItineraryViewer
            itinerary={itinerary}
            markdownContent={markdownContent}
          />
        </div>

        {/* Right: CopilotKit Sidebar */}
        <CopilotSidebar
          agentId="itinerary_planner"
          defaultOpen={true}
          width="24rem"
          labels={{
            modalHeaderTitle: `AI 行程助手 · ${itinerary.destination}`,
            chatInputPlaceholder: "告诉我你想如何修改行程……",
          }}
          autoFocus={true}
        />
      </div>
    </div>
  );
}

export default function ItineraryPlannerPage() {
  return <PlannerContent />;
}
