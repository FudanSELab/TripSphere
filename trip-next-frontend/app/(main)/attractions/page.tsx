import { AttractionSearchBar } from "@/components/attraction-search-bar";
import { AttractionCardList } from "@/components/attraction-card-list";
import { listAttractionsByCity } from "@/lib/data/attraction";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "景点",
  description: "探索全国精彩景点，发现每一处值得一去的地方",
};

export default async function AttractionPage() {
  const [shanghaiResult, nanjingResult, beijingResult] = await Promise.all([
    listAttractionsByCity("上海市"),
    listAttractionsByCity("南京市"),
    listAttractionsByCity("北京市"),
  ]);

  return (
    <div className="flex flex-col gap-10">
      <AttractionSearchBar />

      <section className="flex flex-col gap-4">
        <h2 className="text-2xl font-bold">景点推荐</h2>

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
            <AttractionCardList
              initialAttractions={shanghaiResult.attractions}
              initialNextPageToken={shanghaiResult.nextPageToken}
              city="上海市"
            />
          </TabsContent>
          <TabsContent value="nanjing">
            <AttractionCardList
              initialAttractions={nanjingResult.attractions}
              initialNextPageToken={nanjingResult.nextPageToken}
              city="南京市"
            />
          </TabsContent>
          <TabsContent value="beijing">
            <AttractionCardList
              initialAttractions={beijingResult.attractions}
              initialNextPageToken={beijingResult.nextPageToken}
              city="北京市"
            />
          </TabsContent>
        </Tabs>
      </section>
    </div>
  );
}
