# Phase 6.3 Metrics PR 拆分与验收计划

**分支：** `phase6.3-metrics`

**基线：** `phase6.2-logs/afdc39f`

**当前状态：** 仅完成任务拆分和检查，不创建 commit，不创建 PR，不推送远端。

## 1. 拆分原则

- 每个文件只归属一个 PR，避免后续协作者在同一文件上重复解决冲突。
- 两份 Compose 文件中的 Phase 6.3 配置集中放在 PR-1；应用代码 PR 不重复修改 Compose。
- 文档不单独设 PR：
  - Phase 6.3 范围和基础设施设计随 PR-1 提交。
  - 最终观测清单随 PR-7 提交。
- 每个 PR 可以包含多个语义明确的 commit。
- “可以提交 review”只表示该部分可以独立进入代码审查，不表示整个 Phase 6.3 已完成。

## 2. 合并顺序

推荐顺序：

```text
PR-1 基础设施、Prometheus 抓取和设计文档
  -> PR-2 OTel Collector 和 Tempo
  -> PR-3 Java
  -> PR-4 Python
  -> PR-5 Go
  -> PR-6 原始指标化收敛
  -> PR-7 Grafana 和最终验收清单
```

PR-3、PR-4、PR-5 在 PR-1 和 PR-2 完成后可以并行 review。PR-6 负责删除派生指标写入和 scrape 阶段 label 清洗，PR-7 基于原始指标完成 dashboard 和最终验收清单。

## 3. PR-1：基础设施、Compose、Prometheus 和设计文档

### 文件

- `docker-compose.yaml`
- `deploy/docker-compose/docker-compose.yaml`
- `infra/prometheus/prometheus.yaml`
- `docs/phase6-metrics-plan.md`
- `docs/phase6-deployment-observability-design.md`

### 建议 commit

```text
metrics(infra): add cAdvisor and node-exporter services
metrics(infra): wire OTLP metrics and Prometheus scrape targets
docs(metrics): align phase6.3 scope with infrastructure implementation
```

### 改动内容和意义

- 增加 cAdvisor，采集容器 CPU、内存、OOM、文件系统、磁盘 IO、网络、Socket、TCP 和 UDP 指标。
- 增加 node-exporter，采集宿主机 socket、sockstat 和 netstat 指标。
- 为 OTel Collector 增加 `/hostfs` 宿主机只读挂载。
- 为 Python 和 Go 服务配置 OTLP Metrics。
- 为保留的 Java 服务配置 `OTEL_METRICS_EXPORTER=none`，避免 Java Agent 和 Actuator 重复产生指标。
- Prometheus 增加 Collector、cAdvisor、node-exporter、Java Actuator、Loki 和 Tempo targets。
- 增加指标标签清理规则，避免将 trace ID、用户 ID、地址、端口和进程命令行作为高基数 label。
- 文档固定 Phase 6.3 的范围和职责边界，并排除已删除的独立 Note、POI 服务。

### 当前验收

- 两份 Compose 配置校验通过。
- Prometheus 配置校验通过。
- cAdvisor target 正常，能采集容器级指标。
- node-exporter target 正常。
- 当前 Prometheus targets 为 `13/14 up`。
- `trip-user-service` 的 `/actuator/prometheus` 返回 `401`，因此该 target 为 down。
- 当前 Compose 没有设置 CPU quota，CPU limit 和 CFS throttling 原始指标为空。
- 当前文档中的验收状态和已知问题仍需根据最终检查结果补齐。

### 提交条件

**可以提交 review，但不能宣称 Phase 6.3 全部完成。**

PR 描述必须明确：

1. `trip-user-service` 的 Actuator 认证问题属于 Java 服务配置问题，需在 PR-3 闭环。
2. 当前运行环境没有容器资源限制，CPU limit/throttling 只能标记为环境未覆盖。
3. Compose 和 Prometheus 配置依赖 PR-2 至 PR-7 中的文件，建议按本计划顺序合并。

## 4. PR-2：OTel Collector 和 Tempo 指标管道

### 文件

- `infra/otel-collector/config.yaml`
- `infra/tempo/tempo.yaml`

### 建议 commit

```text
metrics(otel): add hostmetrics receiver and Prometheus export
metrics(otel): add hostmetrics receiver and keep metrics raw
```

### 改动内容和意义

- 增加 hostmetrics receiver，采集宿主机 CPU、内存、文件系统、磁盘和网络。
- 不启用 Collector spanmetrics，避免从 Trace 派生服务请求率、错误率和延迟分布。
- Collector metrics pipeline 只接收 OTLP 应用原生 metrics 和 hostmetrics。
- 关闭 Tempo 内置 service graph/span metrics，避免写入 Trace 派生 metrics。

### 当前验收

- Collector 配置校验通过。
- hostmetrics 指标已经进入 Prometheus。
- Prometheus 不再出现 `traces_spanmetrics_*` 或 `traces_span_metrics_*` 序列。
- Tempo 重建后仅启用 `local-blocks`，未再发现 `service-graphs` 或 `span-metrics` processor。
- Collector metrics receiver/exporter refusal/failure counters 均为 0，Prometheus、Collector、Tempo、cAdvisor 和 node-exporter targets 均为 UP。
- 当前没有错误 span，因此错误率暂无结果属于测试流量不足。

### 提交条件

**可以提交 review。**

PR 描述应说明错误率需要通过实际失败请求在各语言原生 HTTP/gRPC metrics 中单独验收。

## 5. PR-3：Java Actuator 指标

### 文件

- `trip-attraction-service/pom.xml`
- `trip-attraction-service/src/main/resources/application.yaml`
- `trip-hotel-service/pom.xml`
- `trip-hotel-service/src/main/resources/application.yaml`
- `trip-inventory-service/pom.xml`
- `trip-inventory-service/src/main/resources/application.yaml`
- `trip-itinerary-service/pom.xml`
- `trip-itinerary-service/src/main/resources/application.yaml`
- `trip-order-service/pom.xml`
- `trip-order-service/src/main/resources/application.yaml`
- `trip-product-service/pom.xml`
- `trip-product-service/src/main/resources/application.yaml`
- `trip-user-service/pom.xml`
- `trip-user-service/src/main/resources/application.yaml`

### 建议 commit

```text
metrics(java): add Actuator and Prometheus registry
metrics(java): expose Prometheus endpoint for retained services
```

### 改动内容和意义

- 添加 `spring-boot-starter-actuator`。
- 添加 `micrometer-registry-prometheus`。
- 暴露 `/actuator/prometheus`。
- 让 Java 服务由 Prometheus 直接抓取 JVM 和应用指标。
- 与 Compose 中的 `OTEL_METRICS_EXPORTER=none` 配合，避免指标重复上报。

### 当前验收

- 6 个 Java 服务的 Prometheus endpoint 正常。
- `trip-user-service` 的 Prometheus endpoint 返回 `401`。
- 当前 Java 指标覆盖为 `6/7`。

### 提交条件

**暂不能作为完成态提交。**

需要先对 `trip-user-service` 选择并实现一种访问策略：

- 对内部 Prometheus 抓取路径放行。
- 为 Prometheus 配置 Basic Auth。
- 为 management endpoint 配置独立的内部认证策略。

## 6. PR-4：Python runtime、HTTP 和 Celery 指标

### 文件

- `trip-chat-service/Dockerfile`
- `trip-chat-service/src/chat/asgi.py`
- `trip-chat-service/src/chat/metrics.py`
- `trip-itinerary-planner/Dockerfile`
- `trip-itinerary-planner/src/itinerary_planner/asgi.py`
- `trip-itinerary-planner/src/itinerary_planner/metrics.py`
- `trip-order-assistant/Dockerfile`
- `trip-order-assistant/src/order_assistant/asgi.py`
- `trip-order-assistant/src/order_assistant/metrics.py`
- `trip-review-summary/Dockerfile`
- `trip-review-summary/src/review_summary/asgi.py`
- `trip-review-summary/src/review_summary/metrics.py`
- `trip-review-summary/src/review_summary/celery.py`

### 建议 commit

```text
metrics(python): add runtime and HTTP instruments
metrics(python): configure OTLP metric export
metrics(celery): record review-summary worker task metrics
```

### 改动内容和意义

- 增加 Python CPU、内存、线程、文件描述符和进程运行时间指标。
- 增加 HTTP 请求数、耗时、方法和状态码指标。
- 在 ASGI 层接入 metrics middleware。
- 增加 Review Summary Celery worker 的 task 执行、成功、失败和耗时指标。
- 通过 OTLP 将指标发送到 Collector。

### 当前验收

- 5 个 Python 进程实例都能看到 runtime metrics。
- HTTP 请求指标已经产生。
- `trip-review-summary-worker` 的 Celery 指标存在。
- 指标时间戳保持新鲜。
- 当前缺少专门的 Python 单元测试和 middleware 测试。

### 提交条件

**可以提交 review。**

PR 描述中应标记运行时链路已验证、单元测试仍存在覆盖缺口。

## 7. PR-5：Go runtime 指标

### 文件

- `trip-review-service/cmd/server/main.go`
- `trip-review-service/internal/telemetry/metrics.go`
- `trip-review-service/go.mod`
- `trip-review-service/go.sum`

### 建议 commit

```text
metrics(go): add OTLP meter provider and runtime instruments
metrics(go): initialize and gracefully shut down metrics provider
```

### 改动内容和意义

- 增加 OTLP Metrics exporter。
- 增加 goroutine、CPU、heap allocation 和 sys memory 指标。
- 在服务启动时初始化 MeterProvider。
- 在服务退出时执行 shutdown，保证剩余指标刷新。

### 当前验收

- Go metrics 包和服务可以编译。
- Prometheus 已采集到 `trip-review-service` 的 Go 指标。
- 当前没有显式 native gRPC 请求数、耗时和错误指标。
- 服务请求率必须来自 Go 服务自身的原生 gRPC/RPC metrics，不能再由 spanmetrics 替代。
- 完整 `go test ./...` 仍存在已有的认证测试失败，错误为 `Unauthenticated`。

### 提交条件

**暂不能作为完整 Phase 6.3 实现提交。**

需要二选一：

1. 补充 gRPC server metrics。
2. 若不补充 gRPC/server metrics，则明确该服务请求指标在 Phase 6.3 中未闭环，并同步更新设计文档。

已有认证测试失败需要在 PR 描述中单独说明。

## 8. PR-6：原始指标化收敛

### 文件

- `infra/prometheus/prometheus.yaml`
- `infra/otel-collector/config.yaml`
- `infra/grafana/dashboards/tripsphere-metrics.json`

### 建议 commit

```text
metrics(prometheus): keep scraped metrics raw
metrics(otel): remove trace-derived metrics
grafana(metrics): query raw metrics directly
```

### 改动内容和意义

- 删除 Prometheus `rule_files` 和 `infra/prometheus/rules/*.yaml`，停止写入 `tripsphere:*` recording rules。
- 删除 Prometheus scrape 阶段 labeldrop 和 Java `service` 衍生 relabel，避免采集层改写原始指标。
- 删除 Collector spanmetrics pipeline，停止写入 Trace 派生 RED metrics。
- Grafana dashboard 改为直接查询 cAdvisor、hostmetrics、node-exporter 和应用原生 HTTP/gRPC 指标。

### 当前验收

- `promtool check config` 通过，配置不包含 `rule_files`。
- Prometheus active rule groups 为空。
- `tripsphere:*`、`traces_spanmetrics_*`、`traces_span_metrics_*` 查询为空。
- 原始 `container_*`、`system_*`、`node_*`、`http_*`、`grpc_*`、`rpc_*` 指标仍可查询。
- 所有 Prometheus rule group 均为 `health=ok`。
- 规则评估错误为 0。
- 服务请求率规则已经产生数据。
- 错误率规则暂无结果，因为当前测试窗口没有错误 span。
- CPU limit、CFS throttling 和 memory utilization 规则为空，原因是环境没有设置对应资源限制。

### 提交条件

**可以提交 review。**

必须在验收记录中注明资源限制为空属于当前运行环境事实，不能解释为 Prometheus 规则或采集链路故障。

## 9. PR-7：Grafana Dashboard 和最终验收清单

### 文件

- `infra/grafana/provisioning/dashboards/dashboards.yaml`
- `infra/grafana/dashboards/tripsphere-metrics.json`
- `docs/phase6-metrics-observation-checklist.md`

### 建议 commit

```text
grafana(metrics): provision TripSphere metrics dashboard
grafana(metrics): add service and infrastructure panels
docs(metrics): record phase6.3 acceptance results and known gaps
```

### 改动内容和意义

- 配置 Grafana 自动加载 Dashboard。
- 增加容器、主机和服务级指标面板。
- 增加服务筛选变量。
- 在验收清单中记录 Prometheus、Collector、应用指标和 Grafana 的最终结果。

### 当前验收

- Dashboard JSON 和 provisioning 配置已经生成。
- 当前包含 10 类基础面板。
- 尚未完成 Grafana Web UI 人工确认。
- 当前还需要确认或补充：
  - OOM。
  - CPU throttling。
  - 网络 drops/errors。
  - 文件系统使用率。
  - 原生 HTTP/gRPC latency。
  - Collector/Prometheus target health。
  - Python、Go、Java runtime 细节。

### 提交条件

**可以作为 Dashboard MVP 提交 review，但不能作为 Phase 6.3 最终完成态提交。**

需要完成 Grafana Web UI 验收，并将结果写入 `docs/phase6-metrics-observation-checklist.md`。

## 10. 当前整体门禁

### 可以提交 review 的部分

- PR-2：Collector 和 Tempo。
- PR-4：Python 指标。
- PR-6：原始指标化收敛。
- PR-1：基础设施配置，但必须带已知问题说明。

### 需要先闭环的部分

- PR-3：`trip-user-service` 的 `/actuator/prometheus` 返回 `401`。
- PR-5：Go native gRPC/server metrics 需求尚未闭环。
- PR-7：Grafana Web UI 验收和完整面板覆盖尚未完成。

### 不应误判为故障的结果

- 当前没有错误请求，所以 error ratio 查询为空。
- 当前没有 CPU/memory quota，所以 CPU limit、throttling 和 memory utilization 相关原始序列或查询结果为空。
- 已删除的独立 Note、POI 服务不应作为 Phase 6.3 Java 指标缺失统计。

### 当前结论

Phase 6.3 的实现可以拆成上述 7 个 PR，但当前工作区还不能宣称“所有指标完整覆盖并通过最终验收”。提交前至少需要处理 Java user service 认证问题、Go gRPC 指标口径、Grafana 人工验收和最终清单记录。

## 11. PR-1 实测检查记录

**检查日期：** 2026-09-14

**检查范围：** root Compose、deploy Compose、Prometheus 配置、运行中的 Prometheus/cAdvisor/node-exporter，以及 PR-1 相关挂载和环境变量。

### 11.1 静态配置结果

| 检查项 | 结果 |
| --- | --- |
| root Compose `config --quiet` | 通过 |
| deploy Compose `config --quiet` | 通过 |
| Prometheus `promtool check config` | 通过，发现 1 个 rule file |
| `tripsphere-metrics.yaml` `promtool check rules` | 通过，共 52 条规则 |
| Git 冲突文件检查 | 通过，无未合并文件 |
| `git diff --check` | 通过 |

从仓库根目录执行 deploy Compose 时，推荐显式使用绝对环境文件路径：

```bash
docker compose \
  -f deploy/docker-compose/docker-compose.yaml \
  --env-file /home/wws/TripSphere/.env \
  config --quiet
```

如果当前工作目录是 `deploy/docker-compose`，则应使用 `--env-file ../../.env`。

### 11.2 数据目录路径结果

当前 `.env` 中 `TRIPSPHERE_DATA_ROOT` 为空，两份 Compose 都解析到：

```text
/home/wws/TripSphere/volumes
```

使用绝对路径时，两份 Compose 也会解析到同一目录。例如：

```text
TRIPSPHERE_DATA_ROOT=/tmp/tripsphere-phase6-data
```

会在两份 Compose 中解析为同一个 `/tmp/tripsphere-phase6-data/...` 路径。

非绝对路径存在两个问题：

| 输入 | root Compose | deploy Compose | 结果 |
| --- | --- | --- | --- |
| `phase6-relative-data` | 被识别为未声明 named volume | 被识别为未声明 named volume | Compose 直接失败 |
| `./phase6-relative-data` | `/home/wws/TripSphere/phase6-relative-data` | `/home/wws/TripSphere/deploy/docker-compose/phase6-relative-data` | 两份 Compose 数据分叉 |

因此，`TRIPSPHERE_DATA_ROOT` 非空时必须是绝对路径。当前配置没有自动阻止相对路径，部署脚本或人工验收流程必须执行该门禁。

### 11.3 运行时采集结果

Prometheus readiness 返回成功，当前 targets 为：

```text
total=14
up=13
down=1
```

正常的基础设施 targets：

```text
cadvisor:8080
host.docker.internal:19100
otel-collector:8889
otel-collector:8888
prometheus:9090
loki:3100
tempo:3200
```

cAdvisor 和 node-exporter 的健康检查均正常。Prometheus 查询到的典型原始序列数量如下：

| 原始指标 | 当前序列数量 |
| --- | ---: |
| `container_cpu_usage_seconds_total` | 36 |
| `container_memory_working_set_bytes` | 36 |
| `container_network_receive_bytes_total` | 36 |
| `container_sockets` | 36 |
| `system_cpu_time_seconds_total` | 224 |
| `node_sockstat_TCP_inuse` | 1 |

当前 cAdvisor 样本应保留原始容器维度。除 Prometheus target 附加的 `job`、`instance`、`app`、`environment` 外，重点检查以下 cAdvisor 原始 label 是否仍可查询：

```text
app
environment
id
image
instance
job
name
container_label_com_docker_compose_service
```

不再要求 Prometheus 为 cAdvisor 指标生成 TripSphere 专用 `service`/`container` 衍生 label，也不再通过 `labeldrop` 删除 `id`、`image`、`name` 或 `container_label_*`。RCA 数据集导出阶段按实验元数据筛选和关联这些原始 labels。

### 11.4 已发现的问题

#### P1：`trip-user-service` Actuator endpoint 返回 401

Prometheus target：

```text
job=java-services
instance=trip-user-service:24217
health=down
```

直接访问：

```text
GET http://localhost:24217/actuator/health
-> 200

GET http://localhost:24217/actuator/prometheus
-> 401
WWW-Authenticate: Basic realm="Realm"
```

这说明服务存活，但 Prometheus 无法匿名抓取指标。该问题归属 PR-3，不是 cAdvisor、Prometheus target 地址或 Compose 网络问题。PR-3 必须放行内部抓取路径或为 Prometheus 配置认证。

#### P2：当前环境没有 CPU 和 memory quota

运行中的容器检查到：

```text
CpuQuota=0
Memory=0
```

cAdvisor 中也没有有效的 `container_spec_cpu_quota`、CFS throttling 系列，`container_spec_memory_limit_bytes` 为 0。该结果表示当前容器没有配置资源限制，不能用于证明资源限制指标采集失败。若要验收这些指标，需要使用配置了 `cpus`、`cpu_quota` 或 `mem_limit` 的受控 Compose 环境。

#### P2：Prometheus 使用 root 运行存在安全权衡

Prometheus 镜像默认用户为 `nobody`，当前 `/home/wws/TripSphere/volumes/prometheus` 是 `root:root` 且权限为 `755`，因此当前新增的 `user: root` 能保证 bind mount 数据目录可写。

该配置目前没有功能故障，但扩大了 Prometheus 容器权限。后续可以考虑：

- 将数据目录调整为 Prometheus 运行用户可写。
- 使用 Docker named volume。
- 保留 `user: root`，但在部署安全说明中明确原因和风险。

### 11.5 PR-1 结论

PR-1 的 Compose、Prometheus、cAdvisor、node-exporter 和原始 cAdvisor label 保留策略已通过当前环境的静态和运行时检查，**可以提交代码 review**。

提交时必须附带以下未闭环项：

1. PR-3 解决 `trip-user-service` 的 `/actuator/prometheus` 认证问题。
2. 部署验收强制要求非空 `TRIPSPHERE_DATA_ROOT` 使用绝对路径。
3. 当前环境未配置 CPU/memory quota，CPU limit、CFS throttling 和 memory utilization 不能标记为已验证。
4. `user: root` 是当前 root-owned bind mount 的权限方案，需要协作者进行安全审查。

因此，PR-1 可以进入 review，但不能作为 Phase 6.3 全部通过的依据。
