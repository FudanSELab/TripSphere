"use client";

import { CopilotSidebar } from "@copilotkit/react-core/v2";

export default function HomePage() {
  return (
    <div>
      <div className="flex flex-1 flex-col gap-4">
        <h1 className="text-2xl font-bold">欢迎来到 TripSphere</h1>
        <p className="text-muted-foreground">智能旅行平台</p>
      </div>
      <CopilotSidebar
        agentId="default"
        defaultOpen={false}
        width="30rem"
        labels={{
          modalHeaderTitle: "AI旅行助手",
          chatInputPlaceholder: "询问我任何旅游相关的问题",
        }}
        autoFocus={true}
      />
    </div>
  );
}
