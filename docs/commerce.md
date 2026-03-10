# TripSphere 商品订单域技术方案

## 1. 概述

### 1.1 背景

TripSphere 是一个 AI-Native 的在线旅游服务系统。现有信息展示层服务（景点、酒店、POI 等）已基本完成，
需要新增**商品 → 库存 → 订单**的交易能力，让 AI Agent 不仅能"读"，还能代用户"写"——完成查价、下单、
支付确认等闭环操作。

### 1.2 设计目标

- **三服务拆分**：Product / Inventory / Order 独立部署，通过 gRPC 通信
- **静态与动态分离**：Product 管理不变的商品规则，Inventory 管理按日变化的库存和价格
- **分布式事务**：通过库存锁定 → 确认/释放机制保障跨服务数据一致性
- **Agent 可调用**：所有 gRPC 接口可封装为 MCP Tools，供 Agent 编排调用

### 1.3 技术栈

| 层面     | 选型                               | 版本                   |
| -------- | ---------------------------------- | ---------------------- |
| 语言     | Java                               | 21                     |
| 框架     | Spring Boot                        | 3.5.x                  |
| 微服务   | Spring Cloud Alibaba + Nacos       | 2025.0.x               |
| RPC      | gRPC + grpc-spring-boot-starter    | 1.78.0 / 3.1.0.RELEASE |
| 序列化   | Protobuf                           | 4.33.x                 |
| 对象映射 | MapStruct + protobuf-spi-impl      | 1.6.3                  |
| 代码规范 | Spotless (Google Java Format AOSP) | 2.43.0                 |

### 1.4 数据库选型

| 服务                   | 主存储  | 辅助存储         | 选型理由                                                                             |
| ---------------------- | ------- | ---------------- | ------------------------------------------------------------------------------------ |
| trip-product-service   | MongoDB | —                | SPU/SKU 属性灵活多变，`Struct` 字段天然适合文档模型；与现有 poi/itinerary 等服务一致 |
| trip-inventory-service | MySQL   | Redis (只读缓存) | 库存扣减需要行级锁和事务保障，MySQL 是唯一写入源；Redis 仅作为读缓存加速查询         |
| trip-order-service     | MySQL   | Redis            | 订单需要强事务一致性；Redis 用于订单号序列、超时关闭延迟队列、下单去重               |

> **设计决策 — MySQL-first 库存策略**: 所有库存变更通过 MySQL 行锁保证原子性，Redis 在 MySQL 事务提交后
> 以 best-effort 方式同步缓存。这牺牲了极端高并发下的锁定吞吐量，但在 MVP 阶段彻底消除了双写一致性问题。
> 未来可切换为 Redis + MySQL 异步落盘 + 补偿机制。

## 2. 领域模型

### 2.1 三服务职责划分

```mermaid
flowchart LR
    subgraph Product["trip-product-service"]
        P["SPU/SKU 定义与 CRUD<br/>基础价格 (参考价)<br/>商品上下架状态<br/>灵活属性 (Struct)<br/><br/>数据特征: 静态、低频写<br/>存储: MongoDB"]
    end

    subgraph Inventory["trip-inventory-service"]
        I["日历库存/价格管理<br/>库存锁定 / 确认 / 释放<br/>可用性查询<br/>锁定超时自动释放<br/><br/>数据特征: 动态、高频读写<br/>存储: MySQL + Redis"]
    end

    subgraph Order["trip-order-service"]
        O["订单生命周期<br/>订单创建 (Saga 编排)<br/>支付确认 (模拟)<br/>订单取消与回滚<br/>订单查询<br/><br/>数据特征: 事务性、状态机<br/>存储: MySQL + Redis"]
    end
```

### 2.2 与现有服务的关联

```mermaid
flowchart TB
    subgraph Existing["现有信息服务 (只读数据源)"]
        Hotel["trip-hotel-service<br/>(酒店基础信息)"]
        Attraction["trip-attraction-service<br/>(景点基础信息)"]
        POI["trip-poi-service<br/>(地点信息)"]
    end

    subgraph Product["trip-product-service"]
        SPU["SPU<br/>resource_type + resource_id"]
    end

    Hotel -- "resource_id" --> SPU
    Attraction -- "resource_id" --> SPU
    SPU -- "HOTEL_ROOM<br/>hotel_room_123" --> Hotel
    SPU -- "ATTRACTION<br/>attraction_456" --> Attraction
```

SPU 通过 `resource_type` + `resource_id` 关联到酒店或景点，前端展示时可聚合两侧数据。

## 3. 接口设计

### 3.1 trip-product-service

**Proto 文件**: `contracts/protobuf/tripsphere/product/v1/product.proto`

#### 核心模型

| 模型           | 说明                                                                       |
| -------------- | -------------------------------------------------------------------------- |
| `Spu`          | 商品单元，关联一个业务资源 (酒店房型/景点)，包含名称、描述、图片、灵活属性 |
| `Sku`          | 销售单元，挂在 SPU 下，代表一个具体可售规格，含 `base_price` 参考价        |
| `ResourceType` | `HOTEL_ROOM` / `ATTRACTION`                                                |
| `SpuStatus`    | `DRAFT` → `ON_SHELF` → `OFF_SHELF` / `DELETED`                             |
| `SkuStatus`    | `ACTIVE` / `INACTIVE` / `DELETED`                                          |

#### gRPC 接口

| RPC                  | 说明                                              |
| -------------------- | ------------------------------------------------- |
| `CreateSpu`          | 创建 SPU（可同时带 SKU）                          |
| `BatchCreateSpus`    | 批量创建                                          |
| `GetSpuById`         | 查询 SPU 详情（含嵌套 SKU）                       |
| `BatchGetSpus`       | 批量查询 SPU                                      |
| `ListSpusByResource` | 按 resource_type + resource_id 查询 SPU 列表      |
| `UpdateSpu`          | 部分更新 (FieldMask)                              |
| `GetSkuById`         | 按 ID 查询单个 SKU（供 Order/Inventory 服务调用） |
| `BatchGetSkus`       | 批量查询 SKU                                      |

#### 数据示例

```
SPU:
  id: "spu_001"
  name: "故宫博物院门票"
  resource_type: ATTRACTION
  resource_id: "attraction_gugong"
  status: ON_SHELF
  skus:
    - id: "sku_001", name: "成人票", base_price: ¥60, status: ACTIVE
    - id: "sku_002", name: "学生票", base_price: ¥20, status: ACTIVE

SPU:
  id: "spu_002"
  name: "北京饭店 - 标准双床房"
  resource_type: HOTEL_ROOM
  resource_id: "hotel_bj_001"
  status: ON_SHELF
  skus:
    - id: "sku_003", name: "含早", base_price: ¥580, status: ACTIVE
    - id: "sku_004", name: "不含早", base_price: ¥520, status: ACTIVE
```

### 3.2 trip-inventory-service

**Proto 文件**: `contracts/protobuf/tripsphere/inventory/v1/inventory.proto`

#### 核心模型

| 模型             | 说明                                                                                 |
| ---------------- | ------------------------------------------------------------------------------------ |
| `DailyInventory` | 一条 (sku_id, date) 记录，包含 total / available / locked / sold 四个数量 + 当日价格 |
| `InventoryLock`  | 一次锁定操作，包含多个 LockItem，关联 order_id，有超时时间                           |
| `LockItem`       | 锁定的最小粒度：(sku_id, date, quantity)                                             |
| `LockStatus`     | `LOCKED` → `CONFIRMED` / `RELEASED` / `EXPIRED`                                      |

**表关系**: `inventory_lock 1 ──▶ N inventory_lock_item`。
一个 lock 代表一次原子锁定操作（关联一个订单），每个 lock_item 是被锁定的一个 (sku_id, date, quantity) 元组。

#### gRPC 接口

| RPC                      | 类型 | 说明                                                 |
| ------------------------ | ---- | ---------------------------------------------------- |
| `SetDailyInventory`      | 管理 | 设置某 SKU 某天的总库存和价格 (Upsert)               |
| `BatchSetDailyInventory` | 管理 | 批量设置                                             |
| `GetDailyInventory`      | 查询 | 查询单个 (sku, date) 的库存与价格                    |
| `QueryInventoryCalendar` | 查询 | 查询日期区间的库存日历                               |
| `CheckAvailability`      | 查询 | 快速检查 (sku, date, qty) 是否可售                   |
| `LockInventory`          | 事务 | 原子锁定一组 (sku, date, qty)，全部成功或全部失败    |
| `ConfirmLock`            | 事务 | 支付成功后确认锁定，locked → sold（**幂等**）        |
| `ReleaseLock`            | 事务 | 取消或超时后释放锁定，locked → available（**幂等**） |

#### 库存数量关系

```
total_quantity = available_quantity + locked_quantity + sold_quantity
```

- `SetDailyInventory` 设置 `total_quantity`，系统自动计算 `available = total - locked - sold`
- `LockInventory`: `available -= qty`, `locked += qty`
- `ConfirmLock`: `locked -= qty`, `sold += qty`
- `ReleaseLock`: `locked -= qty`, `available += qty`

### 3.3 trip-order-service

**Proto 文件**: `contracts/protobuf/tripsphere/order/v1/order.proto`

#### 核心模型

| 模型          | 说明                                                          |
| ------------- | ------------------------------------------------------------- |
| `Order`       | 订单主体，包含订单项列表、联系人、总金额、来源、时间线        |
| `OrderItem`   | 订单项，快照商品信息 + 日期 + 数量 + 价格 + inventory_lock_id |
| `ContactInfo` | 联系人 (name / phone / email)                                 |
| `OrderSource` | 订单来源 (channel / agent_id / session_id)，区分人工和 Agent  |
| `OrderStatus` | `PENDING_PAYMENT` → `PAID` → `COMPLETED` / `CANCELLED`        |

#### gRPC 接口

| RPC              | 说明                                                    |
| ---------------- | ------------------------------------------------------- |
| `CreateOrder`    | 创建订单，内部编排 Saga（校验商品 → 锁库存 → 生成订单） |
| `GetOrder`       | 查询订单详情                                            |
| `ListUserOrders` | 查询用户订单列表（支持按状态过滤、分页）                |
| `CancelOrder`    | 取消订单（释放库存锁定）                                |
| `ConfirmPayment` | 模拟支付确认（确认库存锁定）                            |

## 4. 核心流程

### 4.1 下单流程 (CreateOrder Saga)

Order Service 作为 Saga 编排者，依次调用 Product 和 Inventory 服务。
gRPC 跨服务调用在 DB 事务之外执行，仅本地建单在事务中完成，避免长事务持有数据库连接。

```mermaid
sequenceDiagram
    participant C as Client / Agent
    participant O as Order Service (Saga Orchestrator)
    participant P as Product Service
    participant I as Inventory Service

    C->>O: CreateOrder(user_id, items, contact, source)
    Note over O: Step 0: 去重检查<br/>(Redis, 10s 窗口, fail-open)

    O->>P: Step 1: BatchGetSkus + BatchGetSpus
    P-->>O: 校验 SKU 状态，获取商品快照

    O->>I: Step 2: LockInventory(items, order_id)
    I-->>O: 返回 InventoryLock (lock_id)
    Note over O,I: ⚠ 基于 order_id 幂等<br/>⚠ 酒店类: 自动展开日期范围 (见 §7.4)

    O->>I: Step 2.5: QueryInventoryCalendar(sku, date_range)
    I-->>O: 返回每日价格 (按 SKU 批量查询)

    Note over O: Step 3: 本地创建 Order (事务)<br/>填入商品快照、实际价格、lock_id<br/>status = PENDING_PAYMENT<br/>expire_at = now + 15min

    O-->>C: 返回 Order
```

**补偿逻辑**: 如果 Step 3 (本地建单) 失败，则调用 `ReleaseLock` 释放已锁定的库存。

### 4.2 支付确认流程

```mermaid
sequenceDiagram
    participant C as Client / Agent
    participant O as Order Service
    participant I as Inventory Service

    C->>O: ConfirmPayment(order_id, payment_method)
    Note over O: ① 校验 status == PENDING_PAYMENT && 未过期

    O->>I: ② ConfirmLock(lock_id)
    I-->>O: locked → sold (幂等，见 §7.5)

    Note over O: ③ UPDATE Order → status = PAID
    O-->>C: 返回更新后的 Order
```

### 4.3 取消订单流程

```mermaid
sequenceDiagram
    participant C as Client / Agent
    participant O as Order Service
    participant I as Inventory Service

    C->>O: CancelOrder(order_id, reason)
    Note over O: ① 校验 status == PENDING_PAYMENT<br/>(已支付的订单取消需走退款，MVP 暂不支持)

    O->>I: ② ReleaseLock(lock_id, reason)
    I-->>O: locked → available (幂等，见 §7.5)

    Note over O: ③ UPDATE Order → status = CANCELLED
    O-->>C: 返回更新后的 Order
```

### 4.4 订单超时自动关闭

下单时将 order_id 写入 Redis Sorted Set（score = 过期时间戳），定时任务每 30s 扫描过期订单并调用 `CancelOrder`。
每次扫描批量上限 50 个，防止瞬时负载过高。库存侧同理，锁定超时也通过 Sorted Set + 定时任务释放。

### 4.5 订单状态机

```mermaid
stateDiagram-v2
    [*] --> PENDING_PAYMENT : 创建订单
    PENDING_PAYMENT --> PAID : 支付成功
    PENDING_PAYMENT --> CANCELLED : 超时 / 用户取消
    PAID --> COMPLETED : 核销 / 完成
    CANCELLED --> [*]
    COMPLETED --> [*]
```

## 5. 数据库设计

### 5.1 trip-product-service (MongoDB)

```
Collection: spus
{
  _id: ObjectId,
  name: String,
  description: String,
  resource_type: String,          // "HOTEL_ROOM" | "ATTRACTION"
  resource_id: String,            // 关联的酒店/景点 ID
  images: [String],
  status: String,                 // "DRAFT" | "ON_SHELF" | "OFF_SHELF" | "DELETED"
  attributes: Object,             // 灵活属性 (Struct)
  skus: [                         // 嵌入式 SKU
    {
      id: String,
      name: String,
      description: String,
      status: String,
      attributes: Object,
      base_price: {
        currency: String,
        units: Long,
        nanos: Int
      }
    }
  ]
}

索引:
  - { resource_type: 1, resource_id: 1 }
  - { status: 1 }
  - { "skus.id": 1 }               // 支持按 SKU ID 查询
```

### 5.2 trip-inventory-service (MySQL + Redis)

#### MySQL 表

```sql
-- 日历库存表
CREATE TABLE daily_inventory (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    sku_id          VARCHAR(64)    NOT NULL,
    inv_date        DATE           NOT NULL,
    total_qty       INT            NOT NULL DEFAULT 0,
    available_qty   INT            NOT NULL DEFAULT 0,
    locked_qty      INT            NOT NULL DEFAULT 0,
    sold_qty        INT            NOT NULL DEFAULT 0,
    price_currency  VARCHAR(3)     NOT NULL DEFAULT 'CNY',
    price_units     BIGINT         NOT NULL DEFAULT 0,
    price_nanos     INT            NOT NULL DEFAULT 0,
    updated_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_sku_date (sku_id, inv_date)
);

-- 库存锁定表 (一个订单最多一个锁)
CREATE TABLE inventory_lock (
    lock_id     VARCHAR(64)   PRIMARY KEY,
    order_id    VARCHAR(64)   NOT NULL,
    status      VARCHAR(16)   NOT NULL DEFAULT 'LOCKED',   -- LOCKED / CONFIRMED / RELEASED / EXPIRED
    created_at  BIGINT        NOT NULL,
    expire_at   BIGINT        NOT NULL,
    UNIQUE KEY uk_order_id (order_id),     -- 保证 LockInventory 天然幂等
    INDEX idx_status_expire (status, expire_at)
);

-- 锁定明细表
CREATE TABLE inventory_lock_item (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    lock_id     VARCHAR(64)   NOT NULL,
    sku_id      VARCHAR(64)   NOT NULL,
    inv_date    DATE          NOT NULL,
    quantity    INT           NOT NULL,
    INDEX idx_lock_id (lock_id)
);
```

#### Redis 数据结构

Redis 在库存服务中**仅作为读缓存**使用，MySQL 是所有写操作的唯一数据源。

```
# 库存热数据缓存 (Hash) — TTL = 7 天
inv:{sku_id}:{date}
  total / available / locked / sold / price_units / price_nanos / price_ccy

# 缓存重建互斥锁 — 防止缓存击穿 (TTL = 5s)
inv:mutex:{sku_id}:{date} → "1"

# 锁定超时 (Sorted Set) — 定时任务扫描后触发释放
inv:lock:expiry  →  score = expire_timestamp, member = lock_id
```

### 5.3 trip-order-service (MySQL + Redis)

#### MySQL 表

```sql
-- 订单主表
CREATE TABLE orders (
    id              VARCHAR(64)   PRIMARY KEY,
    order_no        VARCHAR(32)   NOT NULL UNIQUE,
    user_id         VARCHAR(64)   NOT NULL,
    status          VARCHAR(24)   NOT NULL DEFAULT 'PENDING_PAYMENT',
    total_currency  VARCHAR(3)    NOT NULL DEFAULT 'CNY',
    total_units     BIGINT        NOT NULL DEFAULT 0,
    total_nanos     INT           NOT NULL DEFAULT 0,
    contact_name    VARCHAR(64),
    contact_phone   VARCHAR(20),
    contact_email   VARCHAR(128),
    source_channel  VARCHAR(16),
    source_agent_id VARCHAR(64),
    source_session  VARCHAR(64),
    cancel_reason   VARCHAR(256),
    expire_at       BIGINT,
    created_at      BIGINT        NOT NULL,
    updated_at      BIGINT        NOT NULL,
    paid_at         BIGINT,
    cancelled_at    BIGINT,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_user_status (user_id, status)
);

-- 订单项表
CREATE TABLE order_items (
    id                VARCHAR(64) PRIMARY KEY,
    order_id          VARCHAR(64) NOT NULL,
    spu_id            VARCHAR(64) NOT NULL,
    sku_id            VARCHAR(64) NOT NULL,
    product_name      VARCHAR(256),
    sku_name          VARCHAR(256),
    item_date         DATE        NOT NULL,
    end_date          DATE,
    quantity          INT         NOT NULL DEFAULT 1,
    unit_price_ccy    VARCHAR(3),
    unit_price_units  BIGINT,
    unit_price_nanos  INT,
    subtotal_ccy      VARCHAR(3),
    subtotal_units    BIGINT,
    subtotal_nanos    INT,
    inv_lock_id       VARCHAR(64),
    INDEX idx_order_id (order_id)
);
```

#### Redis 数据结构

```
# 订单超时关闭 (Sorted Set)
order:expire  →  score = expire_timestamp, member = order_id

# 订单号每日序列 (String, TTL = 2 天)
order:seq:{yyyyMMdd} → 自增序列号

# 下单去重锁 (String, TTL = 10s)
order:dedup:{userId}:{items_fingerprint_hash} → "1"
```

## 6. 项目结构

三个服务统一采用如下分层结构，与现有 trip-poi-service / trip-itinerary-service 保持一致：

```
trip-{service}-service/
├── src/main/java/org/tripsphere/{service}/
│   ├── {Service}Application.java
│   ├── api/grpc/                   # gRPC 接入层
│   ├── service/                    # 业务逻辑层
│   ├── repository/                 # 数据访问层
│   ├── model/                      # 领域模型 / 持久化实体
│   ├── mapper/                     # Protobuf ↔ 领域模型映射
│   ├── config/                     # 配置类
│   ├── security/                   # 认证鉴权
│   └── exception/                  # 业务异常
└── src/main/resources/
    ├── application.yaml
    └── application-dev.yaml
```

### 各服务特殊模块

| 服务                   | 额外模块       | 说明                                        |
| ---------------------- | -------------- | ------------------------------------------- |
| trip-inventory-service | `infra/redis/` | Redis 缓存操作封装                          |
| trip-inventory-service | `scheduler/`   | 锁定超时释放定时任务                        |
| trip-order-service     | `saga/`        | CreateOrder Saga 编排器                     |
| trip-order-service     | `grpc/client/` | 调用 Product / Inventory 服务的 gRPC 客户端 |
| trip-order-service     | `scheduler/`   | 订单超时关闭定时任务                        |

## 7. 关键设计要点

### 7.1 库存一致性

**核心原则: MySQL 是唯一写入源，Redis 是只读缓存。**

| 操作类型                   | 一致性策略                                                    |
| -------------------------- | ------------------------------------------------------------- |
| **库存锁定 / 确认 / 释放** | MySQL 悲观锁（`SELECT … FOR UPDATE`），事务中校验并变更       |
| **库存读取**               | Redis 缓存优先 → MySQL fallback；缓存 miss 通过互斥锁防止惊群 |
| **缓存同步**               | MySQL 事务提交后 best-effort 更新 Redis，失败不影响正确性     |
| **锁定超时清理**           | 定时任务扫描 Redis sorted set，依赖 `releaseLock` 幂等性      |

### 7.2 Saga 补偿

| 场景                               | 补偿动作                                     |
| ---------------------------------- | -------------------------------------------- |
| Product 校验失败 (SKU 不存在/下架) | 直接返回错误，无需补偿                       |
| Inventory 锁定失败 (库存不足)      | 直接返回错误，无需补偿                       |
| 本地建单失败 (DB 异常)             | 调用 `ReleaseLock` 释放已锁定库存            |
| 支付确认时 `ConfirmLock` 失败      | 重试；超过重试次数则标记订单为异常，人工介入 |

### 7.3 幂等性设计

| 接口             | 幂等策略                            | 触发场景                    |
| ---------------- | ----------------------------------- | --------------------------- |
| `CreateOrder`    | Redis 去重锁，10s 窗口              | 用户/Agent 短时间内重复提交 |
| `LockInventory`  | `order_id` 唯一约束；已有锁直接返回 | gRPC 超时重试               |
| `ConfirmLock`    | 已 CONFIRMED → 直接返回成功         | 支付回调重复投递            |
| `ReleaseLock`    | 已 RELEASED/EXPIRED → 直接返回成功  | 取消 + 超时清理竞态         |
| `ConfirmPayment` | 基于状态机，PAID 不可重复确认       | 支付网关重复回调            |
| `CancelOrder`    | 基于状态机，终态不可取消            | 用户重复操作                |

### 7.4 酒店日期范围处理

酒店类订单的 `CreateOrderItem` 包含 `date`（入住日）和 `end_date`（退房日），与景点类单日订单不同：

```mermaid
flowchart LR
    A["<b>CreateOrderItem</b><br/>sku_id: sku_003<br/>date: 2/25<br/>end_date: 2/28<br/>quantity: 1"]
    B["<b>LockItem (展开后)</b><br/>sku_id: sku_003<br/>date: 2/25, qty: 1<br/>date: 2/26, qty: 1<br/>date: 2/27, qty: 1"]

    A -- "展开 (入住 2/25 ~ 退房 2/28, 3 晚)" --> B
```

- **库存锁定**: 自动展开为 N 天的 LockItem，每天独立锁定
- **价格计算**: `subtotal` = Σ(每日价格) × quantity；`unit_price` 记录首日单价供展示参考
- **景点类**: 无 `end_date`，只锁定/计价一天

### 7.5 跨服务调用容错

**核心解法: 下游操作幂等 + 上游安全重试。**

当 Order Service 调用 Inventory Service 的 `ConfirmLock` / `ReleaseLock` 时，如果下游成功执行但
gRPC 响应丢失，Order Service 可以安全重试——下游检测到锁已处于终态后直接返回成功，不产生副作用。

同样的机制适用于 `LockInventory`（同一 order_id 已有 LOCKED 锁 → 返回已有锁）。

> **MVP 不处理的场景**: ConfirmLock 成功但 Order 本地 UPDATE 失败（概率极低），
> 此时库存已从 locked 转为 sold，但订单仍为 PENDING_PAYMENT。这种不一致需要
> 运维监控 + 人工介入。生产环境可引入本地事务表 (Outbox Pattern) 解决。

### 7.6 Redis 容错

| 功能                         | Redis 角色 | 不可用时行为                               |
| ---------------------------- | ---------- | ------------------------------------------ |
| 库存缓存 (Inventory)         | 只读缓存   | 降级到 MySQL 直读，不影响正确性            |
| 去重检查 (Order)             | 防重放     | fail-open 放行，依赖 order_no 唯一约束兜底 |
| 订单号生成 (Order)           | 序列号     | 降级为 timestamp-based 生成                |
| 超时队列 (Order / Inventory) | 延迟扫描   | 新订单的超时关闭依赖 Redis 恢复后补录      |

### 7.7 订单号规则

```
格式: TS + yyyyMMdd + 6位序列号
示例: TS20260208000001
```

序列号通过 Redis 每日自增生成，key 设置 2 天 TTL 自动清理。

## 8. Agent 集成 (MCP Tools)

三个服务的 gRPC 接口封装为 MCP Tools 后，供 Agent 通过 A2A 协议调用：

```mermaid
flowchart LR
    Agent["Agent<br/>(journey-assistant /<br/>itinerary-planner)"]

    Agent --> MCP["MCP Tools<br/>(gRPC → MCP 封装)"]

    subgraph ProductService["ProductService"]
        T1["search_products → ListSpusByResource"]
        T2["get_product_detail → GetSpuById"]
    end

    subgraph InventoryService["InventoryService"]
        T3["check_availability → CheckAvailability"]
        T4["get_price_calendar → QueryInventoryCalendar"]
    end

    subgraph OrderService["OrderService"]
        T5["create_order → CreateOrder"]
        T6["get_order → GetOrder"]
        T7["list_user_orders → ListUserOrders"]
        T8["cancel_order → CancelOrder"]
        T9["confirm_payment → ConfirmPayment"]
    end

    MCP --> ProductService
    MCP --> InventoryService
    MCP --> OrderService
```

### Agent 下单示例对话

```
用户: 帮我订明天去故宫的门票，2张成人票

Agent 内部调用链:
  1. search_products(ATTRACTION, "故宫") → 找到 SPU，获取 SKU 列表
  2. check_availability("sku_成人票", 明天, 2) → 确认有票，获取价格
  3. 向用户确认: "故宫成人票 x2，明天，共 ¥120，确认下单吗？"
  4. 用户确认后: create_order(user_id, [{sku_id, date, qty=2}], contact, {channel:"agent"})
  5. 返回: "订单创建成功！订单号 TS20260209000001，请在 15 分钟内支付"
```

`OrderSource.channel = "agent"` + `agent_id` + `session_id` 使得 Agent
创建的订单可追溯到具体对话会话。
