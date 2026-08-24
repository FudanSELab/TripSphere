# Phase 1 Service Discovery Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish consistent `gRPC_port` and `protocol=grpc` discovery metadata for every retained gRPC service and lock the contract with focused tests.

**Architecture:** Java services will declare discovery metadata in Spring config, while `trip-review-service` will inject the same contract in its Go Nacos registration wrapper. Tests stay local and config-driven: Spring Boot checks read the Environment, and Go checks a pure registration-parameter constructor without contacting Nacos. No protobuf, DB, UI, compose, or business-logic changes belong in this phase.

**Tech Stack:** Spring Boot, Spring Cloud Alibaba Nacos, Go 1.25.5, gRPC, JUnit 5, Testify, Maven Wrapper, `go test`

**Spec:** `docs/superpowers/specs/2026-08-24-tripsphere-systematic-refactor-design.md`

## Global Constraints

- Phase 1 only covers service discovery metadata.
- `gRPC_port=<actual grpc port>`
- `protocol=grpc`
- Do not change protobuf, DB schema, UI, compose, or business logic.
- Keep `trip-itinerary-service` in the same contract; it already has `gRPC_port` and only needs the missing `protocol` key.

## Execution Preflight

Run these checks before starting Task 1:

```bash
git status --short --branch
java -version
go version
for service in \
  trip-user-service \
  trip-attraction-service \
  trip-hotel-service \
  trip-product-service \
  trip-inventory-service \
  trip-order-service \
  trip-itinerary-service; do
  test -x "$service/mvnw"
done
```

Expected baseline:

- The existing user modification to `docs/服务改造清单.md` remains untouched.
- No service source, configuration, protobuf, compose, or generated file is modified before Task 1.
- Java 21 and the Maven Wrappers are available.
- Go is available before Task 4. If `go version` fails, stop before Task 4 and report the missing tool; do not install dependencies or widen the task.

The planned Phase 1 file scope is exactly 16 files: 8 existing configuration/registration files and 8 new focused test files. Any additional file requires a scope review before modification.

---

### Task 1: Add discovery metadata to user, attraction, and hotel

**Files:**
- Modify `trip-user-service/src/main/resources/application.yaml`
- Modify `trip-attraction-service/src/main/resources/application.yaml`
- Modify `trip-hotel-service/src/main/resources/application.yaml`
- Create `trip-user-service/src/test/java/org/tripsphere/user/DiscoveryMetadataTests.java`
- Create `trip-attraction-service/src/test/java/org/tripsphere/attraction/DiscoveryMetadataTests.java`
- Create `trip-hotel-service/src/test/java/org/tripsphere/hotel/DiscoveryMetadataTests.java`

**Interfaces:**
- Consumes: Spring `Environment` and `spring.cloud.nacos.discovery.metadata`
- Produces: `gRPC_port` and `protocol` metadata for ports `50056`, `50053`, and `50054`

- [ ] **Step 1: Add the minimal YAML config**

Add this block under the existing Nacos config in each service:

```yaml
spring:
  cloud:
    nacos:
      discovery:
        metadata:
          gRPC_port: ${grpc.server.port:50056}
          protocol: grpc
```

Use the matching port defaults: user `50056`, attraction `50053`, hotel `50054`.

- [ ] **Step 2: Add focused tests**

For all seven Java test files in Tasks 1-3, use these imports:

```java
import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.env.Environment;
```

Use this test body in each class:

```java
@SpringBootTest(properties = {
    "spring.cloud.nacos.discovery.enabled=false",
    "spring.cloud.nacos.discovery.register-enabled=false"
})
class DiscoveryMetadataTests {

    @Autowired
    private Environment environment;

    @Test
    void exposesGrpcDiscoveryMetadata() {
        assertThat(environment.getProperty("spring.cloud.nacos.discovery.metadata.gRPC_port"))
            .isEqualTo(environment.getProperty("grpc.server.port"));
        assertThat(environment.getProperty("spring.cloud.nacos.discovery.metadata.protocol"))
            .isEqualTo("grpc");
    }
}
```

Create the three classes with package declarations `org.tripsphere.user`, `org.tripsphere.attraction`, and `org.tripsphere.hotel` in their respective services.

- [ ] **Step 3: Run the targeted tests**

Run:

```bash
cd trip-user-service && ./mvnw -Dtest=DiscoveryMetadataTests test
cd trip-attraction-service && ./mvnw -Dtest=DiscoveryMetadataTests test
cd trip-hotel-service && ./mvnw -Dtest=DiscoveryMetadataTests test
```

Expected: all three focused tests pass.

- [ ] **Step 4: Run service build checks**

Run:

```bash
cd trip-user-service && ./mvnw test && ./mvnw -DskipTests package
cd trip-attraction-service && ./mvnw test && ./mvnw -DskipTests package
cd trip-hotel-service && ./mvnw test && ./mvnw -DskipTests package
```

- [ ] **Step 5: Commit**

```bash
git add trip-user-service/src/main/resources/application.yaml \
  trip-user-service/src/test/java/org/tripsphere/user/DiscoveryMetadataTests.java \
  trip-attraction-service/src/main/resources/application.yaml \
  trip-attraction-service/src/test/java/org/tripsphere/attraction/DiscoveryMetadataTests.java \
  trip-hotel-service/src/main/resources/application.yaml \
  trip-hotel-service/src/test/java/org/tripsphere/hotel/DiscoveryMetadataTests.java
git commit -m "fix(discovery): add grpc metadata to user attraction hotel"
```

---

### Task 2: Add discovery metadata to product, inventory, and order

**Files:**
- Modify `trip-product-service/src/main/resources/application-dev.yaml`
- Modify `trip-inventory-service/src/main/resources/application-dev.yaml`
- Modify `trip-order-service/src/main/resources/application-dev.yaml`
- Create `trip-product-service/src/test/java/org/tripsphere/product/DiscoveryMetadataTests.java`
- Create `trip-inventory-service/src/test/java/org/tripsphere/inventory/DiscoveryMetadataTests.java`
- Create `trip-order-service/src/test/java/org/tripsphere/order/DiscoveryMetadataTests.java`

**Interfaces:**
- Consumes: Spring `Environment` and existing `spring.cloud.nacos.discovery` blocks
- Produces: `gRPC_port` and `protocol` metadata for ports `50060`, `50061`, and `50062`

- [ ] **Step 1: Add the minimal YAML config**

Add this block under the existing Nacos discovery config in each service:

```yaml
spring:
  cloud:
    nacos:
      discovery:
        metadata:
          gRPC_port: ${grpc.server.port:50060}
          protocol: grpc
```

Use the matching port defaults: product `50060`, inventory `50061`, order `50062`.

- [ ] **Step 2: Add focused tests**

Add these imports to all three test files:

```java
import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.env.Environment;
```

Use this test body in each class, with package declarations `org.tripsphere.product`, `org.tripsphere.inventory`, and `org.tripsphere.order` in their respective services:

```java
@SpringBootTest(properties = {
    "spring.cloud.nacos.discovery.enabled=false",
    "spring.cloud.nacos.discovery.register-enabled=false"
})
class DiscoveryMetadataTests {

    @Autowired
    private Environment environment;

    @Test
    void exposesGrpcDiscoveryMetadata() {
        assertThat(environment.getProperty("spring.cloud.nacos.discovery.metadata.gRPC_port"))
            .isEqualTo(environment.getProperty("grpc.server.port"));
        assertThat(environment.getProperty("spring.cloud.nacos.discovery.metadata.protocol"))
            .isEqualTo("grpc");
    }
}
```

- [ ] **Step 3: Run the targeted tests**

Run:

```bash
cd trip-product-service && ./mvnw -Dtest=DiscoveryMetadataTests test
cd trip-inventory-service && ./mvnw -Dtest=DiscoveryMetadataTests test
cd trip-order-service && ./mvnw -Dtest=DiscoveryMetadataTests test
```

Expected: all three focused tests pass.

- [ ] **Step 4: Run service build checks**

Run:

```bash
cd trip-product-service && ./mvnw test && ./mvnw -DskipTests package
cd trip-inventory-service && ./mvnw test && ./mvnw -DskipTests package
cd trip-order-service && ./mvnw test && ./mvnw -DskipTests package
```

- [ ] **Step 5: Commit**

```bash
git add trip-product-service/src/main/resources/application-dev.yaml \
  trip-product-service/src/test/java/org/tripsphere/product/DiscoveryMetadataTests.java \
  trip-inventory-service/src/main/resources/application-dev.yaml \
  trip-inventory-service/src/test/java/org/tripsphere/inventory/DiscoveryMetadataTests.java \
  trip-order-service/src/main/resources/application-dev.yaml \
  trip-order-service/src/test/java/org/tripsphere/order/DiscoveryMetadataTests.java
git commit -m "fix(discovery): add grpc metadata to product inventory order"
```

---

### Task 3: Complete itinerary discovery metadata

**Files:**
- Modify `trip-itinerary-service/src/main/resources/application.yaml`
- Create `trip-itinerary-service/src/test/java/org/tripsphere/itinerary/DiscoveryMetadataTests.java`

**Interfaces:**
- Consumes: Spring `Environment` and the existing itinerary discovery config
- Produces: `gRPC_port` and `protocol` metadata for port `50052`

- [ ] **Step 1: Add the minimal YAML config**

Extend the existing block in `trip-itinerary-service/src/main/resources/application.yaml`:

```yaml
spring:
  cloud:
    nacos:
      discovery:
        metadata:
          gRPC_port: ${grpc.server.port:50052}
          protocol: grpc
```

- [ ] **Step 2: Add a focused test**

Add these imports:

```java
import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.env.Environment;
```

```java
@SpringBootTest(properties = {
    "spring.cloud.nacos.discovery.enabled=false",
    "spring.cloud.nacos.discovery.register-enabled=false"
})
class DiscoveryMetadataTests {

    @Autowired
    private Environment environment;

    @Test
    void exposesGrpcDiscoveryMetadata() {
        assertThat(environment.getProperty("spring.cloud.nacos.discovery.metadata.gRPC_port"))
            .isEqualTo(environment.getProperty("grpc.server.port"));
        assertThat(environment.getProperty("spring.cloud.nacos.discovery.metadata.protocol"))
            .isEqualTo("grpc");
    }
}
```

- [ ] **Step 3: Run the targeted test**

Run:

```bash
cd trip-itinerary-service && ./mvnw -Dtest=DiscoveryMetadataTests test
```

- [ ] **Step 4: Run service build checks**

Run:

```bash
cd trip-itinerary-service && ./mvnw test && ./mvnw -DskipTests package
```

- [ ] **Step 5: Commit**

```bash
git add trip-itinerary-service/src/main/resources/application.yaml \
  trip-itinerary-service/src/test/java/org/tripsphere/itinerary/DiscoveryMetadataTests.java
git commit -m "fix(discovery): complete itinerary grpc metadata"
```

---

### Task 4: Add Nacos metadata to review-service registration

**Files:**
- Modify `trip-review-service/pkg/nacos/register.go`
- Create `trip-review-service/pkg/nacos/register_test.go`

**Interfaces:**
- Consumes: `vo.RegisterInstanceParam` and the existing `Client.RegisterInstance` wrapper
- Produces: Nacos registration metadata with `gRPC_port` and `protocol` for `trip-review-service`

- [ ] **Step 1: Implement the minimal metadata injection**

Add `strconv` to the imports and add this small unexported constructor in `trip-review-service/pkg/nacos/register.go`:

```go
func newRegisterInstanceParam(serviceName, registerIP string, port uint64) vo.RegisterInstanceParam {
    return vo.RegisterInstanceParam{
        Ip:          registerIP,
        Port:        port,
        ServiceName: serviceName,
        Weight:      1,
        Enable:      true,
        Healthy:     true,
        Ephemeral:   true,
        Metadata: map[string]string{
            "gRPC_port": strconv.FormatUint(port, 10),
            "protocol":  "grpc",
        },
    }
}
```

Call `newRegisterInstanceParam(serviceName, registerIP, port)` from `Register`. Keep the existing IP discovery and `RegisterInstance` call intact.

- [ ] **Step 2: Add a focused test**

```go
package nacos

import (
    "testing"

    "github.com/stretchr/testify/require"
)

func TestRegisterInstanceParamIncludesDiscoveryMetadata(t *testing.T) {
    param := newRegisterInstanceParam("trip-review-service", "127.0.0.1", 50057)

    require.Equal(t, "trip-review-service", param.ServiceName)
    require.Equal(t, uint64(50057), param.Port)
    require.Equal(t, map[string]string{
        "gRPC_port": "50057",
        "protocol":  "grpc",
    }, param.Metadata)
}
```

The test stays independent of the Nacos SDK network client. It verifies the exact registration value that `Register` passes to `RegisterInstance`.

- [ ] **Step 3: Run the targeted test**

Run:

```bash
cd trip-review-service && go test ./pkg/nacos -run TestRegisterInstanceParamIncludesDiscoveryMetadata -v
```

- [ ] **Step 4: Run service build checks**

Run:

```bash
cd trip-review-service && go test ./... && go build ./cmd/server
```

- [ ] **Step 5: Commit**

```bash
git add trip-review-service/pkg/nacos/register.go \
  trip-review-service/pkg/nacos/register_test.go
git commit -m "fix(discovery): add nacos metadata to review service"
```

---

### Phase 1 Completion Gate

- [ ] **Step 1: Run the complete affected-service verification**

Run:

```bash
for service in \
  trip-user-service \
  trip-attraction-service \
  trip-hotel-service \
  trip-product-service \
  trip-inventory-service \
  trip-order-service \
  trip-itinerary-service; do
  (cd "$service" && ./mvnw test && ./mvnw -DskipTests package)
done

cd trip-review-service
go test ./...
go vet ./...
go build ./cmd/server
```

Java has no separate repository lint task in the current Taskfiles, so Maven compilation/tests and package are the required Java type/build checks for this phase. Go uses `go vet` in addition to tests and build. No `bun` or `uv` command is required because Phase 1 does not touch frontend or Python files.

- [ ] **Step 2: Run the optional live discovery smoke test**

If a local Nacos server is already available at `http://localhost:8848`, run the existing review-service check:

```bash
cd trip-review-service && ./scripts/test-nacos.sh
```

If Nacos is unavailable, record the smoke test as not run; do not modify compose or start unrelated infrastructure as part of this phase.

- [ ] **Step 3: Inspect the complete phase diff**

Run:

```bash
phase_base=$(sed -n 's/^BASE: //p' .superpowers/sdd/2026-08-24-phase-1-service-discovery-baseline/progress.md | head -n 1)
test -n "$phase_base"
git diff --check "$phase_base" HEAD
git diff --stat "$phase_base" HEAD
git diff --name-only "$phase_base" HEAD
git status --short --branch
```

Expected changed paths are exactly the 16 files listed in Tasks 1-4, plus no generated, protobuf, compose, database, frontend, Python, or unrelated documentation files. Review the full diff and confirm that the existing `docs/服务改造清单.md` user change is not included in any Phase 1 commit.

- [ ] **Step 4: Self-review and PR handoff**

Confirm:

- Every retained gRPC service has the exact metadata keys `gRPC_port` and `protocol`.
- Each `gRPC_port` resolves from that service's `grpc.server.port` with the current default.
- `trip-review-service` uses the new constructor from `Register`.
- No business request, response, persistence, or runtime dependency changed.
- The PR description includes changes, rationale, affected services, test/build results, optional smoke-test status, risks, breaking changes, and Phase 2 follow-up.

## Phase 1 Exit Criteria

- All retained gRPC services publish `gRPC_port` and `protocol=grpc` through their discovery path.
- `trip-itinerary-service` keeps its existing `gRPC_port` and adds `protocol=grpc`.
- `trip-review-service` registers the same contract through Go Nacos registration.
- Focused tests pass in each touched service.
- Service builds pass in each touched service.
- `git diff --check`, `git status`, and scoped diff review are clean before any commit.

## Phase 1 Scope Guard

If any step reveals a need to touch protobuf, business logic, compose, deploy infra, or the next phase's auth/order/review work, stop and escalate instead of widening this plan.
