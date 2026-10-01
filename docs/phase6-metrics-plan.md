# Phase 6 Metrics 设计与执行计划

**文档状态：** 待 Review  
**实施顺序：** 3 / 3  
**前置条件：** Trace 基线与 Java/Python/Go OTLP Logs 已通过  
**目标：** 建立故障注入与 RCA 数据集所需的原始 Metrics 采集基线，避免在采集层写入聚合或二次派生指标。

## 1. 调研结论与决策

指标按观测对象分配唯一来源：

- cAdvisor：Docker 容器 cgroup CPU、内存、OOM、filesystem、块 I/O、网络收发/丢包/错误，以及显式启用后的 socket 总数、TCP/UDP 状态和高级 TCP 统计。
- Collector `hostmetrics`：Docker 宿主机 CPU、内存、filesystem、物理磁盘和网络。
- node-exporter `prom/node-exporter:v1.9.1`：宿主机 socket、netstat、sockstat 类指标。
- 应用端点/OTLP：Phase 6 保留的 Java 服务暴露 Actuator/Prometheus；Python 和 Go 使用 OTLP Metrics。

不启用 Collector `docker_stats`，避免与 cAdvisor 重复。Prometheus 不启用 recording rules，不在 scrape 阶段做 labeldrop 或 label 派生；Collector 不启用 `spanmetrics`，Tempo metrics-generator 也不生成 span metrics 或 service graphs。服务请求率、错误率和延迟只能在 Grafana/人工查询时由原始应用指标即时计算，不写入 Prometheus TSDB。

`TRIPSPHERE_DATA_ROOT` 非空时必须使用绝对路径。相对路径会被 root Compose 和 deploy Compose 分别按各自 Compose 文件目录解析，导致两份 Compose 指向不同数据目录。默认空值继续使用仓库根目录 `volumes/`；服务器环境应显式设置为专用存储卷绝对路径。

OpenTelemetry system/container semantic conventions 作为概念和属性对齐依据；cAdvisor 原始 Prometheus 指标保持原名，不伪装成 OTel 指标。

官方依据：

- [OTel Metrics Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/general/metrics/)
- [OTel System Metrics](https://opentelemetry.io/docs/specs/semconv/system/system-metrics/)
- [OTel Container Metrics](https://opentelemetry.io/docs/specs/semconv/system/container-metrics/)
- [Collector Host Metrics Receiver](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/receiver/hostmetricsreceiver/README.md)
- [cAdvisor Prometheus Metrics](https://github.com/google/cadvisor/blob/master/docs/storage/prometheus.md)
- [cAdvisor v0.60.5 Runtime Options](https://github.com/google/cadvisor/blob/v0.60.5/docs/runtime_options.md)
- [cAdvisor v0.60.5 Docker Runtime](https://github.com/google/cadvisor/blob/v0.60.5/docs/running.md)
- [node-exporter Collectors](https://github.com/prometheus/node_exporter#enabled-by-default)

## 2. 分阶段范围

### 2.1 M1：容器资源核心指标（必须）

- CPU utilization、throttling、CPU time。
- Memory usage、utilization、limit、OOM。
- Container writable layer usage。
- Container writable layer I/O throughput、IOPS、busy time 和平均读/写 I/O 耗时。
- Docker data-root、`TRIPSPHERE_DATA_ROOT` 和数据卷所在宿主机设备 I/O。
- Network receive/transmit、packet drop 和 error。
- Container TCP/UDP socket 数量与 TCP state 计数，label 只允许 service、container、protocol、state。

### 2.2 M2：宿主机指标（必须）

- 宿主机 CPU、memory、filesystem、物理 disk I/O/latency 和 network。
- 宿主机 TCP/UDP socket、netstat 和 sockstat 指标。
- 明确区分容器 writable layer、named volume、Docker data-root 和物理设备。

### 2.3 M3：服务指标（M1/M2 通过后）

- Java/Python/Go 必须实际产生 runtime/request metrics；Java 需要新增 Actuator/Prometheus registry，Python/Go 需要新增或启用 OTLP Metrics。
- Java/Python/Go 原生 HTTP/gRPC request metrics；服务 RED 只作为查询时视图，不通过 spanmetrics 或 recording rules 写入。
- Collector、Prometheus、cAdvisor 自身健康指标。

### 2.4 不包含

- Alertmanager、生产告警阈值、SLO 和长期容量规划。
- 高可用 Prometheus 或远端长期存储。
- 浏览器 RUM 指标。
- 故障注入控制器与 RCA 数据集导出。
- 已删除服务的应用指标接入，包括独立 POI 和 Note 服务。POI 共享类型和初始化数据仍可保留，但独立 POI 服务不纳入 phase6.3 metrics 覆盖范围。

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
| Utilization | working set / effective limit | 仅在存在有效 limit 时生成；无有效 limit 时展示 working set 和 limit 原始值 |
| OOM events | `container_oom_events_total` | `increase(...[5m])` |
| Memory failures | `container_memory_failures_total` | 作为辅助故障证据 |

`container_oom_events_total` 必须通过目标 Linux/cgroup 环境的 `/metrics` 实测；不能仅因官方指标表存在就判定可用。

### 3.3 容器存储与磁盘 I/O

| 观测项 | cAdvisor 原始指标 | 查询规则 |
| --- | --- | --- |
| Writable usage | `container_fs_usage_bytes` / `container_fs_limit_bytes` | 不代表 named volume 或物理磁盘容量 |
| Throughput | `container_fs_reads_bytes_total` / `container_fs_writes_bytes_total` | 使用 `rate(...[1m])` |
| Operations | `container_fs_reads_total` / `container_fs_writes_total` | 使用 `rate(...[1m])` |
| In-flight I/O | `container_fs_io_current` | 当前正在进行的 I/O 数 |
| Device busy time | `container_fs_io_time_seconds_total` / `container_fs_io_time_weighted_seconds_total` | 使用 `rate(...[1m])`，表达设备忙碌和加权忙碌时间 |
| Average read/write I/O time | `container_fs_read_seconds_total` / `container_fs_write_seconds_total` 与对应 operations | `rate(seconds) / rate(operations)`；命名为 cgroup I/O 平均耗时，不命名为应用请求延迟 |

Docker data-root、`TRIPSPHERE_DATA_ROOT` 和数据卷所在设备的 I/O 不由 `container_fs_*` 归因。实施时先用 `docker info --format '{{.DockerRootDir}}'` 获取实际 Docker data-root，再对 Docker data-root、有效 `TRIPSPHERE_DATA_ROOT` 和 volume mountpoint 使用 `findmnt -T` 记录路径对应的 mountpoint/device，最后用 hostmetrics 的 `system.disk.io`、`system.disk.operations`、`system.disk.operation_time` 和 `system.filesystem.*` 查询同一 device。

### 3.4 容器网络

采集：

```text
container_network_receive_bytes_total
container_network_transmit_bytes_total
container_network_receive_packets_total
container_network_transmit_packets_total
container_network_receive_packets_dropped_total
container_network_transmit_packets_dropped_total
container_network_receive_errors_total
container_network_transmit_errors_total
```

所有 counter 用 `rate()` 或实验窗口 `increase()`，不把累计值展示为当前速率。

### 3.5 Socket 指标

宿主机 socket 指标由 node-exporter 采集，至少覆盖：

```text
node_sockstat_TCP_inuse
node_sockstat_TCP_tw
node_sockstat_TCP_alloc
node_sockstat_UDP_inuse
node_netstat_Tcp_CurrEstab
node_netstat_Tcp_RetransSegs
node_netstat_TcpExt_ListenDrops
node_netstat_TcpExt_ListenOverflows
```

上述 node-exporter 指标必须在 `/metrics` 中实际存在。宿主机 socket 指标不得包含本地/远端 IP、端口或进程命令行。

### cAdvisor 容器 socket 采集方式

cAdvisor v0.60.5 原生支持容器 socket 指标，但相关 metric group 默认关闭，不能只部署 cAdvisor 后假定指标存在。Compose 必须显式启用：

```text
--enable_metrics=cpu,disk,diskIO,memory,network,oom_event,process,tcp,udp,advtcp
--docker_only=true
```

其中 socket 相关的四个 metric group 为：

```text
process
tcp
udp
advtcp
```

若使用 `--enable_metrics`，它会覆盖默认的 `--disable_metrics` 集合，因此必须把容器 CPU、内存、磁盘、网络、OOM 等需要保留的 metric group 一并列出，不能只写上述四项。

对应的 cAdvisor Prometheus 指标为：

| 观测内容 | cAdvisor 指标 | 启用组 | 真实语义 |
| --- | --- | --- | --- |
| 容器所有打开 socket 总数 | `container_sockets` | `process` | 容器进程打开的 socket 数量，不区分 TCP/UDP 或状态 |
| IPv4 TCP 状态 | `container_network_tcp_usage_total` | `tcp` | 通过 `tcp_state` label 输出 established、synsent、listen、timewait 等状态计数 |
| IPv6 TCP 状态 | `container_network_tcp6_usage_total` | `tcp` | IPv6 TCP 状态计数，维度为 `tcp_state` |
| IPv4 UDP 统计 | `container_network_udp_usage_total` | `udp` | 通过 `udp_state` 输出 listen、dropped、rxqueued、txqueued |
| IPv6 UDP 统计 | `container_network_udp6_usage_total` | `udp` | IPv6 UDP 统计，维度为 `udp_state` |
| TCP 高级统计 | `container_network_advance_tcp_stats_total` | `advtcp` | 通过 `tcp_state` 输出内核 TCP 统计，其中 `retranssegs` 可作为重传累计快照 |

因此，`container_sockets` 只能回答“容器当前打开了多少 socket”；TCP 状态必须查询 `container_network_tcp*_usage_total`；UDP 不能被解释成 TCP 风格的 established 数量。cAdvisor v0.60.5 将 TCP/UDP usage 和 `container_network_advance_tcp_stats_total` 声明为 Gauge，即使名称带 `_total` 也不能默认对它们使用 `rate()` 或 `increase()`。`retranssegs` 默认按当前累计快照展示；只有验证容器重启/网络命名空间重建时的重置处理后，才能用 `delta()` 派生变化率。所有这些指标都只保留 cAdvisor 自带的容器身份和状态 label，不采集本地/远端地址、端口、PID 或进程命令行。

启用 `process` 指标时，cAdvisor 官方 Docker 运行说明要求使用 host PID namespace，并以 privileged 方式运行，以便从宿主机 `/proc/<pid>/fd` 读取容器进程的 socket。目标环境还必须实测 cgroup v1/v2、Docker runtime、`/proc` 可见性和权限；不能只依据指标文档判定通过。

容器 socket 指标统一由 cAdvisor 提供，不新增独立容器 socket exporter。为后续 RCA 数据集保留通用原始观测数据，Prometheus 不对 cAdvisor 的原始 labels 做 TripSphere 专用低基数规范化；实验数据导出阶段再按任务需要筛选 label。

### 3.6 宿主机

Collector `hostmetrics` 使用：

```text
root_path: /hostfs
collection_interval: 15s
scrapers: [cpu, memory, filesystem, disk, network]
```

必须显式启用以下 optional metrics：

```text
system.cpu.utilization
system.memory.limit
system.memory.utilization
system.linux.memory.available
system.filesystem.utilization
```

宿主机根目录只读挂载到 `/hostfs`。过滤 `proc`、`sysfs`、`tmpfs`、`overlay`、`cgroup` 等虚拟文件系统。宿主机指标至少覆盖：

```text
system.cpu.time
system.cpu.utilization
system.memory.usage
system.memory.limit
system.memory.utilization
system.linux.memory.available
system.filesystem.usage
system.filesystem.utilization
system.disk.io
system.disk.operations
system.disk.operation_time
system.disk.io_time
system.disk.pending_operations
system.disk.weighted_io_time
system.network.io
system.network.packets
system.network.dropped
system.network.errors
system.network.connections
```

System semantic conventions 仍有 Development/Release Candidate 项，Dashboard 和数据字典记录 Collector 0.144.0 实际产生的 Prometheus 名称，升级时不得无验证改名。按 `translation_strategy: UnderscoreEscapingWithSuffixes` 预期至少生成以下 Prometheus series family，实施时以 Collector exporter 实际输出为准并写入验收记录：

```text
system_cpu_time_seconds_total
system_cpu_utilization_ratio
system_memory_usage_bytes
system_memory_limit_bytes
system_memory_utilization_ratio
system_linux_memory_available_bytes
system_filesystem_usage_bytes
system_filesystem_utilization_ratio
system_disk_io_bytes_total
system_disk_operations_total
system_disk_operation_time_seconds_total
system_disk_io_time_seconds_total
system_disk_pending_operations
system_disk_weighted_io_time_seconds_total
system_network_io_bytes_total
system_network_packets_total
system_network_dropped_total
system_network_errors_total
system_network_connections
```

### 3.7 服务请求指标

服务请求率、错误率和延迟分布只使用应用或 SDK 原生指标：

- Java Actuator/Micrometer：`http_server_requests_seconds_*`、`grpc_server_processing_duration_seconds_*`。
- Python OTel Metrics：`http_server_duration_milliseconds_*`、`http_client_duration_milliseconds_*`、runtime/process 指标。
- Go OTel Metrics：`rpc_server_duration_milliseconds_*`、`grpc_server_*`、runtime/process 指标。

Prometheus 只保存这些原始序列。Dashboard 可用 `rate()`、`increase()`、`histogram_quantile()`、`sum by (...)` 等 PromQL 做查询时计算，但不得通过 recording rules 或 Collector connector 把计算结果写成新的 `tripsphere:*` 指标。

## 4. 原始指标查询契约

Prometheus 配置不得包含 `rule_files`，仓库不得新增 `infra/prometheus/rules/*.yaml`。所有 RCA 数据集采集均从原始 metric families 读取，例如：

- cAdvisor：`container_*`。
- hostmetrics：`system_*`。
- node-exporter：`node_sockstat_*`、`node_netstat_*`。
- Java Actuator：`http_server_requests_seconds_*`、`grpc_server_processing_duration_seconds_*`、JVM/runtime 指标。
- Python/Go OTLP metrics：Collector Prometheus exporter 暴露的 `http_*`、`rpc_*`、`grpc_*`、runtime/process 指标。

容器 TCP/UDP 指标直接查询 cAdvisor 原始序列：`container_sockets`、`container_network_tcp*_usage_total`、`container_network_udp*_usage_total` 和 `container_network_advance_tcp_stats_total`。不得因为指标名包含 `_total` 就对 Gauge 使用 `rate()` 或 `increase()`。

任一清单原始指标缺失时不能填 0。无有效 CPU/memory limit 时只保留 usage 与 limit 原始证据。延迟分位数直接查询各语言原生 histogram，不为每个分位数创建重复 recording rule。

## 5. 执行计划

### Task 0：同步 Logs 基线与 Compose 前置修正

- 本地 `phase6.3-metrics` 必须基于云端最新 `phase6.2-logs`，避免 Metrics PR 重新带入旧 Logs 问题。
- root Compose 仍作为运行时验收入口；deploy Compose 只做静态校验，不同时启动两份 Compose。
- 修复 `TRIPSPHERE_DATA_ROOT` 语义：非空值必须是绝对路径；相对路径要么在配置检查中失败，要么由 `.env.example` 和文档明确禁止。
- 若从旧 named volumes 迁移到 `TRIPSPHERE_DATA_ROOT` 目录，先人工迁移 Prometheus、Collector offset 等数据；不得执行 `docker compose down -v`。
- 确认 Phase 6.2 的 Collector API-key 正则移除、Python logger OTel handler、Celery worker 日志链路不被 Metrics 改造回退。

### Task 1：建立目标环境指标清单

- 记录 Docker、Linux kernel、cgroup mode、storage driver 和 Collector/cAdvisor 版本。
- 保存 cAdvisor、hostmetrics、node-exporter 实际暴露的指标名、labels、单位和 Prometheus `# TYPE`。
- `docs/phase6-metrics-observation-checklist.md` 中任一原始指标缺失都视为实现未完成，先补采集配置或应用 instrumentation。
- Dashboard 可以先按契约预置，但必须直接查询原始指标。原始指标不存在时，对应面板空白视为未通过，不用 recording rules 或占位序列补齐。

### Task 2：接入 cAdvisor

- 使用固定版本 cAdvisor，并按官方 Docker 运行要求只读挂载宿主机根目录、`/var/run`、`/sys`、Docker data-root 和 `/dev/disk`。
- 显式启用本计划所需指标组，至少包含 `process`、`tcp`、`udp`、`advtcp` 以及 CPU、memory、disk、diskIO、network、oom_event；验证 OOM event 和 process 指标所需权限及 `/dev/kmsg` 行为。
- 为 `process` 指标配置 host PID 和 privileged；记录该权限只用于本地故障实验基线。目标环境必须提供该权限以采集容器 socket，不增加替代采集器。
- Prometheus 直接 scrape cAdvisor；Collector 不二次接收或重导出同一批容器指标。
- 保留 cAdvisor 暴露的原始容器 labels，包括 `name`、`id`、`image` 和 `container_label_*`；不在 Prometheus scrape 阶段生成或过滤 TripSphere 专用 service 维度，后续 RCA 导出阶段再关联实验元数据。
- 验证 `container_fs_*` 覆盖 container writable layer 和 cgroup disk I/O；Docker data-root 使用 `docker info --format '{{.DockerRootDir}}'` 获取实际路径，Docker data-root、`TRIPSPHERE_DATA_ROOT` 与数据卷 I/O 通过 `findmnt -T` 映射到宿主机 device，再由 hostmetrics 采集。
- 验证 `container_sockets`、`container_network_tcp*_usage_total`、`container_network_udp*_usage_total` 和 `container_network_advance_tcp_stats_total` 是否实际存在；任一指标缺失都必须先补齐 cAdvisor 配置或运行权限，再将对应 recording rule 和 Dashboard 标记为通过。
- 特权和宿主机挂载只作为本地故障实验方案，不作为生产安全模板。

### Task 3：接入 hostmetrics 与宿主机 socket 指标

- Collector 增加独立 `hostmetrics` receiver 和 `/hostfs` 只读挂载。
- 启用 CPU、memory、filesystem、disk、network scraper；显式打开 `system.cpu.utilization`、`system.memory.limit`、`system.memory.utilization`、`system.linux.memory.available` 和 `system.filesystem.utilization`。
- 配置 filesystem/device include/exclude，验证读到的是宿主机而非 Collector 容器。
- 增加稳定 host/environment resource attributes，不把所有 resource attributes 自动转成 Prometheus labels。
- 增加 `prom/node-exporter:v1.9.1`，按官方容器模式使用 host network、host PID 和 `/host` rootfs 挂载，Prometheus 通过 `host.docker.internal:19100` 直接 scrape `sockstat` 和 `netstat` 指标。
- 宿主机 socket 指标只保留协议和状态级 labels，不保留地址、端口、进程命令行。

### Task 4：验证 cAdvisor 容器 socket 指标

- 验证 cAdvisor 原生 `process`、`tcp`、`udp`、`advtcp` 指标。
- 分别验证 `container_sockets`、TCP/UDP state、TCP `retranssegs` 的语义和 label；IPv4/IPv6 分开后再按需要聚合。
- 通过 cAdvisor `/metrics` 直接检查原始输出；示例（将地址替换为实际 cAdvisor 暴露地址）：

  ```bash
  curl --fail --silent http://localhost:18088/metrics \
    | rg '^(# TYPE )?(container_sockets|container_network_(tcp|tcp6|udp|udp6|advance_tcp).*)'
  ```

- 检查 `# TYPE`：`container_sockets`、TCP/UDP usage 和 advanced TCP stats 都必须按 Gauge 处理；不要因为名称包含 `_total` 就套用 counter 查询。
- cAdvisor 是容器 socket、TCP/UDP state 和 TCP 高级统计的唯一来源；任何原始指标缺失都必须先补齐 cAdvisor 配置或运行权限，不用其他指标替代。

### Task 5：接入现有应用原生指标

- Collector metrics pipeline 只接收 OTLP 应用原生 metrics 与 hostmetrics，并通过现有 Prometheus exporter 暴露。
- 从 Tempo 配置移除重复的 `span-metrics` 和 `service-graphs` processor。
- 保留的 Java 服务增加 `spring-boot-starter-actuator` 与 `micrometer-registry-prometheus`，暴露 `/actuator/prometheus` 并加入 Prometheus scrape；已删除的独立 POI 和 Note 服务不作为 phase6.3 Java metrics 缺口。
- Python 服务增加 OpenTelemetry Metrics SDK/exporter 初始化，Planner、Chat、Order Assistant、Review Summary、Celery worker 均通过 OTLP 上报 runtime/request/task 指标。
- Go Review Service 增加 OpenTelemetry Metrics SDK/exporter 初始化，上报 runtime 与 gRPC/server 指标。
- 所有应用指标必须能在 Collector Prometheus exporter 或应用 Prometheus endpoint 中按 `service.name`/`service` 查询。

### Task 6：完善 Prometheus 与 Dashboard

- Prometheus scrape 自身、Collector exporter、Collector self-telemetry、cAdvisor、node-exporter、Java Actuator endpoint 和实际应用 metrics targets。
- 不加载 Prometheus recording rules；Prometheus 只 scrape 原始 metrics。
- 提供五个最小视图：采集健康、服务原生请求指标、容器资源、宿主机资源、socket/网络状态。
- Dashboard 只使用 checklist 中已通过的原始指标；清单项缺失时该阶段不通过。

## 6. 测试计划

### 静态配置

- `docker compose config` 成功。
- Collector 配置加载成功且不存在 `docker_stats`。
- `promtool check config` 成功，且配置中没有 `rule_files`。
- Prometheus 只有一个 cAdvisor scrape job；无 spanmetrics、Tempo metrics-generator 或 recording rules 写入派生 RED。
- cAdvisor 的 `process`、`tcp`、`udp`、`advtcp` 启用配置与实际 `/metrics` 输出一致；若原始序列不存在，先修复配置或权限后复验，不以其他指标替代。

### 数据契约

- CPU、memory、OOM、filesystem/I/O、network、socket、hostmetrics 和应用 metrics 的每个 checklist 原始指标均有实测结果。
- Docker data-root、`TRIPSPHERE_DATA_ROOT` 和数据卷目录均能映射到宿主机 mountpoint/device，并能查询同 device 的 filesystem/disk 指标。
- cAdvisor 容器指标保留官方原始 labels，不要求生成 TripSphere 专用 `service` label；实验导出阶段负责将原始 labels 与故障元数据关联。
- 无效 limit 和除零场景产生空序列，不产生 0、NaN 或 Inf。
- hostmetrics 资源标识与容器资源标识不会混淆。

### 受控故障负载

- CPU stress 使 usage 增长；有限 quota 实验使 throttling 增长。
- 内存压力使 working set 增长；专用受限测试容器触发 OOM event。
- 临时卷磁盘实验使 throughput/operations 增长，不填满宿主机真实文件系统。
- 网络实验使 receive/transmit 增长；drop/error 不在安全路径强行触发，但必须验证指标存在与查询语义。

### 去重与原始性

- cAdvisor 是容器资源序列唯一来源。
- node-exporter 是宿主机 socket 序列唯一来源。
- cAdvisor 是容器 socket、TCP/UDP state 和 TCP 高级统计的唯一来源。
- Collector `hostmetrics` 是宿主机资源序列唯一来源。
- Prometheus 不使用 recording rules，不在 scrape 阶段删除或派生业务 metric labels。

## 7. 完成标准

- Prometheus 能按 Compose service 查询用户要求的容器 CPU、内存、OOM、磁盘和网络指标。
- Prometheus 能查询宿主机 socket、容器 socket、Docker data-root 和数据卷所在设备 I/O 指标。
- 宿主机 filesystem、物理 disk I/O 和可解释的 operation latency 可查询。
- 容器级读/写 I/O 平均耗时由 `container_fs_read_seconds_total`、`container_fs_write_seconds_total` 和对应 operations 派生，不伪造应用请求延迟。
- 服务请求视图由原生 HTTP/gRPC metrics 查询时计算，不采集 Trace 派生 RED。
- 所有 counter 查询使用 `rate()` 或 `increase()`，所有 utilization 正确处理无 limit 场景。
- Dashboard 和后续 RCA 采集可以通过统一 service 与时间窗口关联 Trace、Logs、Metrics。

## 8. 当前仓库差距与落地修改计划

| 优先级 | 差距 | 修改计划 | 主要文件 |
| --- | --- | --- | --- |
| P0 | `phase6.3-metrics` 必须基于最新 Logs 基线 | 已将本地分支 fast-forward 到 `origin/phase6.2-logs`；后续修改不得回退 Logs 配置 | `infra/otel-collector/config.yaml`、Python logging 配置、两份 Compose |
| P0 | `TRIPSPHERE_DATA_ROOT` 相对路径会在 root/deploy Compose 中解析到不同目录 | 非空值强制要求绝对路径；补充 `.env.example` 和配置校验说明；必要时增加启动前检查脚本 | `.env.example`、`docker-compose.yaml`、`deploy/docker-compose/docker-compose.yaml`、docs |
| P1 | cAdvisor 尚未接入，Prometheus 只 scrape 自身和 Collector exporter | 增加 `cadvisor` 服务及官方宿主机只读挂载；Prometheus 增加唯一 cAdvisor scrape job | 两份 Compose、`infra/prometheus/prometheus.yaml` |
| P1 | 宿主机核心资源指标尚未接入 | Collector 增加 `/hostfs` 挂载和 `hostmetrics` receiver；配置 filesystem/device 过滤 | 两份 Compose、`infra/otel-collector/config.yaml` |
| P1 | 宿主机 socket 指标未接入 | 增加 `prom/node-exporter:v1.9.1`，Prometheus scrape netstat/sockstat 指标 | 两份 Compose、`infra/prometheus/prometheus.yaml` |
| P1 | cAdvisor socket metric group 默认关闭，实际权限和序列尚未验证 | 显式启用 `process`、`tcp`、`udp`、`advtcp` 并验证原生指标；原始指标不存在时先修复 cAdvisor 配置或运行权限，不增加替代采集器 | 两份 Compose、`infra/prometheus/prometheus.yaml` |
| P1 | Docker data-root / 数据卷 I/O 需要可采集路径 | 用 `docker info --format '{{.DockerRootDir}}'` 获取 Docker data-root，再用 `findmnt -T` 将 Docker data-root、`TRIPSPHERE_DATA_ROOT` 和数据卷目录映射到宿主机 device；hostmetrics 采集同 device 的 filesystem/disk 指标 | 指标清单、Dashboard |
| P2 | Tempo metrics-generator 当前仍启用 `span-metrics`/`service-graphs` | 移除 Tempo 重复生成器，避免写入 Trace 派生 metrics | `infra/tempo/tempo.yaml` |
| P2 | 仍存在 Prometheus recording rules | 删除 `rule_files` 和 `infra/prometheus/rules/*.yaml`；Dashboard 直接查询原始指标 | `infra/prometheus/prometheus.yaml`、`infra/grafana/dashboards/` |
| P2 | Grafana 只有 datasource provisioning | 新增 dashboard provisioning 与五个最小 Dashboard | `infra/grafana/provisioning/dashboards/`、`infra/grafana/dashboards/` |
| P3 | 缺少 Metrics 阶段自动验收脚本 | 增加静态配置、Prometheus targets、原始指标存在性、label 基数和占位值检查脚本 | `scripts/` 或 `docs/` 验收命令 |
