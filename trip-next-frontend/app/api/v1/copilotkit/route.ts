import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";
import { config } from "@/lib/env";

const serviceAdapter = new ExperimentalEmptyAdapter();

/* eslint-disable @typescript-eslint/no-explicit-any */
const runtime = new CopilotRuntime({
  agents: {
    default: new HttpAgent({ url: config.copilot.defaultAgentUrl }) as any,
    order_assistant: new HttpAgent({
      url: config.copilot.orderAssistantUrl,
    }) as any,
    itinerary_planner: new HttpAgent({
      url: config.copilot.itineraryPlannerUrl,
    }) as any,
  },
});
/* eslint-enable @typescript-eslint/no-explicit-any */

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/v1/copilotkit",
  });

  return handleRequest(req);
};
