"use client";

import type { Itinerary } from "@/lib/types";
import { useCallback, useState } from "react";

// Planning progress event from backend
export interface PlanningProgressEvent {
  progress_percentage: number;
  status_message: string;
  current_step: string;
  itinerary: Itinerary | null;
}

// Request to plan an itinerary
export interface PlanItineraryRequest {
  user_id: string;
  destination: string;
  start_date: string;
  end_date: string;
  interests: string[];
  pace: "relaxed" | "moderate" | "intense";
  additional_preferences?: string;
}

// Convert snake_case itinerary from backend to camelCase for frontend
function convertItinerary(data: Record<string, unknown>): Itinerary {
  const dayPlans = (data.day_plans as Record<string, unknown>[]) || [];

  return {
    id: data.id as string,
    destination: data.destination as string,
    startDate: data.start_date as string,
    endDate: data.end_date as string,
    dayPlans: dayPlans.map((day) => ({
      dayNumber: day.day_number as number,
      date: day.date as string,
      activities: ((day.activities as Record<string, unknown>[]) || []).map(
        (activity) => ({
          id: activity.id as string,
          name: activity.name as string,
          description: activity.description as string,
          startTime: activity.start_time as string,
          endTime: activity.end_time as string,
          location: {
            name: (activity.location as Record<string, unknown>)
              ?.name as string,
            latitude: (activity.location as Record<string, unknown>)
              ?.latitude as number,
            longitude: (activity.location as Record<string, unknown>)
              ?.longitude as number,
            address: (activity.location as Record<string, unknown>)
              ?.address as string,
          },
          category: activity.category as string,
          cost: activity.estimated_cost
            ? {
                amount: (activity.estimated_cost as Record<string, unknown>)
                  ?.amount as number,
                currency: ((activity.estimated_cost as Record<string, unknown>)
                  ?.currency || "CNY") as string,
              }
            : undefined,
        }),
      ),
      notes: day.notes as string | undefined,
    })),
    summary: data.summary
      ? {
          totalEstimatedCost: (data.summary as Record<string, unknown>)
            .total_estimated_cost as number,
          currency: ((data.summary as Record<string, unknown>).currency ||
            "CNY") as string,
          totalActivities: (data.summary as Record<string, unknown>)
            .total_activities as number,
          highlights: ((data.summary as Record<string, unknown>).highlights ||
            []) as string[],
        }
      : undefined,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

export function useItineraryPlanner() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [currentStep, setCurrentStep] = useState("");
  const [error, setError] = useState<string | null>(null);

  const baseUrl =
    process.env.HTTP_ITINERARY_PLANNER_URL || "http://localhost:24215";

  /**
   * Plan an itinerary with streaming progress updates
   */
  const planItineraryStream = useCallback(
    async (
      request: PlanItineraryRequest,
      onProgress?: (event: PlanningProgressEvent) => void,
      onComplete?: (itinerary: Itinerary) => void,
      onError?: (error: Error) => void,
    ): Promise<Itinerary | null> => {
      setIsGenerating(true);
      setProgress(0);
      setStatusMessage("Starting planning...");
      setCurrentStep("");
      setError(null);

      let finalItinerary: Itinerary | null = null;

      try {
        const response = await fetch(
          `${baseUrl}/api/v1/itineraries/plannings:stream`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Accept: "text/event-stream",
            },
            body: JSON.stringify(request),
          },
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error("No response body");
        }

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");

          // Keep the last incomplete line in buffer
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.trim()) continue;

            // Parse SSE format
            if (line.startsWith("data: ")) {
              const data = line.slice(6).trim();
              if (!data) continue;

              try {
                const event = JSON.parse(data) as Record<string, unknown>;

                // Update progress state
                const progressPercent =
                  (event.progress_percentage as number) || 0;
                const message =
                  (event.status_message as string) || "Processing...";
                const step = (event.current_step as string) || "";

                setProgress(progressPercent);
                setStatusMessage(message);
                setCurrentStep(step);

                // Check if itinerary is included (final event)
                if (event.itinerary) {
                  finalItinerary = convertItinerary(
                    event.itinerary as Record<string, unknown>,
                  );
                }

                // Call progress callback
                onProgress?.({
                  progress_percentage: progressPercent,
                  status_message: message,
                  current_step: step,
                  itinerary: finalItinerary,
                });
              } catch (e) {
                console.warn("Failed to parse SSE data:", data, e);
              }
            } else if (line.startsWith("event: ")) {
              const eventType = line.slice(7).trim();
              if (eventType === "completed") {
                // Planning completed successfully
                if (finalItinerary) {
                  onComplete?.(finalItinerary);
                }
              } else if (eventType === "failed") {
                // Planning failed - error will be in the next data line
                console.error("Planning failed");
              }
            }
          }
        }

        // Call complete callback if we have an itinerary
        if (finalItinerary) {
          onComplete?.(finalItinerary);
        }

        return finalItinerary;
      } catch (e) {
        const err = e instanceof Error ? e : new Error("Planning failed");
        setError(err.message);
        onError?.(err);
        return null;
      } finally {
        setIsGenerating(false);
      }
    },
    [baseUrl],
  );

  /**
   * Plan an itinerary without streaming (blocking call)
   */
  const planItinerary = useCallback(
    async (request: PlanItineraryRequest): Promise<Itinerary | null> => {
      setIsGenerating(true);
      setProgress(0);
      setStatusMessage("Planning your trip...");
      setError(null);

      try {
        const response = await fetch(
          `${baseUrl}/api/v1/itineraries/plannings`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(request),
          },
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = (await response.json()) as Record<string, unknown>;
        const itinerary = convertItinerary(data);

        setProgress(100);
        setStatusMessage("Complete!");

        return itinerary;
      } catch (e) {
        const err = e instanceof Error ? e : new Error("Planning failed");
        setError(err.message);
        return null;
      } finally {
        setIsGenerating(false);
      }
    },
    [baseUrl],
  );

  /**
   * Reset the planner state
   */
  const reset = useCallback(() => {
    setIsGenerating(false);
    setProgress(0);
    setStatusMessage("");
    setCurrentStep("");
    setError(null);
  }, []);

  return {
    isGenerating,
    progress,
    statusMessage,
    currentStep,
    error,
    planItineraryStream,
    planItinerary,
    reset,
  };
}
