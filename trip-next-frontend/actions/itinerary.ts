"use server";

import { headers } from "next/headers";
import { getAuthMetadata, getItineraryService } from "@/lib/grpc/client";
import type { Address } from "@/lib/grpc/generated/tripsphere/common/v1/map";
import {
  ActivityKind,
  type Itinerary as ProtoItinerary,
  type DayPlan as ProtoDayPlan,
  type Activity as ProtoActivity,
  type ItinerarySummary as ProtoItinerarySummary,
  type ReplaceItineraryRequest,
  type ListUserItinerariesRequest,
  type ListUserItinerariesResponse,
  type GetItineraryRequest,
  type GetItineraryResponse,
} from "@/lib/grpc/generated/tripsphere/itinerary/v1/itinerary";
import type { Metadata } from "@grpc/grpc-js";
import { parseDateOnly } from "@/lib/format";

// ── Re-exported public types ───────────────────────────────────────────────

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

// ── Proto ↔ frontend conversion helpers ───────────────────────────────────

function formatAddressLine(addr: Address | undefined): string {
  if (!addr) return "";
  return [addr.province, addr.city, addr.district, addr.detailed]
    .filter(Boolean)
    .join("");
}

function formatDate(
  d: { year: number; month: number; day: number } | undefined,
): string {
  if (!d) return "";
  return `${d.year.toString().padStart(4, "0")}-${d.month.toString().padStart(2, "0")}-${d.day.toString().padStart(2, "0")}`;
}

function parseDate(iso: string): { year: number; month: number; day: number } {
  const dt = parseDateOnly(iso);
  if (!dt) return { year: NaN, month: NaN, day: NaN };
  return {
    year: dt.getFullYear(),
    month: dt.getMonth() + 1,
    day: dt.getDate(),
  };
}

function formatTime(t: { hours: number; minutes: number } | undefined): string {
  if (!t) return "00:00";
  return `${t.hours.toString().padStart(2, "0")}:${t.minutes.toString().padStart(2, "0")}`;
}

function parseTime(hhmm: string): {
  hours: number;
  minutes: number;
  seconds: number;
  nanos: number;
} {
  const [h, m] = hhmm.split(":").map(Number);
  return { hours: h || 0, minutes: m || 0, seconds: 0, nanos: 0 };
}

const KIND_STRING_TO_PROTO: Record<string, ActivityKind> = {
  attraction_visit: ActivityKind.ACTIVITY_KIND_ATTRACTION_VISIT,
  dining: ActivityKind.ACTIVITY_KIND_DINING,
  hotel_stay: ActivityKind.ACTIVITY_KIND_HOTEL_STAY,
  custom: ActivityKind.ACTIVITY_KIND_CUSTOM,
};

const KIND_PROTO_TO_STRING: Partial<Record<ActivityKind, string>> = {
  [ActivityKind.ACTIVITY_KIND_ATTRACTION_VISIT]: "attraction_visit",
  [ActivityKind.ACTIVITY_KIND_DINING]: "dining",
  [ActivityKind.ACTIVITY_KIND_HOTEL_STAY]: "hotel_stay",
  [ActivityKind.ACTIVITY_KIND_CUSTOM]: "custom",
};

function protoActivityToFrontend(a: ProtoActivity): Activity {
  const loc = a.location;
  const addrLine = formatAddressLine(a.address);
  const cost = a.estimatedCost;
  const amount = cost ? Number(cost.units) + cost.nanos / 1_000_000_000 : 0;

  let attraction_id: string | null = null;
  let hotel_id: string | null = null;
  if (a.attraction?.id) attraction_id = a.attraction.id;
  else if (a.hotel?.id) hotel_id = a.hotel.id;

  return {
    id: a.id,
    name: a.title,
    description: a.description,
    start_time: formatTime(a.startTime),
    end_time: formatTime(a.endTime),
    location: {
      name: a.title,
      latitude: loc?.latitude ?? 0,
      longitude: loc?.longitude ?? 0,
      address: addrLine,
    },
    category: a.category || "sightseeing",
    estimated_cost: { amount, currency: cost?.currency || "CNY" },
    kind: KIND_PROTO_TO_STRING[a.kind] ?? "attraction_visit",
    attraction_id,
    hotel_id,
  };
}

function frontendActivityToProto(a: Activity): ProtoActivity {
  const hasCoords = a.location.latitude !== 0 || a.location.longitude !== 0;
  const proto: ProtoActivity = {
    id: a.id,
    title: a.name,
    description: a.description,
    kind:
      KIND_STRING_TO_PROTO[a.kind] ?? ActivityKind.ACTIVITY_KIND_UNSPECIFIED,
    startTime: parseTime(a.start_time),
    endTime: parseTime(a.end_time),
    estimatedCost: {
      currency: a.estimated_cost.currency,
      units: Math.trunc(a.estimated_cost.amount),
      nanos: Math.round((a.estimated_cost.amount % 1) * 1_000_000_000),
    },
    location: hasCoords
      ? { longitude: a.location.longitude, latitude: a.location.latitude }
      : undefined,
    address: a.location.address
      ? {
          province: "",
          city: "",
          district: "",
          detailed: a.location.address,
        }
      : undefined,
    category: a.category,
    metadata: undefined,
  };
  if (a.attraction_id)
    proto.attraction = { id: a.attraction_id } as ProtoActivity["attraction"];
  else if (a.hotel_id)
    proto.hotel = { id: a.hotel_id } as ProtoActivity["hotel"];
  return proto;
}

function protoDayPlanToFrontend(dp: ProtoDayPlan): DayPlan {
  return {
    day_number: dp.dayNumber,
    date: formatDate(dp.date),
    activities: dp.activities.map(protoActivityToFrontend),
    notes: dp.notes,
  };
}

function frontendDayPlanToProto(dp: DayPlan): ProtoDayPlan {
  return {
    id: "",
    date: parseDate(dp.date),
    title: "",
    dayNumber: dp.day_number,
    notes: dp.notes,
    activities: dp.activities.map(frontendActivityToProto),
    metadata: undefined,
  };
}

function moneyToAmount(
  m: { units: number; nanos: number; currency: string } | undefined,
): { amount: number; currency: string } {
  if (!m) return { amount: 0, currency: "CNY" };
  const amount = m.units + m.nanos / 1_000_000_000;
  return { amount, currency: m.currency || "CNY" };
}

function amountToMoney(
  amount: number,
  currency: string,
): { units: number; nanos: number; currency: string } {
  return {
    currency: currency || "CNY",
    units: Math.trunc(amount),
    nanos: Math.round((amount % 1) * 1_000_000_000),
  };
}

function protoItineraryToFrontend(proto: ProtoItinerary): Itinerary {
  let summary: ItinerarySummary | null = null;
  if (proto.summary) {
    const { amount, currency } = moneyToAmount(
      proto.summary.totalEstimatedCost,
    );
    summary = {
      total_estimated_cost: amount,
      currency,
      total_activities: proto.summary.totalActivities,
      highlights: proto.summary.highlights,
    };
  }
  return {
    id: proto.id,
    destination: proto.destinationName || proto.title,
    start_date: formatDate(proto.startDate),
    end_date: formatDate(proto.endDate),
    day_plans: proto.dayPlans.map(protoDayPlanToFrontend),
    summary,
  };
}

function frontendItineraryToProto(
  it: Itinerary,
  markdownContent: string = "",
): ProtoItinerary {
  let summary: ProtoItinerarySummary | undefined;
  if (it.summary) {
    summary = {
      totalEstimatedCost: amountToMoney(
        it.summary.total_estimated_cost,
        it.summary.currency,
      ),
      totalActivities: it.summary.total_activities,
      highlights: it.summary.highlights,
    };
  }
  return {
    id: it.id,
    title: it.destination,
    userId: "",
    destination: undefined,
    startDate: parseDate(it.start_date),
    endDate: parseDate(it.end_date),
    dayPlans: it.day_plans.map(frontendDayPlanToProto),
    metadata: undefined,
    destinationName: it.destination,
    summary,
    markdownContent: markdownContent,
    createdAt: undefined,
    updatedAt: undefined,
  };
}

/** Accept Date (from TS gRPC decode), proto Timestamp shape, or undefined. */
function toIsoString(
  value: Date | { seconds: number; nanos: number } | undefined,
): string {
  if (value == null) return new Date().toISOString();
  if (value instanceof Date) {
    const ms = value.getTime();
    if (Number.isNaN(ms)) return new Date().toISOString();
    return value.toISOString();
  }
  const ms = value.seconds * 1000 + value.nanos / 1_000_000;
  const d = new Date(ms);
  return Number.isNaN(d.getTime()) ? new Date().toISOString() : d.toISOString();
}

// ── gRPC promisify helper ──────────────────────────────────────────────────

function callGrpc<Req, Res>(
  client: ReturnType<typeof getItineraryService>,
  method: keyof ReturnType<typeof getItineraryService>,
  request: Req,
  metadata: Metadata,
): Promise<Res> {
  return new Promise<Res>((resolve, reject) => {
    (
      client[method] as (
        req: Req,
        meta: Metadata,
        cb: (err: unknown, res: Res) => void,
      ) => void
    )(request, metadata, (error: unknown, response: Res) => {
      if (error) reject(error);
      else resolve(response);
    });
  });
}

// ── Planning (HTTP to planner) ─────────────────────────────────────────────

const PLANNER_URL =
  process.env.HTTP_ITINERARY_PLANNER_URL || "http://localhost:24215";

export async function createItineraryPlan(
  input: PlanItineraryInput,
): Promise<PlanItineraryResult> {
  const reqHeaders = await headers();
  const userId = reqHeaders.get("x-user-id") ?? "";
  const h: HeadersInit = {
    "Content-Type": "application/json",
    "x-user-id": userId,
  };

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

// ── Persistence CRUD (gRPC to trip-itinerary-service) ─────────────────────

export async function listMyItineraries(): Promise<SavedItinerarySummary[]> {
  const client = getItineraryService();
  const metadata = await getAuthMetadata();
  const reqHeaders = await headers();
  const userId = reqHeaders.get("x-user-id") ?? "";

  if (!userId) throw new Error("Missing x-user-id header");

  const { itineraries } = await callGrpc<
    ListUserItinerariesRequest,
    ListUserItinerariesResponse
  >(
    client,
    "listUserItineraries",
    { userId, pageSize: 50, pageToken: "" },
    metadata,
  );

  return (itineraries ?? []).map((it) => ({
    id: it.id,
    destination: it.destinationName || it.title,
    start_date: formatDate(it.startDate),
    end_date: formatDate(it.endDate),
    day_count: it.dayPlans.length,
    created_at: toIsoString(it.createdAt),
    updated_at: toIsoString(it.updatedAt),
  }));
}

export async function getItinerary(id: string): Promise<PlanItineraryResult> {
  const client = getItineraryService();
  const metadata = await getAuthMetadata();

  const { itinerary } = await callGrpc<
    GetItineraryRequest,
    GetItineraryResponse
  >(client, "getItinerary", { id }, metadata);

  if (!itinerary) throw new Error("Itinerary not found");

  return {
    itinerary: protoItineraryToFrontend(itinerary),
    markdown_content: itinerary.markdownContent ?? "",
    conversation_messages: [],
  };
}

export async function updateSavedItinerary(
  id: string,
  itinerary: Itinerary,
  markdownContent?: string,
): Promise<void> {
  const client = getItineraryService();
  const metadata = await getAuthMetadata();

  const proto = frontendItineraryToProto(itinerary, markdownContent ?? "");

  await callGrpc<ReplaceItineraryRequest, unknown>(
    client,
    "replaceItinerary",
    { id, itinerary: proto },
    metadata,
  );
}

export async function deleteItinerary(id: string): Promise<void> {
  const client = getItineraryService();
  const metadata = await getAuthMetadata();

  await callGrpc<Parameters<typeof client.deleteItinerary>[0], unknown>(
    client,
    "deleteItinerary",
    { id },
    metadata,
  );
}
