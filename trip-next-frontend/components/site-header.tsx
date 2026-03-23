import Link from "next/link";
import { Search, Bell, ShoppingBag, Sailboat } from "lucide-react";
import { getSession } from "@/lib/session";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { UserNavigation } from "@/components/user-navigation";

export async function SiteHeader({ ...props }: React.ComponentProps<"header">) {
  const session = await getSession();
  return (
    <header
      className="bg-background/80 sticky top-0 z-50 flex h-16 shrink-0 items-center border-b backdrop-blur-sm"
      {...props}
    >
      <div className="mx-auto flex w-full max-w-screen-2xl items-center gap-4 px-4 sm:px-8 lg:px-16">
        <Link
          href="/"
          className="text-primary flex shrink-0 items-center gap-2 text-xl font-semibold tracking-tight"
        >
          <Sailboat className="size-6" />
          <span className="hidden sm:inline">TripSphere</span>
        </Link>

        <div className="relative mx-auto w-full max-w-md">
          <Search className="text-muted-foreground absolute top-1/2 left-3 size-4 -translate-y-1/2" />
          <label htmlFor="site-search" className="sr-only">
            全站搜索
          </label>
          <Input
            id="site-search"
            type="search"
            placeholder="搜索任何旅游相关…"
            className="h-9 pr-4 pl-9"
          />
        </div>

        <div className="flex shrink-0 items-center gap-3">
          {session ? (
            <UserNavigation user={session} />
          ) : (
            <div className="flex h-5 items-center gap-1.5">
              <Button variant="ghost" size="sm" asChild>
                <Link href="/signin">登录</Link>
              </Button>
              <Separator orientation="vertical" />
              <Button variant="ghost" size="sm" asChild>
                <Link href="/signup">注册</Link>
              </Button>
            </div>
          )}

          <Button variant="ghost" size="sm" asChild>
            <Link href="/orders" className="gap-1.5">
              <ShoppingBag className="size-4" />
              <span className="hidden md:inline">我的订单</span>
            </Link>
          </Button>

          <Button variant="ghost" size="icon-sm" className="relative" asChild>
            <Link href="/notification">
              <Bell className="size-4" aria-hidden="true" />
              <Badge
                variant="destructive"
                className="absolute -top-1 -right-1 size-4 justify-center p-0 text-[10px]"
              >
                3
              </Badge>
              <span className="sr-only">消息通知</span>
            </Link>
          </Button>
        </div>
      </div>
    </header>
  );
}
