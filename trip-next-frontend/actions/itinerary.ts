"use server";

import { headers } from "next/headers";

export type TravelInterest =
  | "culture"
  | "classic"
  | "nature"
  | "cityscape"
  | "history";

export type TripPace = "relaxed" | "moderate" | "intense";

export interface PlanItineraryInput {
  destination: string;
  startDate: string;
  endDate: string;
  interests: TravelInterest[];
  pace: TripPace;
  additionalPreferences: string;
}

export interface ActivityLocation {
  name: string;
  longitude: number;
  latitude: number;
  address: string;
}

export interface ActivityCost {
  amount: number;
  currency: string;
}

export interface Activity {
  id: string;
  name: string;
  description: string;
  start_time: string;
  end_time: string;
  location: ActivityLocation;
  category: string;
  estimated_cost: ActivityCost;
  kind: string;
  attraction_id: string | null;
  hotel_id: string | null;
}

export interface DayPlan {
  day_number: number;
  date: string;
  activities: Activity[];
  notes: string;
}

export interface ItinerarySummary {
  total_estimated_cost: number;
  currency: string;
  total_activities: number;
  highlights: string[];
}

export interface Itinerary {
  id: string;
  destination: string;
  start_date: string;
  end_date: string;
  day_plans: DayPlan[];
  summary: ItinerarySummary | null;
}

export interface PlanItineraryResult {
  itinerary: Itinerary;
  markdown_content: string;
  conversation_messages: { role: string; content: string }[];
}

export interface SavedItinerarySummary {
  id: string;
  destination: string;
  start_date: string;
  end_date: string;
  day_count: number;
  created_at: string;
  updated_at: string;
}

const PLANNER_URL =
  process.env.HTTP_ITINERARY_PLANNER_URL || "http://localhost:24215";

// ── Auth helper ────────────────────────────────────────────────────────────

async function getPlannerHeaders(extra?: Record<string, string>): Promise<HeadersInit> {
  const reqHeaders = await headers();
  const userId = reqHeaders.get("x-user-id") ?? "";
  return {
    "Content-Type": "application/json",
    "x-user-id": userId,
    ...extra,
  };
}

// ── Planning ───────────────────────────────────────────────────────────────

export async function createItineraryPlan(
  input: PlanItineraryInput,
): Promise<PlanItineraryResult> {
  const h = await getPlannerHeaders();

  const res = await fetch(`${PLANNER_URL}/api/v1/itineraries/plannings`, {
    method: "POST",
    headers: h,
    body: JSON.stringify({
      destination: input.destination,
      start_date: input.startDate,
      end_date: input.endDate,
      interests: input.interests,
      pace: input.pace,
      additional_preferences: input.additionalPreferences,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Planning failed (${res.status}): ${text}`);
  }

  return res.json();
}

// ── Persistence CRUD ───────────────────────────────────────────────────────

export async function listMyItineraries(): Promise<SavedItinerarySummary[]> {
  const h = await getPlannerHeaders();
  const res = await fetch(`${PLANNER_URL}/api/v1/itineraries`, { headers: h });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`List itineraries failed (${res.status}): ${text}`);
  }
  return res.json();
}

export async function getItinerary(id: string): Promise<PlanItineraryResult> {
  const h = await getPlannerHeaders();
  const res = await fetch(`${PLANNER_URL}/api/v1/itineraries/${id}`, {
    headers: h,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Get itinerary failed (${res.status}): ${text}`);
  }
  return res.json();
}

export async function updateSavedItinerary(
  id: string,
  itinerary: Itinerary,
  markdownContent?: string,
): Promise<void> {
  const h = await getPlannerHeaders();
  const res = await fetch(`${PLANNER_URL}/api/v1/itineraries/${id}`, {
    method: "PUT",
    headers: h,
    body: JSON.stringify({
      itinerary,
      markdown_content: markdownContent ?? null,
    }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Update itinerary failed (${res.status}): ${text}`);
  }
}

export async function deleteItinerary(id: string): Promise<void> {
  const h = await getPlannerHeaders();
  const res = await fetch(`${PLANNER_URL}/api/v1/itineraries/${id}`, {
    method: "DELETE",
    headers: h,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Delete itinerary failed (${res.status}): ${text}`);
  }
}
