# TripSphere 基础业务闭环设计 Spec

**日期：** 2026-08-24
**状态：** 已确认范围；Phase 1 已完成
**适用范围：** 当前 TripSphere 仓库中六条基础业务闭环、单实例部署基础设施、可观测性和无调用方服务清理

## 1. 目标

本轮不把 TripSphere 改造成高可用生产级分布式平台，而是基于现有技术栈完成六条可以运行、可以验证、结果正确的业务闭环，并把它们所依赖的单实例部署、模型网关、服务发现和可观测性接通：

1. 用户注册、登录和身份传递。
2. 景点、酒店、房型和商品浏览。
3. AI 行程生成、持久化和编辑。
4. 酒店/景点评论查看和 CRUD。
5. 基于真实评论的酒店/景点评论问答。
6. SKU 下单、查询、取消、模拟支付和库存生命周期。
7. 单实例 Compose、Nacos、Higress、OTel、Tempo、Prometheus、Grafana、Loki 和日志采集链路。

Phase 1 已完成的服务发现 metadata 作为后续阶段的基础，不再单独重复规划。

## 2. 范围原则

### 2.1 必须完成

- 真实业务入口和真实基础数据。
- 认证身份与资源所有权校验。
- 现有接口中会造成错误结果或无法运行的实现缺口。
- focused tests、受影响服务测试和六条闭环 smoke test。
- 删除没有业务调用方的服务及其构建/启动引用。

### 2.2 不阻塞本轮

- 真实支付渠道；`ConfirmPayment` 只模拟成功并把订单置为 `PAID`。
- 共享 checkpoint、完整 SSE job/result、跨实例草稿持久化和高级补偿机制。
- 多副本、数据复制、自动故障转移、跨实例一致性和弹性伸缩。
- F1-F5 故障注入；但 Compose、Loki、OTel、Tempo、Prometheus、Grafana、Higress 和 Nacos 的基础接入属于本轮。
- 为所有接口建立统一错误码体系。
- 为了协议升级而把订单 A2A 改成其他协议。

## 3. 目标调用关系

```text
frontend
  ├─ user-service
  ├─ attraction-service / hotel-service / product-service
  ├─ itinerary-planner ──> attraction-service / hotel-service
  │                     └─> itinerary-service
  ├─ review-service ──> review-summary
  └─ chat-service ──> order-assistant
                   └─> review-summary
```

`trip-review-summary` 本轮沿用已有 A2A/HTTP 代码作为最小可用入口；不强制迁移 MCP。评论问答的业务重点是接入真实 ReviewService 数据、正确区分酒店/景点和失败状态，而不是更换通信协议。

## 4. 服务边界

### 保留

保留 frontend、user、attraction、hotel、product、inventory、order、itinerary、itinerary-planner、chat、order-assistant、review、review-summary 和 worker。Nacos、MongoDB、PostgreSQL、Redis、Qdrant、Neo4j、Higress、OTel Collector、Tempo、Prometheus、Grafana、Loki 和 Grafana Alloy 保持或补齐单实例运行职责。

POI 的共享 protobuf 类型和初始化数据保留，因为 itinerary contract 和酒店/景点数据生成仍使用它们；独立 `trip-poi-service` 删除。

### 删除

- `trip-poi-service`
- `trip-file-service`
- `trip-note-service`
- `trip-note-creator`
- RocketMQ `rmq-*` 运行时及 review-service 中无效的 RocketMQ 配置

MinIO 当前仍被 review-summary 索引任务作为中间文件存储使用，因此本轮不强制删除；只有索引任务改为不依赖 MinIO 后，才在后续清理中删除。

## 5. 关键业务契约

### 5.1 身份

- user-service 签发 JWT。
- frontend 和各服务沿用当前 session、请求头及 gRPC metadata 传递方式。
- 本轮只验证现有身份参数能够支撑六条业务闭环，不新增统一 metadata 生成、JWT 校验链路或认证架构改造。

### 5.2 行程

- 非流式 planner 接口是生成和持久化的正式入口。
- `ReplaceItinerary` 是编辑保存入口，沿用当前登录会话下的读取和替换行为。
- 只修复会导致基础业务错误的日期、活动、候选数量和坐标问题，不新增共享 job 系统。

### 5.3 评论

- ReviewService 是评论唯一主数据源。
- Create/Update/Delete 沿用当前作者身份和请求参数传递方式。
- review-summary 必须从 ReviewService 分页读取 hotel/attraction 评论。
- 查询上下文必须同时包含 `target_id` 和 `target_type`。
- 空评论、未建立索引和依赖失败必须返回不同的业务状态。

### 5.4 订单

```text
PENDING_PAYMENT -> PAID
PENDING_PAYMENT -> CANCELLED
```

- `ConfirmPayment` 是模拟支付，成功后停在 `PAID`。
- 订单查询、取消和支付沿用当前接口行为，只保证状态和库存流转正确。
- 创建订单前校验 SKU、价格、资源类型、日期和库存。
- 重复 request id 不得创建重复订单。
- 取消和支付分别释放或确认库存锁，不能在库存操作失败时假报成功。

### 5.5 基础设施与可观测性

- root `docker-compose.yaml` 是本地验收的 canonical Compose；`deploy/docker-compose/docker-compose.yaml` 必须同步保留相同的业务服务和基础设施职责。
- Nacos 负责服务注册/发现，Higress 负责 OpenAI 兼容 chat/embedding 路由；业务服务不能在必要依赖不可用时静默降级成“可用”。
- OTel Collector 接收应用 trace 和指标，trace 写入 Tempo，指标写入 Prometheus。
- Grafana Alloy 采集保留服务 stdout/stderr 到 Loki；日志必须携带服务名、环境、请求/trace 关联字段，不能包含 JWT、密码或 API key。
- Grafana 预置 Prometheus、Tempo、Loki 数据源，能按一次真实业务请求关联日志、指标和 trace。
- Loki、Tempo、Prometheus、Grafana 和 Alloy 使用本地卷和单实例配置，不要求复制或自动故障转移。
- 所有核心依赖提供 Compose healthcheck 和 `depends_on` 条件；基础服务的健康检查必须验证真实 API/端口，而不是只检查进程存在。

## 6. 实施顺序

### Phase 2：身份、内容和基础数据

验证 Phase 1 发现链路，沿用现有登录和 metadata 传递方式，移除前端 POI client/config，准备景点、酒店、房型、SKU 和库存数据。只修复会阻塞内容浏览、planner 或 order-assistant 的基础问题。

### Phase 3：AI 行程

修复候选数量不足时的采样问题，补生成结果的基本结构校验，验证 planner 保存到 itinerary-service，接通前端读取、编辑和替换保存。

### Phase 4：评论和评论问答

接通 frontend Review client 和页面，沿用 ReviewService 当前作者身份和 CRUD 行为，接入 review-summary 的真实评论来源和 hotel/attraction 查询，接入 chat 的评论问答路径。删除未实现的静态 summary 入口，但保留本轮实际使用的 A2A/HTTP 入口。

### Phase 5：订单

接通 frontend 支付入口和 order-assistant 支付工具，补联系人、草稿提交和重复请求校验，验证 product、inventory、order 的完整链路。

### Phase 6：部署与可观测性

补齐 canonical Compose、单实例基础设施、健康检查、OTel trace/metrics、Loki 日志采集、Grafana 数据源、Prometheus targets、Tempo 查询和 Higress/Nacos 依赖验证。此阶段必须验证真实业务请求在日志、指标和 trace 中可定位，但不建设 HA。

### Phase 7：删除与验收

删除 POI/File/Note/Note Creator/RocketMQ 及所有引用，保留共享 POI 类型；运行初始化、服务测试、构建检查、基础设施 smoke test 和六条闭环 smoke test。

## 7. 测试要求

每个 Phase 至少包含：

1. 被修改服务的 focused unit test。
2. 受影响服务的完整 test/build。
3. 涉及 gRPC、A2A、数据库或 Compose 的路径至少执行一次真实 smoke test。
5. 失败依赖和空数据场景。
6. 观测链路场景：发送一次带 request/trace 关联的业务请求，在 Loki、Prometheus、Tempo 和 Grafana 中分别验证可见。

命令遵循仓库规则：Java 使用 `./mvnw`，Python 使用 `uv`，前端使用 `bun -b`，Go 使用 `go test`。

## 8. 完成标准

只有满足以下条件才算完成：

- 六条业务闭环都能从真实入口走通。
- 单实例 Compose 能启动并连接所有必需业务依赖和观测组件。
- 订单和库存状态保持一致。
- 评论问答使用真实评论并区分目标类型和失败原因。
- 日志、指标和 trace 已接入 Loki、Prometheus、Tempo，并能通过 Grafana 查询。
- 删除的服务不再出现在 Compose、Taskfile、构建目标、业务 client 或运行配置中。
- 共享 POI 类型仍能生成并支持 itinerary 编译。

高可用、多副本、复制、自动故障转移、跨实例一致性、故障注入和协议迁移作为后续专项，不得反向扩大本轮范围。
