"use client";

import * as React from "react";

import { useAgent } from "@copilotkit/react-core/v2";
import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const QUICK_PROMPTS = [
  {
    label: "三天城市轻松游",
    prompt:
      "我想去一座城市旅行，3天，预算中等，节奏轻松，偏好美食和散步。请先给一个初步行程（含早/中/晚建议与交通方式），再列出你需要我确认的 5 个问题。",
  },
  {
    label: "周末亲子路线",
    prompt:
      "帮我规划一份周末亲子旅行（2天）。要求：有适合小朋友的活动、交通尽量省力、每天安排节奏不要太满。请给出早/中/晚安排和备选方案。",
  },
  {
    label: "目的地不确定",
    prompt:
      "我还没想好去哪。请给我 3 个不同风格的旅行方案（轻松/深度/美食），并告诉我每个方案适合的时间与人群。最后帮我做一个简单推荐。",
  },
] as const;

function newMessageId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `home-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function HomeCopilotQuickstart() {
  const { agent } = useAgent({ agentId: "default" });
  const [pending, setPending] = React.useState(false);
  const [activePrompt, setActivePrompt] = React.useState<string | null>(null);

  const disabled = pending || agent.isRunning;

  const runPrompt = React.useCallback(
    async (prompt: string) => {
      if (disabled) return;

      setActivePrompt(prompt);
      setPending(true);

      try {
        agent.addMessage({
          id: newMessageId(),
          role: "user",
          content: prompt,
        });
        await agent.runAgent();
      } finally {
        setPending(false);
      }
    },
    [agent, disabled],
  );

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        {QUICK_PROMPTS.map((item) => {
          const isActive = activePrompt === item.prompt;
          return (
            <Button
              key={item.label}
              variant={isActive ? "default" : "secondary"}
              size="sm"
              disabled={disabled}
              onClick={() => runPrompt(item.prompt)}
              className={cn("rounded-full gap-1.5")}
            >
              {item.label}
              {isActive && (
                <Sparkles className="size-3.5" aria-hidden="true" />
              )}
            </Button>
          );
        })}
      </div>

      <p className="text-xs leading-relaxed text-muted-foreground">
        点击后即刻开始规划！继续追问或在聊天框里修改需求。
      </p>
    </div>
  );
}

