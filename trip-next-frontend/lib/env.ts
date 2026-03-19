import "server-only";

function env(key: string, fallback: string): string {
  return process.env[key] ?? fallback;
}

export const config = {
  grpc: {
    attractionService: env("ATTRACTION_SERVICE_ADDR", "localhost:50053"),
    hotelService: env("HOTEL_SERVICE_ADDR", "localhost:50054"),
    inventoryService: env("INVENTORY_SERVICE_ADDR", "localhost:50061"),
    itineraryService: env("ITINERARY_SERVICE_ADDR", "localhost:50052"),
    poiService: env("POI_SERVICE_ADDR", "localhost:50058"),
    productService: env("PRODUCT_SERVICE_ADDR", "localhost:50060"),
    userService: env("USER_SERVICE_ADDR", "localhost:50056"),
  },
  copilot: {
    defaultAgentUrl: env(
      "COPILOT_DEFAULT_AGENT_URL",
      "http://localhost:24210/",
    ),
    orderAssistantUrl: env(
      "COPILOT_ORDER_AGENT_URL",
      "http://localhost:24211/",
    ),
  },
  auth: {
    jwtPublicKey: process.env.JWT_PUBLIC_KEY ?? "",
  },
  isProduction: process.env.NODE_ENV === "production",
} as const;
