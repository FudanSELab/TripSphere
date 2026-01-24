"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";
import { useItineraryPlanner } from "@/hooks/use-itinerary-planner";
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
  const [startDate, setStartDate] = useState("2026-12-29");
  const [endDate, setEndDate] = useState("2026-12-31");

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

  // Get activity category style
  const getCategoryStyle = (category: string) => {
    const styles: Record<string, string> = {
      sightseeing: "bg-primary/10 text-primary",
      dining: "bg-secondary/10 text-secondary-foreground",
      transportation: "bg-muted text-muted-foreground",
      shopping: "bg-accent/10 text-accent-foreground",
      entertainment: "bg-primary/20 text-primary",
    };
    return styles[category] || "bg-muted text-muted-foreground";
  };

  return (
    <div className="bg-muted min-h-screen">
      {/* Hero section */}
      <div className="bg-primary text-primary-foreground pt-16 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <span className="bg-primary-foreground/20 mb-4 inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium">
              <Sparkles className="h-4 w-4" />
              AI-Powered Planning
            </span>
            <h1 className="mb-4 text-4xl font-bold sm:text-5xl">
              Plan Your Perfect Trip
            </h1>
            <p className="text-primary-foreground/80 mx-auto max-w-2xl text-xl">
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
              <h2 className="text-foreground mb-6 text-xl font-semibold">
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
                  <label className="text-foreground mb-2 block text-sm font-medium">
                    Destination
                  </label>
                  <div className="relative">
                    <MapPin className="text-muted-foreground absolute top-1/2 left-3 h-5 w-5 -translate-y-1/2" />
                    <input
                      value={destination}
                      onChange={(e) => setDestination(e.target.value)}
                      placeholder="e.g., Shanghai, China"
                      className="border-input focus:ring-primary w-full rounded-lg border py-2 pr-4 pl-10 focus:border-transparent focus:ring-2"
                    />
                  </div>
                </div>

                {/* Dates */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-foreground mb-2 block text-sm font-medium">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="border-input focus:ring-primary w-full rounded-lg border px-3 py-2 focus:border-transparent focus:ring-2"
                    />
                  </div>
                  <div>
                    <label className="text-foreground mb-2 block text-sm font-medium">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="border-input focus:ring-primary w-full rounded-lg border px-3 py-2 focus:border-transparent focus:ring-2"
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
                      <Settings className="text-muted-foreground h-4 w-4" />
                      <span className="text-foreground text-sm font-medium">
                        Preferences
                      </span>
                    </div>
                    {showPreferences ? (
                      <ChevronDown className="text-muted-foreground h-4 w-4" />
                    ) : (
                      <ChevronUp className="text-muted-foreground h-4 w-4" />
                    )}
                  </button>
                </div>

                {/* Preferences Content */}
                {showPreferences && (
                  <div className="space-y-4">
                    {/* Travel Interests */}
                    <div>
                      <label className="text-foreground mb-2 block text-sm font-medium">
                        Travel Interests
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {travelInterests.map((interest) => (
                          <button
                            key={interest.id}
                            type="button"
                            className={`flex items-center gap-1.5 rounded-full px-3 py-2 text-sm font-medium transition-all ${
                              interests.includes(interest.id)
                                ? "bg-primary text-primary-foreground shadow-sm"
                                : "bg-muted text-muted-foreground hover:bg-muted/80"
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
                      <label className="text-foreground mt-6 mb-2 block text-sm font-medium">
                        Trip Pace
                      </label>
                      <div className="grid grid-cols-3 gap-2">
                        {paceOptions.map((option) => (
                          <button
                            key={option.value}
                            type="button"
                            className={`rounded-lg border p-3 text-center transition-all ${
                              pace === option.value
                                ? "border-primary bg-primary/10 text-primary"
                                : "border-border hover:border-border/80"
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
                            <div className="text-muted-foreground mt-1 text-xs">
                              {option.description}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Additional Preferences */}
                    <div>
                      <label className="text-foreground mt-6 mb-2 block text-sm font-medium">
                        Additional Notes
                        <span className="text-muted-foreground ml-1 text-xs font-normal">
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
                        className="border-input focus:ring-primary w-full rounded-lg border px-3 py-2 text-sm focus:border-transparent focus:ring-2"
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
                <div className="bg-primary/10 mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full">
                  <Loader2 className="text-primary h-10 w-10 animate-spin" />
                </div>
                <h3 className="text-foreground mb-2 text-xl font-semibold">
                  {planner.statusMessage || "Planning your trip..."}
                </h3>
                <div className="bg-muted mx-auto h-2 w-64 overflow-hidden rounded-full">
                  <div
                    className="bg-primary h-full rounded-full transition-all duration-500"
                    style={{ width: `${planner.progress}%` }}
                  />
                </div>
                <p className="text-muted-foreground mt-2 text-sm">
                  {planner.progress}% complete
                </p>
                <p className="text-muted-foreground mt-4">
                  This may take a moment...
                </p>
              </div>
            )}

            {/* Error state */}
            {planner.error && !planner.isGenerating && (
              <div className="py-16 text-center">
                <div className="bg-destructive/10 mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full">
                  <span className="text-3xl">❌</span>
                </div>
                <h3 className="text-foreground mb-2 text-xl font-semibold">
                  Planning Failed
                </h3>
                <p className="text-muted-foreground mx-auto max-w-md">
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
                <div className="bg-primary/10 mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full">
                  <Calendar className="text-primary h-10 w-10" />
                </div>
                <h3 className="text-foreground mb-2 text-xl font-semibold">
                  Ready to plan your trip?
                </h3>
                <p className="text-muted-foreground mx-auto max-w-md">
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
                    <h2 className="text-foreground text-2xl font-bold">
                      {itinerary.destination}
                    </h2>
                    <p className="text-muted-foreground mt-1">
                      {formatDayDate(itinerary.startDate)} -{" "}
                      {formatDayDate(itinerary.endDate)}
                    </p>
                  </div>

                  {/* Summary stats */}
                  <div className="border-border mt-6 grid grid-cols-2 gap-4 border-t pt-6">
                    <div className="text-center">
                      <div className="text-foreground text-2xl font-bold">
                        {itinerary.dayPlans.length}
                      </div>
                      <div className="text-muted-foreground text-sm">Days</div>
                    </div>
                    <div className="text-center">
                      <div className="text-foreground text-2xl font-bold">
                        {itinerary.summary?.totalActivities}
                      </div>
                      <div className="text-muted-foreground text-sm">
                        Activities
                      </div>
                    </div>
                  </div>
                </Card>

                {/* Day by day itinerary */}
                <div className="space-y-4">
                  {itinerary.dayPlans.map((day) => (
                    <Card key={day.dayNumber}>
                      {/* Day header */}
                      <button
                        className="hover:bg-muted/50 flex w-full items-center justify-between p-5 transition-colors"
                        onClick={() => toggleDay(day.dayNumber)}
                      >
                        <div className="flex items-center gap-4">
                          <div className="bg-primary/10 text-primary flex h-12 w-12 items-center justify-center rounded-xl font-bold">
                            {day.dayNumber}
                          </div>
                          <div className="text-left">
                            <h3 className="text-foreground font-semibold">
                              Day {day.dayNumber}
                            </h3>
                            <p className="text-muted-foreground text-sm">
                              {formatDayDate(day.date)}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-muted-foreground text-sm">
                            {day.activities.length} activities
                          </span>
                          <ChevronDown
                            className={`text-muted-foreground h-5 w-5 transition-transform ${
                              expandedDays.includes(day.dayNumber)
                                ? "rotate-180"
                                : ""
                            }`}
                          />
                        </div>
                      </button>

                      {/* Day activities */}
                      {expandedDays.includes(day.dayNumber) && (
                        <div className="border-border border-t">
                          <div className="space-y-4 p-5">
                            {day.activities.map((activity) => (
                              <div
                                key={activity.id}
                                className="bg-muted/50 flex gap-4 rounded-xl p-4"
                              >
                                {/* Time */}
                                <div className="shrink-0 text-center">
                                  <div className="text-foreground text-sm font-medium">
                                    {activity.startTime}
                                  </div>
                                  <div className="text-muted-foreground text-xs">
                                    {activity.endTime}
                                  </div>
                                </div>

                                {/* Content */}
                                <div className="min-w-0 flex-1">
                                  <div className="flex items-start justify-between gap-2">
                                    <div>
                                      <h4 className="text-foreground font-medium">
                                        {activity.name}
                                      </h4>
                                      <p className="text-muted-foreground mt-1 text-sm">
                                        {activity.description}
                                      </p>
                                    </div>
                                    <Badge
                                      className={getCategoryStyle(
                                        activity.category,
                                      )}
                                    >
                                      {activity.category}
                                    </Badge>
                                  </div>

                                  <div className="text-muted-foreground mt-3 flex items-center gap-4 text-sm">
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
                              <div className="border-primary/20 bg-primary/5 rounded-xl border p-4">
                                <p className="text-primary text-sm">
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
