# Phase 6 Logs 设计与执行计划

**文档状态：** 已实现，待人工端到端验收
**实施顺序：** 2 / 3
**前置条件：** `docs/phase6-traces-plan.md` 已完成，Logs 阶段不得修改既有 Trace 采集
**目标：** 在不采集前端日志、不实施故障注入的前提下，把业务服务和基础设施日志完整写入 Loki，供后续开源可观测数据集使用。

## 1. 最终架构

```text
Java Logback / Python logging / Go slog
  -> OTel logging bridge
  -> OTLP gRPC/HTTP
  -> OpenTelemetry Collector logs/app pipeline
  -> Loki OTLP HTTP

MongoDB / PostgreSQL / Redis / Nacos / RocketMQ / Qdrant / Neo4j /
MinIO / Higress stdout+stderr
  -> Docker json-file
  -> Collector docker_observer + receiver_creator + filelog
  -> OpenTelemetry Collector logs/infra pipeline
  -> Loki OTLP HTTP
```

Collector 是 Loki 的唯一写入方。不部署 Grafana Alloy。cAdvisor 只属于 Metrics 阶段，不承担日志采集。

## 2. 数据边界

### 2.1 必须保留

- 完整用户 Prompt 和模型响应。
- 完整工具参数和工具响应。
- 完整 AG-UI context。
- 用户 ID、请求 ID、任务 ID、地理位置。
- MongoDB、PostgreSQL、Redis、Qdrant、Neo4j 等数据库业务响应。
- 异常消息、异常栈和第三方依赖错误响应。

### 2.2 唯一脱敏范围

只处理 Amap、OpenAI、Higress upstream 等外部 API key：

- 删除名称明确为 `amap_key`、`amap_api_key`、`openai_api_key`、
  `higress_upstream_api_key` 或 `api_key` 的日志/resource attributes。
- 遮蔽日志正文中上述具名键值。
- 遮蔽 OpenAI `sk-...` 形式密钥。
- 遮蔽 Amap API URL 中的 `key` 查询参数。

不得泛化删除 Authorization、Cookie、JWT、password、token、连接字符串、用户数据或业务正文；不得截断 Prompt、模型响应、工具响应和数据库响应。

## 3. 范围

### 3.1 包含

- Java、Python、Go 业务服务通过 OTLP 上报日志。
- Collector `filelog` 读取基础设施容器 Docker JSON 日志。
- Docker observer 发现动态容器 ID，receiver creator 按“基础设施服务名 + canonical 容器端口”白名单创建唯一的 `filelog` receiver。
- `file_storage` 持久化 Docker 日志读取 offset。
- Loki 单实例存储和 Grafana Logs/Traces 关联。

基础设施白名单以 Compose 实际存在服务为准，包括：

```text
nacos
higress
mongodb
postgres
redis
qdrant
neo4j
minio
rmq-namesrv
rmq-broker
rmq-proxy
rmq-dashboard
```

### 3.2 不包含

- Phase 6 内的故障注入实现。
- 最终数据集导出、清洗、发布流程。
- Next.js 浏览器或服务端日志。
- 修改现有 Trace instrumentation、Trace pipeline 或 Trace 字段。
- Alloy。
- 用 cAdvisor 采集日志。

## 4. 日志身份与存储

业务日志沿用 OTel Resource：

```text
service.name
service.namespace=tripsphere
deployment.environment.name=local
service.version
```

基础设施日志由 Docker observer 注入：

```text
service.name=<Compose container_name>
service.namespace=tripsphere
deployment.environment.name=local
container.id
container.name
container.image.name
log.iostream
log.file.path
```

Loki 只索引低基数字段：

```text
service_name
service_namespace
deployment_environment_name
```

其他字段作为 structured metadata 或正文保存，避免高基数索引。

## 5. 实施任务

### Task 1：Collector 基础设施日志链路

- [x] 增加 `docker_observer` extension，仅使用宿主机已绑定的 endpoint，避免同一端口的重复发现结果。
- [x] 增加 `receiver_creator/infra_logs`，仅匹配基础设施白名单且每个容器只创建一个 receiver。
- [x] 动态读取 `/var/lib/docker/containers/<container-id>/<container-id>-json.log`。
- [x] 使用 container operator 解析 Docker JSON 的正文、时间和 stdout/stderr。
- [x] 首次从文件开头读取，后续通过 `file_storage` offset 续采。
- [x] 基础设施 `filelog` 单行上限高于 Docker 单文件轮转阈值；业务 OTLP 日志不在 Collector 中截断正文或 attributes。
- [x] 拆分 `logs/app` 与 `logs/infra` pipeline，避免业务日志重复。

### Task 2：Compose 宿主机只读访问

- [x] 两份 Compose 为 Collector 挂载 `/var/lib/docker/containers:ro`。
- [x] 两份 Compose 为 Docker observer 挂载 `/var/run/docker.sock:ro`。
- [x] 两份 Compose 增加独立 named volume 保存 filelog offset。
- [x] 不增加 Alloy 或 docker-socket-proxy。

Collector 以 root 运行以读取宿主机 Docker 日志目录和 socket。Docker socket 即使以 `:ro` 挂载仍代表高权限 Docker API 访问。本配置仅用于本地数据采集环境，不作为生产安全模板。

### Task 3：恢复高保真业务日志

- [x] 恢复 AG-UI context、Prompt/查询、模型/工具/数据库响应等被概括或删除的原有日志字段。
- [x] 保留 Python logger 向 root OTel handler 传播所需的最小配置。
- [x] 保留 Java Agent 和 Go `otelslog` 所需的最小日志接入。
- [x] Go logger 自行创建与 Trace 相同身份的 Resource，不修改既有 `tracing.go`。
- [x] Collector 脱敏规则只覆盖外部 API key。
- [x] Loki 容量限制不得把允许保留的数据压缩到 4KB 或 64KB。
- [x] Loki 不限制业务日志单行大小，并为首次基础设施历史日志回放配置受控的 ingestion rate/burst。

### Task 4：清理无关测试资产

- [x] 删除本 Logs 阶段新增的根目录 `tests/observability`。
- [x] 删除为 logging 配置新增的各 Python 单元测试和 Go 单元测试。
- [x] 回退仅为这些测试加入的 pytest 依赖和 lockfile 变化。
- [x] 不删除仓库原本存在的业务测试。

### Task 5：验收

- [x] `docker compose config` 校验两份 Compose。
- [x] Collector 固定版本配置加载成功。
- [x] Loki 配置加载成功。
- [x] Loki 能分别查询业务 OTLP 日志和基础设施 Docker JSON 日志。
- [ ] 同一业务事件只出现一次，前端日志没有进入 Loki。
- [ ] Prompt、模型响应、工具参数/响应、AG-UI context、用户 ID、地理位置和数据库响应保持完整。
- [ ] 固定假 Amap/OpenAI API key 在 Loki 中被遮蔽。
- [ ] 业务日志中的非 API-key Authorization、JWT、password、token 等字段未被通用规则删除。
- [ ] Logs 到 Trace、Trace 到 Logs 关联可用；既有 Trace 输出没有变化。

## 6. 完成标准

- Java、Python、Go 业务日志经 OTLP 到达 Loki。
- Compose 内存在的目标基础设施日志经 Docker JSON `filelog` 到达 Loki。
- 前端、Collector 和可观测后端自身日志未被 `filelog` 采集。
- 不存在 Alloy 或业务日志双写。
- 只脱敏外部 API key，允许数据正文完整保留。
- 没有为了 Phase 6 Logs 引入无关重构或测试目录。
- 所有修改留在当前 `phase6.2-logs` 工作区，人工端到端验收前不提交。
