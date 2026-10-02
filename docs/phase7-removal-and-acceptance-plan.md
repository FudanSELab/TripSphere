# Phase 7 删除无用服务与总验收计划

## 1. 计划背景

本计划依据 [`docs/服务改造清单.md`](./服务改造清单.md) 的 Phase 7 制定，目标是删除没有六条业务闭环调用方的服务和基础设施引用，并完成六条闭环及可观测性基础的总验收。

Phase 7 的目标不是继续扩展业务能力，而是让运行系统只保留六条闭环真正需要的服务，同时确认删除动作没有破坏共享协议、初始化数据和现有业务调用。

## 2. 工作分支与现状

- 工作分支：`phase7-remove-unused-services`
- 基线分支：`phase6.3-metrics`
- 工作目录已有未提交的 Phase 6.3 文档改动，Phase 7 工作不得回退、覆盖或清理这些改动。
- 本计划文档是本分支新增的 Phase 7 交付物。

## 3. 删除范围与保留边界

### 3.1 删除项目

删除以下服务目录及其所有构建、启动和测试入口：

- `trip-poi-service`
- `trip-file-service`
- `trip-note-service`
- `trip-note-creator`

删除 RocketMQ 单实例运行时：

- `rmq-namesrv`
- `rmq-broker`
- `rmq-proxy`
- `rmq-dashboard`

同时删除 `trip-review-service` 中没有实际调用方的 `ROCKETMQ_ENDPOINT` 配置及相关 Compose 依赖。

### 3.2 保留项目

- 保留 `trip-attraction-service`、`trip-hotel-service` 及其主数据调用。
- 保留 POI 共享数据和类型：
  - `contracts/protobuf/tripsphere/poi/v1/types.proto`
  - 行程协议中的 POI 字段
  - initializer 中用于生成景点和酒店数据的 POI 输入
- 只有在完整引用检查确认没有消费者后，才删除独立的 `PoiService` proto 和对应生成目标。
- 保留 MinIO。本轮 `trip-review-summary` 仍使用 MinIO/S3 作为索引中间文件存储，MinIO 清理属于后续专项。
- 保留 Nacos、MongoDB、PostgreSQL、Redis、Qdrant、Neo4j、Higress、OTel Collector、Tempo、Prometheus、Grafana 和 Loki。

## 4. 实施步骤

### 4.1 建立删除安全基线

先在不修改代码的情况下执行全仓引用检查，并逐条分类结果：

```bash
rg -n -i \
  "trip-poi-service|trip-file-service|trip-note-service|trip-note-creator|rmq-|rocketmq|POI_SERVICE_ADDR|FileService|NoteService|PoiService" \
  --glob '!**/.git/**' \
  --glob '!**/target/**' \
  --glob '!**/.venv/**' \
  --glob '!**/.next/**' \
  --glob '!**/node_modules/**' \
  --glob '!**/*.lock' \
  --glob '!volumes/**' .
```

每条匹配结果归入以下类别之一：

1. 待删除的服务目录、配置或生成入口。
2. 需要修改的构建、Compose、环境变量或文档引用。
3. 必须保留的共享 POI 类型、初始化输入或历史迁移说明。

历史计划和改造说明可以保留删除项名称，但不能让这些名称继续出现在构建、启动或业务运行路径中。

### 4.2 删除服务目录和手工测试入口

删除：

```text
trip-poi-service/
trip-file-service/
trip-note-service/
trip-note-creator/
```

同步删除 FileService 的手工测试客户端、Shell/PowerShell 测试脚本和服务专属文档。

删除前确认没有以下类型的业务调用方：

- frontend Server Action 或 gRPC client
- planner、chat、order-assistant、review-summary 的 Python client
- review-service 或其他 Go 服务的 gRPC client
- Nacos 注册/发现配置
- Compose `depends_on` 或健康检查依赖

### 4.3 清理 Taskfile、Compose 和基础设施配置

修改根目录 [`Taskfile.yaml`](../Taskfile.yaml)：

- 删除 `file`、`note`、`poi` 的 Taskfile include。
- 删除对应的 `gen-proto` 任务入口。
- 删除对应的 `build` 和 `build-aliyun` 任务入口。
- 保留所有六条闭环服务和 initializer 的任务入口。

修改以下 Compose 文件：

- [`docker-compose.yaml`](../docker-compose.yaml)
- [`deploy/docker-compose/docker-compose.yaml`](../deploy/docker-compose/docker-compose.yaml)

删除内容：

- 四个待删除业务服务的 Compose service block。
- `rmq-namesrv`、`rmq-broker`、`rmq-proxy`、`rmq-dashboard`。
- `trip-review-service` 的 `ROCKETMQ_ENDPOINT`。
- `trip-review-service` 对 `rmq-proxy` 的 `depends_on` 或等价依赖。
- `.env.example` 中的 RocketMQ 主机、端口和说明。

修改 [`infra/otel-collector/config.yaml`](../infra/otel-collector/config.yaml)：

- 从基础设施 `filelog` 白名单中删除 RocketMQ 容器规则。
- 保留 MongoDB、PostgreSQL、Redis、Nacos、Qdrant、Neo4j、Higress 和 MinIO 的日志采集规则。
- 保持业务 OTLP 日志与基础设施 `filelog` 白名单互斥。

### 4.4 清理 protobuf 和生成入口

保留：

- `contracts/protobuf/tripsphere/poi/v1/types.proto`
- `contracts/protobuf/tripsphere/itinerary/v1/itinerary.proto` 对 POI 类型的必要引用
- 六条闭环服务需要的所有共享协议

根据 4.1 的引用结果处理：

- 删除 `contracts/protobuf/tripsphere/file/v1/file.proto`。
- 删除 `contracts/protobuf/tripsphere/note/v1/metadata.proto`。
- 删除 `contracts/protobuf/tripsphere/poi/v1/metadata.proto`。
- 仅当没有任何消费者使用独立 POI RPC 时，删除 `contracts/protobuf/tripsphere/poi/v1/poi.proto`。

随后执行保留服务的 protobuf 生成，确认生成代码中不再包含删除服务的客户端、服务端或 metadata 类型。生成目录多数属于忽略文件，不将本地生成产物作为无关文件提交。

### 4.5 清理前端、文档和测试引用

检查并修改：

- [`trip-next-frontend/lib/env.ts`](../trip-next-frontend/lib/env.ts)
- [`trip-next-frontend/lib/grpc/client.ts`](../trip-next-frontend/lib/grpc/client.ts)
- `trip-next-frontend` 的 Server Actions、导航和测试客户端
- [`trip-next-frontend/tests/phase2-regressions.test.mjs`](../trip-next-frontend/tests/phase2-regressions.test.mjs)

前端必须满足：

- 不存在 `POI_SERVICE_ADDR`。
- 不存在 `poiService` 或 `getPoiService`。
- 不创建 `PoiServiceClient`、`FileServiceClient` 或 `NoteServiceClient`。
- 景点数据只通过 `trip-attraction-service` 读取。

同步更新：

- [`docs/tripsphere-service-call-usage-by-service.md`](./tripsphere-service-call-usage-by-service.md)
- [`docs/commerce.md`](./commerce.md)
- README、initializer README 和相关服务文档
- initializer 源码中将 POI 数据描述为 `trip-poi-service` 依赖的注释

历史设计文档可以保留删除决策和迁移背景，但应避免把已删除服务描述成当前运行时依赖。

### 4.6 补齐确定性初始化数据

Phase 7 要求 initializer 能够为总验收提供固定数据。目前 initializer 已具备景点、酒店、房型、SPU/SKU 和库存导入能力，但没有独立的固定用户导入入口，因此需要补齐：

- 固定用户 A 和用户 B 的初始化数据。
- 可重复执行的 upsert 或 replace 行为。
- 用户 ID、邮箱、登录密码和角色的稳定输出。
- 景点、酒店、房型、SKU、库存和评论之间的引用校验。
- 执行完成后打印总验收需要的固定 ID、库存日期和评论数量。

初始化顺序：

```text
用户
POI 共享输入
酒店
房型
景点
SPU/SKU
库存
评论及评论索引
```

更新 [`infra/initializer/README.md`](../infra/initializer/README.md)，记录每一步的命令、依赖、默认地址和验收输出。

### 4.7 全仓引用和构建验证

静态引用检查：

```bash
rg -n -i \
  "trip-poi-service|trip-file-service|trip-note-service|trip-note-creator|rmq-|rocketmq|POI_SERVICE_ADDR|FileService|NoteService|PoiService" \
  --glob '!**/.git/**' \
  --glob '!**/target/**' \
  --glob '!**/.venv/**' \
  --glob '!**/.next/**' \
  --glob '!**/node_modules/**' \
  --glob '!**/*.lock' \
  --glob '!volumes/**' .
```

预期结果：

- 运行、构建和业务代码中不再出现删除项。
- 共享 POI 类型和初始化输入仍然存在。
- 仅历史文档或本计划中保留必要的删除说明。

配置和生成检查：

```bash
task buf
task gen-proto
docker compose config
docker compose -f deploy/docker-compose/docker-compose.yaml config
git diff --check
```

服务级检查按仓库工具链执行：

- Java：进入服务目录执行 `./mvnw test` 或针对性测试。
- Go：进入服务目录执行 `go test ./...`。
- Python：使用 `uv run` 执行相关测试。
- Frontend：使用 `bun -b` 执行测试、lint 和构建脚本。

## 5. 总验收顺序

### 5.1 启动基础设施和保留服务

使用 canonical Compose 启动完整单实例环境：

```bash
docker compose up --force-recreate --remove-orphans --detach
docker compose ps
```

确认以下依赖健康或达到清单要求的可用状态：

- Nacos 服务注册和发现
- Higress OpenAI 兼容 chat/embedding 路由
- MongoDB、PostgreSQL、Redis
- Qdrant、Neo4j、MinIO
- OTel Collector、Tempo、Prometheus、Grafana、Loki
- 所有保留业务服务和 agent

删除的服务和 RocketMQ 容器不得出现在 `docker compose ps` 或 Compose 配置中。

### 5.2 六条业务闭环

1. **用户与身份**
   - 用户 A/B 分别登录。
   - 确认 JWT/session 建立成功。
   - 确认订单、评论和行程请求携带正确身份。
   - 确认用户不能读取或修改其他用户的数据。

2. **内容浏览**
   - 读取景点、酒店、房型、商品和 SKU。
   - 确认 planner 和 order-assistant 使用相同的景点、酒店和商品事实数据。

3. **AI 行程**
   - 提交目的地和偏好并生成行程。
   - 确认生成结果保存到 itinerary-service。
   - 刷新后重新读取。
   - 编辑行程并重新保存，确认数据没有丢失。

4. **评论业务**
   - 查看酒店和景点评论。
   - 创建、更新和删除用户 A 自己的评论。
   - 使用用户 B 尝试修改或删除用户 A 的评论，确认被拒绝。
   - 确认详情页评分和评论数正确。

5. **评论问答**
   - 针对酒店和景点分别提问。
   - 确认回答使用真实评论，并且 `target_id`、`target_type` 与详情页实体一致。
   - 分别验证有评论、无评论、未建立索引和依赖服务失败四种结果。

6. **订单业务**
   - 从房型或 SKU 创建订单。
   - 确认库存锁定。
   - 执行模拟支付，确认订单进入 `PAID`。
   - 取消未支付订单，确认库存释放。
   - 重复 request ID 不得产生重复订单。

### 5.3 可观测性关联验证

至少选取一次订单、评论或行程请求，确认可以通过服务名、request ID 和 trace ID 关联查询：

- Grafana/Loki：查询业务服务日志。
- Prometheus：查询服务或 OTel 指标。
- Tempo：查询对应 trace。
- Grafana 数据源：Prometheus、Tempo、Loki 均为健康状态。

同时确认模型请求经过 Higress，Python gRPC 客户端能够通过 Nacos 发现 Java 服务。

## 6. 完成判定

满足以下条件后，Phase 7 才算完成：

- 四个无用服务目录已删除。
- RocketMQ 运行时、配置和日志采集引用已删除。
- 删除项不再出现在构建、启动和业务代码中。
- POI 共享类型、行程协议和初始化输入仍可生成和编译。
- initializer 能够重复导入总验收所需的固定用户和业务数据。
- 六条闭环全部使用真实入口和真实数据通过验收。
- Compose 配置、服务健康状态和 protobuf 生成检查通过。
- 至少一条真实业务请求可以在日志、指标和 trace 之间关联定位。
- `git diff --check` 通过，且没有混入与 Phase 7 无关的文件修改。

## 7. 不纳入本阶段

以下内容不作为 Phase 7 阻塞条件：

- Loki、Tempo、Prometheus、Grafana 的集群化、复制和自动故障转移。
- 服务副本、跨实例一致性和完整补偿系统。
- 共享 checkpoint、SSE job/result 和并发版本控制。
- MCP 协议迁移。
- F1-F5 故障注入专项。
- MinIO 清理。
