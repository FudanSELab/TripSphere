"use client";

import { useEffect, useState } from "react";
import { useCopilotAction, useCopilotReadable } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-core/v2";
import { MapPanel } from "@/components/map-panel";
import { ItineraryViewer } from "@/components/itinerary-viewer";
import type {
  Itinerary,
  PlanItineraryResult,
  DayPlan,
  Activity,
} from "@/actions/itinerary";

function PlannerContent() {
  const [initialData, setInitialData] = useState<PlanItineraryResult | null>(
    null,
  );
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem("itinerary_plan_result");
    if (raw) {
      try {
        setInitialData(JSON.parse(raw) as PlanItineraryResult);
      } catch {
        /* ignore parse errors */
      }
    }
    setLoaded(true);
  }, []);

  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [markdownContent, setMarkdownContent] = useState("");

  useEffect(() => {
    if (initialData) {
      setItinerary(initialData.itinerary);
      setMarkdownContent(initialData.markdown_content);
    }
  }, [initialData]);

  // ---------- CopilotKit Context ----------

  useCopilotReadable({
    description: "Current travel itinerary in structured JSON format",
    value: itinerary,
  });

  useCopilotReadable({
    description: "Current travel itinerary in Markdown format",
    value: markdownContent,
  });

  // ---------- CopilotKit Actions (Tools) ----------

  useCopilotAction({
    name: "updateItinerary",
    description:
      "Update the activities for a specific day. Provide the full list of updated activities.",
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
        description: "Updated activities array for the day",
        required: true,
      },
      {
        name: "notes",
        type: "string",
        description: "Optional updated notes for the day",
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
      setItinerary((prev) => {
        if (!prev) return prev;
        const updated: Itinerary = {
          ...prev,
          day_plans: prev.day_plans.map((dp: DayPlan) =>
            dp.day_number === day
              ? { ...dp, activities, ...(notes !== undefined ? { notes } : {}) }
              : dp,
          ),
        };
        return updated;
      });
      setMarkdownContent("");
      return `Day ${day} updated successfully`;
    },
  });

  useCopilotAction({
    name: "removeSpot",
    description: "Remove a specific spot/activity from a day by name",
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
      let removed = false;
      setItinerary((prev) => {
        if (!prev) return prev;
        const updated: Itinerary = {
          ...prev,
          day_plans: prev.day_plans.map((dp: DayPlan) => {
            if (dp.day_number !== day) return dp;
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
        return updated;
      });
      setMarkdownContent("");
      return removed
        ? `Removed "${spotName}" from Day ${day}`
        : `Could not find "${spotName}" in Day ${day}`;
    },
  });

  useCopilotAction({
    name: "regenerateDay",
    description:
      "Request to regenerate all activities for a specific day with new preferences. Returns updated markdown.",
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
          "New preference or style for the day (e.g. relaxed, food-focused)",
        required: true,
      },
    ],
    handler: async ({
      day,
      preference,
    }: {
      day: number;
      preference: string;
    }) => {
      setMarkdownContent("");
      return `Day ${day} regeneration requested with preference: "${preference}". Please generate the new activities and call updateItinerary to apply them.`;
    },
  });

  useCopilotAction({
    name: "addActivity",
    description: "Add a new activity to a specific day",
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
        description: "The activity to add",
        required: true,
      },
    ],
    handler: async ({ day, activity }: { day: number; activity: Activity }) => {
      setItinerary((prev) => {
        if (!prev) return prev;
        const updated: Itinerary = {
          ...prev,
          day_plans: prev.day_plans.map((dp: DayPlan) =>
            dp.day_number === day
              ? {
                  ...dp,
                  activities: [
                    ...dp.activities,
                    {
                      ...activity,
                      id:
                        activity.id ||
                        `activity-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
                    },
                  ],
                }
              : dp,
          ),
        };
        return updated;
      });
      setMarkdownContent("");
      return `Added "${activity.name}" to Day ${day}`;
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

  // ---------- Render ----------

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
    <div className="flex h-[calc(100vh-4rem)]">
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
          modalHeaderTitle: "AI 行程助手",
          chatInputPlaceholder: "告诉我你想如何修改行程……",
        }}
        autoFocus={true}
      />
    </div>
  );
}

export default function ItineraryPlannerPage() {
  return <PlannerContent />;
}
