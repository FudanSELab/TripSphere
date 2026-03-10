"use client";

import dynamic from "next/dynamic";
import { CopilotKit } from "@copilotkit/react-core";

// Hydration fix: CopilotSidebar uses many Radix UI components that generate
// inconsistent IDs (such as radix-_R_xxx) during SSR and on the client.
// By using ssr: false, we skip server-side rendering and mount only on the client,
// eliminating hydration mismatch issues.
const CopilotSidebarWidget = dynamic(
  () => import("@copilotkit/react-core/v2").then((mod) => mod.CopilotSidebar),
  {
    ssr: false,
    loading: () => null,
  },
);

interface CopilotProviderProps {
  children: React.ReactNode;
}

export function CopilotProvider({ children }: CopilotProviderProps) {
  return (
    <CopilotKit runtimeUrl="/api/v1/copilotkit">
      {children}
      <CopilotSidebarWidget
        agentId="default"
        defaultOpen={false}
        width="30rem"
        labels={{
          modalHeaderTitle: "AI旅行助手",
          chatInputPlaceholder: "询问我任何旅游相关的问题",
        }}
        autoFocus={true}
      />
    </CopilotKit>
  );
}
