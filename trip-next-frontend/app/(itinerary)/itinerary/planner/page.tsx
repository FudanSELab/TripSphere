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

const SYNC_STATUS_LABEL: Record<SyncStatus, string> = {
  saved: "✓ 已保存",
  saving: "⟳ 保存中…",
  unsaved: "● 未保存",
  error: "✕ 保存失败",
};

function SyncStatusBadge({ status }: { status: SyncStatus }) {
  const variantMap = {
    saved: "success",
    unsaved: "warning",
    error: "destructive",
    saving: "outline",
  } as const;

  return (
    <Badge
      variant={variantMap[status]}
      className={cn("rounded-full", status === "saving" && "animate-pulse")}
    >
      {SYNC_STATUS_LABEL[status]}
    </Badge>
  );
}

function PlannerContent() {
  const searchParams = useSearchParams();
  const [loaded, setLoaded] = useState(false);
  const [itineraryId, setItineraryId] = useState<string | null>(null);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [markdownContent, setMarkdownContent] = useState("");
  const [syncStatus, setSyncStatus] = useState<SyncStatus>("saved");

  const { agent } = useAgent({ agentId: "itinerary_planner" });

  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const snapshotRef = useRef<string | null>(null);
  const selfWriteRef = useRef(false);

  const syncToBackend = useCallback(
    async (it: Itinerary, md: string, id: string) => {
      setSyncStatus("saving");
      try {
        await updateSavedItinerary(id, it, md);
        setSyncStatus("saved");
      } catch {
        setSyncStatus("error");
      }
    },
    [],
  );

  useEffect(() => {
    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const idParam = searchParams.get("id");
      let data: { itinerary: Itinerary; markdown_content: string } | null =
        null;
      let resolvedId: string | null = null;

      if (idParam) {
        try {
          data = await getItinerary(idParam);
          resolvedId = idParam;
        } catch {
          /* leave empty */
        }
      } else {
        const raw = sessionStorage.getItem("itinerary_plan_result");
        if (raw) {
          try {
            const parsed = JSON.parse(raw) as PlanItineraryResult;
            data = parsed;
            resolvedId = parsed.itinerary.id;
            const url = new URL(window.location.href);
            url.searchParams.set("id", resolvedId);
            window.history.replaceState({}, "", url.toString());
          } catch {
            /* ignore */
          }
        }
      }

      if (cancelled) return;

      if (data) {
        const snap = JSON.stringify(data.itinerary);
        snapshotRef.current = snap;

        setItinerary(data.itinerary);
        setMarkdownContent(data.markdown_content);
        setItineraryId(resolvedId);

        selfWriteRef.current = true;
        agent.setState({
          itinerary: data.itinerary,
          markdown_content: data.markdown_content,
        });
      }

      setLoaded(true);
    }

    load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

    if (!agentItinerary) return;

    const snap = JSON.stringify(agentItinerary);
    if (snap === snapshotRef.current) return;

    snapshotRef.current = snap;
    setItinerary(agentItinerary);
    if (agentMarkdown !== undefined) setMarkdownContent(agentMarkdown);

    if (itineraryId) {
      setSyncStatus("unsaved");
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
      debounceTimer.current = setTimeout(
        () => syncToBackend(agentItinerary, agentMarkdown ?? "", itineraryId),
        1500,
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agent.state]);

  if (!loaded) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <p className="text-muted-foreground">加载中…</p>
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
          <SyncStatusBadge status={syncStatus} />
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
