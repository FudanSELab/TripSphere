import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test("removes unused poi frontend entry points", () => {
  const envSource = readFileSync(path.join(__dirname, "../lib/env.ts"), "utf8");
  const clientSource = readFileSync(
    path.join(__dirname, "../lib/grpc/client.ts"),
    "utf8",
  );

  assert.ok(!envSource.includes("POI_SERVICE_ADDR"));
  assert.ok(!envSource.includes("poiService:"));
  assert.ok(!clientSource.includes("PoiServiceClient"));
  assert.ok(!clientSource.includes("getPoiService"));
});
