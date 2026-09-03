# TripSphere Phase 5 Order Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the hotel SKU order flow across the frontend, order assistant, order service, and inventory lifecycle while enforcing ownership, durable idempotency, and truthful failure handling.

**Architecture:** Keep the existing Next.js Server Action, gRPC, A2A, Nacos, Product/Inventory/Order, and in-process draft boundaries. Add trusted request identity at the order-service gRPC edge, persist user-scoped request ids with orders, and make frontend and agent callers reuse the existing contracts with authenticated metadata.

**Tech Stack:** Java 21, Spring Boot, Maven Wrapper, PostgreSQL/JPA, Redis, Python with `uv`, Google ADK/A2A, Next.js 16, React 19, TypeScript, Zod, protobuf/gRPC, Shadcn UI.

**Spec:** `docs/superpowers/specs/2026-08-30-phase-5-order-loop-design.md`

## Global Constraints

- Implement only Phase 5 from `docs/服务改造清单.md`; do not modify Compose, observability, service deletion, or Phase 6/7 scope.
- Keep existing protobuf service and message shapes unchanged.
- `ConfirmPayment` is simulated payment with `payment_method="mock"` and ends at `PAID`.
- Keep order-assistant drafts in process memory for this single-instance phase.
- Do not add a real payment provider, message broker, shared draft store, Outbox, refund flow, or `COMPLETED` workflow.
- Per the user's instruction, do not create, modify, or run automated tests. Do not run build, lint, unit, integration, or smoke-test commands.
- Verification is limited to code-level review, formatter-safe edits, targeted source searches, `git diff --check`, and full diff inspection.
- Do not commit this implementation plan. Leave implementation commits to an explicit user request.
- Follow repository tooling rules if a formatting command is needed: frontend uses `bun -b`, Python uses `uv`, Java uses `./mvnw`.

---

### Task 1: Enforce Authenticated Order Ownership

**Files:**
- Create: `trip-order-service/src/main/java/org/tripsphere/order/infrastructure/security/GrpcAuthContext.java`
- Create: `trip-order-service/src/main/java/org/tripsphere/order/infrastructure/security/AuthInterceptor.java`
- Create: `trip-order-service/src/main/java/org/tripsphere/order/application/exception/UnauthenticatedException.java`
- Create: `trip-order-service/src/main/java/org/tripsphere/order/application/exception/PermissionDeniedException.java`
- Create: `trip-order-service/src/main/java/org/tripsphere/order/application/service/OrderAuthorizationService.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/infrastructure/adapter/inbound/grpc/OrderGrpcService.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/infrastructure/adapter/inbound/grpc/advice/GrpcExceptionAdvice.java`
- Modify: order query/cancel/payment use cases under `trip-order-service/src/main/java/org/tripsphere/order/application/service/`

**Interfaces:**
- Consumes: gRPC metadata keys `x-user-id`, `x-user-roles`, and `authorization`.
- Produces: `GrpcAuthContext.current()` and ownership-checked user-facing use-case entry points.

- [x] **Step 1: Add the request auth context and interceptor**

Mirror the established itinerary-service pattern. The context must expose the authenticated user and default to anonymous:

```java
public final class GrpcAuthContext {
    private static final Context.Key<GrpcAuthContext> AUTH_CONTEXT_KEY = Context.key("auth-context");
    private static final Metadata.Key<String> USER_ID_KEY =
            Metadata.Key.of("x-user-id", Metadata.ASCII_STRING_MARSHALLER);

    public static GrpcAuthContext fromMetadata(Metadata metadata) {
        return new GrpcAuthContext(metadata.get(USER_ID_KEY));
    }

    public static GrpcAuthContext current() {
        GrpcAuthContext context = AUTH_CONTEXT_KEY.get();
        return context != null ? context : anonymous();
    }
}
```

The global interceptor must attach the parsed context to the gRPC call without logging authorization values.

- [x] **Step 2: Add authorization exceptions and policy service**

Implement focused policy methods:

```java
public String requireAuthenticated(GrpcAuthContext authContext);
public String requireRequestedUser(GrpcAuthContext authContext, String requestedUserId);
public void requireOrderOwner(String currentUserId, Order order);
```

Missing identity maps to `UNAUTHENTICATED`; a mismatched requested user or order owner maps to `PERMISSION_DENIED`.

- [x] **Step 3: Apply ownership at every gRPC entry**

Use the authenticated user for create and list, and pass it to owned query/mutation use cases:

```java
String currentUserId = authorizationService.requireAuthenticated(GrpcAuthContext.current());
authorizationService.requireRequestedUser(GrpcAuthContext.current(), request.getUserId());
Order order = cancelOrderUseCase.executeForUser(currentUserId, request.getOrderId(), request.getReason());
```

`GetOrder`, `GetOrderByNo`, `CancelOrder`, and `ConfirmPayment` must load the order and verify ownership before returning data or invoking inventory. Keep an internal cancellation path for `OrderExpiryScheduler` that does not depend on gRPC metadata.

- [x] **Step 4: Review the identity boundary**

Confirm by source inspection that no public order RPC can read or mutate an order before authenticating and checking ownership, and that scheduler cancellation still has an explicit internal entry point.

---

### Task 2: Make Order Creation And Inventory Transitions Truthful

**Files:**
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/domain/model/Order.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/infrastructure/adapter/outbound/persistence/entity/OrderEntity.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/infrastructure/adapter/outbound/persistence/mapper/OrderEntityMapper.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/infrastructure/adapter/outbound/persistence/OrderJpaRepository.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/infrastructure/adapter/outbound/persistence/OrderRepositoryImpl.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/application/port/OrderRepository.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/application/port/OrderCachePort.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/infrastructure/adapter/outbound/cache/RedisOrderCacheAdapter.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/application/service/command/CreateOrderUseCase.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/application/service/command/CancelOrderUseCase.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/application/service/command/ConfirmPaymentUseCase.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/application/service/OrderValidationService.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/application/service/OrderItemAssembler.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/application/dto/SpuInfo.java`
- Modify: `trip-order-service/src/main/java/org/tripsphere/order/infrastructure/adapter/outbound/grpc/ProductGrpcAdapter.java`

**Interfaces:**
- Consumes: `CreateOrderCommand.requestId()`, Product SKU/SPU status, Inventory daily prices and lock APIs.
- Produces: database-backed `findByUserIdAndRequestId`, strict sale validation, and failure-propagating cancel/payment flows.

- [x] **Step 1: Persist user-scoped request ids**

Add `requestId` to the domain and entity. Define a composite unique constraint while allowing legacy null request ids:

```java
@Table(
        name = "orders",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_orders_user_request_id",
                columnNames = {"userId", "requestId"}))
```

Add `Optional<Order> findByUserIdAndRequestId(String userId, String requestId)` through the JPA adapter and include `requestId` in both mapper directions.

- [x] **Step 2: Make Redis idempotency user-scoped and secondary**

Change cache signatures and keys to include the user:

```java
Optional<String> getIdempotentOrderId(String userId, String requestId);
void saveIdempotentOrderId(String userId, String requestId, String orderId, long ttlSeconds);
```

In `CreateOrderUseCase`, accept a cache hit only when the loaded order matches both user and request id, then query the database as the authoritative fallback. Persist `requestId` on the new order and cache the mapping only after save.

- [x] **Step 3: Validate contacts, dates, SKU and SPU sale state**

Reject missing contact name/phone/email, invalid email, past dates, inactive SKUs, absent SPUs, off-shelf SPUs, unsupported resource types, and invalid hotel/attraction date shapes. Extend `SpuInfo` with an `active` flag mapped from `SPU_STATUS_ON_SHELF`.

```java
if (command.contact() == null || command.contact().name().isBlank()) {
    throw new InvalidArgumentException("Contact name is required");
}
if (item.date().isBefore(LocalDate.now())) {
    throw new InvalidArgumentException("Order date must not be in the past");
}
```

- [x] **Step 4: Require Inventory prices**

Remove the base-price fallback from `OrderItemAssembler`. Every requested inventory date must have a positive actual price; downstream query failure or a missing day must throw and let `CreateOrderUseCase` release the acquired lock.

```java
Money price = priceCache.get(sku.id() + ":" + date);
if (price == null) {
    throw new InvalidArgumentException("Inventory price not found for SKU " + sku.id() + " on " + date);
}
```

- [x] **Step 5: Preflight state before inventory mutation**

Expose non-mutating domain checks such as `validateCanCancel()` and `validateCanConfirmPayment()`. Call them before ReleaseLock/ConfirmLock, then mutate and save only after every inventory call succeeds.

Cancellation must propagate an inventory release failure as `OrderStateException`; it must not log-and-continue. Payment must reject expired/non-pending orders before confirming locks.

- [x] **Step 6: Review persistence and transition ordering**

Trace duplicate create, normal create, missing price, cancel failure, and payment failure through the source. Confirm each path either returns the existing order or preserves order/inventory truth without a false success response.

---

### Task 3: Complete Order Assistant Draft And Payment Tools

**Files:**
- Create: `trip-order-assistant/src/order_assistant/tools/context.py`
- Modify: `trip-order-assistant/src/order_assistant/tools/order.py`
- Modify: `trip-order-assistant/src/order_assistant/tools/order_draft.py`
- Modify: `trip-order-assistant/src/order_assistant/agent.py`
- Modify: `trip-order-assistant/src/order_assistant/agent.json`

**Interfaces:**
- Consumes: A2A metadata stored in `tool_context.state["headers"]` and existing Product/Order gRPC stubs.
- Produces: owner-checked draft lifecycle and authenticated get/cancel/pay gRPC calls.

- [x] **Step 1: Centralize outgoing metadata conversion**

Convert stored headers into gRPC metadata and pass it to every OrderService call:

```python
def _grpc_metadata(tool_context: ToolContext) -> tuple[tuple[str, str], ...]:
    headers = tool_context.state.get("headers", {})
    return tuple(
        (key, value)
        for key, value in (
            ("x-user-id", headers.get("user_id")),
            ("x-user-roles", headers.get("user_roles")),
            ("authorization", headers.get("authorization")),
        )
        if value
    )
```

Add `tool_context: ToolContext` to get-by-id, get-by-number, cancel, and confirm-payment tools.

- [x] **Step 2: Enforce draft ownership and stable state**

Store `request_id`, `confirmed=False`, contact, items, source, and owner at creation. Add one helper that returns a draft only when the current `tool_context` user owns it; use it for every read and mutation.

Any item/contact mutation resets `confirmed` to false. Validate ISO dates and positive quantity before contacting ProductService.

- [x] **Step 3: Add contact and confirmation tools**

Add `set_order_draft_contact(order_draft_id, name, phone, email, tool_context)` and `confirm_order_draft(order_draft_id, tool_context)`. Confirmation requires complete contact information and at least one item.

- [x] **Step 4: Make submission idempotent and cleanup successful drafts**

`submit_order_draft` must reject unconfirmed drafts, send the draft's stable request id and authenticated metadata, retain the draft on failure, and delete it only after a successful response.

- [x] **Step 5: Add simulated payment and capability descriptions**

Add `confirm_payment(order_id, tool_context)` calling `ConfirmPayment` with `payment_method="mock"`. Update instruction ordering and AgentCard skills/output description so the published capability matches creation, query, cancellation, and payment tools.

- [x] **Step 6: Review every tool result path**

Confirm that no tool returns `status="success"` after a gRPC failure, that no draft operation omits owner validation, and that no authorization header value is logged.

---

### Task 4: Add Authenticated Frontend Order Mutations

**Files:**
- Modify: `trip-next-frontend/actions/order.ts`

**Interfaces:**
- Consumes: server session, `getAuthMetadata()`, generated OrderService client.
- Produces: typed `createOrder`, `cancelOrder`, and `confirmPayment` action results.

- [x] **Step 1: Define and validate action inputs**

Use Zod to validate UUID request id, SKU, ISO dates, positive integer quantity, non-empty contact name/phone, and email. Never accept a user id from the client input.

```typescript
const createOrderSchema = z.object({
  requestId: z.uuid(),
  skuId: z.string().trim().min(1),
  checkInDate: z.iso.date(),
  checkOutDate: z.iso.date(),
  quantity: z.number().int().positive(),
  contact: z.object({
    name: z.string().trim().min(1),
    phone: z.string().trim().min(1),
    email: z.email(),
  }),
});
```

- [x] **Step 2: Implement authenticated creation**

Load `getSession()` inside the action, reject anonymous callers, set `x-user-id` explicitly on metadata, translate ISO dates to generated protobuf Date shapes, and call `CreateOrder` with `source.channel="web"`.

- [x] **Step 3: Implement truthful cancel and simulated payment results**

Require a server session for cancel and payment, set authenticated metadata, revalidate `/orders` only on success, and return the backend error message on failure.

- [x] **Step 4: Review the Server Action trust boundary**

Confirm every mutation authenticates inside the action as required by the local Next.js 16 forms guide, and no client-provided owner value reaches the backend.

---

### Task 5: Build The Hotel Booking Dialog And Payment UI

**Files:**
- Create: `trip-next-frontend/components/hotel-detail/hotel-booking-dialog.tsx`
- Modify: `trip-next-frontend/components/hotel-detail/sku-row.tsx`
- Modify: `trip-next-frontend/components/hotel-detail/room-type-card.tsx`
- Modify: `trip-next-frontend/components/hotel-detail/hotel-room-list.tsx`
- Modify: `trip-next-frontend/components/orders/order-card.tsx`

**Interfaces:**
- Consumes: SKU id/name/price, default dates, optional session contact defaults, and frontend order actions.
- Produces: accessible booking dialog and visible cancel/payment state feedback.

- [x] **Step 1: Pass safe booking defaults from the server component**

`HotelRoomList` loads the optional session once, derives local `YYYY-MM-DD` defaults for today/tomorrow, and passes only name/email defaults plus login state through RoomTypeCard/SkuRow. Do not expose the JWT.

- [x] **Step 2: Implement the booking dialog**

Use existing Shadcn Dialog, Input, Label, Button, and Spinner components. Generate one `crypto.randomUUID()` per submitted attempt, disable controls while pending, validate checkout after check-in in the client for immediate feedback, and call the Server Action for authoritative validation.

```typescript
const result = await createOrder({
  requestId: crypto.randomUUID(),
  skuId,
  checkInDate,
  checkOutDate,
  quantity,
  contact: { name, phone, email },
});
```

On success close the dialog and `router.push("/orders")`; on failure keep the form open and render an `aria-live="polite"` error. Anonymous users are sent to `/signin` when selecting “预订”.

- [x] **Step 3: Connect payment and improve mutation feedback**

In `OrderCard`, keep cancel/pay actions limited to `PENDING_PAYMENT`, disable both buttons while either mutation runs, display the returned error inline, and call `router.refresh()` after success.

- [x] **Step 4: Review accessibility and component boundaries**

Confirm every input has a label, errors use an aria-live region, Dialog title/description are present, loading buttons remain readable, and server-only session/grpc imports do not cross into Client Components.

---

### Task 6: Perform Code-Level Phase Review

**Files:**
- Review: all files changed by Tasks 1-5
- Review: `docs/superpowers/specs/2026-08-30-phase-5-order-loop-design.md`
- Review: `docs/服务改造清单.md:127-138`

**Interfaces:**
- Consumes: complete Phase 5 diff.
- Produces: reviewed, untested implementation with explicit residual risks.

- [x] **Step 1: Inspect changed paths and scope**

Run read-only source/diff checks:

```bash
git status --short
git diff --name-only
git diff --stat
```

Expected paths are limited to the design/plan documents and the frontend, order-assistant, and order-service files listed above. Inventory service remains unchanged unless a newly discovered correctness defect requires a documented scope update.

- [x] **Step 2: Search for incomplete Phase 5 markers and leaked secrets**

```bash
rg -n "TODO|NotImplemented|confirm_payment|request_id|x-user-id|authorization" \
  trip-order-service/src/main trip-order-assistant/src trip-next-frontend/actions trip-next-frontend/components
```

Review matches manually. Authorization values must never be logged; Phase 5 TODOs in changed paths must be resolved or explicitly reported.

- [x] **Step 3: Check patch integrity without running tests**

```bash
git diff --check
git diff
```

Do not run compilation, lint, unit, integration, or smoke tests. Record that runtime correctness remains unverified by explicit user instruction.

- [x] **Step 4: Report completion and remaining plan**

Summarize implemented flows, code-review findings, files changed, the absence of test evidence, and the remaining Phase 6/7 work. Do not claim the code passes tests or runs successfully.
