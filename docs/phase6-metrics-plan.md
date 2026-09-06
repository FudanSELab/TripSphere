# Phase 6 Metrics 设计与执行计划

**文档状态：** 待 Review  
**实施顺序：** 3 / 3  
**前置条件：** Trace 基线与 Java/Python/Go OTLP Logs 已通过  
**目标：** 先建立故障注入与 RCA 所需的容器资源指标，再补充宿主机和服务 RED 指标。

## 1. 调研结论与决策

指标按观测对象分配唯一来源：

- cAdvisor：Docker 容器 cgroup CPU、内存、OOM、filesystem、块 I/O 和网络。
- Collector `hostmetrics`：Docker 宿主机 CPU、内存、filesystem、物理磁盘和网络。
- 现有应用端点/OTLP：语言运行时及框架已经生成的指标。
- Collector `spanmetrics`：从已验收 Trace 派生跨语言 RED 指标。

不启用 Collector `docker_stats`，避免与 cAdvisor 重复。Tempo metrics-generator 与 Collector spanmetrics 不能同时写入同一组 RED 指标；本计划选择 Collector spanmetrics，并关闭 Tempo 的 `span-metrics`/`service-graphs` 生成器。若执行时决定保留 Tempo metrics-generator，则必须删除 Collector spanmetrics 任务，不得双写。

OpenTelemetry system/container semantic conventions 作为概念和属性对齐依据；cAdvisor 原始 Prometheus 指标保持原名，不伪装成 OTel 指标。

官方依据：

- [OTel Metrics Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/general/metrics/)
- [OTel System Metrics](https://opentelemetry.io/docs/specs/semconv/system/system-metrics/)
- [OTel Container Metrics](https://opentelemetry.io/docs/specs/semconv/system/container-metrics/)
- [Collector Host Metrics Receiver](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/receiver/hostmetricsreceiver/README.md)
- [Collector Span Metrics Connector](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/connector/spanmetricsconnector/README.md)
- [cAdvisor Prometheus Metrics](https://github.com/google/cadvisor/blob/master/docs/storage/prometheus.md)
- [Prometheus Recording Rules](https://prometheus.io/docs/prometheus/latest/configuration/recording_rules/)

## 2. 分阶段范围

### 2.1 M1：容器资源核心指标（必须）

- CPU utilization、throttling、CPU time。
- Memory usage、utilization、limit、OOM。
- Container writable layer usage。
- Disk I/O throughput、operations 和可用的 I/O time。
- Network receive/transmit、packet drop 和 error。

### 2.2 M2：宿主机指标（必须）

- 宿主机 CPU、memory、filesystem、物理 disk I/O/latency 和 network。
- 明确区分容器 writable layer、named volume、Docker data-root 和物理设备。

### 2.3 M3：服务指标（M1/M2 通过后）

- 现有 Java/Python/Go 已产生的指标，不为追求形式统一重写 SDK。
- 从 Trace 派生的低基数 RED 指标。
- Collector、Prometheus、cAdvisor 自身健康指标。

### 2.4 不包含

- Alertmanager、生产告警阈值、SLO 和长期容量规划。
- 高可用 Prometheus 或远端长期存储。
- 浏览器 RUM 指标。
- 故障注入控制器与 RCA 数据集导出。

## 3. 指标契约

### 3.1 容器 CPU

| 观测项 | cAdvisor 原始指标 | 查询规则 |
| --- | --- | --- |
| CPU time | `container_cpu_usage_seconds_total` | 累计 CPU 秒，仅用于求 rate/delta |
| CPU usage | 同上 | `rate(...[1m])`，单位 CPU cores |
| CPU limit | `container_spec_cpu_quota` / `container_spec_cpu_period` | quota > 0 时计算 cores |
| CPU utilization | usage cores / limit cores | 仅有有效 quota 时生成 |
| Throttling ratio | `container_cpu_cfs_throttled_periods_total` / `container_cpu_cfs_periods_total` | 两个 counter 的 rate 比值 |
| Throttled time | `container_cpu_cfs_throttled_seconds_total` | `rate(...[1m])` |

无限额容器展示 usage cores，不以宿主机核数冒充容器 limit。

### 3.2 容器内存与 OOM

| 观测项 | cAdvisor 原始指标 | 查询规则 |
| --- | --- | --- |
| Memory usage | `container_memory_usage_bytes` | 含 cache 的总使用量 |
| Working set | `container_memory_working_set_bytes` | Dashboard 主展示值 |
| Memory limit | `container_spec_memory_limit_bytes` | 过滤无限额/宿主机级哨兵值 |
| Utilization | working set / effective limit | 无有效 limit 时返回 N/A |
| OOM events | `container_oom_events_total` | `increase(...[5m])` |
| Memory failures | `container_memory_failures_total` | 作为辅助故障证据 |

`container_oom_events_total` 必须通过目标 Linux/cgroup 环境的 `/metrics` 实测；不能仅因官方指标表存在就判定可用。

### 3.3 容器存储与磁盘 I/O

| 观测项 | cAdvisor 原始指标 | 限制 |
| --- | --- | --- |
| Writable usage | `container_fs_usage_bytes` / `container_fs_limit_bytes` | 不代表 named volume 或物理磁盘容量 |
| Throughput | `container_fs_reads_bytes_total` / `container_fs_writes_bytes_total` | 使用 `rate(...[1m])` |
| Operations | `container_fs_reads_total` / `container_fs_writes_total` | 使用 `rate(...[1m])` |
| Device busy time | `container_fs_io_time_seconds_total` | 只能表达设备忙碌时间，不直接命名为请求 latency |

cAdvisor/cgroup 在不同内核、存储驱动和 cgroup 版本下不保证提供可信的容器级 I/O latency。容器级 latency 缺失时显示 N/A，不用 `io_time / operations` 伪造请求延迟。物理磁盘平均操作耗时由 hostmetrics 的 operation time 与 operations 在同设备、同方向上计算。

### 3.4 容器网络

采集：

```text
container_network_receive_bytes_total
container_network_transmit_bytes_total
container_network_receive_packets_dropped_total
container_network_transmit_packets_dropped_total
container_network_receive_errors_total
container_network_transmit_errors_total
```

所有 counter 用 `rate()` 或实验窗口 `increase()`，不把累计值展示为当前速率。

### 3.5 宿主机

Collector `hostmetrics` 使用：

```text
root_path: /hostfs
collection_interval: 15s
scrapers: [cpu, memory, filesystem, disk, network]
```

宿主机根目录只读挂载到 `/hostfs`。过滤 `proc`、`sysfs`、`tmpfs`、`overlay`、`cgroup` 等虚拟文件系统。System semantic conventions 仍有 Development/Release Candidate 项，Dashboard 和数据字典记录实际 Collector 版本产生的名称，升级时不得无验证改名。

### 3.6 RED 与基数

Collector spanmetrics 仅保留服务分析所需维度：

```text
service.name
span.name
span.kind
status.code
```

URL 原文、request ID、trace ID、user ID、task ID 不得成为 metric labels。`span.name` 必须已经由自动插桩归一化为路由或操作名；发现高基数动态名称时先修复/过滤，再启用 spanmetrics。

## 4. Recording Rules

只有原始指标已在目标环境验证后才创建对应规则：

```text
tripsphere:container_cpu_usage_cores:rate1m
tripsphere:container_cpu_utilization:ratio
tripsphere:container_cpu_throttled_periods:ratio1m
tripsphere:container_cpu_throttled_seconds:rate1m
tripsphere:container_memory_working_set_bytes
tripsphere:container_memory_utilization:ratio
tripsphere:container_oom_events:increase5m
tripsphere:container_disk_read_bytes:rate1m
tripsphere:container_disk_write_bytes:rate1m
tripsphere:container_disk_reads:rate1m
tripsphere:container_disk_writes:rate1m
tripsphere:container_network_receive_bytes:rate1m
tripsphere:container_network_transmit_bytes:rate1m
tripsphere:container_network_receive_drops:rate1m
tripsphere:container_network_transmit_drops:rate1m
tripsphere:container_network_receive_errors:rate1m
tripsphere:container_network_transmit_errors:rate1m
tripsphere:host_filesystem_utilization:ratio
tripsphere:host_disk_operation_latency_seconds:rate1m
tripsphere:service_request_rate:rate1m
tripsphere:service_error_rate:ratio1m
```

不为缺失序列填零。延迟分位数直接查询 spanmetrics histogram，不为每个分位数创建重复 recording rule。

## 5. 执行计划

### Task 1：建立目标环境指标清单

- 记录 Docker、Linux kernel、cgroup mode、storage driver 和 Collector/cAdvisor 版本。
- 保存 cAdvisor 与 hostmetrics 实际暴露的指标名、labels、单位和缺失项。
- 将缺失或语义不可靠的指标标记为 N/A，并记录原因。
- 在清单通过前不编写依赖这些指标的 Dashboard 和 recording rules。

### Task 2：接入 cAdvisor

- 使用固定版本 cAdvisor，并按官方 Docker 运行要求只读挂载宿主机根目录、`/var/run`、`/sys`、Docker data-root 和 `/dev/disk`。
- 仅启用本计划所需指标组，验证 OOM event 所需权限和 `/dev/kmsg` 行为。
- Prometheus 直接 scrape cAdvisor；Collector 不二次接收或重导出同一批容器指标。
- 通过 Compose labels 将容器映射为稳定 service，只保留非空 Compose service 的序列。
- 特权和宿主机挂载只作为本地故障实验方案，不作为生产安全模板。

### Task 3：接入 hostmetrics

- Collector 增加独立 `hostmetrics` receiver 和 `/hostfs` 只读挂载。
- 启用 CPU、memory、filesystem、disk、network scraper 及必要的显式指标开关。
- 配置 filesystem/device include/exclude，验证读到的是宿主机而非 Collector 容器。
- 增加稳定 host/environment resource attributes，不把所有 resource attributes 自动转成 Prometheus labels。

### Task 4：接入 spanmetrics 和现有应用指标

- 先审计 Trace 中的 `span.name` 基数。
- 在 Collector traces pipeline 后接入单个 spanmetrics connector，配置 cumulative temporality、duration buckets、series expiration 和 aggregation cardinality limit。
- Collector metrics pipeline 接收 OTLP、hostmetrics 和 spanmetrics，并通过现有 Prometheus exporter 暴露。
- 从 Tempo 配置移除重复的 `span-metrics` 和 `service-graphs` processor。
- Java/Python/Go 只启用当前依赖已支持的指标；新增 SDK instrumentation 需要单独证明缺口，不能阻塞 M1/M2。

### Task 5：完善 Prometheus 与 Dashboard

- Prometheus scrape 自身、Collector exporter、Collector self-telemetry 和 cAdvisor。
- 加载经过 `promtool check rules` 的 recording rules。
- 提供四个最小视图：采集健康、服务 RED、容器资源、宿主机资源。
- 不支持的指标展示 N/A，并链接到 Task 1 的环境说明。

## 6. 测试计划

### 静态配置

- `docker compose config` 成功。
- Collector 配置加载成功且不存在 `docker_stats`。
- `promtool check config` 与 `promtool check rules` 成功。
- Prometheus 只有一个 cAdvisor scrape job，RED 只有一个 writer。

### 数据契约

- CPU、memory、OOM、filesystem/I/O 和 network 的每个必需原始指标均有实测结果或明确 N/A。
- 每个保留 Compose 服务具有非空且稳定的 service label。
- 无效 limit 和除零场景产生空序列，不产生 0、NaN 或 Inf。
- hostmetrics 资源标识与容器资源标识不会混淆。

### 受控故障负载

- CPU stress 使 usage 增长；有限 quota 实验使 throttling 增长。
- 内存压力使 working set 增长；专用受限测试容器触发 OOM event。
- 临时卷磁盘实验使 throughput/operations 增长，不填满宿主机真实文件系统。
- 网络实验使 receive/transmit 增长；drop/error 若无法安全触发，至少验证指标存在与查询语义。

### 去重与基数

- cAdvisor 是容器资源序列唯一来源。
- Collector spanmetrics 是 RED 唯一 writer。
- Metrics labels 不包含请求、Trace、用户、任务 ID 或完整 URL。
- 超出基数限制时 Collector self-telemetry 可观察，进程不崩溃。

## 7. 完成标准

- Prometheus 能按 Compose service 查询用户要求的容器 CPU、内存、OOM、磁盘和网络指标。
- 宿主机 filesystem、物理 disk I/O 和可解释的 operation latency 可查询。
- 容器级 disk latency 不可用时明确标记 N/A，没有伪造指标。
- Trace 派生 RED 与容器/宿主机指标各自只有一个事实源。
- 所有 counter 查询使用 `rate()` 或 `increase()`，所有 utilization 正确处理无 limit 场景。
- Dashboard 和后续 RCA 采集可以通过统一 service 与时间窗口关联 Trace、Logs、Metrics。
