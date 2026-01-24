import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
      {
        protocol: "https",
        hostname: "**.amazonaws.com",
      },
      {
        protocol: "http",
        hostname: "47.120.37.103",
        port: "9000",
      },
    ],
  },
  async rewrites() {
    // The environment variables are available at build time
    const httpChatUrl = process.env.HTTP_CHAT_URL || "http://localhost:24210";
    const httpItineraryPlannerUrl =
      process.env.HTTP_ITINERARY_PLANNER_URL || "http://localhost:24215";

    return [
      // Chat service - non-streaming endpoints
      {
        source: "/api/v1/conversations",
        destination: `${httpChatUrl}/api/v1/conversations`,
      },
      {
        source: "/api/v1/conversations/:path*",
        destination: `${httpChatUrl}/api/v1/conversations/:path*`,
      },
      {
        source: "/api/v1/messages",
        destination: `${httpChatUrl}/api/v1/messages`,
      },
      // Itinerary planner - non-streaming endpoint
      {
        source: "/api/v1/itineraries/plannings",
        destination: `${httpItineraryPlannerUrl}/api/v1/itineraries/plannings`,
      },
      // Note: SSE streaming endpoints are handled by API Routes
      // - /api/v1/messages/stream -> app/api/v1/messages/stream/route.ts
      // - /api/v1/itineraries/plannings/stream -> app/api/v1/itineraries/plannings/stream/route.ts
    ];
  },
};

export default nextConfig;
