import Link from "next/link";
import {
  Hotel,
  Sailboat,
  Notebook,
  Sparkles,
  Ticket,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { HomeAtmosphereStrip } from "../../components/home/home-atmosphere-strip";
import { HomeCopilotQuickstart } from "../../components/home/home-copilot-quickstart";

export default function HomePage() {
  return (
    <div className="flex flex-col gap-10">
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="relative overflow-hidden">
          <div className="pointer-events-none absolute inset-0 -z-10 bg-gradient-to-br from-primary/20 via-transparent to-secondary/20" />

          <CardHeader className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="gap-1">
                <Sparkles className="size-3.5" aria-hidden="true" />
                AI Native
              </Badge>
              <Badge variant="secondary" className="gap-1">
                <Sparkles className="size-3.5" aria-hidden="true" />
                一键规划
              </Badge>
            </div>

            <CardTitle className="text-3xl leading-tight tracking-tight sm:text-4xl">
              TripSphere
            </CardTitle>
          </CardHeader>

          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-wrap gap-2">
              <Button asChild variant="default">
                <Link href="/itinerary" className="gap-1.5">
                  <Sparkles className="size-4" aria-hidden="true" />
                  直接规划行程
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/hotels" className="gap-1.5">
                  <Hotel className="size-4" aria-hidden="true" />
                  查酒店
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/attractions" className="gap-1.5">
                  <Ticket className="size-4" aria-hidden="true" />
                  看景点
                </Link>
              </Button>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <Sailboat className="size-4" aria-hidden="true" />
              支持从“需求”到“每天安排”的完整链路。
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="space-y-2">
            <CardTitle className="text-xl">AI 旅行助手</CardTitle>
            <CardDescription>
              在右侧 AI 旅行助手中输入你的需求，开启你的梦幻旅程。
            </CardDescription>
          </CardHeader>

          <CardContent>
            <HomeCopilotQuickstart />
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-col gap-6">
        <HomeAtmosphereStrip />

        <section className="flex flex-col gap-4">
          <div className="flex items-end justify-between gap-4">
            <h2 className="text-2xl font-bold">常用入口</h2>
            <Badge variant="outline">简洁导航</Badge>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Card>
              <CardContent className="flex flex-col gap-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <Hotel className="text-primary size-5" aria-hidden="true" />
                    <h3 className="text-lg font-semibold">酒店</h3>
                  </div>
                  <Badge variant="secondary">探索</Badge>
                </div>
                <p className="text-muted-foreground">
                  按城市快速筛选优质酒店，并查看推荐与分页列表。
                </p>
                <Button asChild variant="outline" className="mt-1 w-fit">
                  <Link href="/hotels">开始搜索</Link>
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="flex flex-col gap-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <Ticket className="text-primary size-5" aria-hidden="true" />
                    <h3 className="text-lg font-semibold">景点</h3>
                  </div>
                  <Badge variant="secondary">发现</Badge>
                </div>
                <p className="text-muted-foreground">
                  从景点列表出发，快速挑选适合的目的地与玩法。
                </p>
                <Button asChild variant="outline" className="mt-1 w-fit">
                  <Link href="/attractions">查看推荐</Link>
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="flex flex-col gap-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="text-primary size-5" aria-hidden="true" />
                    <h3 className="text-lg font-semibold">我的行程</h3>
                  </div>
                  <Badge variant="secondary">AI 结果</Badge>
                </div>
                <p className="text-muted-foreground">
                  保存并回看你的路线；继续调整，让行程更贴合你的节奏。
                </p>
                <Button asChild variant="outline" className="mt-1 w-fit">
                  <Link href="/itinerary">打开规划</Link>
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="flex flex-col gap-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <Notebook className="text-primary size-5" aria-hidden="true" />
                    <h3 className="text-lg font-semibold">笔记攻略</h3>
                  </div>
                  <Badge variant="secondary">灵感</Badge>
                </div>
                <p className="text-muted-foreground">
                  整理你的旅行记录与攻略，未来再次出发更从容。
                </p>
                <Button asChild variant="outline" className="mt-1 w-fit">
                  <Link href="/notes">查看笔记</Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </div>
  );
}
