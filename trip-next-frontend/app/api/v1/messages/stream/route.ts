import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

// Get the backend URL from environment variable
const getBackendUrl = () => {
  return process.env.HTTP_CHAT_URL || "http://localhost:24210";
};

export async function POST(req: NextRequest) {
  const backendUrl = getBackendUrl();
  const targetUrl = `${backendUrl}/api/v1/messages/stream`;

  try {
    // Get the request body
    const body = await req.text();

    // Forward headers (especially X-User-Id)
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    };

    // Forward X-User-Id header
    const userId = req.headers.get("X-User-Id");
    if (userId) {
      headers["X-User-Id"] = userId;
    }

    // Forward the request to the backend
    const response = await fetch(targetUrl, {
      method: "POST",
      headers,
      body,
    });

    if (!response.ok) {
      return new Response(
        JSON.stringify({ error: `Backend error: ${response.status}` }),
        {
          status: response.status,
          headers: { "Content-Type": "application/json" },
        },
      );
    }

    // Check if we got a readable stream
    if (!response.body) {
      return new Response(JSON.stringify({ error: "No response body" }), {
        status: 500,
        headers: { "Content-Type": "application/json" },
      });
    }

    // Create a TransformStream to pass through the SSE data
    const { readable, writable } = new TransformStream();

    // Pipe the backend response to the client
    const reader = response.body.getReader();
    const writer = writable.getWriter();

    // Process the stream in the background
    (async () => {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            await writer.close();
            break;
          }
          await writer.write(value);
        }
      } catch (error) {
        console.error("Stream processing error:", error);
        try {
          await writer.abort(error as Error);
        } catch {
          // Writer may already be closed
        }
      }
    })();

    // Return the streaming response
    return new Response(readable, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-transform",
        Connection: "keep-alive",
        "X-Accel-Buffering": "no", // Disable nginx buffering
      },
    });
  } catch (error) {
    console.error("SSE proxy error:", error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : "Unknown error",
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      },
    );
  }
}
