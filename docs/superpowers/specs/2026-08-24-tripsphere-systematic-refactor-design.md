# TripSphere 系统性改造设计 Spec

**日期：** 2026-08-24
**状态：** 待用户 Review
**适用范围：** 当前 TripSphere 仓库的服务、前端、服务发现、Agent/MCP、数据索引和部署配置改造

## 1. 目标

将当前 TripSphere 改造成一套可以由单份 canonical Compose 配置启动、验证和故障注入的 AI-native 分布式旅行系统，完整闭合以下六条用户可见链路：

1. 用户注册、登录和身份传递。
2. 景点、酒店、商品和房型浏览。
3. AI 行程规划和行程持久化。
4. 酒店/景点评论 CRUD、索引和统计。
5. 通过 `trip-review-summary` MCP Tool 查询评论摘要和索引状态。
6. 订单草稿、创建、查询、取消、模拟支付和库存生命周期。

改造必须遵循现有技术栈和 protobuf/gRPC 边界，不进行未经批准的架构重设计。

## 2. 已确认的设计决策

### 2.1 支付

`ConfirmPayment` 是模拟支付接口：

- 不接入真实支付渠道。
- 校验订单存在性、用户归属和当前状态。
- 确认库存锁。
- 模拟支付成功后，订单状态停在 `PAID`。
- 不自动推进到 `COMPLETED`。
- 重复确认必须是幂等行为，不能重复扣减或重复确认库存。

### 2.2 Review Summary 对外协议

`trip-review-summary` 生产环境完全移除 A2A，对外只提供 MCP Tool：

- 删除生产 A2A executor、AgentCard、A2A task store、A2A 路由和生产 A2A 注册逻辑。
- 提供 Streamable HTTP MCP endpoint：`/mcp`。
- 至少提供以下工具：
  - `query_review_summary`
  - `get_review_index_status`
  - `request_review_index`
- `trip-chat-service` 通过 MCP 调用 review-summary，不再把 review-summary 当作远程 A2A agent。
- 后续阶段不得为了兼容旧调用重新引入生产 A2A。

## 3. 当前系统理解

### 3.1 服务分层

| 层 | 服务/组件 | 主要职责 |
|---|---|---|
| 前端 | `trip-next-frontend` | 页面、Server Actions、静态 gRPC 客户端、CopilotKit 状态同步 |
| 身份 | `trip-user-service` | 注册、登录、JWT 签发、当前用户查询 |
| 内容 | `trip-attraction-service`、`trip-hotel-service` | 景点、酒店、房型及附近/列表查询 |
| 商品 | `trip-product-service` | SPU/SKU、资源类型、价格和可售事实 |
| 库存 | `trip-inventory-service` | DB 权威库存、Redis 缓存/锁、锁确认和释放 |
| 订单 | `trip-order-service` | 订单状态、库存协同、幂等、取消和模拟支付 |
| 行程 | `trip-itinerary-service`、`trip-itinerary-planner` | 行程持久化、规划工作流、流式进度 |
| 对话 | `trip-chat-service` | 会话、记忆、远程 agent 编排、MCP 调用 |
| 订单 Agent | `trip-order-assistant` | 订单草稿、商品选择、下单、取消确认、支付状态 |
| 评论 | `trip-review-service` | 酒店/景点评论 CRUD、归属和分页 |
| 评论索引 | `trip-review-summary`、worker | 评论文本单元、Qdrant/Neo4j 索引、摘要、任务状态 |
| 基础设施 | Nacos、Higress、MongoDB、Postgres、Redis、Qdrant、Neo4j、OTel、Tempo、Prometheus、Grafana、Loki | 发现、路由、存储、队列、索引和观测 |

### 3.2 目标调用关系

```text
frontend
  ├─ user-service
  ├─ attraction-service / hotel-service / product-service
  ├─ itinerary-planner ──> attraction-service / hotel-service
  │                     └─> itinerary-service
  ├─ review-service ──> review-summary MCP
  ├─ order-service ──> product-service / inventory-service
  └─ CopilotKit ──> chat-service
                     ├─ review-summary MCP
                     └─ order-assistant A2A
                           └─ product-service / order-service
```

其中 order-assistant 的 A2A 是 chat 与 order-assistant 之间的业务协作协议；review-summary 不再使用 A2A，而是 MCP Tool。

### 3.3 当前主要差距

- 多个 Java 服务和 `trip-review-service` 没有稳定发布 `gRPC_port` Nacos 元数据。
- order-service 的读取、取消和支付接口尚未统一执行认证和资源归属校验。
- review-service 创建、更新、删除仍部分信任请求体中的 `user_id`。
- planner 在候选少于 15 条时可能抛出采样异常，并存在固定上海坐标兜底。
- planner 的流式接口和非流式接口尚未共享持久化 job/result 模型。
- order-assistant 的 `ORDER_DRAFTS` 是进程内状态，没有跨实例持久化和 owner 校验。
- review-summary 当前没有 ReviewService 数据源，索引流程仍默认 attraction，并通过现有 A2A 对外提供查询。
- chat 当前没有 review-summary MCP 配置和调用链路。
- 前端缺少评论 CRUD、模拟支付确认和完整订单入口。
- root compose 与 `deploy/docker-compose/docker-compose.yaml` 的服务集合不一致。

## 4. 跨服务契约

### 4.1 身份和认证元数据

保留现有 gRPC metadata 名称，统一其语义：

| Metadata | 语义 | 规则 |
|---|---|---|
| `authorization` | 原始 Bearer JWT | 只允许在受信任的服务边界传递；日志禁止记录完整值 |
| `x-user-id` | 已验证 JWT 的 subject | 写操作不得使用请求体中的用户 ID 覆盖它 |
| `x-user-roles` | 已验证用户角色 | 作为授权输入，不作为身份来源 |
| `x-request-id` | 请求关联 ID | 无值时由入口生成并向下游传递 |
| `x-trace-id` | 链路关联 ID | 与 OTel trace 对齐 |

JWT 至少统一 `sub`、`roles`、`iss`、`exp` 和签名密钥配置。服务必须区分“未认证”“无权限”“资源不存在”和“依赖不可用”。

### 4.2 服务发现

所有保留 gRPC 服务在 Nacos 实例 metadata 中发布：

```text
gRPC_port=<actual grpc port>
protocol=grpc
```

`gRPC_port` 的大小写和名称保持现有客户端约定。客户端优先使用 metadata，不以硬编码端口作为正常路径。发现不到实例、实例缺少 metadata 和依赖连接失败必须产生可区分的错误。

### 4.3 订单状态

目标状态至少包括：

```text
PENDING_PAYMENT -> PAID
PENDING_PAYMENT -> CANCELLED
```

`ConfirmPayment` 只允许 `PENDING_PAYMENT -> PAID`，并确认库存锁。取消只允许在业务允许的未支付状态执行，并释放库存；释放失败必须留下可重试的补偿状态，不能静默丢失。

### 4.4 行程规划结果

规划必须形成可查询的 job/result 语义：

- 非流式接口负责创建任务并等待/返回最终结果。
- 流式接口只负责推送同一任务的进度事件。
- 任务结果必须能够通过明确的查询路径取得。
- 事件至少包含 `job_id`、递增事件序号、状态和必要的结果引用。
- 失败状态区分 `dependency_unavailable`、`no_data`、`model_failed`。

### 4.5 Review Summary MCP

MCP Tool 的输入必须包含不可由用户自然语言覆盖的目标上下文：

```json
{
  "target_id": "...",
  "target_type": "hotel|attraction",
  "entity_name": "..."
}
```

工具行为：

- `query_review_summary`：读取已构建索引的摘要/检索结果。
- `get_review_index_status`：返回 `never_built`、`building`、`ready`、`stale`、`failed` 或 `empty`。
- `request_review_index`：创建或复用幂等索引任务。

索引输入必须来自 review-service 的评论快照，经过文本单元、向量和图索引流程后写入 Qdrant/Neo4j；任务状态和索引版本写入 MongoDB。不得依赖默认 attraction 目标。

### 4.6 结构化错误和日志

服务间错误至少能区分：

```text
unauthenticated
forbidden
not_found
invalid_argument
no_data
dependency_unavailable
conflict
model_failed
retryable
```

日志统一结构化，携带 `service`、`environment`、`level`、`request_id`、`trace_id`、`user_id`、`task_id`、`index_version` 等字段；禁止输出 JWT、密码和其他敏感凭据。

## 5. 实施阶段和边界

每个阶段都必须有独立分支、独立 PR、独立测试结果和 scope review。除计划明确的文件外，不修改基础设施、schema、protobuf 或其他服务。

### Phase 1：服务发现基线

统一保留服务的 `gRPC_port` 注册 metadata，先解决客户端发现不稳定问题。不得改变业务行为。

### Phase 2：身份与认证边界

统一 JWT claims、metadata 传递、服务端认证上下文和 owner 校验。优先处理 user、order、review、itinerary 及调用链中的身份转发。

### Phase 3：内容、商品和库存事实

完成 attraction、hotel、product 的稳定返回语义、SPU/SKU 映射、fixtures 和 inventory 的权威存储/锁/缓存基础。

### Phase 4：订单生命周期

实现订单归属、幂等、库存补偿、取消和 `PENDING_PAYMENT -> PAID` 模拟支付语义，并覆盖服务级和端到端测试。

### Phase 5：行程和 Planner

实现行程权限、版本条件、输入校验、候选采样修复、依赖错误分类，以及共享 job/result 的流式/非流式模型。

### Phase 6：Review Service 与前端评论

实现酒店/景点评论 CRUD、归属校验、分页/统计、稳定 gRPC 入口和前端评论页面/Server Actions。

### Phase 7：Review Summary 索引和 Worker

接入 ReviewService，迁移到 Mongo 持久化任务状态，完成 Qdrant/Neo4j 索引、版本、重试和 worker 健康检查，移除 MinIO/S3 中间文件依赖。

### Phase 8：Review MCP 与 Chat

实现 `/mcp` 和三个 review 工具，删除 review-summary 生产 A2A 全部代码与注册，接入 chat，并传递不可变目标上下文。

### Phase 9：Order Assistant 与订单前端

将订单草稿迁移到 Redis，增加 owner/确认 token/幂等校验，完善 A2A 配置和认证转发，完成前端下单、待支付和模拟支付确认。

### Phase 10：部署、删除和可观测性

选定 `deploy/docker-compose/docker-compose.yaml` 为 canonical compose，补齐 review-service、review-summary、worker、Neo4j，并删除 POI、File、Note、note-creator、RocketMQ、MinIO 及所有引用；加入 Loki 和结构化日志链路。

### Phase 11：端到端验收和故障注入

按用户六条链路和 F1-F5 故障分类执行基线测试，记录预期错误、恢复行为、可观测字段和未覆盖风险。

## 6. 删除范围

只有在调用方迁移完成并通过全仓引用检查后，才允许删除：

- `trip-poi-service`
- `trip-file-service`
- `trip-note-service`
- `trip-note-creator`
- RocketMQ 相关服务和配置
- MinIO 相关服务和 review-summary 中间存储代码

删除必须同时检查：

- root 和 deploy compose
- Taskfile
- protobuf 文件和生成引用
- frontend env/client/action
- Nacos/Higress 配置
- Dockerfile、启动脚本和文档

## 7. 测试和 Review 规则

每个阶段完成时按以下顺序执行：

1. 先运行该阶段新增或受影响的 focused tests。
2. 运行受影响服务的 lint、type check、build。
3. 运行跨服务测试或 compose smoke test。
4. 检查 `git status`、`git diff --check`、`git diff --stat` 和完整 diff。
5. 对照阶段文件清单审查越界修改。
6. 做 self-review，确认没有 debug code、临时兼容逻辑或无关格式化。
7. 按一个明确逻辑变化创建 commit。

每个 PR 必须说明：修改内容、修改原因、涉及服务、测试结果、潜在风险、breaking changes 和后续阶段。

## 8. Breaking Changes

以下变化属于有意的内部 breaking change，必须在对应 PR 中明确标注：

- review-summary 生产 A2A 被完全移除，调用方必须迁移到 MCP。
- 删除 POI、File、Note、note-creator 及 RocketMQ/MinIO 运行时组件。
- 服务端不再信任请求体中的 `user_id`，调用方必须发送认证 metadata。
- 订单支付确认语义固定为进入 `PAID`，不再隐式进入 `COMPLETED`。

protobuf contract、数据库 schema 和外部用户可见 API 若需要变更，必须在实施前单独报告并等待确认。

## 9. 停止条件

实施过程中遇到以下任一情况必须暂停，不得自行猜测：

- 计划与当前代码的接口、状态机或数据模型冲突。
- 需要修改计划之外的服务、API、protobuf、数据库 schema 或基础设施。
- 某阶段预计修改文件明显超过该阶段清单。
- 现有用户工作区修改与目标行为冲突。
- 为了兼容旧调用需要重新引入 review-summary 生产 A2A。

## 10. 第一阶段入口

Spec 获得批准后，单独创建 Phase 1 implementation plan。Phase 1 只覆盖服务发现 metadata，不提前实现身份授权、订单、评论、MCP 或部署删除工作。

建议分支：

```text
codex/phase-1-service-discovery-baseline
```

建议逻辑 commit：

```text
fix(discovery): publish grpc metadata for retained java services
fix(discovery): publish grpc metadata for review service
```
