"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { DayPlan, Itinerary } from "@/lib/types";
import {
  Calendar,
  ChevronDown,
  Edit3,
  GripVertical,
  Loader2,
  MapPin,
  Plus,
  Save,
  Sparkles,
} from "lucide-react";
import { useState } from "react";

const availableInterests = [
  "Culture",
  "Food",
  "Nature",
  "Adventure",
  "Shopping",
  "History",
  "Art",
  "Nightlife",
  "Family",
  "Photography",
];

const budgetOptions = [
  { value: "budget", label: "Budget", description: "Economical options" },
  { value: "moderate", label: "Moderate", description: "Balanced comfort" },
  { value: "luxury", label: "Luxury", description: "Premium experience" },
];

export default function ItineraryPage() {
  // Form state
  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [interests, setInterests] = useState<string[]>([]);
  const [budgetLevel, setBudgetLevel] = useState<
    "budget" | "moderate" | "luxury"
  >("moderate");
  const [numTravelers, setNumTravelers] = useState(2);

  // Generated itinerary state
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [generationStatus, setGenerationStatus] = useState("");
  const [expandedDays, setExpandedDays] = useState<number[]>([1]);

  // Toggle interest selection
  const toggleInterest = (interest: string) => {
    setInterests((prev) =>
      prev.includes(interest)
        ? prev.filter((i) => i !== interest)
        : [...prev, interest],
    );
  };

  // Generate itinerary
  const generateItinerary = async () => {
    if (!destination || !startDate || !endDate) {
      return;
    }

    setIsGenerating(true);
    setGenerationProgress(0);
    setGenerationStatus("Analyzing your preferences...");

    // Simulate AI generation with progress
    const steps = [
      { progress: 20, status: "Researching destination..." },
      { progress: 40, status: "Finding best attractions..." },
      { progress: 60, status: "Optimizing route..." },
      { progress: 80, status: "Adding recommendations..." },
      { progress: 100, status: "Finalizing itinerary..." },
    ];

    for (const step of steps) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      setGenerationProgress(step.progress);
      setGenerationStatus(step.status);
    }

    // Mock generated itinerary
    const start = new Date(startDate);
    const end = new Date(endDate);
    const numDays =
      Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1;

    const mockDayPlans: DayPlan[] = Array.from({ length: numDays }, (_, i) => {
      const date = new Date(start);
      date.setDate(date.getDate() + i);

      return {
        dayNumber: i + 1,
        date: date.toISOString().split("T")[0],
        activities: [
          {
            id: `${i}-1`,
            name:
              i === 0
                ? "Arrival & Check-in"
                : `Morning at ${["West Lake", "The Bund", "Yu Garden", "Temple"][i % 4]}`,
            description: "Start your day with a visit to this iconic location.",
            startTime: "09:00",
            endTime: "12:00",
            location: {
              name: destination,
              latitude: 31.23,
              longitude: 121.47,
              address: destination,
            },
            category: "sightseeing",
            cost: { amount: 0, currency: "CNY" },
          },
          {
            id: `${i}-2`,
            name: `Lunch at Local Restaurant`,
            description:
              "Enjoy authentic local cuisine at a recommended restaurant.",
            startTime: "12:30",
            endTime: "14:00",
            location: {
              name: "Local Restaurant",
              latitude: 31.23,
              longitude: 121.47,
              address: destination,
            },
            category: "dining",
            cost: { amount: 150, currency: "CNY" },
          },
          {
            id: `${i}-3`,
            name:
              i === numDays - 1
                ? "Departure"
                : `Afternoon at ${["Shopping District", "Museum", "Park", "Landmark"][i % 4]}`,
            description: "Continue exploring the city and its attractions.",
            startTime: "15:00",
            endTime: "18:00",
            location: {
              name: destination,
              latitude: 31.23,
              longitude: 121.47,
              address: destination,
            },
            category: i === numDays - 1 ? "transportation" : "sightseeing",
            cost: { amount: 80, currency: "CNY" },
          },
        ],
        notes:
          i === 0
            ? "Remember to exchange currency and get a local SIM card."
            : "",
      };
    });

    setItinerary({
      id: "itinerary-" + Date.now(),
      destination: destination,
      startDate: startDate,
      endDate: endDate,
      dayPlans: mockDayPlans,
      summary: {
        totalEstimatedCost: numDays * 230,
        currency: "CNY",
        totalActivities: numDays * 3,
        highlights: [
          "Local cuisine experience",
          "Cultural immersion",
          "Scenic landmarks",
        ],
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    });

    setExpandedDays([1]);
    setIsGenerating(false);
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

                {/* Travelers */}
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Number of Travelers
                  </label>
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      className="flex h-10 w-10 items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-50"
                      disabled={numTravelers <= 1}
                      onClick={() =>
                        setNumTravelers(Math.max(1, numTravelers - 1))
                      }
                    >
                      -
                    </button>
                    <span className="w-8 text-center text-lg font-medium text-gray-900">
                      {numTravelers}
                    </span>
                    <button
                      type="button"
                      className="flex h-10 w-10 items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50"
                      onClick={() => setNumTravelers(numTravelers + 1)}
                    >
                      +
                    </button>
                  </div>
                </div>

                {/* Budget level */}
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Budget Level
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {budgetOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        className={`rounded-lg border p-3 text-center transition-all ${
                          budgetLevel === option.value
                            ? "border-green-500 bg-green-50 text-green-700"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                        onClick={() =>
                          setBudgetLevel(
                            option.value as "budget" | "moderate" | "luxury",
                          )
                        }
                      >
                        <div className="text-sm font-medium">
                          {option.label}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Interests */}
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Interests
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {availableInterests.map((interest) => (
                      <button
                        key={interest}
                        type="button"
                        className={`rounded-full px-3 py-1.5 text-sm font-medium transition-all ${
                          interests.includes(interest)
                            ? "bg-green-600 text-white"
                            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                        }`}
                        onClick={() => toggleInterest(interest)}
                      >
                        {interest}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Generate button */}
                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  disabled={
                    !destination || !startDate || !endDate || isGenerating
                  }
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="h-5 w-5" />
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
            {isGenerating && (
              <div className="py-16 text-center">
                <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-green-100">
                  <Loader2 className="h-10 w-10 text-green-600" />
                </div>
                <h3 className="mb-2 text-xl font-semibold text-gray-900">
                  {generationStatus}
                </h3>
                <div className="mx-auto h-2 w-64 overflow-hidden rounded-full bg-gray-200">
                  <div
                    className="h-full rounded-full bg-green-600 transition-all duration-500"
                    style={{ width: `${generationProgress}%` }}
                  />
                </div>
                <p className="mt-4 text-gray-500">This may take a moment...</p>
              </div>
            )}

            {/* Empty state */}
            {!isGenerating && !itinerary && (
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
            {!isGenerating && itinerary && (
              <div className="space-y-6">
                {/* Summary card */}
                <Card>
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">
                        {itinerary.destination}
                      </h2>
                      <p className="mt-1 text-gray-500">
                        {formatDayDate(itinerary.startDate)} -{" "}
                        {formatDayDate(itinerary.endDate)}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        <Edit3 className="h-4 w-4" />
                        Edit
                      </Button>
                      <Button variant="default" size="sm">
                        <Save className="h-4 w-4" />
                        Save
                      </Button>
                    </div>
                  </div>

                  {/* Summary stats */}
                  <div className="mt-6 grid grid-cols-3 gap-4 border-t border-gray-100 pt-6">
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
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        ¥{itinerary.summary?.totalEstimatedCost}
                      </div>
                      <div className="text-sm text-gray-500">Est. Cost</div>
                    </div>
                  </div>

                  {/* Highlights */}
                  {itinerary.summary?.highlights &&
                    itinerary.summary.highlights.length > 0 && (
                      <div className="mt-6">
                        <h4 className="mb-2 text-sm font-medium text-gray-700">
                          Highlights
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {itinerary.summary.highlights.map((highlight) => (
                            <Badge
                              key={highlight}
                              className="bg-green-100 text-green-700"
                            >
                              {highlight}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
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
                                className="group flex gap-4 rounded-xl bg-gray-50 p-4 transition-colors hover:bg-gray-100"
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

                                {/* Actions */}
                                <div className="shrink-0 opacity-0 transition-opacity group-hover:opacity-100">
                                  <button className="rounded-lg p-2 text-gray-400 hover:bg-white hover:text-gray-600">
                                    <GripVertical className="h-4 w-4" />
                                  </button>
                                </div>
                              </div>
                            ))}

                            {/* Add activity button */}
                            <button className="flex w-full items-center justify-center gap-2 rounded-xl border-2 border-dashed border-gray-200 py-3 text-gray-400 transition-colors hover:border-green-500 hover:text-green-600">
                              <Plus className="h-4 w-4" />
                              Add Activity
                            </button>

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
