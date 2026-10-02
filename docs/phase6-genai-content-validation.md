# Phase 6 GenAI 内容采集配置与验收

**文档状态：** 已补配置，待环境重建后端到端验收
**需求来源：** Phase 6 可观测基线；用于后续故障注入与 RCA 数据集构建
**适用范围：** `trip-chat-service`、`trip-itinerary-planner`、`trip-order-assistant`、`trip-review-summary`、`trip-review-summary-worker`

## 1. 目标

Phase 6 的 GenAI 内容采集目标是让模型调用、Agent 调用、工具调用和 Review Summary 查询在 Trace/Log 中保留足够上下文，用于后续 RCA 样本还原：

- 用户输入、系统/用户消息、模型输出。
- LLM invocation parameters。
- LLM tool definitions、工具参数和工具响应。
- embedding 输入文本。
- OTel GenAI 语义字段；当前依赖版本不支持时，至少保留 OpenInference 字段。

本阶段不采集外部 API key、Authorization、Cookie、JWT、密码等凭据。

## 2. 配置口径

Python AI 服务同时使用 OpenTelemetry Python 自动插桩和 OpenInference 插桩。仅设置 `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` 不足以覆盖 OpenInference，因此需要同时显式设置 OpenInference 内容开关。

当前配置要求：

```text
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=SPAN_AND_EVENT
OPENINFERENCE_HIDE_INPUTS=false
OPENINFERENCE_HIDE_OUTPUTS=false
OPENINFERENCE_HIDE_INPUT_MESSAGES=false
OPENINFERENCE_HIDE_OUTPUT_MESSAGES=false
OPENINFERENCE_HIDE_INPUT_TEXT=false
OPENINFERENCE_HIDE_OUTPUT_TEXT=false
OPENINFERENCE_HIDE_INPUT_IMAGES=false
OPENINFERENCE_HIDE_EMBEDDINGS_TEXT=false
OPENINFERENCE_HIDE_PROMPTS=false
OPENINFERENCE_HIDE_CHOICES=false
OPENINFERENCE_HIDE_LLM_INVOCATION_PARAMETERS=false
OPENINFERENCE_HIDE_LLM_TOOLS=false
OPENINFERENCE_ENABLE_GENAI_SEMCONV=true
```

不同服务锁定的 OpenInference 版本不完全一致。较老版本不识别 `OPENINFERENCE_ENABLE_GENAI_SEMCONV` 或 `OPENINFERENCE_HIDE_LLM_TOOLS` 时会忽略这些变量；核心输入、输出、消息、文本、prompt、choice 和 embedding 文本开关仍会生效。

## 3. 已修改位置

- 运行时镜像默认值：四个 Python AI 服务 Dockerfile。
- 本地 canonical Compose：`docker-compose.yaml`。
- deploy Compose：`deploy/docker-compose/docker-compose.yaml`。

`trip-review-summary-worker` 复用 `trip-review-summary` 镜像，因此 Dockerfile 修改只需落在 `trip-review-summary/Dockerfile`；worker 自身仍需要在 Compose 中显式声明运行时环境变量。

## 4. 验收流程

### 4.1 静态配置验收

```bash
rg -n 'OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT|OPENINFERENCE_HIDE_INPUTS|OPENINFERENCE_HIDE_PROMPTS|OPENINFERENCE_ENABLE_GENAI_SEMCONV' \
  trip-chat-service/Dockerfile \
  trip-itinerary-planner/Dockerfile \
  trip-order-assistant/Dockerfile \
  trip-review-summary/Dockerfile \
  docker-compose.yaml \
  deploy/docker-compose/docker-compose.yaml

AMAP_KEY=validation docker compose config -q
AMAP_KEY=validation docker compose -f deploy/docker-compose/docker-compose.yaml config -q
git diff --check
```

通过标准：

- 上述 5 个运行时服务均包含完整 OpenInference 内容开关。
- 两份 Compose 均可解析。
- diff 不存在空白错误。

### 4.2 容器环境验收

重建并重启相关 Python AI 服务后执行：

```bash
for service_name in \
  trip-chat-service \
  trip-itinerary-planner \
  trip-order-assistant \
  trip-review-summary \
  trip-review-summary-worker
do
  printf '\n--- %s ---\n' "$service_name"
  docker inspect "$service_name" --format '{{range .Config.Env}}{{println .}}{{end}}' \
    | rg '^(OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT|OPENINFERENCE_)' \
    | sort
done
```

通过标准：

- `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=SPAN_AND_EVENT` 存在。
- 所有 `OPENINFERENCE_HIDE_*` 内容开关为 `false`。
- 支持新语义字段的服务包含 `OPENINFERENCE_ENABLE_GENAI_SEMCONV=true`。

### 4.3 Trace 内容验收

触发一条真实业务请求，优先使用 chat 到 review-summary 的链路，并设置固定请求 ID：

```bash
REQUEST_ID=phase6-genai-content-$(date +%s)
```

查询 Tempo 中该请求附近的 Trace，检查 GenAI span attributes 或 events：

- OpenInference 字段：`input.value`、`output.value`、`llm.input_messages.*`、`llm.output_messages.*`、`llm.invocation_parameters`、`llm.tools.*`。
- OTel GenAI 字段：`gen_ai.input.messages`、`gen_ai.output.messages`、`gen_ai.request.*`、`gen_ai.response.*`、`gen_ai.usage.*`。

通过标准：

- 至少能看到模型调用的输入和输出内容。
- Agent 工具调用能看到工具名、参数或响应内容。
- Review Summary 查询能看到检索/总结相关输入输出内容。
- Trace 中不得出现 OpenAI/Amap/Higress API key 或 Authorization/Cookie/JWT。

### 4.4 Log 内容验收

在 Loki 中按服务和 `request_id` 查询同一请求窗口：

```logql
{service_name=~"trip-chat-service|trip-review-summary|trip-review-summary-worker"} | request_id = "<REQUEST_ID>"
```

通过标准：

- 日志可与 Trace 通过 `request_id`、`trace_id` 或 `span_id` 关联。
- 业务日志保留用户输入、模型输出、工具参数/响应等 RCA 所需上下文。
- 日志中不得出现外部 API key、Authorization、Cookie、JWT、密码。

## 5. 与 Review Summary pinned 模式的关系

当前 Review Summary 索引由脚本导入，查询验收使用 `REVIEW_INDEX_VALIDATION_MODE=pinned`。该模式下通过 review-summary 查询时不一定产生 `trip-review-service` 的下游 Trace/Log，这是合理现象，不影响验证 GenAI 内容采集。

对 RCA 数据集构建的影响是：

- pinned 查询可以作为稳定的 Review Summary/RAG 基线样本。
- 不应把缺少 `trip-review-service` 下游调用误判为 Phase 6 GenAI 内容采集失败。
- 后续若需要覆盖实时评论写入或评论服务依赖故障，应在 Phase 7 或故障注入阶段另建非 pinned 链路样本。

## 6. 完成标准

- Dockerfile 和两份 Compose 的 GenAI 内容采集配置一致。
- 重建后容器环境变量与配置口径一致。
- Tempo 中可查询到 GenAI 输入、输出、参数、工具或 token usage 相关字段。
- Loki 中可按请求关联到相同业务事件。
- 可观测数据保留 RCA 所需业务上下文，同时不泄漏外部凭据。
