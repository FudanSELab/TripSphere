"use server";

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

const PLANNER_URL =
  process.env.HTTP_ITINERARY_PLANNER_URL || "http://localhost:24215";

export async function createItineraryPlan(
  input: PlanItineraryInput,
): Promise<PlanItineraryResult> {
  const res = await fetch(`${PLANNER_URL}/api/v1/itineraries/plannings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: "anonymous",
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
