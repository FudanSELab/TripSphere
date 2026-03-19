"use client";

import { CopilotKit } from "@copilotkit/react-core";

const RUNTIME_URL = "/api/v1/copilotkit";

export function CopilotProvider({ children }: { children: React.ReactNode }) {
  return <CopilotKit runtimeUrl={RUNTIME_URL}>{children}</CopilotKit>;
}
