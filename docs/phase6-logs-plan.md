# Phase 6 Logs 设计与执行计划

**文档状态：** 待 Review  
**实施顺序：** 2 / 3  
**前置条件：** `docs/phase6-traces-plan.md` 的业务 Trace 基线已通过  
**目标：** Java、Python、Go 业务日志统一通过 OTLP 发送到 OTel Collector，再由 Collector 转发到 Loki。

## 1. 调研结论与决策

OpenTelemetry 自动 Trace 插桩、日志上下文关联和日志导出是独立能力。Java/Python 自动插桩不会自动意味着现有 stdout/stderr 已进入 OTel Logs pipeline；必须启用对应 logging bridge 和 OTLP Logs exporter。Go 当前使用标准库 `log/slog`，需要显式配置 OTel LoggerProvider 和 `otelslog` bridge。

本计划采用单一入库路径：

```text
Java Logback -- Java Agent logging instrumentation --+
Python logging -- Python OTel logging handler --------+--> OTLP gRPC/HTTP
Go log/slog -- otelslog bridge -----------------------+        |
                                                              v
                                                     OTel Collector
                                                              |
                                                        OTLP HTTP
                                                              v
                                                             Loki
```

明确决策：

- 不部署 Grafana Alloy。
- 不使用 Collector `filelog` receiver。
- 不挂载或读取 `/var/lib/docker/containers`。
- 不把 Docker JSON stdout/stderr 作为日志采集链路。
- Collector 是应用日志的唯一接收中间件，也是 Loki 的唯一写入方。
- 应用可保留少量 console 输出用于本地诊断，但该输出不被采集，不能作为 Loki 数据来源。
- 本阶段强制覆盖 Java、Python 和 Go 业务服务；Next.js 与基础设施日志另行规划。

官方依据：

- [OpenTelemetry Logging](https://opentelemetry.io/docs/specs/otel/logs/)
- [Python Logs Auto-Instrumentation Example](https://opentelemetry.io/docs/zero-code/python/logs-example/)
- [Python Agent Configuration](https://opentelemetry.io/docs/zero-code/python/configuration/)
- [Java Agent Supported Libraries](https://opentelemetry.io/docs/zero-code/java/agent/supported-libraries/)
- [OpenTelemetry Go `otelslog` Bridge](https://pkg.go.dev/go.opentelemetry.io/contrib/bridges/otelslog)
- [OpenTelemetry Go Log SDK](https://pkg.go.dev/go.opentelemetry.io/otel/sdk/log)
- [OpenTelemetry Go OTLP Log gRPC Exporter](https://pkg.go.dev/go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc)
- [Loki OTLP Ingestion](https://grafana.com/docs/loki/latest/send-data/otel/)

## 2. 范围

### 2.1 包含

- Java Agent 对 Logback 日志的 OTel bridge 与 OTLP 导出。
- Python `logging` 的自动日志 handler 与 OTLP 导出。
- Go `log/slog` 到 OTel Logs 的 bridge、SDK 和 OTLP 导出。
- Collector OTLP Logs 接收、规范化、脱敏、批处理和 Loki 转发。
- Loki 单实例存储、Grafana 查询及 Trace 双向关联。

### 2.2 不包含

- Alloy、Docker JSON、filelog、journald 或文件日志采集。
- Next.js 浏览器日志、Next.js 服务端日志和基础设施容器日志。
- 业务审计日志、长期归档、告警和 RCA 数据集导出。
- 完整 Prompt、模型响应、工具参数或数据库响应正文。
- 在 Logs 阶段升级现有 Trace instrumentation。

## 3. 统一日志契约

### 3.1 Resource Attributes

与 Trace 基线完全一致：

```text
service.name
service.namespace=tripsphere
deployment.environment.name=local
service.version
```

`service.name` 必须使用逻辑服务名；同一镜像启动的 API 与 Worker 使用不同名称。

### 3.2 LogRecord

| OTel 字段 | 规则 |
| --- | --- |
| `Timestamp` | 使用事件产生时间 |
| `ObservedTimestamp` | 由 SDK/Collector 设置 |
| `SeverityText` / `SeverityNumber` | 保留语言日志级别并映射到 OTel severity |
| `Body` | 日志消息，不包装第二层 JSON envelope |
| `TraceId` / `SpanId` | 活跃 Span 中必须由 bridge 关联 |
| `event.name` | 仅有稳定事件名称时使用 |
| `error.type` | 错误日志记录稳定异常/错误类型 |
| `exception.stacktrace` | 有异常时可记录，但必须限制大小 |
| `request.id` / `task.id` | 上下文真实存在时记录为 attributes |

不制造空 `trace_id`，也不把 Trace ID 重复拼接到日志正文。

### 3.3 Loki 映射

低基数 Loki labels 仅保留：

```text
service_name
service_namespace
deployment_environment_name
```

`trace_id`、`span_id`、`request_id`、`task_id`、severity 和错误属性使用 structured metadata。Loki 会把 OTel attribute 名中的 `.` 规范为 `_`；查询与 Grafana derived field 使用规范化后的名字。

## 4. 执行计划

### Task 1：建设 Collector → Loki 管线

- 保留 Collector `otlp` receiver 的 gRPC `4317` 和 HTTP `4318`。
- 新增专用 logs pipeline，processor 顺序为内存保护、资源/属性规范化、脱敏、批处理。
- 使用 `otlphttp/loki` exporter 写入 `http://loki:3100/otlp`。
- 关闭 logs pipeline 的 detailed debug exporter，避免日志正文出现在 Collector console。
- 不配置 `filelog` receiver、Docker socket、Docker 日志目录或 file storage offset。
- Collector 暴露 receiver accepted/refused、processor dropped、exporter sent/failed 等自身指标。

### Task 2：建设 Loki

- 使用固定版本的单实例 Loki、TSDB v13 schema、filesystem storage 和 7 天 retention。
- 显式设置 `limits_config.allow_structured_metadata: true`。
- 配置 OTLP resource attribute 的索引策略，只索引第 3.3 节低基数字段。
- 限制 structured metadata 单条大小；超大异常栈在 Collector 前置截断。
- 增加 `/ready` healthcheck 和本地持久卷。

### Task 3：接入 Java Logs

- 保留现有 Java Agent，不在应用中再创建第二个 LoggerProvider。
- 为 Java 服务显式设置 `OTEL_LOGS_EXPORTER=otlp`、Logs endpoint/protocol 和统一 resource attributes。
- 使用 Java Agent 自带的 Logback appender instrumentation；先用运行数据确认 agent 已注入 appender，再决定是否需要调整 instrumentation 开关。
- MDC 只允许白名单 `request.id`、`task.id`，不得使用 `*` 捕获全部 MDC。
- 在活动 Span 中生成测试日志，验证 LogRecord 原生 `TraceId`/`SpanId`，不通过 pattern 把它们拼入 body。

### Task 4：接入 Python Logs

- 保留 `opentelemetry-instrument` 和现有 Python logger 调用。
- 设置 `OTEL_LOGS_EXPORTER=otlp`、Logs endpoint/protocol 和统一 resource attributes。
- OTel Python `<1.40` 使用 `OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true`；`>=1.40` 使用 `OTEL_PYTHON_LOG_AUTO_INSTRUMENTATION=true`，以各服务 lockfile 的实际版本选择，不同时设置两个开关。
- 检查 root、Uvicorn、FastAPI、Celery 和业务 logger 的 handler/propagate，确保每条日志只进入一次 OTel handler。
- 现有 `FileHandler` 不再作为部署日志路径；若存在，仅在确认没有其他用途后从容器配置中移除。
- 不在本阶段统一升级 Python OTel 或 OpenInference 版本。

### Task 5：接入 Go Logs

目标服务为 `trip-review-service`，其现有 `log/slog` 调用继续作为应用日志 API。

- 增加与当前 OTel Go 版本兼容的 `go.opentelemetry.io/otel/sdk/log`、`otlploggrpc` 和 `go.opentelemetry.io/contrib/bridges/otelslog` 直接依赖。
- 启动时创建与 Trace 共用 Resource 的 LoggerProvider、OTLP gRPC exporter 和 BatchProcessor。
- 使用 `otelslog.NewHandler` 设置默认 `slog.Logger`；部署模式不组合 stdout JSON handler，避免形成第二事实源。
- 请求路径使用 `slog.*Context(ctx, ...)`，使 bridge 能从 `context.Context` 关联 TraceId/SpanId；启动和关闭日志允许没有 Trace ID。
- 初始化失败必须返回启动错误，不能静默退化为 no-op logger 并声称日志已启用。
- 退出时先停止接收请求，再 `ForceFlush`/`Shutdown` LoggerProvider，并设置有界超时。

### Task 6：脱敏与大小控制

应用层禁止记录 Authorization、Cookie、JWT、密码、secret、API key、连接字符串凭据、完整 Prompt/模型响应和完整配置对象。

Collector 作为第二道防线：

- 删除名称匹配敏感键的 attributes。
- 遮蔽 body 中的 Bearer token、JWT 形态和常见密钥键值。
- 截断超限 body 与 `exception.stacktrace` 并记录 `truncated=true`。
- 在 Loki exporter 之前完成全部脱敏。

### Task 7：Grafana 关联

- 预置 Loki datasource。
- 配置 Loki derived field，从 structured metadata 的 `trace_id` 跳转 Tempo。
- 配置 Tempo Trace-to-Logs，以 `service.name -> service_name` 和 Span 前后 2 秒窗口筛选日志。
- 提供按 service、severity、Trace ID、request ID 和 task ID 的查询示例。

## 5. 测试计划

### 静态配置

- `docker compose config` 成功。
- Collector 配置加载成功，logs pipeline 只有 OTLP receiver 和真实 Loki exporter。
- 配置与 Compose 中不存在 Alloy、filelog、Docker socket 和 Docker 日志目录挂载。
- Loki 配置检查通过且 structured metadata 已启用。

### 分语言验证

- Java：在活动 Span 中写入一个唯一测试事件，Loki 恰好查询到一次。
- Python：分别验证业务 logger、Uvicorn/FastAPI 和 Celery Worker，不因 handler/propagate 重复。
- Go：分别验证 `slog.InfoContext` 和 `slog.ErrorContext`，severity、attributes 和 Trace 关联正确。
- 无活动 Span 的启动日志可以没有 TraceId/SpanId。

### 关联与安全

- 三种语言各选一条日志，`trace_id` 与 Tempo 中的 Trace ID 完全一致。
- Grafana 日志到 Trace、Trace 到日志均可跳转。
- 固定假 JWT、password、API key 和 Authorization 原文不出现在 Loki。
- 超大异常栈被截断，不使同批其他日志被 Loki 拒绝。

### 故障行为

- Loki 暂时不可用时，Collector exporter failure 可观测且应用不被同步导出永久阻塞。
- Collector 暂时不可用时，Java/Python/Go 批处理器有界失败，不无限占用内存。
- Collector 恢复后新日志可继续写入；本阶段不承诺应用进程崩溃时的零丢失。

## 6. 完成标准

- Java、Python、Go 业务服务的日志均经 OTLP 到达 Collector 和 Loki。
- Loki 中不存在来自 Alloy、filelog 或 Docker JSON 的同一日志副本。
- 三种语言的 LogRecord 使用统一服务身份、severity 和错误字段。
- 活动 Trace 内的日志携带正确的原生 TraceId/SpanId。
- 敏感信息和超大字段在进入 Loki 前得到处理。
- Grafana 支持 Logs 与 Tempo 双向关联。
- Next.js 与基础设施日志未被误报为本阶段已覆盖。
