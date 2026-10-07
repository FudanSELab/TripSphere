# Phase 6 Metrics 观测数据类型清单

**来源文档：** [phase6-metrics-plan.md](phase6-metrics-plan.md)
**文档状态：** 待人工审核
**用途：** 在 Metrics 实施前固定必须采集的数据类型、原始指标和验收口径。

本清单只保留可以通过 Phase 6 计划接入并验收的指标。每一项都必须有明确数据源、Prometheus target 和原始序列；若任一原始序列缺失，视为实现未完成，不能用 0、占位值或其他不等价指标替代。

## 1. 指标来源边界

| 观测对象 | 唯一数据来源 | 必须配置 | 去重要求 |
| --- | --- | --- | --- |
| Docker 容器资源 | cAdvisor `ghcr.io/google/cadvisor:v0.60.5` | `--enable_metrics=cpu,disk,diskIO,memory,network,oom_event,process,tcp,udp,advtcp` | 不启用 Collector `docker_stats` |
| 容器 socket/TCP/UDP | cAdvisor `process`、`tcp`、`udp`、`advtcp` metric group | cAdvisor 使用 host PID namespace 和 privileged 权限 | 不增加独立 socket exporter |
| Docker 宿主机资源 | Collector `hostmetrics` 0.144.0 | `root_path: /hostfs`，启用 `cpu`、`memory`、`filesystem`、`disk`、`network` scraper 和必要 optional metrics | 不把 Collector 容器自身资源当宿主机资源 |
| 宿主机 socket/netstat | node-exporter `prom/node-exporter:v1.9.1` | 使用 host network、host PID 和 `/host` rootfs 只读挂载，启用默认 `sockstat`、`netstat` collector | Prometheus 通过 `host.docker.internal:19100` 直接 scrape |
| 应用 runtime/request metrics | Java Actuator/Prometheus endpoint；Python/Go OTLP Metrics | Compose 显式暴露或上报到 Collector metrics pipeline | 作为服务请求视图的唯一 metrics 来源 |
| 服务请求视图 | 应用原生 HTTP/gRPC metrics | Grafana/人工查询时用 PromQL 计算 rate、error ratio 和 latency | 不启用 spanmetrics、Tempo metrics-generator 或 recording rules |
| 采集链路健康 | Prometheus、Collector、cAdvisor、node-exporter 自身指标 | Prometheus targets 全部 `up` | 能区分采集失败和业务值为 0 |

## 2. 容器资源指标

### 2.1 CPU

| 编号 | 需要观测的数据类型 | 原始指标 | 观测/派生口径 |
| --- | --- | --- | --- |
| C-CPU-01 | 累计 CPU 时间 | `container_cpu_usage_seconds_total` | 原始 counter，保留为故障窗口证据 |
| C-CPU-02 | CPU 使用量 | `container_cpu_usage_seconds_total` | `rate(...[1m])`，单位 CPU cores |
| C-CPU-03 | CPU limit | `container_spec_cpu_quota`、`container_spec_cpu_period` | `quota / period`，仅 `quota > 0` 生成 |
| C-CPU-04 | CPU 利用率 | C-CPU-02 与 C-CPU-03 | `usage_cores / limit_cores`；无 quota 时只展示 usage cores |
| C-CPU-05 | CPU throttling 比例 | `container_cpu_cfs_throttled_periods_total`、`container_cpu_cfs_periods_total` | 两个 counter 的 `rate()` 比值 |
| C-CPU-06 | CPU throttled time | `container_cpu_cfs_throttled_seconds_total` | `rate(...[1m])` |

### 2.2 内存与 OOM

| 编号 | 需要观测的数据类型 | 原始指标 | 观测/派生口径 |
| --- | --- | --- | --- |
| C-MEM-01 | 内存总使用量 | `container_memory_usage_bytes` | 当前总使用量，包含 cache |
| C-MEM-02 | 内存 working set | `container_memory_working_set_bytes` | Dashboard 主展示值 |
| C-MEM-03 | 内存 limit | `container_spec_memory_limit_bytes` | 过滤无限额/宿主机级哨兵值后使用 |
| C-MEM-04 | 内存利用率 | C-MEM-02 与 C-MEM-03 | `working_set / effective_limit` |
| C-MEM-05 | OOM 事件 | `container_oom_events_total` | `increase(...[5m])` |
| C-MEM-06 | 内存失败事件 | `container_memory_failures_total` | 内存压力辅助证据 |

### 2.3 文件系统、磁盘和卷 I/O

| 编号 | 需要观测的数据类型 | 原始指标或来源 | 观测/派生口径 |
| --- | --- | --- | --- |
| C-DISK-01 | 容器 writable layer 使用量 | `container_fs_usage_bytes`、`container_fs_limit_bytes` | writable layer utilization |
| C-DISK-02 | 容器读吞吐 | `container_fs_reads_bytes_total` | `rate(...[1m])` |
| C-DISK-03 | 容器写吞吐 | `container_fs_writes_bytes_total` | `rate(...[1m])` |
| C-DISK-04 | 容器读 IOPS | `container_fs_reads_total` | `rate(...[1m])` |
| C-DISK-05 | 容器写 IOPS | `container_fs_writes_total` | `rate(...[1m])` |
| C-DISK-06 | 容器当前 I/O 与设备忙碌时间 | `container_fs_io_current`、`container_fs_io_time_seconds_total`、`container_fs_io_time_weighted_seconds_total` | 当前 in-flight I/O 和 busy time counter |
| C-DISK-07 | 容器平均读/写 I/O 耗时 | `container_fs_read_seconds_total`、`container_fs_write_seconds_total`、`container_fs_reads_total`、`container_fs_writes_total` | `rate(seconds) / rate(operations)`；这是 cgroup I/O 平均耗时，不命名为应用请求延迟 |
| C-DISK-08 | Docker data-root 所在设备 I/O | `system.disk.io`、`system.disk.operations`、`system.disk.operation_time`，以及实际 Docker root 的 `findmnt -T` 映射 | 用 `docker info --format '{{.DockerRootDir}}'` 获取实际 data-root，再记录其 mountpoint/device，并查询同 device 的宿主机 disk 指标 |
| C-DISK-09 | `TRIPSPHERE_DATA_ROOT`/数据卷所在设备 I/O | `system.filesystem.usage`、`system.filesystem.utilization`、`system.disk.io`、`system.disk.operations`、`system.disk.operation_time`，以及有效数据根目录/volume mountpoint 的 `findmnt -T` 映射 | 观测数据目录所在真实 filesystem 和物理 device；不把 `container_fs_*` 解释为 named volume 指标 |

### 2.4 容器网络

| 编号 | 需要观测的数据类型 | 原始指标 | 观测/派生口径 |
| --- | --- | --- | --- |
| C-NET-01 | 接收字节吞吐 | `container_network_receive_bytes_total` | `rate(...[1m])` |
| C-NET-02 | 发送字节吞吐 | `container_network_transmit_bytes_total` | `rate(...[1m])` |
| C-NET-03 | 接收包数 | `container_network_receive_packets_total` | `rate(...[1m])` |
| C-NET-04 | 发送包数 | `container_network_transmit_packets_total` | `rate(...[1m])` |
| C-NET-05 | 接收丢包 | `container_network_receive_packets_dropped_total` | `rate()` 或故障窗口 `increase()` |
| C-NET-06 | 发送丢包 | `container_network_transmit_packets_dropped_total` | `rate()` 或故障窗口 `increase()` |
| C-NET-07 | 接收错误 | `container_network_receive_errors_total` | `rate()` 或故障窗口 `increase()` |
| C-NET-08 | 发送错误 | `container_network_transmit_errors_total` | `rate()` 或故障窗口 `increase()` |

## 3. Socket 与连接指标

### 3.1 容器 socket

cAdvisor 必须以 host PID namespace 和 privileged 权限运行，否则 `process` 组无法稳定读取宿主机 `/proc/<pid>/fd`。容器 socket 指标全部来自 cAdvisor，不部署替代 exporter。

关键参数：

```text
--enable_metrics=cpu,disk,diskIO,memory,network,oom_event,process,tcp,udp,advtcp
--docker_only=true
```

| 编号 | 需要观测的数据类型 | 原始指标 | 观测/派生口径 |
| --- | --- | --- | --- |
| C-SOCK-01 | 容器打开 socket 总数 | `container_sockets` | gauge；表示所有打开 socket，不区分协议或状态 |
| C-SOCK-02 | IPv4 TCP state | `container_network_tcp_usage_total` | gauge；按 `tcp_state` 查询 `established`、`listen`、`timewait` 等 |
| C-SOCK-03 | IPv6 TCP state | `container_network_tcp6_usage_total` | gauge；按 `tcp_state` 查询 |
| C-SOCK-04 | IPv4 UDP state/queue | `container_network_udp_usage_total` | gauge；按 `udp_state` 查询 `listen`、`dropped`、`rxqueued`、`txqueued` |
| C-SOCK-05 | IPv6 UDP state/queue | `container_network_udp6_usage_total` | gauge；按 `udp_state` 查询 |
| C-SOCK-06 | TCP 高级统计与重传 | `container_network_advance_tcp_stats_total` | gauge；`tcp_state="retranssegs"` 是重传累计快照，不对它默认 `rate()` |

实施时必须直接检查 cAdvisor `/metrics`：

```bash
curl --fail --silent http://localhost:18088/metrics \
  | rg '^(# TYPE )?(container_sockets|container_network_(tcp|tcp6|udp|udp6|advance_tcp).*)'
```

验收时还必须用至少一个已有监听服务和一次受控业务请求验证状态语义：对 Redis/PostgreSQL/Java gRPC/HTTP 服务等常驻监听容器查询 `tcp_state="listen"`；产生一次连接后在同一时间窗查询 `tcp_state="established"` 或 `tcp_state="timewait"`。Prometheus 保留 cAdvisor 原始 labels，实验数据导出阶段再按 RCA 任务筛选维度。

### 3.2 宿主机 socket、netstat 和 sockstat

| 编号 | 需要观测的数据类型 | 原始指标 | 观测/派生口径 |
| --- | --- | --- | --- |
| H-SOCK-01 | TCP in-use socket 数量 | `node_sockstat_TCP_inuse` | gauge |
| H-SOCK-02 | TCP TIME_WAIT 数量 | `node_sockstat_TCP_tw` | gauge |
| H-SOCK-03 | TCP allocated socket 数量 | `node_sockstat_TCP_alloc` | gauge |
| H-SOCK-04 | UDP in-use socket 数量 | `node_sockstat_UDP_inuse` | gauge |
| H-SOCK-05 | 当前 TCP established 数量 | `node_netstat_Tcp_CurrEstab` | 当前值 |
| H-SOCK-06 | TCP retransmit 段数 | `node_netstat_Tcp_RetransSegs` | Linux netstat 累计值；故障窗口使用 `increase()` |
| H-SOCK-07 | TCP listen drops | `node_netstat_TcpExt_ListenDrops` | Linux netstat 累计值；故障窗口使用 `increase()` |
| H-SOCK-08 | TCP listen overflows | `node_netstat_TcpExt_ListenOverflows` | Linux netstat 累计值；故障窗口使用 `increase()` |

宿主机 socket 指标不得包含本地/远端 IP、端口或进程命令行。

验收时必须在 node-exporter target 上确认 `node_sockstat_TCP_inuse`、`node_netstat_Tcp_CurrEstab` 等当前值存在，并在同一受控连接窗口内确认相关 current/gauge 或累计 counter 的查询语义。

## 4. 宿主机资源指标

Collector `hostmetrics` 必须通过 `/hostfs` 读取宿主机视图。以下 optional metrics 必须显式启用：`system.cpu.utilization`、`system.memory.limit`、`system.memory.utilization`、`system.linux.memory.available`、`system.filesystem.utilization`。

下表中的 `system.*` 是 OTel 原始 metric name。Collector Prometheus exporter 使用 `translation_strategy: UnderscoreEscapingWithSuffixes` 后，实施验收还必须确认对应 Prometheus series family 存在：

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

| 编号 | 需要观测的数据类型 | 原始指标 | 观测/派生口径 |
| --- | --- | --- | --- |
| H-CPU-01 | CPU 时间 | `system.cpu.time` | cumulative seconds，按 `cpu`、`state` 查询 |
| H-CPU-02 | CPU 利用率 | `system.cpu.utilization` | gauge，按 `cpu`、`state` 查询 |
| H-MEM-01 | 内存使用量 | `system.memory.usage` | 按 `state` 查询 `used`、`free`、`cached` 等 |
| H-MEM-02 | 内存总量和利用率 | `system.memory.limit`、`system.memory.utilization`、`system.linux.memory.available` | 总量、利用率和 Linux available memory |
| H-FS-01 | 文件系统容量/使用量 | `system.filesystem.usage` | 按 `mountpoint`、`device`、`type`、`state` 查询 |
| H-FS-02 | 文件系统利用率 | `system.filesystem.utilization` | 按真实 mountpoint 查询，过滤虚拟文件系统 |
| H-DISK-01 | 物理磁盘读写吞吐 | `system.disk.io` | 按 `device`、`direction` 使用 `rate()` |
| H-DISK-02 | 物理磁盘操作数 | `system.disk.operations` | 按 `device`、`direction` 使用 `rate()` |
| H-DISK-03 | 物理磁盘 operation time | `system.disk.operation_time` | 按 `device`、`direction` 使用 `rate()` |
| H-DISK-04 | 物理磁盘平均操作耗时 | `system.disk.operation_time`、`system.disk.operations` | `rate(operation_time) / rate(operations)` |
| H-DISK-05 | 物理磁盘 busy/queue 证据 | `system.disk.io_time`、`system.disk.pending_operations`、`system.disk.weighted_io_time` | 设备忙碌时间、队列长度和加权 I/O 时间 |
| H-NET-01 | 宿主机网络字节和包数 | `system.network.io`、`system.network.packets` | 按 `device`、`direction` 使用 `rate()` |
| H-NET-02 | 宿主机网络丢包和错误 | `system.network.dropped`、`system.network.errors` | 按 `device`、`direction` 使用 `rate()` 或 `increase()` |
| H-NET-03 | 宿主机 TCP 连接状态 | `system.network.connections` | 按 `protocol`、`state` 查询 |

## 5. 应用服务和 RED 指标

应用指标验收范围只包含保留业务服务。已删除的独立 POI 和 Note 服务不计入 Java Actuator/Prometheus 覆盖缺口；POI 共享类型和初始化数据仍按 Phase 7 规则保留。

| 编号 | 需要观测的数据类型 | 来源 | 观测/派生口径 |
| --- | --- | --- | --- |
| APP-01 | Java runtime/framework metrics | Spring Boot Actuator + Prometheus registry | 每个 Phase 6 保留 Java 服务暴露 `/actuator/prometheus`，Prometheus 直接 scrape |
| APP-02 | Python runtime/request metrics | OpenTelemetry Python metrics SDK -> Collector OTLP -> Prometheus exporter | Planner、Chat、Order Assistant、Review Summary、Celery worker 都必须上报 |
| APP-03 | Go runtime/request metrics | OpenTelemetry Go metrics SDK -> Collector OTLP -> Prometheus exporter | Review Service 必须上报 runtime 与 gRPC/server 指标 |
| APP-04 | 服务指标采集状态 | Prometheus target、Collector self-telemetry | 区分“服务无请求”和“指标未上报” |
| RED-01 | 请求率 | 应用原生 HTTP/gRPC counter | 查询 `http_server_requests_seconds_count`、`http_server_duration_milliseconds_count`、`grpc_server_processing_duration_seconds_count`、`rpc_server_duration_milliseconds_count` 等原始指标 |
| RED-02 | 错误率 | 应用原生 HTTP/gRPC status labels | 查询时按 `status`、`outcome`、`statusCode`、`http_status_code`、`rpc_grpc_status_code` 计算，不写入派生序列 |
| RED-03 | 请求延迟分布 | 应用原生 HTTP/gRPC histogram | 保留 histogram buckets，由 Dashboard 查询分位数 |
| RED-04 | 请求指标采集健康 | Collector self-telemetry、Prometheus target 和各语言原始 request metrics | 区分“服务无请求”和“指标未上报” |

## 6. 采集组件和后端健康数据

| 编号 | 需要观测的数据类型 | 原始指标/接口 | 验收重点 |
| --- | --- | --- | --- |
| SYS-01 | Prometheus scrape 状态 | `up`、`scrape_duration_seconds`、`scrape_samples_scraped` | Prometheus、Collector、cAdvisor、node-exporter 和应用 targets 均可查询 |
| SYS-02 | Collector metrics pipeline 健康 | Collector self-telemetry | receiver、processor、connector、exporter 错误和 dropped data 可见 |
| SYS-03 | cAdvisor 健康 | cAdvisor `/metrics` 与 `up{job="cadvisor"}` | 所有 cAdvisor 原始指标实际存在 |
| SYS-04 | node-exporter 健康 | node-exporter `/metrics` 与 `up{job="node-exporter"}` | sockstat/netstat 序列实际存在 |
| SYS-05 | Metrics 持久化和保留 | Prometheus TSDB 和 `TRIPSPHERE_DATA_ROOT` | 保留 7 天，数据目录路径唯一且明确 |

## 7. 标签和维度约束

| 指标类别 | 允许的主要维度 |
| --- | --- |
| 容器资源 | cAdvisor 原始 labels，例如 `name`、`id`、`image`、`container_label_*`、必要的 `device`/`interface` |
| 容器 socket | cAdvisor 原始 labels，例如 `name`、`id`、`image`、`container_label_*`、`tcp_state`/`udp_state` |
| 宿主机资源 | `host`、`device`、`mountpoint`、`direction`、`interface`、环境标识 |
| 服务请求视图 | 各语言原生 HTTP/gRPC 指标自带的 service、method、route/status 相关 labels |
| 应用原生指标 | 保留应用框架本身定义的原始维度；高基数风险在验收记录中标出 |

Prometheus 不在 scrape 阶段删除或派生业务 metric labels。以下内容若出现在应用原生指标中，需要在验收记录中标出基数风险；cAdvisor 原始 labels 不在 scrape 阶段做 TripSphere 专用清理，后续 RCA 数据集导出阶段再筛选：

```text
URL 原文
完整 query string
local_address
remote_address
local_port
remote_port
进程 PID
进程命令行
trace_id
span_id
request_id
task_id
user_id
```

## 8. 环境事实和门禁

路径映射使用实际 Compose 生效值，不直接假定 Docker 默认目录：

```bash
DOCKER_ROOT_DIR="$(docker info --format '{{.DockerRootDir}}')"
EFFECTIVE_DATA_ROOT="${TRIPSPHERE_DATA_ROOT:-$PWD/volumes}"

docker info --format 'DockerRootDir={{.DockerRootDir}}'
findmnt -T "$DOCKER_ROOT_DIR"
findmnt -T "$EFFECTIVE_DATA_ROOT"
docker volume ls --format '{{.Name}}' \
  | while read -r volume_name; do
      docker volume inspect "$volume_name" \
        --format '{{.Name}} {{.Mountpoint}}'
    done
```

对实际使用的 named volume mountpoint 继续执行 `findmnt -T <mountpoint>`，并将输出中的 `SOURCE`/device 与 hostmetrics 的 `system.device` 对照。`TRIPSPHERE_DATA_ROOT` 非空时必须是绝对路径；root Compose 和 deploy Compose 的有效数据根目录必须解析到同一服务器存储位置。

实施验收前必须记录：

- Docker 版本、Linux kernel 版本、cgroup v1/v2、storage driver。
- Collector、cAdvisor、node-exporter、Prometheus 版本。
- Docker data-root、`TRIPSPHERE_DATA_ROOT`、数据卷目录对应的 mountpoint 和 physical device。
- cAdvisor `/metrics` 中所有 `container_*` 原始指标的 `# TYPE`。
- Collector Prometheus exporter 输出的 hostmetrics 实际 Prometheus 名称，尤其是 `translation_strategy: UnderscoreEscapingWithSuffixes` 后的名称。
- node-exporter sockstat/netstat 指标是否存在。

任一清单项缺失时，不能把该项标记为通过；必须先补 Compose、Collector、Prometheus 或应用 instrumentation。指标缺失应优先修复原始数据源，不通过 `tripsphere:*` recording rules、spanmetrics 或占位序列替代。

## 9. 逐项验收记录模板

| 编号 | 原始指标/接口已存在 | 来源唯一 | labels 合规 | 查询口径已验证 | 结果 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
|  | [ ] | [ ] | [ ] | [ ] | pass/fail |  |
|  | [ ] | [ ] | [ ] | [ ] | pass/fail |  |
|  | [ ] | [ ] | [ ] | [ ] | pass/fail |  |
