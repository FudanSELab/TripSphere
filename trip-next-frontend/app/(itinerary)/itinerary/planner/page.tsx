"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import Link from "next/link";
import { useAgent } from "@copilotkit/react-core/v2";
import { CopilotSidebar } from "@copilotkit/react-core/v2";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { MapPlaceholder } from "@/components/itinerary/map-placeholder";
import { ItineraryViewer } from "@/components/itinerary/itinerary-viewer";
import {
  getItinerary,
  updateSavedItinerary,
  type Itinerary,
  type PlanItineraryResult,
} from "@/actions/itinerary";

type SyncStatus = "saved" | "saving" | "unsaved" | "error";

interface PendingSave {
  id: string;
  itinerary: Itinerary;
  markdown: string;
  snapshot: string;
}

function createPersistenceSnapshot(itinerary: Itinerary, markdown: string) {
  return JSON.stringify({ itinerary, markdown });
}

const SYNC_STATUS_LABEL: Record<SyncStatus, string> = {
  saved: "✓ 已保存",
  saving: "⟳ 保存中…",
  unsaved: "● 未保存",
  error: "✕ 保存失败，点击重试",
};

function SyncStatusBadge({
  status,
  onRetry,
}: {
  status: SyncStatus;
  onRetry: () => void;
}) {
  const variantMap = {
    saved: "success",
    unsaved: "warning",
    error: "destructive",
    saving: "outline",
  } as const;

  const badge = (
    <Badge
      variant={variantMap[status]}
      className={cn("rounded-full", status === "saving" && "animate-pulse")}
    >
      {SYNC_STATUS_LABEL[status]}
    </Badge>
  );

  if (status !== "error") return badge;

  return (
    <button
      type="button"
      onClick={onRetry}
      className="cursor-pointer"
      aria-label="重新保存行程"
    >
      {badge}
    </button>
  );
}

function PlannerContent() {
  const searchParams = useSearchParams();
  const queryItineraryId = searchParams.get("id");
  const [loaded, setLoaded] = useState(false);
  const [itineraryId, setItineraryId] = useState<string | null>(null);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [markdownContent, setMarkdownContent] = useState("");
  const [syncStatus, setSyncStatus] = useState<SyncStatus>("saved");
  const [loadError, setLoadError] = useState<string | null>(null);

  const { agent } = useAgent({ agentId: "itinerary_planner" });

  const mountedRef = useRef(true);
  const persistedSnapshotsRef = useRef(new Map<string, string>());
  const pendingSavesRef = useRef(new Map<string, PendingSave>());
  const failedSnapshotsRef = useRef(new Set<string>());
  const saveInFlightRef = useRef(false);
  const selfWriteRef = useRef(false);
  const activeItineraryIdRef = useRef<string | null>(null);
  const itineraryIdRef = useRef<string | null>(null);
  const localItineraryRef = useRef<Itinerary | null>(null);
  const localMarkdownRef = useRef("");

  const processSaveQueue = useCallback(
    async function processSaveQueue() {
      if (saveInFlightRef.current) return;

      const pendingSave = [...pendingSavesRef.current.values()].find(
        (candidate) => !failedSnapshotsRef.current.has(candidate.snapshot),
      );
      if (!pendingSave) return;

      saveInFlightRef.current = true;
      if (
        mountedRef.current &&
        activeItineraryIdRef.current === pendingSave.id
      ) {
        setSyncStatus("saving");
      }

      try {
        await updateSavedItinerary(
          pendingSave.id,
          pendingSave.itinerary,
          pendingSave.markdown,
        );

        const latestSave = pendingSavesRef.current.get(pendingSave.id);
        if (latestSave?.snapshot === pendingSave.snapshot) {
          pendingSavesRef.current.delete(pendingSave.id);
        }
        failedSnapshotsRef.current.delete(pendingSave.snapshot);
        persistedSnapshotsRef.current.set(
          pendingSave.id,
          pendingSave.snapshot,
        );

        if (
          mountedRef.current &&
          activeItineraryIdRef.current === pendingSave.id
        ) {
          setSyncStatus(
            pendingSavesRef.current.has(pendingSave.id) ? "unsaved" : "saved",
          );
        }
      } catch (error) {
        failedSnapshotsRef.current.add(pendingSave.snapshot);
        console.error("[Planner] Failed to sync itinerary", {
          id: pendingSave.id,
          error,
        });
        if (
          mountedRef.current &&
          activeItineraryIdRef.current === pendingSave.id
        ) {
          setSyncStatus("error");
        }
      } finally {
        saveInFlightRef.current = false;
        const hasProcessableSave = [...pendingSavesRef.current.values()].some(
          (candidate) => !failedSnapshotsRef.current.has(candidate.snapshot),
        );
        if (hasProcessableSave) void processSaveQueue();
      }
    },
    [],
  );

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    localItineraryRef.current = itinerary;
  }, [itinerary]);

  useEffect(() => {
    localMarkdownRef.current = markdownContent;
  }, [markdownContent]);

  useEffect(() => {
    itineraryIdRef.current = itineraryId;
    activeItineraryIdRef.current = itineraryId;
  }, [itineraryId]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoaded(false);
      setLoadError(null);

      let data: { itinerary: Itinerary; markdown_content: string } | null =
        null;
      let resolvedId: string | null = null;

      if (queryItineraryId) {
        try {
          data = await getItinerary(queryItineraryId);
          resolvedId = queryItineraryId;
        } catch (error) {
          console.error("[Planner] Failed to load itinerary", {
            id: queryItineraryId,
            error,
          });
          if (cancelled) return;
          setItinerary(null);
          setLoadError("行程加载失败，请稍后重试。");
          setLoaded(true);
          return;
        }
      } else {
        const raw = sessionStorage.getItem("itinerary_plan_result");
        if (raw) {
          try {
            const parsed = JSON.parse(raw) as PlanItineraryResult;
            if (parsed.itinerary?.id) {
              data = parsed;
              resolvedId = parsed.itinerary.id;
              const url = new URL(window.location.href);
              url.searchParams.set("id", resolvedId);
              window.history.replaceState({}, "", url.toString());
            }
          } catch {
            /* ignore */
          } finally {
            // Prevent stale session data from overriding future plans.
            sessionStorage.removeItem("itinerary_plan_result");
          }
        }
      }

      if (cancelled) return;

      if (data) {
        const snap = createPersistenceSnapshot(
          data.itinerary,
          data.markdown_content,
        );
        persistedSnapshotsRef.current.set(resolvedId ?? data.itinerary.id, snap);

        setItinerary(data.itinerary);
        setMarkdownContent(data.markdown_content);
        setItineraryId(resolvedId);
        itineraryIdRef.current = resolvedId;
        activeItineraryIdRef.current = resolvedId;
        localItineraryRef.current = data.itinerary;
        localMarkdownRef.current = data.markdown_content;
        setSyncStatus("saved");

        selfWriteRef.current = true;
        agent.setState({
          itinerary: data.itinerary,
          markdown_content: data.markdown_content,
        });
      } else {
        setItinerary(null);
        setMarkdownContent("");
        setItineraryId(null);
        itineraryIdRef.current = null;
        activeItineraryIdRef.current = null;
        localItineraryRef.current = null;
        localMarkdownRef.current = "";
      }

      setLoaded(true);
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [agent, queryItineraryId]);

  useEffect(() => {
    if (!loaded) return;

    if (selfWriteRef.current) {
      selfWriteRef.current = false;
      return;
    }

    const agentItinerary = (
      agent.state as { itinerary?: Itinerary; markdown_content?: string } | null
    )?.itinerary;
    const agentMarkdown = (agent.state as { markdown_content?: string } | null)
      ?.markdown_content;

    const activeId = activeItineraryIdRef.current;
    const localItinerary = localItineraryRef.current;
    if (!activeId) return;

    if (!agentItinerary?.id) {
      if (localItinerary?.id && localItinerary.id === activeId) {
        selfWriteRef.current = true;
        agent.setState({
          itinerary: localItinerary,
          markdown_content: localMarkdownRef.current,
        });
      }
      return;
    }

    if (activeId && agentItinerary.id !== activeId) {
      if (localItinerary?.id === activeId) {
        selfWriteRef.current = true;
        agent.setState({
          itinerary: localItinerary,
          markdown_content: localMarkdownRef.current,
        });
      }
      return;
    }

    const nextMarkdown = agentMarkdown ?? localMarkdownRef.current;
    const snap = createPersistenceSnapshot(agentItinerary, nextMarkdown);
    const persistedSnapshot = persistedSnapshotsRef.current.get(activeId);
    const pendingSnapshot = pendingSavesRef.current.get(activeId)?.snapshot;
    if (snap === persistedSnapshot || snap === pendingSnapshot) return;

    setItinerary(agentItinerary);
    setItineraryId(agentItinerary.id);
    itineraryIdRef.current = agentItinerary.id;
    activeItineraryIdRef.current = agentItinerary.id;
    localItineraryRef.current = agentItinerary;
    if (agentMarkdown !== undefined) setMarkdownContent(agentMarkdown);
    localMarkdownRef.current = nextMarkdown;

    const saveId = itineraryIdRef.current;
    if (saveId && saveId === agentItinerary.id) {
      setSyncStatus("unsaved");
      const previousSave = pendingSavesRef.current.get(saveId);
      if (previousSave) {
        failedSnapshotsRef.current.delete(previousSave.snapshot);
      }
      pendingSavesRef.current.set(saveId, {
        id: saveId,
        itinerary: agentItinerary,
        markdown: nextMarkdown,
        snapshot: snap,
      });
      void processSaveQueue();
    }
  }, [agent, agent.state, loaded, processSaveQueue]);

  const retrySave = useCallback(() => {
    const activeId = activeItineraryIdRef.current;
    if (!activeId) return;
    const pendingSave = pendingSavesRef.current.get(activeId);
    if (!pendingSave) return;
    failedSnapshotsRef.current.delete(pendingSave.snapshot);
    setSyncStatus("unsaved");
    void processSaveQueue();
  }, [processSaveQueue]);

  if (!loaded) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <p className="text-muted-foreground">加载中…</p>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <div className="text-center">
          <p role="alert" className="text-destructive text-lg font-medium">
            {loadError}
          </p>
          <div className="mt-3 flex justify-center gap-4 text-sm">
            <button
              type="button"
              className="text-primary hover:underline"
              onClick={() => window.location.reload()}
            >
              重试
            </button>
            <Link href="/itinerary" className="text-primary hover:underline">
              返回我的行程
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!itinerary) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <div className="text-center">
          <p className="text-foreground text-lg font-medium">暂无行程数据</p>
          <Link
            href="/itinerary"
            className="text-primary mt-2 inline-block text-sm hover:underline"
          >
            返回规划页面
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      <div className="border-border bg-background flex shrink-0 items-center justify-between border-b px-4 py-2">
        <div className="text-muted-foreground flex items-center gap-2 text-sm">
          <span className="text-foreground font-medium">
            {itinerary.destination}
          </span>
          <span>·</span>
          <span>
            {itinerary.start_date} ~ {itinerary.end_date}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <SyncStatusBadge status={syncStatus} onRetry={retrySave} />
          <Link
            href="/itinerary"
            className="text-primary text-xs hover:underline"
          >
            我的行程
          </Link>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <div className="hidden min-w-0 flex-1 overflow-hidden border-r lg:block">
          <MapPlaceholder />
        </div>

        <div className="w-[40rem] shrink-0 overflow-hidden">
          <ItineraryViewer
            itinerary={itinerary}
            markdownContent={markdownContent}
          />
        </div>

        <CopilotSidebar
          key={itinerary.id}
          agentId="itinerary_planner"
          defaultOpen={true}
          width="30rem"
          labels={{
            modalHeaderTitle: `AI行程助手 · ${itinerary.destination}`,
            chatInputPlaceholder: "告诉我你想如何修改行程…",
          }}
        />
      </div>
    </div>
  );
}

export default function ItineraryPlannerPage() {
  return (
    <Suspense>
      <PlannerContent />
    </Suspense>
  );
}
