import { HotelHeroSearch } from "@/components/hotel-hero-search";
import { HotelCardList } from "@/components/hotel-card-list";
import { listHotels } from "@/actions/hotel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "酒店",
  description: "搜索和预订全球优质酒店",
};

export default async function HotelPage() {
  const today = new Date().toISOString().split("T")[0];

  const [shanghaiResult, nanjingResult, beijingResult] = await Promise.all([
    listHotels("上海市"),
    listHotels("南京市"),
    listHotels("北京市"),
  ]);

  return (
    <div className="flex flex-col gap-10">
      <HotelHeroSearch today={today} />

      <section className="flex flex-col gap-4">
        <h2 className="text-2xl font-bold">酒店推荐</h2>

        <Tabs defaultValue="shanghai">
          <TabsList variant="line" className="mb-2 gap-4">
            <TabsTrigger value="shanghai" className="px-2 text-base">
              上海
            </TabsTrigger>
            <TabsTrigger value="nanjing" className="px-2 text-base">
              南京
            </TabsTrigger>
            <TabsTrigger value="beijing" className="px-2 text-base">
              北京
            </TabsTrigger>
          </TabsList>

          <TabsContent value="shanghai">
            <HotelCardList
              initialHotels={shanghaiResult.hotels}
              initialNextPageToken={shanghaiResult.nextPageToken}
              city="上海市"
            />
          </TabsContent>
          <TabsContent value="nanjing">
            <HotelCardList
              initialHotels={nanjingResult.hotels}
              initialNextPageToken={nanjingResult.nextPageToken}
              city="南京市"
            />
          </TabsContent>
          <TabsContent value="beijing">
            <HotelCardList
              initialHotels={beijingResult.hotels}
              initialNextPageToken={beijingResult.nextPageToken}
              city="北京市"
            />
          </TabsContent>
        </Tabs>
      </section>
    </div>
  );
}
