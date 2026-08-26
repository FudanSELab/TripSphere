# TripSphere Phase 4 Reviews And Review Q&A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete hotel/attraction review CRUD and make chat answer from the matching entity's real ReviewService reviews with traceable evidence and truthful business states.

**Architecture:** Keep the existing protobuf methods, frontend Server Actions, Celery/MinIO indexing pipeline, Qdrant/Neo4j stores, and A2A delegation. ReviewService remains the only review source of truth; frontend and review-summary both paginate `ListReviewsByEntity`, while chat sends page-controlled target metadata to review-summary through the existing A2A request metadata hook.

**Tech Stack:** Go, MongoDB, protobuf/gRPC, Next.js 16, React 19, CopilotKit V2, TypeScript, Python 3.12 with `uv`, Celery, MinIO, Qdrant, Neo4j, Nacos AI, Google ADK and A2A SDK.

**Spec:** `docs/superpowers/specs/2026-08-24-tripsphere-systematic-refactor-design.md`

## Global Constraints

- Implement only Phase 4 from `docs/服务改造清单.md:113-125` and Task 4 from the basic-business-loops plan.
- ReviewService is the only review source of truth; do not add a second review database or preloaded text-unit source.
- Keep the existing `CreateReview`, `UpdateReview`, `DeleteReview`, and `ListReviewsByEntity` protobuf methods and request shapes.
- Keep the current frontend session, request-header, and gRPC metadata propagation; do not introduce a new authentication architecture.
- Keep the existing Celery index task, MinIO intermediate files, Qdrant/Neo4j stores, and review-summary A2A/HTTP integration.
- Support both `hotel` and `attraction`; every review-summary query and index lookup must use both `target_id` and `target_type`.
- Page-controlled A2A request metadata is the only target source. User text and A2A message/file parts must not provide or override target identity.
- Distinguish `empty_reviews`, `index_missing`, and `dependency_failure`; never translate dependency failure into an empty-review result.
- Do not add automatic index rebuilds to review CRUD. The existing explicit index task remains the refresh mechanism.
- Do not add or run tests or builds in this implementation. The user requested coding and code review only.
- Preserve unrelated files and the three untracked build logs in `/home/wws/TripSphere`.

---

### Task 1: Enforce Review Ownership And Stable CRUD Errors

**Files:**
- Modify: `trip-review-service/internal/domain/errors.go`
- Modify: `trip-review-service/internal/repository/review_repo.go`
- Modify: `trip-review-service/internal/service/review_service.go`

**Interfaces:**
- Consumes: incoming `x-user-id` gRPC metadata and the unchanged review protobuf.
- Produces: authenticated CRUD semantics used by frontend actions; `AlreadyExists` for the unique entity/user review constraint.

- [ ] **Step 1: Add the duplicate-review domain error**

Add `ErrReviewAlreadyExists` beside the existing review domain errors and an `IsAlreadyExistsError(error) bool` helper.

- [ ] **Step 2: Translate Mongo duplicate-key failures**

In `ReviewRepo.Create`, use `mongo.IsDuplicateKeyError(err)` and wrap `domain.ErrReviewAlreadyExists`; keep all other database errors wrapped as internal repository failures.

- [ ] **Step 3: Make authenticated metadata authoritative**

For Create/Update/Delete:

```text
missing x-user-id                         -> Unauthenticated
Create request user_id conflicts with it -> PermissionDenied
existing review belongs to another user  -> PermissionDenied
```

Create must require the existing request `user_id` to equal the authenticated metadata user ID and persist the request value; it must not silently rewrite the author. Update/Delete must load the existing review before mutation and enforce ownership. Keep the current updateable fields (`rating`, `content`, `images`, `dimensions`) unchanged.

- [ ] **Step 4: Tighten entity validation and error mapping**

Accept only HOTEL and ATTRACTION entity types. Map duplicate reviews to `codes.AlreadyExists`, missing reviews to `codes.NotFound`, invalid input to `codes.InvalidArgument`, and repository failures to `codes.Internal`.

- [ ] **Step 5: Self-review and commit**

Review the diff without running tests or builds, then commit:

```bash
git commit -m "fix(review): enforce authenticated review ownership"
```

---

### Task 2: Add Frontend Review Data And Mutation Interfaces

**Files:**
- Modify: `trip-next-frontend/lib/env.ts`
- Modify: `trip-next-frontend/lib/grpc/client.ts`
- Create: `trip-next-frontend/lib/review/types.ts`
- Create: `trip-next-frontend/lib/data/review.ts`
- Create: `trip-next-frontend/actions/review.ts`

**Interfaces:**
- Consumes: generated `ReviewServiceClient`, existing `getAuthMetadata()`, and Task 1 error semantics.
- Produces:

```ts
type ReviewTargetType = "hotel" | "attraction";
interface ReviewStats { averageRating: number | null; reviewCount: number }
interface ReviewOverview {
  reviews: Review[];
  userReview?: Review;
  stats: ReviewStats;
  error?: string;
}
getReviewOverview(targetId, targetType): Promise<ReviewOverview>
getReviewStats(targetId, targetType): Promise<ReviewStats>
createReview(input): Promise<ReviewActionResult>
updateReview(input): Promise<ReviewActionResult>
deleteReview(input): Promise<ReviewActionResult>
```

- [ ] **Step 1: Register the frontend ReviewService client**

Add `REVIEW_SERVICE_ADDR` with `localhost:50057`, import the generated client, and expose `getReviewService()` through the existing client cache.

- [ ] **Step 2: Centralize target-type conversion**

Map only `hotel` and `attraction` to protobuf `EntityType`; reject all other values. Keep UI-facing target types free of protobuf enum numbers.

- [ ] **Step 3: Implement truthful pagination**

Paginate with `pageSize: 100` until `nextPageToken` is empty. When authenticated, add `userReview` exactly once because ReviewService excludes it from the normal list. Detect repeated page tokens and surface service failures as `ReviewOverview.error`, not as an empty list.

- [ ] **Step 4: Compute exact statistics**

Compute count and average from the fully paginated result. Empty results produce `{ averageRating: null, reviewCount: 0 }`; do not hard-code counts or averages.

- [ ] **Step 5: Implement authenticated Server Actions**

Validate target ID, target type, review ID, integer rating `1..5`, and bounded non-empty content. Obtain the author from `getSession()` instead of accepting user ID from the browser, pass existing auth metadata, and revalidate the affected detail path plus `/hotels` for hotel statistics.

- [ ] **Step 6: Self-review and commit**

Review the diff without running tests or builds, then commit:

```bash
git commit -m "feat(frontend): add review data and mutation actions"
```

---

### Task 3: Build The Hotel And Attraction Review UI

**Files:**
- Create: `trip-next-frontend/components/review/review-rating.tsx`
- Create: `trip-next-frontend/components/review/review-form.tsx`
- Create: `trip-next-frontend/components/review/review-section.tsx`
- Create: `trip-next-frontend/components/context/review-target-context.tsx`
- Modify: `trip-next-frontend/app/(main)/hotels/[id]/page.tsx`
- Modify: `trip-next-frontend/app/(main)/attractions/[id]/page.tsx`
- Modify: `trip-next-frontend/lib/mappers/hotel.ts`
- Modify: `trip-next-frontend/components/hotel-card.tsx`

**Interfaces:**
- Consumes: Task 2 review overview/actions/statistics.
- Produces: reusable CRUD UI and CopilotKit context value:

```json
{"targetId":"...","targetType":"hotel|attraction","targetName":"..."}
```

with description `review target context`.

- [ ] **Step 1: Add accessible rating and form controls**

Use semantic theme tokens and Lucide stars, keyboard-accessible buttons/radio semantics, visible labels, pending/disabled states, and inline error messages. Do not hard-code colors.

- [ ] **Step 2: Add the reusable review section**

Display exact average/count, current-user create-or-edit controls, delete confirmation, other reviews, dates, stars, empty state, anonymous sign-in guidance, and a distinct service-error state. Refresh server data after successful mutations.

- [ ] **Step 3: Replace detail placeholders**

Mount the same review section for hotel and attraction using the correct target type. Add a review tab to the attraction page and replace the hotel placeholder.

- [ ] **Step 4: Mount immutable page target context**

Use CopilotKit V2 `useAgentContext` outside tab-specific content so target context remains mounted regardless of the active tab. The context value must come only from server-loaded entity data and route parameters.

- [ ] **Step 5: Remove unbacked hotel-card statistics**

Remove the unconditional `rating: null` and `reviews: 0` mapping and the corresponding false “暂无评分/0条点评” card output. Exact ReviewService rating/count remains visible in each detail page; do not introduce full-pagination N+1 calls for every hotel card.

- [ ] **Step 6: Self-review and commit**

Review accessibility, component boundaries, Server/Client component placement, and the diff without running tests or builds, then commit:

```bash
git commit -m "feat(frontend): add hotel and attraction review UI"
```

---

### Task 4: Source Review Indexes From ReviewService

**Files:**
- Modify: `trip-review-summary/src/review_summary/infra/nacos/naming.py`
- Create: `trip-review-summary/src/review_summary/clients/reviews.py`
- Create: `trip-review-summary/src/review_summary/index/review_snapshot.py`
- Modify: `trip-review-summary/src/review_summary/index/tasks/collect_text_units.py`
- Modify: `trip-review-summary/src/review_summary/index/tasks/finalize_graph.py`
- Modify: `trip-review-summary/src/review_summary/index/tasks/create_text_embeddings.py`
- Modify: `trip-review-summary/src/review_summary/index/operations/create_graph.py`
- Modify: `trip-review-summary/src/review_summary/vector_stores/text_unit.py`
- Modify: `trip-review-summary/src/review_summary/vector_stores/entity.py`

**Interfaces:**
- Consumes: Nacos `gRPC_port` metadata and generated Python ReviewService protobuf modules.
- Produces:

```python
ReviewServiceClient.list_all(target_id: str, target_type: TargetType) -> list[ReviewRecord]
compute_review_snapshot(reviews: Sequence[ReviewRecord]) -> str
reviews_to_text_units(reviews, target_id, target_type, snapshot) -> list[TextUnit]
```

Every indexed payload carries `target_id`, `target_type`, `review_snapshot`, `review_id`, `user_id`, `rating`, and `updated_at` where applicable.

- [ ] **Step 1: Add Nacos-backed ReviewService pagination**

Discover only healthy `trip-review-service` instances and require `gRPC_port`; do not silently fall back to a hard-coded port. Paginate `ListReviewsByEntity` without user auth metadata so all reviews are returned.

- [ ] **Step 2: Build deterministic review snapshots**

Hash sorted review ID/update-time pairs. Convert every review, including rating-only reviews, into non-empty source text with a deterministic review UUID as the text-unit ID and evidence attributes.

- [ ] **Step 3: Embed real review text units**

Replace the current Qdrant pre-read in `collect_text_units` with ReviewService fetch, text conversion, `text-embedding-3-large` embeddings, Qdrant save, and the existing MinIO parquet output.

- [ ] **Step 4: Replace stale target indexes safely**

After live reviews and embeddings are ready, delete the target's previous text units, entities, and Neo4j graph, then save the new text units. Empty reviews must clear stale target indexes before returning an explicit empty-review failure from the indexing task.

- [ ] **Step 5: Propagate snapshot identity through the graph**

Add `review_snapshot` to finalized entity/relationship attributes, Neo4j properties, and entity-vector payloads so query preflight can reject stale or partially rebuilt indexes.

- [ ] **Step 6: Self-review and commit**

Review pagination termination, target filters, resource shutdown, stale-data removal, evidence attributes, and the diff without running tests or builds, then commit:

```bash
git commit -m "feat(review-summary): index reviews from ReviewService"
```

---

### Task 5: Make Review Q&A Truthful And Evidence-Backed

**Files:**
- Create: `trip-review-summary/src/review_summary/query/review_state.py`
- Modify: `trip-review-summary/src/review_summary/query/structured_search/local_search/mixed_content.py`
- Modify: `trip-review-summary/src/review_summary/query/structured_search/local_search/search.py`
- Modify: `trip-review-summary/src/review_summary/prompts/query/local_search_system_prompt.py`
- Modify: `trip-review-summary/src/review_summary/agent/executor.py`
- Modify: `trip-review-summary/src/review_summary/agent/card.py`
- Modify: `trip-review-summary/src/review_summary/asgi.py`
- Delete: `trip-review-summary/src/review_summary/routers/summaries.py`
- Delete: `trip-review-summary/src/review_summary/query/tasks/create_static_summary.py`
- Delete: `trip-review-summary/src/review_summary/config/query/create_static_summary_config.py`

**Interfaces:**
- Consumes: Task 4 live review client, target-aware vector stores, snapshot evidence, and A2A `RequestContext.metadata`.
- Produces A2A data payloads:

```json
{"status":"success","target_id":"...","target_type":"hotel","answer":"...","evidence":[...]}
{"status":"empty_reviews","target_id":"...","target_type":"hotel","message":"..."}
{"status":"index_missing","target_id":"...","target_type":"hotel","message":"..."}
{"status":"dependency_failure","target_id":"...","target_type":"hotel","message":"..."}
```

- [ ] **Step 1: Validate authoritative target context**

Read `target_id` and `target_type` only from A2A request metadata. Remove the legacy JSON file-part extraction so message content cannot become target identity. Reject missing IDs and target types outside `hotel|attraction`.

- [ ] **Step 2: Add live/index preflight**

Fetch current ReviewService reviews. Return `empty_reviews` when there are none. Verify text units, entity vectors, Neo4j graph, and `review_snapshot`; return `index_missing` for absent, partial, or stale indexes. Convert ReviewService/Nacos/Qdrant/Neo4j failures to `dependency_failure`.

- [ ] **Step 3: Carry target type through local search**

Add required `target_type` parameters through executor, `LocalSearch.search`, `LocalSearchMixedContext.build_context`, entity lookup, and text-unit lookup. Remove all implicit attraction defaults from production query paths.

- [ ] **Step 4: Prevent false successful answers**

Do not swallow model/search exceptions into an empty response. Make the prompt use only supplied review evidence and return the sources DataFrame as structured evidence with the generated answer.

- [ ] **Step 5: Update A2A capability and remove static summary**

Describe both hotel and attraction review analysis in the agent card. Remove the complete unimplemented static-summary router/task/config while keeping `/indices` and A2A routes. Add a basic readiness endpoint that becomes available only after lifespan initialization.

- [ ] **Step 6: Self-review and commit**

Review every status branch, target filter, evidence field, retained A2A/index route, and the diff without running tests or builds, then commit:

```bash
git commit -m "feat(review-summary): add truthful review Q&A states"
```

---

### Task 6: Connect Chat Delegation And Compose Runtime Wiring

**Files:**
- Modify: `trip-chat-service/src/chat/agent/agui.py`
- Modify: `trip-chat-service/src/chat/agent/remote_agent.py`
- Modify: `trip-chat-service/src/chat/prompts/agent.py`
- Modify: `docker-compose.yaml`

**Interfaces:**
- Consumes: frontend context description `review target context`, Task 5 `review_summary` Nacos Agent Card, and its readiness endpoint.
- Produces: A2A request metadata `{target_id, target_type}` for review-summary while preserving order-assistant auth metadata and delegation.

- [ ] **Step 1: Centralize immutable review-target extraction**

Parse `_ag_ui_context`, validate the JSON shape and target type, and return the page-provided target. Never extract target identity from user text.

- [ ] **Step 2: Add review-summary discovery**

Add `review_summary` beside `order_assistant` in the configured remote-agent list. Preserve the existing order-assistant path and auth headers.

- [ ] **Step 3: Add target A2A metadata**

When a valid review target exists, add `target_id` and `target_type` to `a2a_request_meta_provider` output. Omit them when no detail-page context is mounted; do not send null metadata values.

- [ ] **Step 4: Teach the delegator when to use review-summary**

Update the root instruction to delegate hotel/attraction review questions and rely on page target context rather than IDs supplied in conversational text.

- [ ] **Step 5: Wire the canonical local Compose manifest**

Add `REVIEW_SERVICE_ADDR=trip-review-service:50057` to frontend, correct ReviewService's `MONGODB_URI`, add the relevant ReviewService/summary/worker dependencies, and make chat wait for review-summary readiness so one-time startup discovery cannot permanently omit it. Do not add the currently absent review stack to `deploy/docker-compose/docker-compose.yaml`; full root/deploy parity remains Phase 6 scope.

- [ ] **Step 6: Final self-review and commit**

Review metadata authority, order-assistant regression risk, Compose dependency direction, and the diff without running tests or builds, then commit:

```bash
git commit -m "feat(chat): connect review summary delegation"
```

---

## Final Review Checklist

- ReviewService author identity comes from authenticated metadata and users cannot mutate another user's review.
- Hotel and attraction details both list, create, update, and delete real reviews.
- Current-user review is counted once; service failures are not displayed as empty review lists.
- Hotel cards no longer render unconditional zero review counts; exact statistics are shown on details without list-page N+1 pagination.
- review-summary fetches ReviewService pages for both target types and retains Celery/MinIO/A2A/HTTP indexing boundaries.
- Rebuilds remove stale target data and query preflight rejects missing, partial, or stale snapshots.
- Review answers contain source evidence and distinguish all required states.
- User text cannot override page-controlled target metadata.
- Static summary is removed; index and A2A routes remain.
- Existing order-assistant delegation remains configured.
- No test or build commands were run.
