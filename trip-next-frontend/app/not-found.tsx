import Link from "next/link";
import { SearchX } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-6">
      <div className="bg-muted flex size-16 items-center justify-center rounded-full">
        <SearchX className="text-muted-foreground size-8" />
      </div>
      <div className="flex flex-col items-center gap-2 text-center">
        <h2 className="text-foreground text-xl font-semibold">页面未找到</h2>
        <p className="text-muted-foreground max-w-md text-sm">
          抱歉，您访问的页面不存在或已被移除。
        </p>
      </div>
      <Button asChild>
        <Link href="/">返回首页</Link>
      </Button>
    </div>
  );
}
