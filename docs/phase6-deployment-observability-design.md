# Phase 6 部署与可观测性基线设计草案

**文档状态：** 待 Review  
**需求来源：** `docs/服务改造清单.md` Phase 6  
**适用范围：** TripSphere 单实例 Docker Compose 部署与可观测性基线  
**主要目标：** 为后续故障注入和 RCA benchmark 数据集制作补全 Logs、Metrics、Traces 采集能力，使一次真实业务请求能够跨信号关联查询。

## 1. 背景与 Motivation

TripSphere 是 AI Native 微服务系统。后续工作将在业务服务、Agent、模型网关、服务发现和数据依赖上进行故障注入，并根据故障期间采集的可观测数据构建 RCA benchmark 数据集。

Phase 6 不实施 F1-F5 故障注入，也不实现最终的数据集导出程序，而是建立故障实验所需的可观测性与部署基线：

- 单份 canonical Compose 能启动保留的业务服务及其基础设施依赖。
- OpenTelemetry Collector 统一接收应用 Logs、Metrics、Traces，并采集 Docker 宿主机指标；cAdvisor 采集容器资源指标，Prometheus 统一存储和查询指标。
- Grafana 提供日志、指标、Trace 的查询入口和跨信号关联能力。
- 采集容器与 Docker 宿主机的 CPU、内存、文件系统、磁盘 I/O 和网络指标，为后续资源故障 RCA 提供证据。
- 可观测数据包含必要的业务关联字段，但不采集 JWT、密码、API key 等敏感信息。

本阶段的“客户端”指本地 Grafana 查询端，不新增外部 OTLP endpoint，也不新增 RCA 数据集导出客户端或数据格式。

## 2. 与 Phase 6 原文的关系

除以下一项明确覆盖外，本设计严格以 `docs/服务改造清单.md` Phase 6 为范围边界：

> Phase 6 原文要求增加 Grafana Alloy；本设计根据当前决策不使用 Alloy，改由 OpenTelemetry Collector 直接负责日志采集和转发。

因此，最终日志链路为：

```text
应用 stdout/stderr
  -> Docker json-file
  -> OTel Collector filelog receiver
  -> 规范化、关联字段提取和脱敏
  -> Loki OTLP HTTP endpoint
  -> Grafana
```

该覆盖必须在后续 Review 中再次确认。不得为了形式上满足原文而保留一个没有真实采集职责的 Alloy 容器。

## 3. 范围边界

### 3.1 本阶段包含

- 以 root `docker-compose.yaml` 作为本地验收 canonical Compose。
- 同步 `deploy/docker-compose/docker-compose.yaml` 中所有保留业务服务和必需基础设施的职责。
- 补齐 Nacos、Higress、MongoDB、PostgreSQL、Redis、Qdrant、Neo4j、MinIO、OTel Collector、cAdvisor、Tempo、Prometheus、Grafana、Loki 的健康检查、启动依赖、容器内地址和本地持久化。
- 补齐保留业务服务的日志规范、Trace、Metrics、健康检查和关联上下文。
- 自动初始化并验证 Higress 的 OpenAI-compatible chat 与 embedding 路由。
- 验证 Python gRPC 客户端通过 Nacos 发现 Java 服务。
- 用一条确定性的订单业务请求验收 Logs、Metrics、Traces 关联。

### 3.2 本阶段不包含

- F1-F5 故障注入的实现和执行。
- RCA benchmark 样本格式、标签、数据切片或外部导出客户端。
- Loki、Tempo、Prometheus、Grafana 的集群、复制、自动故障转移或高可用。
- 业务协议迁移、共享 checkpoint、复杂补偿和跨实例一致性。
- Phase 7 中 POI、File、Note、Note Creator、RocketMQ 的删除。
- MinIO 清理；在 review-summary worker 仍使用 MinIO 时继续保留。

## 4. 当前仓库基线与主要缺口

当前实现已经具备部分基础：

- Java 服务 Dockerfile 已使用 OpenTelemetry Java Agent，并配置 OTLP endpoint。
- Python Agent 服务已使用 `opentelemetry-instrument` 启动。
- Next.js 已通过 `@vercel/otel` 注册 `trip-next-frontend`。
- OTel Collector 已接收 OTLP，Trace 转发 Tempo，Metrics 暴露 Prometheus exporter。
- Tempo、Prometheus、Grafana 已存在基础 Compose 服务。
- Docker 日志使用 `json-file`，并配置单文件大小和轮转数量。

仍需解决的关键缺口：

- Collector 的 logs pipeline 目前只有 debug exporter，没有写入 Loki。
- Compose 中没有 Loki；按本设计也不会增加 Alloy。
- 当前没有容器和 Docker 宿主机资源指标；Collector 也没有持久化日志 offset 和真实健康端点。
- Prometheus 目前只抓取自身和 Collector exporter，未覆盖保留服务和 Collector 自身指标。
- Grafana 没有文件化预置 Prometheus、Tempo、Loki 数据源及 dashboard。
- Java、Python、Go、Next.js 的日志格式和关联字段不统一。
- `trip-review-service` 没有完整的 OTel gRPC Trace/Metrics 初始化。
- 多个服务没有真实 readiness；部分 health endpoint 只返回固定成功。
- root Compose 与 deploy Compose 的保留服务、基础设施和配置路径不一致。
- deploy Compose 缺失 Prometheus、Neo4j、MinIO、review-service、review-summary 和 worker 等保留项。
- Higress 依赖人工控制台配置，无法在全新数据卷上重复创建 chat/embedding 路由。
- 个别服务在 Nacos 等必要依赖失败时仅告警并继续启动，可能形成假健康状态。

## 5. 总体架构

### 5.1 信号流

```text
应用 OTLP Traces -------------------------------> OTel Collector ----> Tempo
应用 OTLP Metrics ------------------------------> OTel Collector --+
Docker JSON stdout/stderr ----------------------> OTel Collector ----> Loki OTLP HTTP
Docker 宿主机 CPU/内存/磁盘/文件系统/网络 -------> OTel Collector --+
                                                                  |
容器 CPU/内存/文件系统/块 I/O/网络/OOM ----------> cAdvisor --------+--> Prometheus
Collector 自身 telemetry metrics --------------------------------+

Tempo + Prometheus + Loki ---------------------------> Grafana
```

Collector 是应用遥测、日志和宿主机指标的统一采集与转发中间件；cAdvisor 是容器资源指标的唯一事实源：

- `otlp` receiver 接收 gRPC `4317` 和 HTTP `4318` 上报的 Trace、Metrics，以及未来需要时的 OTLP Logs。
- `filelog` receiver 读取 Docker `json-file` 日志。
- `hostmetrics` receiver 从挂载到 `/hostfs` 的宿主机视图采集 CPU、内存、文件系统、磁盘和网络指标。
- `spanmetrics` connector 从 Trace 派生请求量、错误量和延迟指标，覆盖没有原生 Prometheus endpoint 的服务。
- `health_check` extension 提供 Collector 健康检查。
- `file_storage` extension 保存 filelog offset，Collector 重启后不从头重复读取日志。
- Trace 使用 OTLP gRPC 写入 Tempo。
- Logs 使用 `otlphttp` 写入 Loki 原生 OTLP endpoint。
- 应用 OTLP metrics、span-derived metrics 和 host metrics 通过 Collector Prometheus exporter 暴露，由 Prometheus 抓取。
- cAdvisor 通过 Docker/cgroup 接口采集容器指标并暴露原生 `/metrics`，由 Prometheus 直接抓取；不得同时启用 `docker_stats` 生成重复序列。

应用日志只走 stdout/stderr 加 filelog 的单一路径。应用侧显式关闭 OTLP Logs exporter，避免同一日志经 stdout 和 OTLP 重复写入 Loki。

### 5.2 宿主机访问权限

Collector 需要只读挂载：

- `/var/lib/docker/containers`：读取 Docker JSON 日志。
- `/` 到 `/hostfs`：供 `hostmetrics` 从宿主机视图读取 `/proc`、`/sys`、文件系统和磁盘状态。

Collector 还需挂载独立持久卷保存 filelog offset。`hostmetrics.root_path` 必须设置为 `/hostfs`，避免误采集 Collector 容器自身的文件系统和进程命名空间。

cAdvisor 固定使用 `ghcr.io/google/cadvisor:v0.60.5`，按其 Docker 部署要求只读挂载 `/`、`/var/run`、`/sys`、`/var/lib/docker`、`/dev/disk`，并访问 `/dev/kmsg`。cAdvisor 通常需要 privileged 权限；这些宿主机能力仅作为本地单机故障实验基线使用，不得直接复用为生产安全方案。Collector 和 cAdvisor 只暴露 Phase 6 所需的 OTLP、健康和指标端口，不开放无关接口。

## 6. Compose 部署契约

### 6.1 Canonical Compose

root `docker-compose.yaml` 是唯一的本地验收入口。执行：

```bash
docker compose config
docker compose up -d
```

应能解析并启动保留业务服务及必需基础设施。

`deploy/docker-compose/docker-compose.yaml` 必须作为独立 Compose 文件正确解析，修正其相对 build context、配置挂载和数据卷路径，不能依赖调用者碰巧从仓库根目录启动。

### 6.2 服务集合

两份 Compose 必须同步包含以下保留集合：

```text
业务服务：
trip-next-frontend
trip-user-service
trip-attraction-service
trip-hotel-service
trip-product-service
trip-inventory-service
trip-order-service
trip-itinerary-service
trip-itinerary-planner
trip-chat-service
trip-order-assistant
trip-review-service
trip-review-summary
trip-review-summary-worker

基础设施：
nacos
higress
mongodb
postgres
redis
qdrant
neo4j
minio
otel-collector
cadvisor
tempo
prometheus
loki
grafana
higress-init
```

root Compose 当前存在的 Phase 7 待删服务不在 Phase 6 删除，也不要求补到 deploy Compose。Phase 6 的清单一致性测试只比较上述保留集合。

### 6.3 通用遥测环境变量

所有保留应用容器统一设置：

```text
OTEL_SERVICE_NAME=<compose service name>
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317 或 http://otel-collector:4318
OTEL_RESOURCE_ATTRIBUTES=deployment.environment.name=local,service.namespace=tripsphere
OTEL_LOGS_EXPORTER=none
```

Java Agent 使用 OTLP HTTP 时保持 `4318`；Python 和 Next.js 使用其当前支持的 OTLP 协议与 endpoint。不得只依赖 Dockerfile 中的默认地址，Compose 必须显式表达容器部署契约。

每个容器增加可由 Docker `json-file` 记录的显式标签：

```text
tripsphere.service=<compose service name>
tripsphere.environment=local
```

Docker logging options 保留：

```text
max-size=10m
max-file=3
```

同时把上述标签写入 Docker JSON 日志的 `attrs`，供 Collector 建立 `service.name` 和 `deployment.environment.name` 资源属性。

## 7. 日志规范、关联和脱敏

### 7.1 统一字段

保留服务的结构化日志采用统一字段名：

| 字段 | 含义 | 要求 |
| --- | --- | --- |
| `timestamp` | 事件时间 | 必须 |
| `severity` | 日志级别 | 必须，规范化为 TRACE/DEBUG/INFO/WARN/ERROR |
| `service` | 服务名 | 必须，由容器标签映射 |
| `environment` | 环境 | 必须，默认 `local` |
| `message` | 事件描述 | 必须 |
| `request_id` | 业务请求关联 ID | 请求上下文存在时必须 |
| `trace_id` | OTel Trace ID | 活跃 Span 存在时必须 |
| `span_id` | OTel Span ID | 活跃 Span 存在时必须 |
| `user_id` | 已认证用户 ID | 业务上下文存在时必须 |
| `task_id` | Agent/A2A/Celery 任务 ID | 任务上下文存在时必须 |
| `rpc.method` / `http.route` | 调用入口 | 相应协议存在时记录 |
| `error.type` | 错误类型 | 错误事件记录 |

不是每条日志都强行填充不存在的 `user_id` 或 `task_id`。字段只在上下文真实存在时出现，禁止使用空字符串制造虚假关联。

### 7.2 Loki 索引策略

低基数字段作为 Loki labels：

```text
service
environment
severity
```

高基数字段保留为日志 JSON 字段或 Loki structured metadata：

```text
request_id
trace_id
span_id
user_id
task_id
```

查询示例应覆盖：

```logql
{service="trip-order-service", environment="local"} | json | request_id="<request-id>"
{service="trip-order-service"} | json | trace_id="<trace-id>"
{service="trip-review-summary-worker"} | json | task_id="<task-id>"
```

不得把 `request_id`、`trace_id`、`user_id`、`task_id` 设为常规索引 label，以免产生高基数流。

### 7.3 上下文传播

- HTTP 入口读取合法的 `x-request-id`；缺失时生成 UUID，并在响应中返回。
- gRPC 调用通过 metadata 传播 `x-request-id`、现有身份字段和 W3C Trace Context。
- HTTP/A2A 调用传播 `traceparent` 和 `x-request-id`。
- Celery 任务使用 Celery task ID 作为 `task_id`，并在任务 headers 中传播 `request_id` 和 Trace Context。
- 前端、Agent、业务服务不得信任客户端自行提交的 `user_id`；继续使用现有认证会话和可信 metadata 来源。
- 自动插桩能够传播 Trace Context 的标准 HTTP/gRPC 链路继续使用自动插桩；只为 A2A、Celery 或现有封装未覆盖的边界补手工传播。

### 7.4 敏感数据约束

业务代码不得记录：

- `Authorization`、JWT、cookie 或完整请求 headers。
- 登录、注册请求体及密码字段。
- OpenAI/Higress/provider API key。
- MongoDB、PostgreSQL、Neo4j、Nacos 等连接字符串中的凭据。
- 完整配置对象或 Pydantic settings 对象。

Collector 作为第二道防线：

- 删除名称匹配 `authorization`、`cookie`、`password`、`passwd`、`secret`、`token`、`api_key` 的日志属性。
- 对日志 body 中的 Bearer token、JWT 形态、password/API key 键值进行遮蔽。
- 脱敏处理发生在 Loki exporter 之前。

脱敏测试使用固定假凭据，断言 Collector 输出和 Loki 查询结果都不包含原文。

## 8. 各技术栈接入

### 8.1 Java / Spring Boot

- 保留现有 OpenTelemetry Java Agent。
- 统一配置 `service.name`、environment 和 OTLP endpoint。
- 使用 Spring Boot 3.5 的结构化 console logging，并确保 OTel MDC 中的 `trace_id`、`span_id` 进入 JSON。
- 增加 Actuator 与 Prometheus registry，暴露 `/actuator/health` 和 `/actuator/prometheus`。
- Compose healthcheck 使用 `/actuator/health/readiness` 或明确的健康端点，不使用单纯进程存在检查。
- Prometheus 抓取 Java 服务真实暴露的 metrics endpoint；OTel span metrics 仍用于跨语言统一 RED 视图。

涉及服务：attraction、hotel、product、inventory、order、itinerary、user。

### 8.2 Python / FastAPI / Agent / Celery

- 保留 `opentelemetry-instrument` 自动插桩。
- 将现有文本 formatter 改为结构化 stdout/stderr formatter。
- 日志过滤器从当前 OTel Span 和请求/任务上下文注入统一字段。
- 删除或替换会输出完整 settings、用户 prompt、模型输入输出或下游响应对象的日志。
- FastAPI readiness 必须验证启动时创建的必要依赖，不得固定返回 healthy。
- Celery worker healthcheck 使用真实 worker ping，并验证 broker 连接。
- review-summary API 与 worker 使用不同 `OTEL_SERVICE_NAME`，但共享 `service.namespace=tripsphere`。

涉及服务：chat、itinerary-planner、order-assistant、review-summary、review-summary-worker。

### 8.3 Go / Review Service

- 将 OpenTelemetry SDK、OTLP exporter 和 gRPC instrumentation 声明为直接依赖。
- 启动时初始化 TracerProvider、MeterProvider 和 resource attributes，退出时 flush/shutdown。
- gRPC server 使用 OTel stats handler/interceptor，保留 recovery 与业务 logging interceptor。
- logging interceptor 从当前 Span 和 gRPC metadata 注入 `trace_id`、`span_id`、`request_id`、`user_id`。
- Nacos 是 Compose 部署的必要依赖；配置了 Nacos 时初始化或注册失败必须令启动/readiness 失败，不能只告警后静默禁用服务发现。
- Compose healthcheck 调用已注册的标准 gRPC Health 服务。

### 8.4 Next.js

- 保留 `@vercel/otel` 注册。
- 在服务端入口生成或传递 `x-request-id`，并与 Server Action、gRPC metadata、Agent HTTP 请求关联。
- 服务端日志使用统一结构化字段，禁止浏览器端输出 JWT/session 内容。
- 增加真实 HTTP health endpoint，验证 Next.js server 可接受请求；下游依赖健康由业务服务和 Compose 依赖分别判断。

## 9. Metrics 设计

### 9.1 指标来源与边界

Prometheus 必须覆盖：

- Prometheus 自身 `/metrics`。
- OTel Collector 自身 telemetry metrics。
- Collector Prometheus exporter 中的应用 OTLP metrics、span-derived metrics 和 `hostmetrics`。
- cAdvisor 原生 `/metrics`，作为容器资源指标的唯一事实源。
- 所有实际暴露 `/actuator/prometheus` 的 Java 服务。
- Loki、Tempo、Higress 等已暴露且稳定的组件 metrics endpoint。

指标按以下边界解释：

- cAdvisor 负责容器归因：容器 CPU、内存、writable layer、块 I/O、网络和 OOM。
- Collector `hostmetrics` 负责 Docker 宿主机及数据卷所在文件系统和物理磁盘。磁盘容量和 I/O latency 以宿主机指标为权威口径。
- `container_fs_*` 只代表容器可见的 writable layer，不得等同于 Docker named volume 或宿主机物理磁盘。
- 在 overlay2、cgroup v2 或底层驱动不提供容器 I/O time 时，容器级 latency 显示 unavailable，不得用 0 冒充无延迟。
- 对于没有原生 Prometheus endpoint 的 Python、Go、Next.js 服务，OTLP runtime/request metrics 和 span metrics 是最低观测保证；不得因为没有 `/metrics` 就从 dashboard 和验收清单中遗漏。

Prometheus 抓取 cAdvisor 时，把 `container_label_com_docker_compose_service` 规范化为 `service`，并附加 `environment="local"`。Dashboard 和 recording rules 只查询具有非空 `service` 的 Compose 容器，避免把 root cgroup、匿名容器和镜像构建残留混入服务面板。

### 9.2 容器资源指标契约

原始 Counter 必须通过 `rate()` 或 `increase()` 转为窗口值；不得直接把累计值展示为利用率、吞吐或延迟。

| 观测项 | cAdvisor 原始指标 | PromQL 语义与约束 |
| --- | --- | --- |
| CPU time | `container_cpu_usage_seconds_total` | 累计 CPU 秒数，保留为故障时间窗的原始证据 |
| CPU usage | `container_cpu_usage_seconds_total` | `rate(...[1m])`，单位为 CPU cores |
| CPU limit | `container_spec_cpu_quota`、`container_spec_cpu_period` | quota 大于 0 时，limit cores 为 `quota / period` |
| CPU utilization | CPU usage 与 CPU limit | 仅对显式 quota 计算 `usage_cores / limit_cores`；无限额容器展示 cores，不生成虚假百分比 |
| CPU throttling | `container_cpu_cfs_periods_total`、`container_cpu_cfs_throttled_periods_total`、`container_cpu_cfs_throttled_seconds_total` | 同时展示 throttled-period ratio 与每秒 throttled time；分母为 0 时显示 unavailable |
| Memory usage | `container_memory_usage_bytes`、`container_memory_working_set_bytes` | working set 为主面板；total usage 作为包含 cache 的辅助证据 |
| Memory limit | `container_spec_memory_limit_bytes` | 展示原始限制；等于或接近宿主机容量的“无限制”值不得解释为显式容器 limit |
| Memory utilization | working set 与有效 memory limit | 仅对显式且有限的 limit 计算 `working_set / limit`，否则显示 unavailable |
| OOM | `container_oom_events_total` | 使用 `increase(...[5m])`，并与 `container_start_time_seconds`、容器健康和重启现象关联 |
| Filesystem usage | `container_fs_usage_bytes`、`container_fs_limit_bytes` | 计算 writable layer utilization；命名卷容量由宿主机 filesystem 指标判断 |
| Disk throughput | `container_fs_reads_bytes_total`、`container_fs_writes_bytes_total` | 使用 `rate(...[1m])` 得到 read/write bytes/s |
| Disk IOPS | `container_fs_reads_total`、`container_fs_writes_total` | 使用 `rate(...[1m])` 得到 read/write operations/s |
| Container disk latency | `container_fs_read_seconds_total`、`container_fs_write_seconds_total` 与对应 operations | 用 `rate(time) / rate(operations)` 计算平均值；只作为 best-effort 容器归因 |
| Network receive/transmit | `container_network_receive_bytes_total`、`container_network_transmit_bytes_total` | 使用 `rate(...[1m])` 得到 bytes/s |
| Packet drop | `container_network_receive_packets_dropped_total`、`container_network_transmit_packets_dropped_total` | 使用 `rate(...[1m])` 或故障窗口 `increase()` |
| Network error | `container_network_receive_errors_total`、`container_network_transmit_errors_total` | 使用 `rate(...[1m])` 或故障窗口 `increase()` |

cAdvisor 必须显式启用 `oom_event` 指标组。所有表中列出的原始指标必须通过实际 `/metrics` 输出验证，不能只以 cAdvisor 文档存在该指标作为验收通过。指标定义以 [cAdvisor Prometheus metrics](https://github.com/google/cadvisor/blob/master/docs/storage/prometheus.md) 为依据。

### 9.3 Docker 宿主机指标契约

Collector `hostmetrics` 至少启用 `cpu`、`memory`、`filesystem`、`disk`、`network` scraper，并采集：

- `system.cpu.time`、`system.cpu.utilization`。
- `system.memory.usage`、`system.memory.limit`、`system.memory.utilization`。
- `system.filesystem.usage`、`system.filesystem.limit`、`system.filesystem.utilization`。
- `system.disk.io`、`system.disk.operations`、`system.disk.io_time`、`system.disk.operation_time`。
- `system.network.io`、`system.network.packet.dropped`、`system.network.errors`。

Collector 使用 system resource detector 为这些指标补充稳定的 `host.name`、`host.id`、`os.type` 和 `deployment.environment.name=local`；Prometheus exporter 只把这些查询必需的资源属性复制为 metric labels，不启用无选择的全量 resource-to-label 转换。

宿主机 filesystem 过滤 `proc`、`sysfs`、`devtmpfs`、`devpts`、`tmpfs`、`overlay`、`squashfs`、`cgroup`、`cgroup2` 等虚拟文件系统，只保留承载 Docker data-root 和 TripSphere 数据卷的真实 mountpoint。磁盘平均 latency 使用同一 `system.device` 和读写方向上的 `rate(system.disk.operation_time) / rate(system.disk.operations)`；operations 为 0 时显示 unavailable。

### 9.4 OpenTelemetry semantic conventions

OpenTelemetry 已定义 system 与 container metric semantic conventions，但当前 container metrics 规范整体仍处于 Development。Phase 6 遵循以下策略：

- `hostmetrics` 保留 OTel 标准 `system.*` 名称、UCUM unit 和 `system.device`、`system.filesystem.mountpoint`、`disk.io.direction`、`network.io.direction` 等标准属性。
- cAdvisor 原生指标在 Prometheus 中保持原名，不通过 transform 伪装成 OTel 指标；只在设计和数据字典中记录概念映射。
- CPU 对应 `container.cpu.time` / `container.cpu.usage`，内存对应 `container.memory.usage` / `container.memory.working_set`，块 I/O 对应 `container.disk.io`，网络字节对应 `container.network.io`，文件系统对应 `container.filesystem.usage` / `container.filesystem.capacity`。
- CPU limit/throttling、memory limit、OOM、network drop/error 和 container I/O latency 当前没有覆盖完整且稳定的 container semantic convention，因此保留 cAdvisor 指标作为公开原始契约，不创建私有但貌似标准的 `container.*` 名称。
- 本阶段是 Docker Compose，不引入 `k8s.*` resource attributes 或 Kubernetes metric conventions。

语义约定以 [OTel container metrics](https://opentelemetry.io/docs/specs/semconv/system/container-metrics/) 和 [OTel system metrics](https://opentelemetry.io/docs/specs/semconv/system/system-metrics/) 为依据。Collector Prometheus exporter 显式固定 `translation_strategy: UnderscoreEscapingWithSuffixes`，并以当前锁定的 Collector `0.144.0` 做输出名称契约测试，防止升级后单位或 `_total` 后缀变化导致查询静默失效。

### 9.5 Recording rules 与 Dashboard 查询契约

新增 Prometheus recording rules，将原始实现差异收敛为 Dashboard 和 RCA 查询使用的稳定序列：

```text
tripsphere:container_cpu_usage_cores:rate1m
tripsphere:container_cpu_limit_cores
tripsphere:container_cpu_utilization:ratio
tripsphere:container_cpu_throttled_periods:ratio1m
tripsphere:container_cpu_throttled_seconds:rate1m
tripsphere:container_memory_utilization:ratio
tripsphere:container_oom_events:increase5m
tripsphere:container_filesystem_utilization:ratio
tripsphere:container_disk_read_bytes:rate1m
tripsphere:container_disk_write_bytes:rate1m
tripsphere:container_disk_read_latency_seconds:rate1m
tripsphere:container_disk_write_latency_seconds:rate1m
tripsphere:container_network_receive_bytes:rate1m
tripsphere:container_network_transmit_bytes:rate1m
tripsphere:container_network_receive_drops:rate1m
tripsphere:container_network_transmit_drops:rate1m
tripsphere:container_network_receive_errors:rate1m
tripsphere:container_network_transmit_errors:rate1m
tripsphere:host_filesystem_utilization:ratio
tripsphere:host_disk_io_latency_seconds:rate1m
```

基础 dashboard 至少展示服务 RED、容器 CPU、容器内存/OOM、容器网络、容器 I/O、宿主机文件系统/磁盘，以及 `up`/健康状态和 Collector pipeline 自身状态。Phase 6 不引入 Alertmanager、通知链路或告警阈值；recording rules 只用于稳定查询、Dashboard 和 RCA 数据采集。

## 10. 存储与保留策略

Loki、Tempo、Prometheus、Grafana 和 Collector file storage 使用本地持久卷，单实例运行。

统一保留窗口为 7 天：

- Tempo Trace 保留 168 小时。
- Loki 使用 TSDB + filesystem 和 Compactor，保留 168 小时。
- Prometheus 使用 `--storage.tsdb.retention.time=7d`。

Loki 启用 structured metadata，并使用原生 OTLP HTTP ingestion。文件系统存储只用于本地开发和实验，不声明为生产级持久化或高可用方案。

## 11. Grafana 预置

通过版本库内配置文件预置以下数据源：

| 数据源 | 容器内地址 | 固定 UID |
| --- | --- | --- |
| Prometheus | `http://prometheus:9090` | `prometheus` |
| Tempo | `http://tempo:3200` | `tempo` |
| Loki | `http://loki:3100` | `loki` |

Tempo 数据源配置 trace-to-logs：

- 按 `service.name -> service` 映射缩小日志范围。
- 启用 trace ID 过滤。
- 时间窗口默认扩展 Span 前后 2 秒。

Loki 数据源配置 derived field：

- 从 `trace_id` 提取 Trace ID。
- 使用内部链接跳转到 UID 为 `tempo` 的数据源。

基础 dashboard 提供八个区域：

1. 服务、容器和观测管线健康状态。
2. RED 指标：请求率、错误率和延迟。
3. 容器 CPU usage、limit、utilization 和 throttling。
4. 容器 memory usage、limit、utilization 和 OOM events。
5. 容器网络收发、packet drop 和 network error。
6. 容器 filesystem usage、disk throughput、IOPS 和可用时的 best-effort latency。
7. Docker 宿主机 filesystem utilization 和物理磁盘 I/O latency。
8. 日志与 Trace 查询及双向跳转。

资源面板只使用第 9.5 节定义的 `tripsphere:*` recording rules。无限资源限制、零 I/O operations 和平台不支持的指标统一显示 N/A，不通过填 0 制造正常状态。

dashboard 只服务单实例验收与故障实验观察，不增加告警升级、容量规划和 HA 面板。

## 12. Higress 自动初始化

新增一次性 `higress-init` 服务，在 Higress readiness 成功后幂等配置 OpenAI-compatible provider 和模型路由。

输入环境变量：

```text
HIGRESS_UPSTREAM_BASE_URL
HIGRESS_UPSTREAM_API_KEY
HIGRESS_CHAT_MODEL
HIGRESS_EMBEDDING_MODEL
```

约束：

- 四个变量在需要启动 AI 服务的完整验收环境中均为必填。
- API key 只能通过环境或未提交的 `.env` 提供，不写入 Compose、脚本、日志或 dashboard。
- 初始化逻辑先查询现有 provider/route，再创建或更新，因此重复运行结果一致。
- 对内统一暴露 `/v1/chat/completions` 和 `/v1/embeddings`。
- chat 与 embedding 分别发送最小 smoke 请求，任一失败时 `higress-init` 退出非零。
- chat、planner、order-assistant、review-summary 和 worker 依赖 `higress-init` 成功完成，而不只依赖 Higress 容器进程启动。
- 初始化和 smoke 日志只记录 provider 类型、模型名、状态码和耗时，不记录 API key 或完整请求/响应正文。

具体 management API payload 必须以仓库固定的 Higress `2.1.11` 镜像实际接口为准，并由契约测试验证；不得改用未锁版本的 `latest` 接口。

## 13. Nacos 与必要依赖

- 所有 Java gRPC 服务在 Nacos 注册 `gRPC_port` 和 `protocol=grpc` metadata。
- Python discovery 客户端不使用默认端口掩盖缺失 metadata。
- smoke test 通过 Python Nacos SDK 查询健康实例，并使用返回的 host、`gRPC_port` 建立真实 gRPC channel。
- planner 验证发现 attraction/hotel；order-assistant 验证发现 product/order。
- Nacos 不可用或服务注册失败时，依赖发现的应用启动/readiness 必须失败。
- Higress、数据库、Redis、Qdrant、Neo4j、MinIO 等必要依赖不可用时，服务不得回退到 localhost、假数据或固定 healthy。
- readiness 表示服务能够承担其 Phase 6 验收职责；liveness 只表示进程存活，两者不得混为一个永远成功的端点。

## 14. 实施顺序

### Task 1：锁定 Compose 契约和配置校验

- 定义保留服务与基础设施清单。
- 修正 deploy Compose 相对路径和环境变量默认/必填语义。
- 增加静态测试，分别解析两份 Compose，并比较保留集合、端口、卷、healthcheck 和必要依赖。
- 保持 Phase 7 待删项不变。

### Task 2：建设 Loki 与 Collector 三信号管线

- 增加 Loki 单实例 TSDB/filesystem 配置和 7 天保留。
- 扩展 Collector receivers、processors、connectors、exporters 和 extensions。
- 增加 filelog offset 持久化、Docker 日志目录和 `/hostfs` 只读挂载。
- 增加字段规范化、敏感属性删除和 body 遮蔽规则。
- 增加 Collector、Loki 的真实 healthcheck。

### Task 3：补齐 Metrics 和 Prometheus

- 在两份 Compose 中加入固定版本 cAdvisor，配置必要宿主机挂载、权限、healthcheck 和 `oom_event` 指标组。
- 接入 Collector `hostmetrics` 与 `spanmetrics`；不得启用 `docker_stats`。
- 增加 cAdvisor、Collector 自身、应用 exporter、Java Actuator 和可用基础设施 metrics targets。
- 规范化 Compose `service`/`environment` labels，并加入第 9.5 节定义的 recording rules。
- 配置 Prometheus 7 天保留和持久卷。
- 验证容器、宿主机和 RED 指标包含稳定标识；验证 Collector `0.144.0` 的 OTel→Prometheus 指标名转换契约。

### Task 4：统一应用遥测和关联字段

- Java：结构化日志、Actuator、OTel resource 与 readiness。
- Python：结构化 logging、请求/任务 context、真实 readiness。
- Go：OTel SDK、gRPC instrumentation、trace-aware `slog` 和强依赖 Nacos。
- Next.js：request ID、服务端日志和 health endpoint。
- 补 HTTP、gRPC、A2A、Celery 的关联上下文传播，并禁止重复 OTLP logs。

### Task 5：预置 Grafana

- 增加三个数据源 provisioning 文件。
- 配置 Tempo↔Loki 双向关联。
- 增加服务健康/资源、RED、日志关联、Trace 查询 dashboard。
- Grafana 依赖 Prometheus、Tempo、Loki 健康后启动。

### Task 6：自动初始化 Higress 并验证 Nacos

- 实现幂等 `higress-init`。
- 增加 chat/embedding 两类 smoke。
- 增加 Nacos 注册 metadata 和 Python→Java discovery smoke。
- 把必要 AI/discovery 初始化结果纳入应用依赖和 readiness。

### Task 7：端到端验收与文档

- 从干净的观测数据卷启动 root Compose。
- 运行初始化数据流程并执行订单关联样本。
- 使用 API 与 Grafana 验证 Logs、Metrics、Traces。
- 验证 deploy Compose 独立解析及保留集合一致。
- 在 README 中记录启动参数、查询示例、健康检查、权限风险和清理方法。

## 15. 测试与验收计划

### 15.1 静态配置测试

- `docker compose config` 在提供明确测试环境变量后成功。
- deploy Compose 从自身目录和仓库根目录指定 `-f` 时均能解析到正确路径。
- 两份 Compose 的保留集合一致。
- 每个核心基础设施和保留应用都有 healthcheck。
- 应用对必要依赖使用 `service_healthy` 或 `service_completed_successfully`。
- OTel Collector 配置检查通过，且 logs/metrics/traces pipeline 都有非 debug 的实际出口。
- Prometheus 配置和 recording rules 通过 `promtool check config`、`promtool check rules`；Grafana provisioning JSON/YAML 可解析。
- Collector 配置中不存在 `docker_stats`，Prometheus 只有一个 cAdvisor 容器资源 scrape job。
- 仓库追踪文件中不存在真实凭据。

### 15.2 组件测试

- Collector 能读取一条带容器标签的 Docker JSON 日志，并映射正确 service/environment。
- JSON、logfmt 和未解析文本日志都不会导致 pipeline 中断；未解析日志仍保留原始 body 和容器资源属性。
- 敏感属性和正文中的固定假 JWT/password/API key 均被遮蔽。
- cAdvisor、Collector exporter 和 Prometheus targets 均为 `up`；每个保留 Compose 服务都有非空 `service` 和 `environment` label。
- cAdvisor 实际暴露第 9.2 节要求的 CPU、内存、文件系统、块 I/O、网络和 OOM 原始指标。
- Collector `hostmetrics` 从 `/hostfs` 采集宿主机指标，而不是 Collector 容器自身指标；虚拟文件系统不进入正式 Dashboard。
- 第 9.5 节所有 recording rules 均能查询；不适用或不受平台支持的 utilization/latency 序列为空而不是伪造为 0。
- 同一容器不存在来自 cAdvisor 与 Collector `docker_stats` 的重复资源时间序列。
- span metrics 能从成功和失败 Span 生成请求数、错误数和延迟。
- Loki、Tempo、Prometheus 重启后数据卷仍可查询，且保留参数为 7 天。
- Grafana 启动后 API 返回三个预置数据源和基础 dashboard。

### 15.3 各语言 focused tests

- Java 使用各服务 `./mvnw test`，验证 Actuator、日志字段和 Trace context。
- Python 使用 `uv run pytest`，验证 formatter、context propagation、readiness 和敏感信息不落日志。
- Go 使用 `go test ./...`，验证 gRPC OTel、日志关联、Nacos 启动失败和 graceful shutdown。
- Next.js 使用 `bun -b run lint`、`bun -b run build` 及现有测试入口，验证 request ID 和服务端/客户端边界。

### 15.4 基础设施 smoke

至少验证：

```text
Nacos readiness
Higress readiness
higress-init completed successfully
MongoDB ping
PostgreSQL pg_isready
Redis PING
Qdrant health
Neo4j protocol query
MinIO health
OTel Collector health
Tempo ready
Prometheus ready
cAdvisor ready
Loki ready
Grafana health
```

Higress smoke 必须分别调用：

```text
POST /v1/chat/completions
POST /v1/embeddings
```

Nacos smoke 必须由 Python 客户端发现至少一个 Java gRPC 服务并完成真实 RPC/Health 调用，不能只查询 Nacos HTTP 列表。

### 15.5 三信号关联验收

固定使用订单闭环作为自动关联样本：

1. 使用初始化数据和认证用户选择有效 SKU。
2. 生成唯一 `request_id`，创建订单并锁定库存。
3. 执行模拟支付，验证订单为 `PAID` 且库存锁已确认；另一个独立用例创建后取消，验证库存释放。
4. 从返回 header 或 Trace 查询获得 `trace_id`。
5. Loki 按 `request_id` 和 `trace_id` 查询 frontend、order、product、inventory 的关联日志。
6. Tempo 按 `trace_id` 查询跨服务 Span，确认父子关系和错误状态正确。
7. Prometheus 查询对应服务 RED 指标，并查询订单链涉及容器的资源指标。
8. Prometheus 查询 Docker 宿主机文件系统利用率和物理磁盘 I/O latency，确认数据卷所在设备在同一时间窗可观察。
9. Grafana dashboard 展示同一时间窗，并能在 Trace 和日志之间跳转。

### 15.6 资源指标受控验收

使用专用测试容器和临时卷执行，不修改业务服务基线，也不填满宿主机真实文件系统：

- CPU stress：确认 `container_cpu_usage_seconds_total` 增长，CPU cores recording rule 非零。
- CPU quota stress：确认 throttled periods/time 增长，CPU utilization 只在有效 quota 下出现。
- Memory limit：在受控小内存限制下触发测试进程 OOM，确认 `container_oom_events_total` 和五分钟增量规则增长，并能关联容器重新启动时间。
- Disk I/O：在专用临时卷执行读写，确认容器 throughput/IOPS 与宿主机磁盘 operations/operation time 同时变化。
- Network traffic：在两个测试容器间产生流量，确认 receive/transmit bytes 增长；drop/error 指标必须存在，即使正常路径下值为 0。
- cgroup v1/v2：记录运行环境能力。容器 latency 在底层不支持时允许 unavailable，但宿主机磁盘 latency 必须可查询。

### 15.7 失败场景

- Collector 暂时不可用时，应用业务进程不因同步遥测导出永久阻塞；恢复后新数据可继续上报。
- Loki 不可用时 Collector 明确暴露 exporter 失败指标和错误日志，不能静默丢弃。
- Nacos 不可用时依赖发现的服务 readiness 失败。
- Higress 初始化失败时 AI 服务不进入 ready 状态。
- 数据库、Redis、Qdrant、Neo4j 或 MinIO 不可用时，对应服务不返回固定 healthy。
- 非法/缺失 request ID 不污染其他请求上下文；服务生成新的合法 ID。
- 敏感字段即使被错误写入结构化属性，也会在 Collector 出口前删除或遮蔽。

## 16. 完成标准

只有同时满足以下条件，Phase 6 才可判定完成：

- root Compose 能启动所有保留业务服务和必需基础设施，核心依赖达到 healthy/completed 状态。
- deploy Compose 可独立解析，并同步包含全部保留职责。
- Loki、Tempo、Prometheus、Grafana 均使用单实例本地卷和 7 天保留。
- OTel Collector 的 Logs、Metrics、Traces 都有真实接收、处理和后端出口，不以 debug exporter 代替存储。
- Collector 能采集业务 stdout/stderr、应用遥测和 Docker 宿主机指标；cAdvisor 能采集保留容器资源指标。
- Prometheus 可查询 CPU time/usage/utilization/throttling、memory usage/utilization/limit、OOM、filesystem usage、disk throughput/IOPS/latency、network receive/transmit/drop/error；不适用或平台不支持的指标明确为 unavailable。
- Dashboard 和 RCA 查询使用稳定的 `tripsphere:*` recording rules，且不存在 `docker_stats` 与 cAdvisor 重复采集。
- 日志可按 service、environment、severity、request_id、trace_id、user_id、task_id 查询。
- JWT、密码、API key 和认证 header 不出现在 Loki 验收结果中。
- Grafana 已预置 Prometheus、Tempo、Loki，并能关联 Trace 与日志。
- 一次真实订单请求可在 Logs、Metrics、Traces 中用 request ID/trace ID 关联定位。
- Higress chat 和 embedding 路由在全新环境中可幂等初始化并通过 smoke。
- Python gRPC 客户端能通过 Nacos 发现 Java 服务并完成真实调用。
- 必要依赖失败时服务失败可见，不静默回退到 localhost、假数据或固定健康。

## 17. 下次 Review 重点

下次计划 Review 应重点确认：

1. 用 OTel Collector 替代 Alloy 是否作为 Phase 6 的最终需求修订写回 `docs/服务改造清单.md`。
2. cAdvisor 的 privileged、`/dev/kmsg` 和宿主机目录挂载风险是否可接受；该部署不得直接作为生产模板。
3. Higress `2.1.11` 的自动初始化 API、认证方式和幂等更新语义是否已通过实际镜像验证。
4. 日志正文脱敏规则是否会误删 RCA 所需的错误上下文。
5. request ID 在 Next.js、A2A、gRPC 和 Celery 边界的具体落点是否覆盖完整。
6. 当前 Docker storage driver 与 cgroup 版本是否能输出容器 filesystem 和 I/O time；若不能，Dashboard 是否正确显示 unavailable 并回退到宿主机证据。
7. Java Actuator 指标与 OTel Java Agent 指标是否存在需要去重的同义指标。
8. 订单闭环是否继续作为唯一自动三信号关联样本，或增加 AI 行程作为人工补充验收。
