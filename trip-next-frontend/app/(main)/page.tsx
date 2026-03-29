import Image from "next/image";
import Link from "next/link";
import { Hotel, Notebook, Sailboat, Sparkles, Ticket } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { HomeAtmosphereStrip } from "@/components/home/home-atmosphere-strip";
import { HomeCopilotQuickstart } from "@/components/home/home-copilot-quickstart";
import { HomeEntryCard } from "@/components/home/home-entry-card";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type HeroAction = {
  href: string;
  label: string;
  icon: LucideIcon;
  variant: "default" | "outline";
};

type HomeShortcut = {
  title: string;
  description: string;
  href: string;
  ctaLabel: string;
  icon: LucideIcon;
};

const HERO_ACTIONS: readonly HeroAction[] = [
  {
    href: "/itinerary",
    label: "AI规划行程",
    icon: Sparkles,
    variant: "default",
  },
  {
    href: "/hotels",
    label: "查酒店",
    icon: Hotel,
    variant: "outline",
  },
  {
    href: "/attractions",
    label: "看景点",
    icon: Ticket,
    variant: "outline",
  },
];

const HOME_SHORTCUTS: readonly HomeShortcut[] = [
  {
    title: "酒店",
    description: "按城市快速筛选优质酒店，并查看推荐与分页列表。",
    href: "/hotels",
    ctaLabel: "开始搜索",
    icon: Hotel,
  },
  {
    title: "景点",
    description: "从景点列表出发，快速挑选适合的目的地与玩法。",
    href: "/attractions",
    ctaLabel: "查看推荐",
    icon: Ticket,
  },
  {
    title: "我的行程",
    description: "保存并回看你的路线；继续调整，让行程更贴合你的节奏。",
    href: "/itinerary",
    ctaLabel: "打开规划",
    icon: Sparkles,
  },
  {
    title: "笔记攻略",
    description: "整理你的旅行记录与攻略，未来再次出发更从容。",
    href: "/notes",
    ctaLabel: "查看笔记",
    icon: Notebook,
  },
];

export default function HomePage() {
  return (
    <div className="flex flex-col gap-10">
      <div className="grid gap-4 lg:grid-cols-2">
        <Card
          className="relative overflow-hidden bg-[length:46%] bg-right-top bg-no-repeat"
          style={{
            backgroundImage:
              "url('/images/round-icons-hEWd0sz0gc4-unsplash.svg')",
          }}
        >
          <div className="from-primary/20 to-secondary/20 pointer-events-none absolute inset-0 -z-10 bg-gradient-to-br via-transparent" />

          <CardHeader className="flex flex-col gap-3">
            <CardTitle className="text-3xl leading-tight tracking-tight sm:text-4xl">
              TripSphere
            </CardTitle>
          </CardHeader>

          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-wrap gap-2">
              {HERO_ACTIONS.map((action) => (
                <Button key={action.href} asChild variant={action.variant}>
                  <Link href={action.href} className="gap-1.5">
                    <action.icon data-icon="inline-start" aria-hidden="true" />
                    {action.label}
                  </Link>
                </Button>
              ))}
            </div>

            <div className="text-muted-foreground flex flex-wrap items-center gap-2 text-sm">
              <Sailboat className="size-4" aria-hidden="true" />
              支持从“需求”到“每日安排”的完整链路
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden">
          <Image
            src="/images/ian-dooley-hpTH5b6mo2s-unsplash.jpg"
            alt=""
            fill
            className="object-cover object-[30%_bottom]"
            sizes="(max-width: 1024px) 100vw, 50vw"
          />

          <CardHeader className="relative z-10 flex flex-col gap-2">
            <CardTitle className="text-xl text-white">AI旅行助手</CardTitle>
            <CardDescription className="text-white/80">
              让右侧AI旅行助手解答你的旅途问题
            </CardDescription>
          </CardHeader>

          <CardContent className="relative z-10">
            <HomeCopilotQuickstart />
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-col gap-10">
        <section
          className="flex flex-col gap-4"
          aria-labelledby="home-shortcuts-heading"
        >
          <div className="flex items-end justify-between gap-4">
            <h2
              id="home-shortcuts-heading"
              className="text-2xl font-bold text-balance"
            >
              常用入口
            </h2>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {HOME_SHORTCUTS.map((shortcut) => (
              <HomeEntryCard
                key={shortcut.href}
                title={shortcut.title}
                description={shortcut.description}
                href={shortcut.href}
                ctaLabel={shortcut.ctaLabel}
                icon={shortcut.icon}
              />
            ))}
          </div>
        </section>

        <HomeAtmosphereStrip />
      </div>
    </div>
  );
}
