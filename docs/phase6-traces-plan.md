# Phase 6 Trace 设计与执行计划

**文档状态：** 待 Review  
**实施顺序：** 1 / 3  
**变更策略：** 冻结现有 Trace 实现，先验收；只有实际业务链路断裂时才修改。

## 1. 当前结论

Trace 已不是 Phase 6 的建设重点。2026-09-06 通过 Tempo `/api/search` 已查询到来自 Java、Python、Next.js 和 Python Worker 的真实数据，包括 `trip-user-service`、`trip-order-service`、`trip-inventory-service`、`trip-hotel-service`、`trip-product-service`、`trip-chat-service`、`trip-itinerary-planner`、`trip-review-summary`、`trip-review-summary-worker` 和 `trip-next-frontend`。

当前仓库也已具备：

- Java 服务使用 OpenTelemetry Java Agent。
- Python 服务由 `opentelemetry-instrument` 启动，并保留现有 OpenInference 插装。
- Next.js 使用 `@vercel/otel`。
- OTel Collector 同时监听 OTLP gRPC `4317` 与 HTTP `4318`，并向 Tempo 转发。
- Tempo 显式监听容器网络地址并使用本地存储。

Tempo 中存在数据只能证明采集管线工作，健康检查、定时任务和单服务 Trace 不能替代跨服务业务链路验收。

官方依据：

- [OpenTelemetry Zero-code Instrumentation](https://opentelemetry.io/docs/concepts/instrumentation/zero-code/)
- [OpenTelemetry Context Propagation](https://opentelemetry.io/docs/concepts/context-propagation/)
- [OpenTelemetry Java Agent](https://opentelemetry.io/docs/zero-code/java/agent/)
- [OpenTelemetry Python Zero-code Instrumentation](https://opentelemetry.io/docs/zero-code/python/)
- [OpenTelemetry gRPC Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/rpc/grpc/)

## 2. 本阶段目标与边界

### 2.1 目标

- 保存一条可重复查询的真实业务 Trace，作为后续 Logs、Metrics 和 RCA 数据集的关联基线。
- 确认基线链路中跨 HTTP、gRPC、A2A 或任务边界的父子关系。
- 固定所有信号共用的服务身份字段。

### 2.2 默认不做

- 不升级 Java Agent、Python OTel、OpenInference 或 `@vercel/otel`。
- 不重建现有 TracerProvider、exporter、propagator 或 sampler。
- 不增加全量业务方法 Span。
- 不因某个服务未出现在 Tempo 最近查询结果中就修改该服务。
- 不在 Trace 阶段引入 spanmetrics、日志或资源指标配置。

## 3. 冻结契约

三信号使用相同的资源身份：

```text
service.name=<compose-service-name>
service.namespace=tripsphere
deployment.environment.name=local
service.version=<release-or-git-sha>
```

Trace 保持当前 OTLP 协议与入口，不为追求形式统一切换 Java/Python/Next.js 的已工作协议。W3C `tracecontext` 与 `baggage` 由现有 instrumentation 传播；只有实测出现断链且自动插桩无法覆盖时，才在该边界手工 inject/extract。

Span 与 Baggage 不得包含 JWT、Cookie、API key、完整 Prompt、完整模型响应或用户隐私数据。

## 4. 执行计划

### Task 1：保存 Trace 基线

- 记录 Collector、Tempo 和各语言插桩的当前版本与有效配置。
- 调用一条确定性的订单、行程或评论业务路径，不使用 `/health`、`/ready`、`/actuator/prometheus` 作为验收请求。
- 保存 Trace ID、请求时间、入口服务、涉及服务和查询方法。
- 导出或截图只作为人工证据；自动验收以 Tempo API 返回为准。

### Task 2：检查业务链路完整性

对基线 Trace 逐项检查：

- 根 Span 属于真实入口。
- 跨服务 client/server 或 producer/consumer Span 使用同一 Trace ID。
- 父子关系能够解释实际调用顺序。
- 错误请求带有符合现有 instrumentation 行为的错误状态或异常事件。
- 同一边界不存在重复的 server Span。
- `service.name` 与 Compose service 一致。

### Task 3：仅对已证实断点修补

若 Task 2 通过，本任务无代码变更并结束 Trace 阶段。

若 Task 2 失败，先记录断点的调用方、被调用方、协议和缺失方向，再采用最小修补：

1. 先修正已有自动插桩的启动或环境配置。
2. 再检查自定义 client、carrier、异步任务 header 是否绕开自动传播。
3. 只有前两项无法覆盖时才增加局部手工传播。
4. 只有 RCA 确实需要且自动 Span 不表达该步骤时才增加业务 Span。

不得借此任务统一升级依赖或重构所有服务。

## 5. 验收

### 配置验收

- `docker compose config` 成功。
- Collector traces pipeline 存在非 debug 的 Tempo exporter。
- Tempo OTLP receiver 可由 Collector 访问。
- 所有基线服务具有唯一且稳定的 `service.name`。

### 数据验收

- Tempo API 能按保存的 Trace ID 查询到完整业务 Trace。
- Trace 至少跨越两个业务服务，而非只有健康检查或基础设施 Span。
- 所需 HTTP、gRPC、A2A 或任务边界的父子关系可解释。
- 基线中没有敏感字段和重复 server Span。

## 6. 完成标准

- 一条真实跨服务 Trace 被保存为后续阶段的固定关联样本。
- Trace 验收通过时，现有应用插桩和 Collector/Tempo 配置保持不变。
- 若发生修补，每个改动都能对应一个复现过的具体断点。
- Logs 阶段可以使用该 Trace 验证 `trace_id`、`span_id` 关联。
