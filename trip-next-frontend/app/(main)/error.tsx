"use client";

import { useEffect } from "react";
import { AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function MainError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[MainError]", error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center gap-6 py-24">
      <div className="bg-destructive/10 flex size-16 items-center justify-center rounded-full">
        <AlertCircle className="text-destructive size-8" />
      </div>
      <div className="flex flex-col items-center gap-2 text-center">
        <h2 className="text-foreground text-xl font-semibold">页面加载出错</h2>
        <p className="text-muted-foreground max-w-md text-sm">
          很抱歉，加载页面时遇到了问题。这可能是暂时的网络问题，请稍后再试。
        </p>
        {error.digest && (
          <p className="text-muted-foreground/70 mt-1 font-mono text-xs">
            错误代码: {error.digest}
          </p>
        )}
      </div>
      <Button onClick={reset} variant="outline" className="gap-2">
        <RotateCcw className="size-4" />
        重试
      </Button>
    </div>
  );
}
