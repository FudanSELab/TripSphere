import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

const chatUrl = process.env.HTTP_CHAT_URL || "http://localhost:24210";
const plannerUrl =
  process.env.HTTP_ITINERARY_PLANNER_URL || "http://localhost:24215";

const serviceAdapter = new ExperimentalEmptyAdapter();

const runtime = new CopilotRuntime({
  agents: {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    default: new HttpAgent({ url: "http://localhost:24210/" }) as any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    order_assistant: new HttpAgent({ url: "http://localhost:24211/" }) as any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    itinerary_planner: new HttpAgent({ url: `${plannerUrl}/copilotkit` }) as any,
  },
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/v1/copilotkit",
  });

  return handleRequest(req);
};
