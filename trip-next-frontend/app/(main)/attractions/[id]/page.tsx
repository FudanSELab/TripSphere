import { Suspense } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AttractionHeaderCard } from "@/components/attraction-detail/attraction-header-card";
import { OpeningHoursCard } from "@/components/attraction-detail/opening-hours-card";
import {
  NearbyAttractions,
  NearbyAttractionsSkeleton,
} from "@/components/attraction-detail/nearby-attractions";
import { getAttractionById } from "@/lib/data/attraction";

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { id } = await params;
  const attraction = await getAttractionById(id);

  if (!attraction) {
    return { title: "景点未找到" };
  }

  return {
    title: attraction.name,
    description:
      attraction.introduction?.slice(0, 160) ||
      `查看${attraction.name}的详情、开放时间和门票信息`,
  };
}

export default async function AttractionDetailPage({ params }: PageProps) {
  const { id } = await params;
  const attraction = await getAttractionById(id);

  if (!attraction) {
    notFound();
  }

  const city = attraction.address?.city ?? "";
  const cityShort = city.replace("市", "");

  return (
    <div className="flex flex-col gap-6">
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link href="/">TripSphere</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link href="/attractions">景点</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          {cityShort && (
            <>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link href="/attractions">{cityShort}景点</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
            </>
          )}
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{attraction.name}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <AttractionHeaderCard attraction={attraction} />

      <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
        <div className="bg-card rounded-xl border">
          <div className="border-b px-6 pt-4">
            <Tabs defaultValue="intro">
              <TabsList variant="line" className="gap-6">
                <TabsTrigger value="intro" className="px-2 text-base">
                  简介
                </TabsTrigger>
                <TabsTrigger value="hours" className="px-2 text-base">
                  开放时间
                </TabsTrigger>
                <TabsTrigger value="transport" className="px-2 text-base">
                  交通
                </TabsTrigger>
                <TabsTrigger value="policy" className="px-2 text-base">
                  政策
                </TabsTrigger>
              </TabsList>

              <TabsContent value="intro" className="flex flex-col gap-4 p-6">
                <h3 className="text-lg font-bold">景点简介</h3>
                {attraction.introduction ? (
                  <p className="text-muted-foreground leading-relaxed whitespace-pre-line">
                    {attraction.introduction}
                  </p>
                ) : (
                  <p className="text-muted-foreground">暂无景点介绍信息</p>
                )}

                {attraction.tags.length > 0 && (
                  <div className="flex flex-col gap-2 pt-2">
                    <h4 className="text-muted-foreground text-sm font-semibold">
                      景点标签
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {attraction.tags.map((tag) => (
                        <Badge key={tag} variant="secondary">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="hours" className="p-6">
                <OpeningHoursCard
                  openingHours={attraction.openingHours}
                  temporarilyClosed={attraction.temporarilyClosed}
                />
              </TabsContent>

              <TabsContent
                value="transport"
                className="flex flex-col gap-4 p-6"
              >
                <h3 className="text-lg font-bold">交通信息</h3>
                {attraction.address ? (
                  <div className="text-muted-foreground flex flex-col gap-2 text-sm">
                    <p>
                      地址:{" "}
                      {[
                        attraction.address.province,
                        attraction.address.city,
                        attraction.address.district,
                        attraction.address.detailed,
                      ]
                        .filter(Boolean)
                        .join("")}
                    </p>
                    {attraction.location && (
                      <p className="text-xs">
                        坐标: {attraction.location.latitude?.toFixed(6)},{" "}
                        {attraction.location.longitude?.toFixed(6)}
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-muted-foreground">暂无交通信息</p>
                )}
              </TabsContent>

              <TabsContent value="policy" className="flex flex-col gap-4 p-6">
                <h3 className="text-lg font-bold">参观政策</h3>
                {attraction.ticketInfo ? (
                  <div className="text-muted-foreground flex flex-col gap-2 text-sm">
                    {attraction.temporarilyClosed && (
                      <Alert variant="destructive">
                        <AlertDescription>
                          该景点暂停开放，请关注官方通知
                        </AlertDescription>
                      </Alert>
                    )}
                    <p>
                      门票政策:
                      请以景点官方公布信息为准，具体价格可能因季节及优惠活动有所浮动
                    </p>
                  </div>
                ) : (
                  <p className="text-muted-foreground">暂无政策信息</p>
                )}
              </TabsContent>
            </Tabs>
          </div>
        </div>

        <aside className="flex flex-col gap-4">
          {attraction.location && (
            <Suspense fallback={<NearbyAttractionsSkeleton />}>
              <NearbyAttractions
                currentId={attraction.id}
                location={attraction.location}
                radiusMeters={5000}
              />
            </Suspense>
          )}
        </aside>
      </div>
    </div>
  );
}
