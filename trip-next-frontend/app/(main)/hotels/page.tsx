import { HotelHeroSearch } from "@/components/hotel-hero-search";
import { HotelCardList } from "@/components/hotel-card-list";
import { listHotels } from "@/actions/hotel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default async function HotelPage() {
  const today = new Date().toISOString().split("T")[0];
  const { hotels, nextPageToken } = await listHotels("上海市");

  return (
    <div className="flex flex-col gap-10">
      <HotelHeroSearch today={today} />

      {/* Hotel Recommendations */}
      <section className="flex flex-col gap-4">
        <h2 className="text-2xl font-bold">酒店推荐</h2>

        <Tabs defaultValue="shanghai">
          <TabsList variant="line" className="gap-4">
            <TabsTrigger value="shanghai" className="px-2 text-base">
              上海
            </TabsTrigger>
          </TabsList>

          <TabsContent value="shanghai">
            <HotelCardList
              initialHotels={hotels}
              initialNextPageToken={nextPageToken}
              city="上海"
            />
          </TabsContent>
        </Tabs>
      </section>
    </div>
  );
}
