# RCA Benchmark

# Microservice Fault

## Resource Fault

### CPU Hog

1. `trip-chat-service` — ChaosBlade CPU

2. `trip-order-service` — ChaosBlade CPU

3. `trip-itinerary-planner` — ChaosBlade CPU

### Memory Leak

1. `trip-order-service` — ChaosBlade Memory

2. `trip-chat-service` —  ChaosBlade Memory

3. `trip-itinerary-planner` —  ChaosBlade Memory

4. `trip-review-summary` —  ChaosBlade Memory

### Disk I/O Stress

1. PostgreSQL 数据卷 — fio 数据库 I/O 压力

2. MongoDB 数据卷 — fio 数据库 I/O 压力

3. Redis 持久化目录 — fio 数据库 I/O 压力

### Socket Stress

1. `trip-chat-service` HTTP Agent 入口 — stress\-ng

2. `trip-itinerary-planner` SSE 入口 —  stress\-ng

3. `trip-order-service` gRPC 入口 —  stress\-ng

## Network Fault

### Network Delay

1. `trip-chat-service` → Higress — Toxiproxy latency

2. `trip-itinerary-planner` → `trip-attraction-service` — Toxiproxy latency

3. `trip-itinerary-planner` → `trip-hotel-service` — Toxiproxy latency

4. `trip-itinerary-planner` → `trip-itinerary-service` — Toxiproxy latency（？）

5. `trip-order-assistant` → `trip-product-service` — Toxiproxy latency

### Packet Loss

1. `trip-next-frontend` → `trip-user-service` gRPC — Toxiproxy packet loss

2. `trip-itinerary-planner` → `trip-attraction-service` gRPC — Toxiproxy packet loss

3. `trip-itinerary-planner` → `trip-hotel-service` gRPC — Toxiproxy packet loss

4. `trip-order-service` → `trip-inventory-service` gRPC — Toxiproxy packet loss

5. `trip-chat-service` → `trip-order-assistant` A2A HTTP — Toxiproxy packet loss

## Configuration Fault

### Parameter Misconfiguration

3. `trip-hotel-service` → MongoDB — invalid MongoDB URI/database

4. `trip-attraction-service` → MongoDB — invalid MongoDB URI/database

5. `trip-itinerary-service` → MongoDB — invalid MongoDB URI/database

6. `trip-user-service` → PostgreSQL — invalid PostgreSQL URL/database

7. `trip-order-service` → PostgreSQL — invalid PostgreSQL URL/database

8. `trip-inventory-service` → PostgreSQL — invalid PostgreSQL URL/database

9. `trip-order-service` → Redis — invalid Redis host/port/database

10. `trip-review-summary` → Redis — invalid Redis host/port/database

11. `trip-itinerary-planner` \-\> `trip-attraction-service`: wrong `gRPC_port` value

12. `trip-order-assistant` \-\> `trip-product-service`: wrong `gRPC_port` value

13. `trip-user-service` → Nacos — invalid Spring Cloud Nacos address

14. `trip-attraction-service` → Nacos — invalid Spring Cloud Nacos address

15. `trip-itinerary-planner`  — invalid `AMAP_KEY`

16. Wrong MongoDB password

17. Wrong JWT Token

### Compatibility Misconfiguration

1. `trip-itinerary-planner` \-\> `trip-attraction-service`: protocol metadata mismatch

2. `trip-itinerary-planner` \-\> `trip-hotel-service`: gRPC/HTTP protocol mismatch

3. `trip-order-service` \-\> `trip-product-service`: protobuf schema/version mismatch

### Component  Misconfiguration

1. `trip-itinerary-planner` \-\> `trip-attraction-service`: service instance missing from Nacos

2. `trip-itinerary-planner` \-\> `trip-hotel-service`: service registration missing

3. `trip-order-service` \-\> `trip-product-service`: product service not registered

4. `trip-order-service` \-\> `trip-inventory-service`: inventory service not registered

5. `trip-itinerary-planner` \-\> attraction/hotel: required `gRPC_port` metadata missing

6. `trip-order-assistant` \-\> order/product: required dependency registration missing

## Code\-Level Fault

### Exception Handling Error \(**Missing Exception Handlers**?\)

1. `trip-itinerary-planner` attraction lookup — remove the exception handler around the `trip-attraction-service` gRPC call, allowing downstream failures to propagate through the planning request\.

2. `trip-itinerary-planner` geocoding — remove the exception handler around the geocoding call, allowing a failed lookup to propagate and abort itinerary planning\.

3. `trip-itinerary-planner` Markdown generation — remove the exception handler around the final LLM call, allowing a provider failure to propagate instead of producing fallback Markdown\.

4. `trip-review-summary` — remove the generic exception handler around review analysis, allowing search or index failures to propagate instead of returning a structured dependency\-failure state\.

5. `trip-itinerary-planner` `regenerate_day` tool — remove the handler around structured\-output and activity\-time parsing, allowing malformed model results to propagate as an uncaught tool exception\.

### Parameter Misuse

1. `trip-user-service` registration — missing name/email/password

2. `trip-user-service` login — invalid email/password type or format

3. `trip-attraction-service` query — missing city or attraction ID

### Wrong Return Values

1. `trip-product-service` → `trip-order-service` — missing SKU or price fields

### Incorrect Business Logic

1. `trip-order-service` cancellation — cancellation from an invalid order state

2. `trip-order-service` payment confirmation — repeated confirmation for a paid order

3. `trip-inventory-service` expiration — stale lock\-expiration index

### Abnormal Execution

1. `trip-itinerary-planner` — planner artificial delay

2. `trip-review-summary` repeatedly reads from or writes to Parquet files

3. `trip-review-summary-worker` — Celery index task repeatedly requeues itself after completion, so the task\-processing loop never reaches a terminal state\.

4. `trip-itinerary-planner` → `trip-attraction-service` — continue retrying the gRPC request after a terminal downstream error\.

5. `trip-review-summary-worker` — retain Parquet DataFrames across completed indexing tasks, causing memory usage to grow over the worker lifetime\.

6. `trip-user-service` — process stop

# Agentic Fault

## Agentic Configuration Fault

### LLM Access Misconfiguration

1. `trip-chat-service` → Higress — invalid `OPENAI_BASE_URL`

2. `trip-itinerary-planner` → Higress — invalid `OPENAI_BASE_URL`

3. `trip-chat-service` → Higress — invalid `OPENAI_API_KEY`

4. `trip-itinerary-planner` → Higress — invalid `OPENAI_API_KEY`

5. `trip-review-summary` → Higress — invalid `OPENAI_API_KEY`

### Agent Registration Misconfiguration

1. `trip-chat-service` → Nacos AI AgentCard Registry — invalid Nacos AI server address

2. `trip-order-assistant` → Nacos AI AgentCard Registry — invalid Nacos AI server address

3. `trip-review-summary` → Nacos AI MCP Registry — invalid Nacos AI server address

4. `trip-chat-service` → Nacos AI — missing or invalid remote AgentCard

5. `trip-order-assistant` → Nacos AI — invalid AgentCard endpoint

6. `trip-order-assistant` → Nacos AI — incompatible AgentCard skills or capabilities

7. `trip-review-summary` → Nacos AI MCP Registry — invalid MCP server name or version

8. `trip-review-summary` → Nacos AI MCP Registry — invalid MCP endpoint, namespace, or group

### External Service Access Misconfiguration

1. `trip-chat-service` → Review Summary MCP — invalid `REVIEW_SUMMARY_URL`

2. `trip-chat-service` → Review Summary MCP — invalid MCP endpoint or `/mcp` path

3. `trip-itinerary-planner` → AMap — invalid `AMAP_KEY`

4. `trip-chat-service` → Qdrant/Mem0 — invalid `QDRANT_URL`

5. `trip-review-summary` → Neo4j — invalid URI, username, password, or database

6. `trip-review-summary-worker` → MinIO — invalid endpoint or access credentials

### Runtime Environment Misconfiguration

1. `trip-review-summary` → Celery — invalid `CELERY_BROKER_URL`

2. `trip-review-summary-worker` → Celery — invalid `CELERY_BROKER_URL`

3. `trip-review-summary` → Celery — invalid result backend

4. `trip-review-summary-worker` → Celery — incompatible broker/result\\\-backend configuration

5. `trip-review-summary` → index validation — invalid `REVIEW_INDEX_VALIDATION_MODE`

## LLM API Fault

### Error Response

1. `trip-chat-service` → LLM — HTTP 429

2. `trip-itinerary-planner` → LLM — HTTP 5xx

3. `trip-order-assistant` → LLM — provider error

4. `trip-review-summary` → LLM — provider error

### Request Timeout

1. `trip-chat-service` → LLM — request timeout

2. `trip-itinerary-planner` → LLM — request timeout

### Empty Response

1. `trip-chat-service` → LLM — empty content

2. `trip-itinerary-planner` → LLM — empty content

### Truncated Response

1. `trip-itinerary-planner` → LLM — truncated structured response

2. `trip-chat-service` streaming response — stream ends before completion

3. `trip-itinerary-planner` streaming response — stream ends before completion

### Corrupted Response

1. `trip-chat-service` → LLM — corrupted or invalidly encoded content

2. `trip-itinerary-planner` → LLM — corrupted or invalidly encoded content

### Schema Mismatch

1. `trip-itinerary-planner` → LLM — missing `day_plans` field

2. `trip-chat-service` → LLM — conflicting content and tool calls

3. `trip-itinerary-planner` → LLM — conflicting content and tool calls

## Planning Fault

### Inexecution Plan

1. `trip-itinerary-planner` — circular date or activity dependency

2. `trip-itinerary-planner` — invalid activity time ordering

3. `trip-order-assistant` — submit order without completing the draft

### Critical Information Loss

1. `trip-itinerary-planner` — missing city

2. `trip-itinerary-planner` — missing start or end date

3. `trip-itinerary-planner` — missing additional information when revising day plans

4. `trip-review-summary` index planning — missing target type

## Memory Fault

### Memory Loss

1. `trip-chat-service` — delete MongoDB session

2. `trip-chat-service` — truncate early conversation history

3. `trip-order-assistant` — lose in\-process order drafts after restart

5. `trip-chat-service` context — remove target ID or target type

6. `trip-review-summary` context — remove target ID or target type

### Stale Memory

1. `trip-chat-service` — retrieve expired Mem0/Qdrant memory

2. `trip-chat-service` — retrieve contradictory user memories

3. `trip-chat-service` — low\-priority context overrides explicit user constraints

4. `trip-itinerary-planner` — low\-priority context overrides explicit user constraints

5. `trip-chat-service` — tool result disagrees with session state

### Context Length Violation

1. `trip-itinerary-planner` — exceed the model context window

2. `trip-chat-service` — exceed the model context window

## Reasoning Fault

### Hallucination

1. `trip-itinerary-planner` — return an attraction outside the candidate set

2. `trip-itinerary-planner` — use a hotel from the wrong city

3. `trip-review-summary` — generate unsupported facts

4. `trip-review-summary` — fabricate review sources

5. `trip-order-assistant` — report a price different from ProductService

6. `trip-review-summary` — make a definite claim when no reviews exist

## Action Fault

### Parameter Filling Error

1. `trip-order-assistant` order tool — use an incorrect order ID

2. `trip-order-assistant` create\-draft tool — omit contact or user context

3. `trip-order-assistant` hotel order — use a check\-in date later than check\-out

4. `trip-order-assistant` order item — use zero or negative quantity

### Tool Format Error

1. `trip-order-assistant` tool call — malformed JSON arguments

2. `trip-order-assistant` tool call — string/number type mismatch

3. `trip-order-assistant` tool call — missing required field

4. `trip-itinerary-planner` → `geocoding_tool` — malformed JSON tool arguments

### Tool Selection Error

1. `trip-itinerary-planner` — choose hotel tool for an attraction request

2. `trip-order-assistant` — choose SPU instead of SKU

3. `trip-order-assistant` — omit ProductService lookup before creating an order

4. `trip-chat-service` hotel context — invoke the wrong context tool

## Inter\-Agent Fault

### Role Ambiguity

1. `trip-order-assistant` AgentCard — vague role description

2. `trip-order-assistant` AgentCard — overlapping or conflicting capabilities

### Blind Trust

1. `trip-chat-service` → `trip-order-assistant` — trust result without checking `trip-order-service` state

### Instruction Ambiguity

1. `trip-chat-service` → `trip-itinerary-planner` — “安排周末去上海，住便宜的酒店” without exact dates or budget

2. `trip-chat-service` → `trip-itinerary-planner` — “安排轻松一点的行程” without an explicit pace or activity constraint

3. `trip-chat-service` → `trip-order-assistant` — “订最便宜的那个” when multiple products or rooms match

### Instruction Logic Conflict

1. `trip-itinerary-planner` — destination conflicts with the user instruction

2. `trip-order-assistant` — cancellation confirmation conflicts with the cancel tool call

3. `trip-chat-service` → `trip-order-assistant` — different user intents arrive across the handoff



