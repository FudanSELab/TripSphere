# TripSphere Basic Business Loops Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish and verify the six user-visible TripSphere business loops, connect the required single-instance deployment and observability baseline, and remove services with no business callers.

**Architecture:** Keep the existing gRPC, HTTP, frontend Server Actions, planner, chat and order-assistant boundaries. Use existing service discovery and current session/request identity propagation from Phase 1, ReviewService as the review source of truth, and the existing review-summary A2A/HTTP path as the smallest review Q&A integration. Run the retained services in one Compose environment with Nacos/Higress dependencies and a single observability path through Grafana Alloy, Loki, OTel Collector, Tempo, Prometheus and Grafana.

**Tech Stack:** Java/Spring Boot with Maven Wrapper, Go, Python with `uv`, Next.js with `bun -b`, protobuf/gRPC, MongoDB, PostgreSQL, Redis, Qdrant, Neo4j, Nacos, Higress, Docker Compose, Grafana Alloy, Loki, OTel Collector, Tempo, Prometheus and Grafana.

**Spec:** `docs/superpowers/specs/2026-08-24-tripsphere-systematic-refactor-design.md`

## Global Constraints

- Phase 1 service-discovery metadata is complete and must not be reimplemented.
- `ConfirmPayment` is simulated payment and ends in `PAID`.
- Existing frontend session, request-header and gRPC metadata propagation is retained; no metadata unification or authentication architecture refactor is required in this plan.
- Keep shared POI protobuf types and initialization data; remove only the independent POI service.
- The single-instance observability baseline is required: Loki, Grafana Alloy, OTel Collector, Tempo, Prometheus, Grafana, Higress, Nacos and Compose health checks must be connected and verifiable.
- Do not add replicas, data replication, automatic failover, horizontal scaling or cross-instance consistency mechanisms.
- Do not add a real payment provider, shared checkpoint system, new message broker or new business service.
- Use `./mvnw`, `uv`, `bun -b` and `go test` according to the repository rules.

### Task 1: Verify The Existing Baseline

**Files:**
- Read: `docs/superpowers/plans/2026-08-24-phase-1-service-discovery-baseline.md`
- Read: `trip-*/src/test`, `trip-review-service/**/*_test.go`
- Read: `docker-compose.yaml`, `deploy/docker-compose/docker-compose.yaml`, `Taskfile.yaml`
- Read: `infra/otel-collector/config.yaml`, `infra/tempo/tempo.yaml`, `infra/prometheus/prometheus.yaml`
- Modify: `docs/服务改造清单.md` only if the recorded Phase 1 status is inaccurate

**Interfaces:**
- Consumes: Phase 1 merged branch at commit `10f4702`.
- Produces: A recorded baseline showing discovery metadata tests and current service startup assumptions.

- [ ] **Step 1: Run the Phase 1 focused tests**

Run the discovery tests in the Java services and review service:

```bash
for service in trip-user-service trip-attraction-service trip-hotel-service trip-product-service trip-inventory-service trip-order-service trip-itinerary-service; do
  (cd "$service" && ./mvnw -q -Dtest='*DiscoveryMetadataTests' test)
done
(cd trip-review-service && go test ./pkg/nacos)
```

Expected: each command exits with code 0.

- [ ] **Step 2: Check the current dependency graph**

Run:

```bash
rg -n -i "trip-poi-service|trip-file-service|trip-note-service|trip-note-creator|rmq-|rocketmq|minio" \
  --glob '!**/.venv/**' --glob '!**/node_modules/**' --glob '!volumes/**' .
```

Expected: the output is used as the deletion checklist; shared POI data references and review-summary MinIO references are explicitly retained until their consumers are handled.

- [ ] **Step 3: Record the baseline**

Document the actual focused-test result and the service references in the Phase 2 work log or pull request description. Do not modify application behavior in this task.

### Task 2: Make Identity And Content Usable

**Files:**
- Modify: `trip-next-frontend/lib/grpc/client.ts`
- Modify: `trip-next-frontend/lib/env.ts`
- Modify: `trip-next-frontend/lib/data/*`
- Modify: `trip-next-frontend/actions/*`
- Modify: `infra/initializer/*` and its data fixtures
- Test: affected service tests and frontend tests colocated with the changed modules

**Interfaces:**
- Consumes: Existing session/request identity parameters and Phase 1 `gRPC_port` discovery metadata.
- Produces: Stable attraction, hotel, room type, SKU and inventory fixtures.

- [ ] **Step 1: Remove unused frontend POI entry points**

Remove `POI_SERVICE_ADDR`, the POI gRPC client and `getPoiService` only after confirming no frontend caller remains. Keep the existing session and metadata propagation unchanged.

- [ ] **Step 2: Fix only blocking content contracts**

Verify that:

```text
attraction/hotel lookup -> real entity or explicit empty result
room type -> the same SKU id used by product-service
SKU -> resource type, price, status and sale dates
inventory -> the same SKU/date pair accepted by order-service
```

Do not add operator CRUD endpoints or new data models for this task.

- [ ] **Step 4: Prepare deterministic fixtures**

Use `infra/initializer` to load at least two users, one city, hotel/room data, attraction data, matching SKUs, inventory days and comments needed by later tasks. Print stable ids and counts.

- [ ] **Step 5: Run focused verification**

Run:

```bash
(cd trip-user-service && ./mvnw -q test)
(cd trip-attraction-service && ./mvnw -q test)
(cd trip-hotel-service && ./mvnw -q test)
(cd trip-product-service && ./mvnw -q test)
(cd trip-inventory-service && ./mvnw -q test)
```

For changed Python/TypeScript modules, run the service-local `uv` test command or `bun -b` lint/typecheck command defined by that service's Taskfile/package scripts.

### Task 3: Complete The Itinerary Loop

**Files:**
- Modify: `trip-itinerary-planner/src/itinerary_planner/*`
- Modify: `trip-itinerary-service/src/main/*`
- Modify: `trip-next-frontend/actions/itinerary.ts`
- Modify: `trip-next-frontend/lib/data/itinerary.ts`
- Test: planner tests, itinerary service tests and frontend action tests

**Interfaces:**
- Consumes: attraction/hotel discovery and content fixtures from Task 2.
- Produces: a persisted itinerary id that frontend can read, replace and delete in the current session flow.

- [ ] **Step 1: Write planner regression tests**

Cover:

```text
available candidates < requested sample size -> return all available candidates
unknown/unavailable dependency -> explicit failure, not fake Shanghai data
generated itinerary -> valid dates, activities and referenced entity ids
```

- [ ] **Step 2: Implement the smallest planner fixes**

Use the existing non-streaming planning endpoint as the canonical generation path. Replace fixed-size sampling with bounded sampling and reject invalid generated structure before persistence. Do not introduce a shared planning job or checkpoint store.

- [ ] **Step 3: Verify persistence**

Exercise create, list, get, replace and delete through itinerary-service. Keep the existing session/request identity behavior and protobuf shape unless a failing business path proves a contract change is required.

- [ ] **Step 4: Run itinerary verification**

Run the planner's `uv` tests, the itinerary service's `./mvnw -q test`, and the frontend's focused itinerary checks. Then run one real create -> reload -> replace -> reload smoke path against initialized services.

### Task 4: Complete Reviews And Review Q&A

**Files:**
- Modify: `trip-review-service/internal/service/review_service.go`
- Modify: `trip-review-service/internal/repository/*`
- Modify: `trip-next-frontend/lib/grpc/*`, `trip-next-frontend/lib/data/*`, `trip-next-frontend/actions/*`
- Modify: hotel/attraction detail components and review components in `trip-next-frontend`
- Modify: `trip-review-summary/src/review_summary/*`
- Modify: `trip-chat-service/src/chat/*`
- Test: `trip-review-service/**/*_test.go`, review-summary tests and frontend/chat focused tests

**Interfaces:**
- Consumes: ReviewService protobuf methods `CreateReview`, `UpdateReview`, `DeleteReview`, `ListReviewsByEntity`; current review-summary A2A/HTTP path.
- Produces: real hotel/attraction review CRUD and chat answers based on the matching target's reviews.

- [ ] **Step 1: Add frontend review data flow**

Implement the gRPC client and Server Actions for list/current-user/create/update/delete. Replace detail-page placeholders and hard-coded review counts with ReviewService data. Pass immutable `target_id` and `target_type` into the detail-page chat context.

- [ ] **Step 2: Connect real reviews to review-summary**

Add the ReviewService client and paginate through `ListReviewsByEntity` for both `hotel` and `attraction`. Convert returned reviews into the existing indexing input. Keep current MinIO-backed intermediate files in this phase so deleting MinIO does not break the worker.

- [ ] **Step 3: Make review Q&A truthful**

Keep the existing A2A/HTTP entry for this phase and make its query path:

```text
target_id + target_type -> review snapshot/index -> answer with evidence
```

Remove or disable only the unimplemented static summary endpoint. Return distinct states for empty reviews, missing index and dependency failure. Add `review-summary` to chat's configured/discovered review capability without changing the existing order-assistant A2A path.

- [ ] **Step 6: Run review verification**

Run:

```bash
(cd trip-review-service && go test ./...)
(cd trip-review-summary && uv run pytest)
(cd trip-chat-service && uv run pytest)
```

Also run one real flow for both target types:

```text
create review -> build/refresh index -> ask review question -> verify target and evidence
```

### Task 5: Complete The Order Loop

**Files:**
- Modify: `trip-order-service/src/main/*`
- Modify: `trip-inventory-service/src/main/*` only where order behavior is incorrect
- Modify: `trip-order-assistant/src/order_assistant/tools/*`
- Modify: `trip-next-frontend/actions/order.ts`, order components and order data adapters
- Test: order, inventory, order-assistant and frontend order tests

**Interfaces:**
- Consumes: product/SKU/inventory contracts and the existing session/request identity parameters.
- Produces: draft -> order -> pending payment -> paid/cancelled flow.

- [ ] **Step 1: Add order state tests**

Cover:

```text
PENDING_PAYMENT -> PAID succeeds once
PENDING_PAYMENT -> CANCELLED releases inventory
repeating the same request id does not create a second order
inventory failure is returned as failure, not success
```

- [ ] **Step 2: Finish order-assistant tools**

Use the current draft implementation unless it prevents the single-instance basic flow. Add contact information, submit, query, cancel and `confirm_payment`. Preserve the existing downstream authentication parameter passing.

- [ ] **Step 3: Finish frontend order actions**

Connect SKU/room selection to order creation, show pending payment orders, call `ConfirmPayment`, refresh to show `PAID`, and keep cancel available only for allowed states.

- [ ] **Step 5: Run order verification**

Run the order and inventory Maven tests, order-assistant `uv` tests, frontend `bun -b` checks, and one real flow:

```text
SKU -> create order -> lock inventory -> confirm payment -> PAID
SKU -> create second pending order -> cancel -> inventory released
```

### Task 6: Complete Deployment And Observability Baseline

**Files:**
- Create: `infra/loki/loki.yaml`
- Create: `infra/alloy/config.alloy`
- Create: `infra/grafana/provisioning/datasources/datasources.yaml`
- Create: `infra/grafana/provisioning/dashboards/dashboards.yaml`
- Create: `infra/grafana/dashboards/tripsphere-overview.json`
- Modify: `infra/otel-collector/config.yaml`
- Modify: `infra/tempo/tempo.yaml`
- Modify: `infra/prometheus/prometheus.yaml`
- Modify: `docker-compose.yaml`
- Modify: `deploy/docker-compose/docker-compose.yaml`
- Modify: retained service Compose environment blocks and existing health/metrics endpoint files when a service cannot participate in the required telemetry or readiness checks

**Interfaces:**
- Consumes: the service list and real request paths from Tasks 2-5.
- Produces: a single-instance Compose environment where dependencies start in order and one request can be found in logs, metrics and traces.

- [ ] **Step 1: Define the canonical Compose contract**

Use root `docker-compose.yaml` as the local acceptance canonical Compose. Keep `deploy/docker-compose/docker-compose.yaml` synchronized with the same retained business and observability responsibilities; it may use environment variables for credentials and hostnames, but it must not omit required services.

The retained baseline must include:

```text
Nacos, Higress
MongoDB, PostgreSQL, Redis, Qdrant, Neo4j, MinIO while review-summary uses it
OTel Collector, Tempo, Prometheus, Grafana, Loki, Grafana Alloy
all retained application services and review-summary worker
```

- [ ] **Step 2: Add Loki and Grafana Alloy log collection**

Configure Loki with a local filesystem store and bounded retention suitable for development. Configure Grafana Alloy to read Docker JSON logs for the Compose project and push them to Loki with labels:

```text
service
environment
container
level
```

The collector configuration must not forward JWTs, passwords, API keys or full authorization headers. Preserve the existing `json-file` Docker logging rotation and mount only the read-only Docker log paths needed by Alloy.

- [ ] **Step 3: Connect OTel, Tempo and Prometheus**

Update `infra/otel-collector/config.yaml` so:

```text
OTLP traces -> Tempo
OTLP metrics -> Prometheus exporter endpoint
debug output -> development troubleshooting only
```

Enable the Collector `health_check` extension on port `13133` and expose it in both Compose files. Keep the existing OTLP receivers on `4317` and `4318`.

Do not claim logs are observable through OTel unless the application log path is actually connected. Add Prometheus scrape targets for Prometheus, OTel Collector and every retained service that exposes a metrics endpoint; use health endpoints for services without native metrics.

- [ ] **Step 4: Provision Grafana data sources and dashboard**

Provision Prometheus, Tempo and Loki data sources from files mounted by Compose. Add one small dashboard or saved-query set covering:

```text
request rate/error count
service latency or OTel span count
logs filtered by service/request_id/trace_id
trace lookup by trace_id
```

The dashboard only needs to support the single-instance acceptance flow; it does not need HA capacity planning or alert escalation.

- [ ] **Step 5: Complete dependency health checks**

Add real Compose health checks and `depends_on` conditions for Nacos, Higress, OTel Collector, Tempo, Prometheus, Grafana, Loki, Alloy, MongoDB, PostgreSQL, Redis, Qdrant and Neo4j. A health check must call the component's health/readiness endpoint or a real protocol command; process existence alone is insufficient.

Verify that chat, planner, order-assistant and review-summary fail visibly when required Nacos or Higress dependencies are unavailable. Do not silently continue with fake data or localhost endpoints.

- [ ] **Step 6: Verify the observability path with a real request**

Run:

```bash
docker compose config
docker compose up -d
curl -fsS http://localhost:18080/v3/console/health/readiness
curl -fsS http://localhost:13133
curl -fsS http://localhost:9090/-/ready
curl -fsS http://localhost:3000/
curl -fsS http://localhost:13000/api/health
curl -fsS http://localhost:3200/ready
curl -fsS http://localhost:3100/ready
curl -fsS http://localhost:12345/-/ready
```

Use the Higress OpenAI-compatible smoke request documented in `README.md` against `http://localhost:28080/v1`, and verify the retained services appear healthy in `docker compose ps`.

Then execute one itinerary, review or order request using the existing session/request flow and verify:

```text
Grafana Loki query returns the service log
Prometheus contains the service/OTel metric
Tempo contains the trace id
Grafana data sources report healthy
Higress chat/embedding route and Nacos service discovery both respond
```

### Task 7: Remove Unused Services And References

**Files:**
- Delete: `trip-poi-service/`
- Delete: `trip-file-service/`
- Delete: `trip-note-service/`
- Delete: `trip-note-creator/`
- Modify: `Taskfile.yaml`
- Modify: `docker-compose.yaml`
- Modify: `deploy/docker-compose/docker-compose.yaml` if it contains the removed entries
- Modify: `contracts/protobuf/tripsphere/poi/v1/poi.proto` and generated targets only after reference checks
- Modify: frontend env/client and initializer documentation
- Modify: review-service RocketMQ configuration

**Interfaces:**
- Consumes: completed callers from Tasks 2-6.
- Produces: no build/start/runtime path for the deleted services; shared POI types remain available.

- [ ] **Step 1: Prove each deletion is safe**

Run:

```bash
rg -n -i "trip-poi-service|trip-file-service|trip-note-service|trip-note-creator|rmq-|rocketmq" \
  --glob '!**/.venv/**' --glob '!**/node_modules/**' --glob '!volumes/**' .
```

Classify every remaining match as a file to delete, a build/config reference to remove, or a shared POI data/type reference to retain.

- [ ] **Step 2: Remove build and runtime entries**

Remove the deleted service includes and generation/build tasks from `Taskfile.yaml`, their Compose service blocks and dependent environment variables. Remove RocketMQ dependencies from review-service and Compose.

- [ ] **Step 3: Preserve shared POI contracts**

Keep `contracts/protobuf/tripsphere/poi/v1/types.proto` and any generated types required by itinerary. Remove the standalone `PoiService` contract only if the full generated-code reference check proves no consumer remains.

- [ ] **Step 4: Verify the deletion**

Run:

```bash
task gen-proto
docker compose config
rg -n -i "trip-poi-service|trip-file-service|trip-note-service|trip-note-creator|rmq-|rocketmq" \
  --glob '!**/.venv/**' --glob '!**/node_modules/**' --glob '!volumes/**' .
```

Expected: protobuf generation and Compose validation succeed; only explicitly retained historical documentation or migration notes may mention removed names.

### Task 8: Run The Six-Loop Acceptance

**Files:**
- Read: `docs/服务改造清单.md`
- Read: `docs/superpowers/specs/2026-08-24-tripsphere-systematic-refactor-design.md`
- Modify: focused smoke scripts or initializer output only when required by a failing acceptance path

**Interfaces:**
- Consumes: Tasks 2-6.
- Produces: reproducible acceptance evidence for all six loops.

- [ ] **Step 1: Initialize deterministic data**

Run the documented `infra/initializer` command and record user ids, entity ids, SKU ids, inventory dates and review counts.

- [ ] **Step 2: Execute the six flows**

```text
login A/B
read attraction/hotel/room/SKU
generate/save/edit/reload itinerary
list/create/update/delete reviews with the existing session/request parameters
ask hotel and attraction review questions with empty/error cases
create/cancel/pay orders with inventory checks
```

- [ ] **Step 3: Verify infrastructure and repository hygiene**

Run:

```bash
docker compose ps
docker compose config
git diff --check
git status --short
```

Review the full diff for generated-file churn, unrelated formatting and accidental reintroduction of removed services. Confirm that the Compose status shows healthy Nacos, Higress, storage, observability and application dependencies.

- [ ] **Step 4: Record completion**

The implementation is complete only when every flow has a successful result, logs/metrics/traces are queryable through the observability stack, and deleted services are absent from build/start/runtime references.
