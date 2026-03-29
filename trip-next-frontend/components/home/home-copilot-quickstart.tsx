"use client";

import * as React from "react";

import { useAgent } from "@copilotkit/react-core/v2";
import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

const HOME_QUICK_PROMPTS = [
  {
    label: "热门城市天气",
    prompt: "请问今天上海、南京、杭州的天气情况如何？",
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

  const isDisabled = pending || agent.isRunning;

  const runPrompt = React.useCallback(
    async (prompt: string) => {
      if (isDisabled) return;

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
    [agent, isDisabled],
  );

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        {HOME_QUICK_PROMPTS.map((item) => {
          const isActive = activePrompt === item.prompt;
          return (
            <Button
              key={item.label}
              variant={isActive ? "default" : "secondary"}
              size="sm"
              disabled={isDisabled}
              onClick={() => runPrompt(item.prompt)}
              className="gap-1.5 rounded-full"
            >
              {item.label}
              {isActive && (
                <Sparkles data-icon="inline-end" aria-hidden="true" />
              )}
            </Button>
          );
        })}
      </div>
    </div>
  );
}
