# Phase 6 Logs 人工验收手册

## 1. 验收边界

本手册验证两条日志入口：

```text
业务 Java/Python/Go -> OTLP -> Collector logs/app -> Loki
基础设施 stdout/stderr -> Docker json-file -> Collector filelog -> Loki
```

同时确认：

- 不部署 Alloy。
- 前端日志不进入 Loki。
- 既有 Trace 链路不变。
- cAdvisor 不承担日志采集。
- 只遮蔽 Amap、OpenAI 等外部 API key。
- Prompt、模型响应、工具参数/响应、AG-UI context、用户 ID、地理位置和数据库业务响应保持完整。

## 2. 静态配置检查

从仓库根目录执行：

```bash
docker compose config --quiet

AMAP_KEY=phase6-config-placeholder \
docker compose \
  --env-file .env \
  -f deploy/docker-compose/docker-compose.yaml \
  config --quiet
```

Collector 与 Loki 使用固定版本镜像校验：

```bash
docker run --rm \
  --entrypoint /otelcol-contrib \
  -v "$PWD/infra/otel-collector/config.yaml:/etc/otelcol-contrib/config.yaml:ro" \
  otel/opentelemetry-collector-contrib:0.144.0 \
  validate --config=/etc/otelcol-contrib/config.yaml

docker run --rm \
  -v "$PWD/infra/loki/loki.yaml:/etc/loki/loki.yaml:ro" \
  grafana/loki:3.6.4 \
  -config.file=/etc/loki/loki.yaml -verify-config=true
```

预期：命令均以退出码 0 结束。

## 3. 重建核心服务

不删除卷：

```bash
docker compose up -d --force-recreate loki otel-collector grafana
docker compose ps loki otel-collector grafana
```

确认健康接口：

```bash
curl --fail http://localhost:3100/ready
curl --fail http://localhost:13133/
curl --fail http://localhost:13000/api/health
```

查看 Collector 启动日志，不能出现配置解析、Docker socket 权限、日志目录权限或动态 receiver 创建失败：

```bash
docker compose logs --since=10m otel-collector
```

Collector 默认会对同一日志点采样，`starting receiver` 通常只显示前 10 条，不能用该行数判断基础设施覆盖数量。应以本节后续的 Loki `service_name` 查询逐项验收；需要临时诊断时可在独立配置中关闭 telemetry log sampling，不要把 debug 设置带入正式配置。

首次从 Docker JSON 文件开头回放历史日志时，也不能持续出现 Loki `429` 或 `ResourceExhausted`。本地单实例 Loki 使用 32 MiB/s ingestion rate 和 64 MiB burst；该设置用于消化历史回放，不改变日志内容。

## 4. 基础设施 filelog 验收

### 4.1 检查宿主机访问和 offset

```bash
docker inspect otel-collector \
  --format '{{range .Mounts}}{{println .Source "->" .Destination .Mode}}{{end}}'
```

预期至少包含：

```text
/var/lib/docker/containers -> /var/lib/docker/containers ro
/var/run/docker.sock -> /var/run/docker.sock ro
tripsphere-otel-collector-file-storage -> /var/lib/otelcol/file_storage rw
```

Collector self metrics 应出现 file consumer 指标：

```bash
curl --silent http://localhost:8888/metrics \
  | grep -E 'otelcol_fileconsumer_(open|reading)_files'
```

### 4.2 验证基础设施服务标签

依次重启待验收基础设施容器，使其产生新的启动日志；不附带 `-v`：

```bash
docker compose restart mongodb postgres redis nacos qdrant neo4j minio higress
docker compose restart rmq-namesrv rmq-broker rmq-proxy rmq-dashboard
```

等待服务恢复后查询 Loki 的服务标签：

```bash
curl --get --silent http://localhost:3100/loki/api/v1/label/service_name/values
```

root Compose 预期至少出现：

```text
mongodb postgres redis nacos qdrant neo4j minio higress
rmq-namesrv rmq-broker rmq-proxy rmq-dashboard
```

逐个查询最近日志：

```bash
curl --get --silent http://localhost:3100/loki/api/v1/query_range \
  --data-urlencode 'query={service_name="mongodb"}' \
  --data-urlencode 'limit=20'

curl --get --silent http://localhost:3100/loki/api/v1/query_range \
  --data-urlencode 'query={service_name="rmq-broker"}' \
  --data-urlencode 'limit=20'
```

验收每条日志的 `service_namespace=tripsphere`、
`deployment_environment_name=local`、`container_id`、`container_name`、
`container_image_name`、`log_iostream` 和正文。

### 4.3 验证排除项

以下查询必须没有 filelog 数据流：

```logql
{service_name="trip-next-frontend"}
{service_name="otel-collector"}
{service_name="loki"}
{service_name="grafana"}
{service_name="tempo"}
{service_name="prometheus"}
```

业务服务只能出现 OTLP Resource 身份，不应带 `log_file_path`。如同一业务事件出现一条带 `log_file_path`、一条带原生 Trace ID，则说明白名单失效，验收不通过。

## 5. 业务 OTLP 验收

分别执行一条 Java、Python、Go 真实业务请求。记录请求时间、服务名和返回的 Trace ID，然后查询：

```logql
{service_name="trip-order-service"}
{service_name="trip-chat-service"}
{service_name="trip-review-service"}
```

每种语言检查：

1. 日志正文与真实操作一致。
2. 活跃 Span 内日志具有原生 `trace_id` 和 `span_id`。
3. 同一个业务事件只出现一次。
4. Grafana 日志详情中的 TraceID 能跳转到 Tempo。
5. Tempo 的 Trace to Logs 能返回对应日志。

## 6. 数据保真验收

通过正常业务入口提交带唯一标记的非秘密测试内容，例如：

```text
PHASE6_PROMPT_KEEP_20260909
PHASE6_TOOL_ARGUMENT_KEEP_20260909
PHASE6_AGUI_CONTEXT_KEEP_20260909
PHASE6_LOCATION_KEEP_20260909
PHASE6_DB_RESPONSE_KEEP_20260909
```

在 Grafana Explore 或 Loki API 中搜索每个标记，确认完整值仍在，且没有 `[REDACTED]`、`[truncated]` 或字符缺失。还应检查真实模型响应、工具响应和数据库业务响应能够按原有日志级别查询。

## 7. API key 脱敏验收

只使用固定假 key，不要把真实 key 写入命令历史。通过业务测试请求或 OTLP 测试客户端生成包含以下形式的日志：

```text
OPENAI_API_KEY=sk-phase6-fake-key-1234567890
AMAP_KEY=phase6-fake-amap-key
https://restapi.amap.com/v3/geocode/geo?key=phase6-fake-amap-key
```

预期 Loki 中字段名和其余上下文仍存在，但值替换为 `[REDACTED_API_KEY]`。随后用原值搜索，结果必须为空。

另外生成包含固定假 JWT、password、token、Cookie 和数据库 URI 的非 API-key 日志，确认这些内容不会被 Collector 的通用规则删除。本项只验证当前明确的数据边界，不表示这些内容适合在其他环境公开。

## 8. offset 与重启验收

1. 记录某基础设施服务当前最后一条 Loki 日志时间。
2. 重启 Collector：

```bash
docker compose restart otel-collector
```

3. 确认历史 Docker JSON 没有从头重复写入。
4. 再重启一个基础设施服务，确认新日志继续到达 Loki。
5. 检查 Collector 没有 offset storage 错误。

## 9. 验收记录

记录以下证据：

- 验收日期和验收人。
- 实际 Docker、Collector、Loki 镜像版本。
- 两份 Compose 和两个固定版本配置校验结果。
- 每个基础设施服务的一条 Loki 查询结果。
- Java、Python、Go 各一个 Trace ID 和双向跳转截图。
- 数据保真标记查询结果。
- 固定假 API key 脱敏查询结果。
- Collector 重启前后的 offset/去重结果。

此前基于“仅业务 OTLP、无 filelog”和广泛脱敏规则生成的自动验收记录已经失效，不能作为当前方案的验收证据。人工完成本手册前，Phase 6 Logs 状态保持“已实现，待人工验收”。
