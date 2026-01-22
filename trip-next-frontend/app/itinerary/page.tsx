"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/lib/hooks/use-auth";
import { useItineraryPlanner } from "@/lib/hooks/use-itinerary-planner";
import type { Itinerary } from "@/lib/types";
import {
  Calendar,
  ChevronDown,
  ChevronUp,
  Loader2,
  MapPin,
  Settings,
  Sparkles,
} from "lucide-react";
import { useState } from "react";

// Travel preference options
const travelInterests = [
  { id: "culture", label: "Culture", icon: "🎭" },
  { id: "classic", label: "Classic", icon: "⭐" },
  { id: "nature", label: "Nature", icon: "🏞️" },
  { id: "cityscape", label: "Cityscape", icon: "🏙️" },
  { id: "history", label: "History", icon: "🏛️" },
];

const paceOptions = [
  { value: "relaxed", label: "Relaxed", description: "2-3 places/d" },
  { value: "moderate", label: "Moderate", description: "3-4 places/d" },
  { value: "intense", label: "Intense", description: "5+ places/d" },
];

export default function ItineraryPage() {
  const auth = useAuth();
  const planner = useItineraryPlanner();

  // Form state
  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // Preference state
  const [interests, setInterests] = useState<string[]>([]);
  const [pace, setPace] = useState<"relaxed" | "moderate" | "intense">(
    "moderate",
  );
  const [additionalPreferences, setAdditionalPreferences] = useState("");
  const [showPreferences, setShowPreferences] = useState(true);

  // Generated itinerary state
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [expandedDays, setExpandedDays] = useState<number[]>([1]);

  // Toggle interest selection
  const toggleInterest = (interestId: string) => {
    setInterests((prev) =>
      prev.includes(interestId)
        ? prev.filter((i) => i !== interestId)
        : [...prev, interestId],
    );
  };

  // Generate itinerary using streaming API
  const generateItinerary = async () => {
    if (!destination || !startDate || !endDate) {
      return;
    }

    // Reset previous itinerary
    setItinerary(null);

    // Call streaming API
    const result = await planner.planItineraryStream(
      {
        user_id: auth.user?.id || "anonymous",
        destination,
        start_date: startDate,
        end_date: endDate,
        interests,
        pace,
        additional_preferences: additionalPreferences,
      },
      // onProgress callback
      (event) => {
        console.log("Progress:", event);
      },
      // onComplete callback
      (completedItinerary) => {
        setItinerary(completedItinerary);
        setExpandedDays([1]);
      },
      // onError callback
      (error) => {
        console.error("Planning failed:", error);
      },
    );

    // Also set itinerary from result if not set by callback
    if (result && !itinerary) {
      setItinerary(result);
      setExpandedDays([1]);
    }
  };

  // Toggle day expansion
  const toggleDay = (dayNumber: number) => {
    setExpandedDays((prev) =>
      prev.includes(dayNumber)
        ? prev.filter((d) => d !== dayNumber)
        : [...prev, dayNumber],
    );
  };

  // Format date for display
  const formatDayDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
  };

  // Get activity category color
  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      sightseeing: "bg-blue-100 text-blue-700",
      dining: "bg-orange-100 text-orange-700",
      transportation: "bg-gray-100 text-gray-700",
      shopping: "bg-pink-100 text-pink-700",
      entertainment: "bg-purple-100 text-purple-700",
    };
    return colors[category] || "bg-gray-100 text-gray-700";
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero section */}
      <div className="bg-linear-to-br from-green-600 to-emerald-600 pt-32 pb-16 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <span className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/20 px-4 py-2 text-sm font-medium">
              <Sparkles className="h-4 w-4" />
              AI-Powered Planning
            </span>
            <h1 className="mb-4 text-4xl font-bold sm:text-5xl">
              Plan Your Perfect Trip
            </h1>
            <p className="mx-auto max-w-2xl text-xl text-white/80">
              Let our AI create a personalized itinerary based on your
              preferences, interests, and travel style.
            </p>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Planning form */}
          <div className="lg:col-span-1">
            <Card className="sticky top-24">
              <h2 className="mb-6 text-xl font-semibold text-gray-900">
                Trip Details
              </h2>

              <form
                className="space-y-5"
                onSubmit={(e) => {
                  e.preventDefault();
                  generateItinerary();
                }}
              >
                {/* Destination */}
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Destination
                  </label>
                  <div className="relative">
                    <MapPin className="absolute top-1/2 left-3 h-5 w-5 -translate-y-1/2 text-gray-400" />
                    <input
                      value={destination}
                      onChange={(e) => setDestination(e.target.value)}
                      placeholder="e.g., Shanghai, China"
                      className="w-full rounded-lg border border-gray-300 py-2 pr-4 pl-10 focus:border-transparent focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                </div>

                {/* Dates */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                </div>

                {/* Preferences Section Header */}
                <div className="pt-2">
                  <button
                    type="button"
                    className="flex w-full items-center justify-between text-left"
                    onClick={() => setShowPreferences(!showPreferences)}
                  >
                    <div className="flex items-center gap-2">
                      <Settings className="h-4 w-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-900">
                        Preferences
                      </span>
                    </div>
                    {showPreferences ? (
                      <ChevronDown className="h-4 w-4 text-gray-500" />
                    ) : (
                      <ChevronUp className="h-4 w-4 text-gray-500" />
                    )}
                  </button>
                </div>

                {/* Preferences Content */}
                {showPreferences && (
                  <div className="space-y-4">
                    {/* Travel Interests */}
                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        Travel Interests
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {travelInterests.map((interest) => (
                          <button
                            key={interest.id}
                            type="button"
                            className={`flex items-center gap-1.5 rounded-full px-3 py-2 text-sm font-medium transition-all ${
                              interests.includes(interest.id)
                                ? "bg-green-600 text-white shadow-sm"
                                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                            }`}
                            onClick={() => toggleInterest(interest.id)}
                          >
                            <span>{interest.icon}</span>
                            <span>{interest.label}</span>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Pace Selection */}
                    <div>
                      <label className="mt-6 mb-2 block text-sm font-medium text-gray-700">
                        Trip Pace
                      </label>
                      <div className="grid grid-cols-3 gap-2">
                        {paceOptions.map((option) => (
                          <button
                            key={option.value}
                            type="button"
                            className={`rounded-lg border p-3 text-center transition-all ${
                              pace === option.value
                                ? "border-green-500 bg-green-50 text-green-700"
                                : "border-gray-200 hover:border-gray-300"
                            }`}
                            onClick={() =>
                              setPace(
                                option.value as
                                  | "relaxed"
                                  | "moderate"
                                  | "intense",
                              )
                            }
                          >
                            <div className="text-sm font-medium">
                              {option.label}
                            </div>
                            <div className="mt-1 text-xs text-gray-500">
                              {option.description}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Additional Preferences */}
                    <div>
                      <label className="mt-6 mb-2 block text-sm font-medium text-gray-700">
                        Additional Notes
                        <span className="ml-1 text-xs font-normal text-gray-500">
                          (Optional)
                        </span>
                      </label>
                      <textarea
                        value={additionalPreferences}
                        onChange={(e) =>
                          setAdditionalPreferences(e.target.value)
                        }
                        placeholder="E.g., prefer less crowded places, want to visit local markets..."
                        rows={3}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-transparent focus:ring-2 focus:ring-green-500"
                      />
                    </div>
                  </div>
                )}

                {/* Generate button */}
                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  disabled={
                    !destination ||
                    !startDate ||
                    !endDate ||
                    planner.isGenerating
                  }
                >
                  {planner.isGenerating ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-5 w-5" />
                      Generate Itinerary
                    </>
                  )}
                </Button>
              </form>
            </Card>
          </div>

          {/* Itinerary display */}
          <div className="lg:col-span-2">
            {/* Loading state */}
            {planner.isGenerating && (
              <div className="py-16 text-center">
                <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-green-100">
                  <Loader2 className="h-10 w-10 animate-spin text-green-600" />
                </div>
                <h3 className="mb-2 text-xl font-semibold text-gray-900">
                  {planner.statusMessage || "Planning your trip..."}
                </h3>
                <div className="mx-auto h-2 w-64 overflow-hidden rounded-full bg-gray-200">
                  <div
                    className="h-full rounded-full bg-green-600 transition-all duration-500"
                    style={{ width: `${planner.progress}%` }}
                  />
                </div>
                <p className="mt-2 text-sm text-gray-400">
                  {planner.progress}% complete
                </p>
                <p className="mt-4 text-gray-500">This may take a moment...</p>
              </div>
            )}

            {/* Error state */}
            {planner.error && !planner.isGenerating && (
              <div className="py-16 text-center">
                <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-red-100">
                  <span className="text-3xl">❌</span>
                </div>
                <h3 className="mb-2 text-xl font-semibold text-gray-900">
                  Planning Failed
                </h3>
                <p className="mx-auto max-w-md text-gray-500">
                  {planner.error}
                </p>
                <Button
                  className="mt-4"
                  variant="outline"
                  onClick={() => planner.reset()}
                >
                  Try Again
                </Button>
              </div>
            )}

            {/* Empty state */}
            {!planner.isGenerating && !planner.error && !itinerary && (
              <div className="py-16 text-center">
                <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-green-100">
                  <Calendar className="h-10 w-10 text-green-600" />
                </div>
                <h3 className="mb-2 text-xl font-semibold text-gray-900">
                  Ready to plan your trip?
                </h3>
                <p className="mx-auto max-w-md text-gray-500">
                  Fill in your trip details on the left and let our AI create a
                  personalized itinerary just for you.
                </p>
              </div>
            )}

            {/* Generated itinerary */}
            {!planner.isGenerating && itinerary && (
              <div className="space-y-6">
                {/* Summary card */}
                <Card>
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">
                      {itinerary.destination}
                    </h2>
                    <p className="mt-1 text-gray-500">
                      {formatDayDate(itinerary.startDate)} -{" "}
                      {formatDayDate(itinerary.endDate)}
                    </p>
                  </div>

                  {/* Summary stats */}
                  <div className="mt-6 grid grid-cols-2 gap-4 border-t border-gray-100 pt-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {itinerary.dayPlans.length}
                      </div>
                      <div className="text-sm text-gray-500">Days</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {itinerary.summary?.totalActivities}
                      </div>
                      <div className="text-sm text-gray-500">Activities</div>
                    </div>
                  </div>
                </Card>

                {/* Day by day itinerary */}
                <div className="space-y-4">
                  {itinerary.dayPlans.map((day) => (
                    <Card key={day.dayNumber} padding="none">
                      {/* Day header */}
                      <button
                        className="flex w-full items-center justify-between p-5 transition-colors hover:bg-gray-50"
                        onClick={() => toggleDay(day.dayNumber)}
                      >
                        <div className="flex items-center gap-4">
                          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-100 font-bold text-green-600">
                            {day.dayNumber}
                          </div>
                          <div className="text-left">
                            <h3 className="font-semibold text-gray-900">
                              Day {day.dayNumber}
                            </h3>
                            <p className="text-sm text-gray-500">
                              {formatDayDate(day.date)}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-sm text-gray-500">
                            {day.activities.length} activities
                          </span>
                          <ChevronDown
                            className={`h-5 w-5 text-gray-400 transition-transform ${
                              expandedDays.includes(day.dayNumber)
                                ? "rotate-180"
                                : ""
                            }`}
                          />
                        </div>
                      </button>

                      {/* Day activities */}
                      {expandedDays.includes(day.dayNumber) && (
                        <div className="border-t border-gray-100">
                          <div className="space-y-4 p-5">
                            {day.activities.map((activity) => (
                              <div
                                key={activity.id}
                                className="flex gap-4 rounded-xl bg-gray-50 p-4"
                              >
                                {/* Time */}
                                <div className="shrink-0 text-center">
                                  <div className="text-sm font-medium text-gray-900">
                                    {activity.startTime}
                                  </div>
                                  <div className="text-xs text-gray-500">
                                    {activity.endTime}
                                  </div>
                                </div>

                                {/* Content */}
                                <div className="min-w-0 flex-1">
                                  <div className="flex items-start justify-between gap-2">
                                    <div>
                                      <h4 className="font-medium text-gray-900">
                                        {activity.name}
                                      </h4>
                                      <p className="mt-1 text-sm text-gray-500">
                                        {activity.description}
                                      </p>
                                    </div>
                                    <Badge
                                      className={getCategoryColor(
                                        activity.category,
                                      )}
                                      size="sm"
                                    >
                                      {activity.category}
                                    </Badge>
                                  </div>

                                  <div className="mt-3 flex items-center gap-4 text-sm text-gray-500">
                                    <span className="flex items-center gap-1">
                                      <MapPin className="h-4 w-4" />
                                      {activity.location.name}
                                    </span>
                                    {activity.cost?.amount ? (
                                      <span className="flex items-center gap-1">
                                        ¥{activity.cost.amount}
                                      </span>
                                    ) : null}
                                  </div>
                                </div>
                              </div>
                            ))}

                            {/* Day notes */}
                            {day.notes && (
                              <div className="rounded-xl border border-amber-100 bg-amber-50 p-4">
                                <p className="text-sm text-amber-800">
                                  <strong>Note:</strong> {day.notes}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
