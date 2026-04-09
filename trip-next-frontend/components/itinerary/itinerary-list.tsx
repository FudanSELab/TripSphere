import { revalidatePath } from "next/cache";
import {
  deleteItinerary,
  type SavedItinerarySummary,
} from "@/actions/itinerary";
import { ItineraryListClient } from "@/components/itinerary/itinerary-list-client";
import { Alert, AlertDescription } from "@/components/ui/alert";

async function deleteItineraryAction(formData: FormData) {
  "use server";
  const id = formData.get("id") as string;
  await deleteItinerary(id);
  revalidatePath("/itinerary");
}

interface Props {
  dataPromise: Promise<SavedItinerarySummary[]>;
}

export async function ItineraryList({ dataPromise }: Props) {
  let items: SavedItinerarySummary[] = [];
  let error: string | null = null;

  try {
    items = await dataPromise;
  } catch (err) {
    error = err instanceof Error ? err.message : "加载失败";
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (items.length === 0) {
    return (
      <div className="border-border flex flex-col items-center rounded-xl border border-dashed py-10 text-center">
        <span className="text-4xl">🗺️</span>
        <p className="text-muted-foreground mt-3 text-sm font-medium">
          还没有保存的行程
        </p>
        <p className="text-muted-foreground/70 mt-1 text-xs">
          用AI规划你的第一次旅行吧！
        </p>
      </div>
    );
  }

  return <ItineraryListClient items={items} onDelete={deleteItineraryAction} />;
}
