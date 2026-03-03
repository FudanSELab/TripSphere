import { ItineraryPlanForm } from "@/components/itinerary-plan-form";

export default function ItineraryPage() {
  const today = new Date().toISOString().split("T")[0];

  return (
    <main className="mx-auto w-full max-w-screen-2xl px-[10rem] py-6">
      <ItineraryPlanForm today={today} />
    </main>
  );
}
