"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useCoAgent } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-core/v2";
import { MapPanel } from "@/components/map-panel";
import { ItineraryViewer } from "@/components/itinerary-viewer";
import {
  getItinerary,
  updateSavedItinerary,
  type Itinerary,
  type PlanItineraryResult,
} from "@/actions/itinerary";

// ── Agent state shape (mirrors Python ChatState) ──────────────────────────

interface AgentState {
  itinerary: Itinerary | null;
  markdown_content: string;
}

// ── Sync status badge ──────────────────────────────────────────────────────

type SyncStatus = "saved" | "saving" | "unsaved" | "error";

function SyncBadge({ status }: { status: SyncStatus }) {
  const cfg: Record<SyncStatus, { label: string; cls: string }> = {
    saved: {
      label: "✓ 已保存",
      cls: "bg-emerald-50 text-emerald-600 border-emerald-200",
    },
    saving: {
      label: "⟳ 保存中…",
      cls: "bg-blue-50 text-blue-500 border-blue-200 animate-pulse",
    },
    unsaved: {
      label: "● 未保存",
      cls: "bg-amber-50 text-amber-600 border-amber-200",
    },
    error: {
      label: "✕ 保存失败",
      cls: "bg-red-50 text-red-500 border-red-200",
    },
  };
  const { label, cls } = cfg[status];
  return (
    <span
      className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${cls}`}
    >
      {label}
    </span>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

function PlannerContent() {
  const [loaded, setLoaded] = useState(false);
  const [itineraryId, setItineraryId] = useState<string | null>(null);
  const [syncStatus, setSyncStatus] = useState<SyncStatus>("saved");

  // ── Local React state drives all rendering ────────────────────────────
  // These are updated immediately on load and whenever the backend agent
  // sends a StateSnapshotEvent (via the useCoAgent setState callback below).
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [markdownContent, setMarkdownContent] = useState<string>("");

  // ── CoAgent — external-state-management mode ──────────────────────────
  // We pass our React state *in*, so CopilotKit sends it to the backend
  // on every agent run (the agent always starts with the latest itinerary).
  // When the backend tools mutate itinerary/markdown and emit a
  // StateSnapshotEvent, CopilotKit calls our setState callback, which
  // updates the React state and triggers a re-render immediately.
  useCoAgent<AgentState>({
    name: "itinerary_planner",
    state: { itinerary, markdown_content: markdownContent },
    setState: (newState) => {
      const next =
        typeof newState === "function"
          ? newState({ itinerary, markdown_content: markdownContent })
          : newState;
      if (next.itinerary != null) setItinerary(next.itinerary);
      if (next.markdown_content !== undefined)
        setMarkdownContent(next.markdown_content);
    },
  });

  // ── Skip sync on initial state population ────────────────────────────
  const isFirstLoad = useRef(true);

  // ── Load itinerary ───────────────────────────────────────────────────────

  useEffect(() => {
    async function load() {
      const params = new URLSearchParams(window.location.search);
      const idParam = params.get("id");

      if (idParam) {
        // Load from persisted backend storage
        try {
          const data = await getItinerary(idParam);
          isFirstLoad.current = true;
          setItinerary(data.itinerary);
          setMarkdownContent(data.markdown_content);
          setItineraryId(idParam);
        } catch (err) {
          console.error("Failed to load itinerary:", err);
        }
      } else {
        // Load fresh plan from sessionStorage (just-planned itinerary)
        const raw = sessionStorage.getItem("itinerary_plan_result");
        if (raw) {
          try {
            const data = JSON.parse(raw) as PlanItineraryResult;
            // Update URL so future reloads/refreshes load from MongoDB
            const url = new URL(window.location.href);
            url.searchParams.set("id", data.itinerary.id);
            window.history.replaceState({}, "", url.toString());
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

  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // Skip the very first population from REST API
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
          <span className="font-medium text-gray-700">
            {itinerary.destination}
          </span>
          <span>·</span>
          <span>
            {itinerary.start_date} ~ {itinerary.end_date}
          </span>
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
