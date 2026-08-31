# TripSphere 改造后故障注入实施表

**日期：** 2026-08-25  
**适用基线：** `2026-08-24-tripsphere-systematic-refactor-design.md` 完成 Phase 2–7 后  
**规划样本数：** 约 110（F1≈20、F2≈30、F3≈10、F4≈10、F5≈40；按实际边界可增删）

## 1. 使用边界

本表是改造完成后的实际执行清单，不要求建设多副本、跨实例 checkpoint、自动故障转移或真实支付渠道。所有故障都应能在单实例 Compose 中通过以下方式重复。

### 1.1 两个注入平面

故障分类以**故障发生的链路边界**为准，而不是以请求最终是否经过 LLM 为准：

```text
业务服务
  └─ F2：service-side fault wrapper / Toxiproxy / ChaosBlade
       └─ chat、planner、order-assistant、review-summary → Higress
            └─ F5：Higress upstream LLM fault wrapper
                 └─ Higress → LLM provider
```

- **F2 Network Fault**：业务服务到 Higress（或 Higress 外侧 service-side wrapper）的延迟、丢包、reset、不可达和吞吐故障；也包括业务服务之间的 HTTP/gRPC/A2A 网络故障。
- **F5 Agentic Fault**：Higress 到 LLM 上游的模型响应、structured output、tool call、规划、推理、记忆、handoff 和安全策略故障。LLM fault wrapper 应作为 Higress 的 upstream endpoint，而不是把这些故障伪装成业务服务网络故障。

| 代号 | 注入方式 | 说明 |
|---|---|---|
| `APP` | 应用 failpoint | 测试 profile 或 `FI_*` 环境变量；在 outbound adapter、缓存、持久化和流式出口注入一次性/按次数故障 |
| `CB` | ChaosBlade | 对 Compose 容器或进程执行 CPU、内存、网络延迟、丢包、reset、kill；例如 `chaosblade create cpu load`、`chaosblade create network delay` |
| `TPX` | Toxiproxy | 在 service-side wrapper 与 Higress、gRPC 依赖之间建立 proxy，注入 latency、bandwidth、timeout、reset |
| `HFW` | Higress LLM fault wrapper | 作为 Higress upstream endpoint，按 `fault_profile` 返回 429/5xx、空响应、截断流、非法 JSON、tool call 和错误 reasoning fixture |
| `CFG` | 配置/注册变异 | 修改 Compose 环境变量、Nacos 注册 metadata、Higress upstream、AgentCard 或 A2A metadata fixture |
| `DATA` | 可恢复测试数据 | 使用临时数据库/Redis/Qdrant/Neo4j fixture、TTL 调整、缺索引或空数据，不直接破坏开发卷 |
| `PROC` | Compose 生命周期 | `docker compose stop/pause/kill/restart`，并记录恢复前后状态 |

每个样本必须记录：

```text
fault_id, class, target, boundary, injection_tool, injection_method,
precondition, expected_invariant, observed_status,
request_id, trace_id, cleanup
```

## 2. F1 Resource Fault（20 个）

| ID | 故障 | 注入对象/边界 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F1-01 | chat CPU 配额降低 | `trip-chat-service` 进程 | `CB`: `chaosblade create cpu load --process ... --cpu-percent 90`；Compose 临时 `cpus=0.25` | 请求最终超时或明确失败；无错误成功；trace 有耗时 |
| F1-02 | planner CPU 配额降低 | `trip-itinerary-planner` | `CB` 对容器注入 CPU load，或 Compose 临时 `cpus=0.25` | planner 返回超时/失败状态；不保存半成品行程 |
| F1-03 | order-assistant CPU 抢占 | `trip-order-assistant` | `CB`: `create cpu fullload --container tripsphere-order-assistant` | A2A 请求失败可归因；不重复调用订单工具 |
| F1-04 | order-service CPU 限制 | `trip-order-service` | Compose override `cpus=0.25`，再执行 `docker compose up -d trip-order-service` | 下单不假报成功；库存锁不泄漏 |
| F1-05 | inventory-service CPU 限制 | `trip-inventory-service` | `CB` 对 inventory JVM 进程执行 CPU load | lock/confirm/release 超时返回明确错误 |
| F1-06 | Higress CPU 限制 | `higress` | `CB`: 对 `higress` 容器执行 CPU load；不修改 LLM upstream 响应 | LLM 依赖失败可见；chat/planner 不伪造成功 |
| F1-07 | Nacos CPU 限制 | `nacos` | Compose override `cpus=0.25` 或 `CB` 容器 CPU load | 新请求发现失败可归因；已建立连接行为可记录 |
| F1-08 | chat 内存上限 | `trip-chat-service` | `CB`: `chaosblade create mem`，或 Compose `mem_limit=256m` | 服务不被误判健康；新请求返回依赖不可用 |
| F1-09 | planner 内存上限 | `trip-itinerary-planner` | `CB` 对 planner 容器注入内存压力，验证 healthcheck 与超时 | 生成结果不是截断 JSON；失败可重试 |
| F1-10 | order-service 内存上限 | `trip-order-service` | Compose `mem_limit` 或 `CB mem`，在持久化前触发 OOM | 订单状态不从 `PENDING_PAYMENT` 错写为 `PAID` |
| F1-11 | review-summary 内存上限 | `trip-review-summary` | `CB` 对 uvicorn 进程注入内存压力 | A2A task 为 failed；不返回空成功摘要 |
| F1-12 | Mongo 写入延迟 | Mongo outbound adapter | `APP`: `FI_MONGO_WRITE_DELAY_MS=3000`，仅影响测试请求 | session/review 写入超时明确；不重复写入 |
| F1-13 | PostgreSQL commit 延迟 | order/inventory repository | `APP`: `FI_DB_COMMIT_DELAY_MS=3000`，在事务 commit hook 延迟 | 订单与库存保持一致；trace 标出 DB span |
| F1-14 | Redis 操作延迟 | order/inventory cache adapter | `APP`: `FI_REDIS_DELAY_MS=3000`，分别覆盖幂等键和库存锁 key | 幂等/锁超时不假报成功 |
| F1-15 | Qdrant 查询 IO 延迟 | review-summary/chat retrieval | `APP`: `FI_QDRANT_QUERY_DELAY_MS=3000` | 返回“依赖超时”，不当作“无评论” |
| F1-16 | worker 临时写盘失败 | review-summary worker staging | `APP`: `FI_WORKER_DISK_ERROR=ENOSPC`，只作用于临时目录 | Celery 任务失败；无半成品索引 |
| F1-17 | chat 容器停止 | `trip-chat-service` 容器边界 | `PROC`: `docker compose stop trip-chat-service`，发送请求后再 `up -d` | frontend 得到明确 5xx/超时；恢复后健康检查恢复 |
| F1-18 | planner 容器暂停/恢复 | `trip-itinerary-planner` | `PROC`: `docker pause trip-itinerary-planner`，断开一次 SSE 后 `docker unpause` | SSE/请求不会伪造完成；恢复后新请求可用 |
| F1-19 | order-service kill/restart | `trip-order-service` | `PROC`: `docker compose kill -s SIGKILL trip-order-service && docker compose up -d trip-order-service` | 未完成订单保持原状态；库存锁可查询 |
| F1-20 | Nacos/Higress 重启风暴 | `nacos`、`higress` | `PROC`: 循环执行 `docker compose restart nacos higress` 3 次 | 业务错误可归因；无服务注册脏数据；恢复后可重新发现 |

## 3. F2 Network Fault（30 个）

### 3.1 延迟（F2.1，10 个）

| ID | 故障 | 注入边界 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F2-01 | frontend→chat 延迟 | HTTP/SSE | `TPX`: 在 frontend→chat service-side wrapper 建立 proxy，添加 `latency=2000ms` | 前端显示加载/超时，不重复提交 |
| F2-02 | frontend→planner 首包延迟 | SSE | `CB` 网络延迟或 `TPX` 对 planner HTTP proxy 添加首包前 3000ms delay | SSE 有明确超时；不保存空行程 |
| F2-03 | chat→Higress wrapper 延迟 | 业务服务→Higress 外侧 wrapper | `TPX`: `toxics add latency latency=5000`；故障发生在 caller→Higress 边界 | 返回模型依赖超时；trace 跨网关可关联 |
| F2-04 | planner→Higress wrapper 延迟 | planner→Higress HTTP | `CB` 对 planner 出站网卡注入 5000ms delay，或 `TPX` upstream proxy | planner 不把 fallback 当真实完整结果 |
| F2-05 | chat→Qdrant 延迟 | memory/retrieval HTTP | `TPX`: Qdrant proxy 添加 3000ms latency | 降级为无记忆并标记依赖失败，不跨用户检索 |
| F2-06 | chat→Mongo 延迟 | session Mongo TCP | `CB` 对 chat→Mongo 网络注入 delay，或 `TPX` Mongo proxy | session 读写失败明确；不写入错误用户 |
| F2-07 | order-assistant→product 延迟 | gRPC | `TPX` gRPC proxy 添加 2000ms latency；不改 product 响应内容 | 工具返回 error；草稿不追加未验证 SKU |
| F2-08 | order-assistant→order 延迟 | gRPC/A2A | `CB` 对 order-assistant 出站连接注入 delay，或 `TPX` order proxy | 不重复取消/下单 |
| F2-09 | order→inventory 延迟 | lock/confirm/release gRPC | `TPX` inventory proxy 添加 3000ms latency | 订单状态与库存锁一致 |
| F2-10 | review-summary→Neo4j 延迟 | GraphRAG 查询 | `TPX` Neo4j proxy 添加 3000ms latency | task failed 或明确部分依赖失败 |

### 3.2 丢包、重置和截断（F2.2，10 个）

| ID | 故障 | 注入边界 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F2-11 | chat→Higress wrapper TCP reset | 业务服务→Higress 外侧 wrapper | `TPX`: `toxics add reset`；或 `CB` 对 chat 出站连接执行 reset | chat 返回模型依赖失败 |
| F2-12 | planner→Higress wrapper TCP reset | planner→Higress HTTP | `TPX` planner proxy 注入 reset；不触碰 Higress→LLM upstream | 不产生“成功”回复 |
| F2-13 | Higress wrapper→chat 响应截断 | wrapper→业务服务响应边界 | `TPX` 在响应 body 达到指定字节数后 abort；这是网络截断，不是 LLM 语义故障 | 客户端收到中断状态；不落库为完整回答 |
| F2-14 | planner SSE cutoff | planner→frontend | `TPX` 在第 N 个 event 后 reset，或 `CB` 对 planner HTTP 连接 reset | itinerary 不进入已完成状态 |
| F2-15 | chat→order-assistant A2A reset | A2A | `TPX` A2A proxy 注入 reset；保留原始 headers 便于验证 metadata | chat 说明订单 Agent 不可用；身份 metadata 不泄露 |
| F2-16 | order-assistant→product gRPC unavailable | gRPC | `CB` 对 product service port 注入 blackhole，或 `TPX` 关闭 upstream | SKU 未确认时不能加入草稿 |
| F2-17 | order→inventory connection reset | gRPC | `TPX` inventory proxy 注入 reset | 创建订单失败且 lock 不残留 |
| F2-18 | planner→attraction gRPC reset | gRPC | `CB` 对 attraction service port 注入 reset | 结果标记景点依赖失败 |
| F2-19 | planner→hotel gRPC reset | gRPC | `TPX` hotel gRPC proxy 注入 reset | 不返回虚构酒店；候选为空可识别 |
| F2-20 | review-summary→Qdrant reset | vector search | `TPX` Qdrant proxy 注入 reset | task failed，不误报“无评论” |

### 3.3 局部不可达（F2.3，5 个）

| ID | 故障 | 注入边界 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F2-21 | Nacos 对 chat 不可达 | 服务发现 | `CB` 对 chat→Nacos 端口注入 blackhole；不修改 Nacos 注册数据 | 启动失败或能力明确不可用 |
| F2-22 | planner 对 Higress wrapper 不可达 | 模型网关网络边界 | `TPX` 将 planner upstream 路由到 blackhole，或 `docker network disconnect` 测试网络 | planner 返回模型依赖错误 |
| F2-23 | product 对 order-assistant 不可达 | 工具依赖 | `CB` 对 product gRPC 端口注入 blackhole | 草稿不写入无效 SKU |
| F2-24 | inventory 对 order 不可达 | 库存依赖 | 测试网络执行 `docker network disconnect tripsphere trip-inventory-service` | 下单失败；数据库不产生可支付订单 |
| F2-25 | Redis 对 worker 不可达 | Celery broker/result | `CB` 对 worker→Redis 端口注入 blackhole，或临时切换 `CELERY_BROKER_URL` | 任务状态为失败/未知，不伪造已完成 |

### 3.4 吞吐受限（F2.4，5 个）

| ID | 故障 | 注入边界 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F2-26 | chat→Higress wrapper 吞吐受限 | HTTP/SSE | `TPX`: 添加 `bandwidth=16kbps`；不修改 LLM 内容 | SSE 保持顺序；超时策略生效 |
| F2-27 | planner 大响应分块变慢 | planner→frontend SSE | `CB` 网络 bandwidth limit 或 `TPX` 每块添加 200ms delay | 不出现重复/乱序 event |
| F2-28 | Qdrant 大结果集变慢 | review-summary retrieval | `DATA` fixture 返回上限结果，`TPX` 限制 Qdrant proxy bandwidth | 查询有 limit；不会无限占用内存 |
| F2-29 | Neo4j 大图结果变慢 | GraphRAG | `DATA` fixture 增大关系集，`TPX` 限制 Neo4j proxy bandwidth | 查询有边界；task 可失败并归因 |
| F2-30 | OTel 导出变慢 | service→OTel | `CB` 对 OTLP exporter 注入 latency/drop；业务请求线程不阻塞 | 业务请求不被遥测阻塞；本地日志仍有 request/trace id |

## 4. F3 Configuration Fault（10 个）

| ID | 故障 | 注入对象/边界 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F3-01 | chat Nacos 地址错误 | chat discovery | `CFG`: Compose override `NACOS_SERVER_ADDRESS=bad-nacos:8848`，重启 chat | 启动失败或订单 Agent 能力显式不可用 |
| F3-02 | planner 服务名错误 | planner→attraction/hotel | `CFG`: Nacos naming fixture 将 service name 改为不存在值 | 返回 discovery error；不使用静态假数据冒充成功 |
| F3-03 | order-assistant gRPC metadata 端口错误 | assistant→product/order | `CFG`: Nacos instance metadata 将 `gRPC_port` 改为 `59999` | 工具返回连接错误；无副作用 |
| F3-04 | product endpoint 错误 | order-assistant product | `CFG`: Compose service alias 指向不存在容器名 | SKU 查询失败可定位 |
| F3-05 | inventory endpoint 错误 | order inventory | `CFG`: Nacos metadata 将 inventory IP/port 改为 blackhole | 下单不生成支付中订单 |
| F3-06 | Higress base URL 错误 | 所有 LLM 服务→Higress | `CFG`: 将 `OPENAI_BASE_URL` 改为 `/wrong-v1`，不改 LLM wrapper | 返回 provider 错误；不静默 fallback |
| F3-07 | OpenAI API key 错误 | Higress→LLM upstream | `HFW`: fake upstream 校验 key，`CFG` 注入错误 `OPENAI_API_KEY` | 401/429 被保留为模型依赖错误 |
| F3-08 | 模型名/provider 错误 | chat/planner/review-summary→Higress | `CFG`: 将 model/provider 改为 fake gateway 未注册名称 | 返回配置错误，trace 带 provider |
| F3-09 | order-assistant AgentCard 缺失 | chat→A2A discovery | `CFG`: 从 Nacos AI 发布记录删除 card，再刷新 chat remote-agent cache | chat 明确报告订单 Agent 不可用 |
| F3-10 | AgentCard/A2A metadata 版本不匹配 | chat/order-assistant/review-summary | `CFG`: 修改 AgentCard schema 或 `x-user-id` header key | 请求拒绝或 task failed；用户身份不丢失 |

## 5. F4 Code-Level Fault（10 个）

| ID | 故障 | 注入边界 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F4-01 | CreateOrder 缺必填字段 | order API contract | `APP`/contract test 发送空 `user_id/items/contact` | 4xx/InvalidArgument；不锁库存 |
| F4-02 | Cancel/Payment 非法状态 | order workflow | `APP` 准备 `PAID` fixture，再调用 Cancel/ConfirmPayment | 状态机拒绝；状态不回退 |
| F4-03 | 重复 request id | order idempotency | `APP` 并发发送两次相同 request id，Redis 保持真实实现 | 只产生一个订单和一组库存锁 |
| F4-04 | 持久化失败后补偿失败 | order→inventory | `APP`: `FI_ORDER_SAVE_ERROR=1,FI_INVENTORY_RELEASE_ERROR=1` | 返回失败；告警可见；不假报订单创建 |
| F4-05 | 支付确认库存失败 | order→inventory workflow | `APP`: `FI_INVENTORY_CONFIRM_ERROR=1`，调用 ConfirmPayment | 不能进入 `PAID`；锁状态可查询 |
| F4-06 | 取消释放库存失败 | order cancellation workflow | `APP`: `FI_INVENTORY_RELEASE_ERROR=1`，调用 CancelOrder | 不得静默返回成功；订单/库存不一致要显式暴露 |
| F4-07 | ReplaceItinerary 日期非法 | itinerary contract | contract test 发送 `end_date < start_date` | 4xx；不覆盖旧行程 |
| F4-08 | planner 候选数量不足 | planner→attraction | `APP`: attraction fake gRPC 仅返回 1–2 个候选，验证采样边界 | 不抛未分类异常；生成结果可验证 |
| F4-09 | review-summary 缺 target_type | review query contract | A2A contract fixture 删除 `target_type` data part | task failed；不混淆 hotel/attraction |
| F4-10 | 下游返回结构变化 | adapter contract | `HFW`/fake gRPC server 返回缺字段、未知枚举或破坏性 JSON | 明确 dependency/contract error；无脏数据写入 |

## 6. F5 Agentic Fault（40 个）

### 6.1 LLM 接口/响应（F5.1，4 个）

| ID | 故障 | 注入对象 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F5-01 | LLM 429 | Higress→LLM upstream | `HFW`: 将 `fault_profile=llm_429` 配置为 Higress upstream，固定返回 429 + `Retry-After` | 错误归因为模型限流；不无限重试 |
| F5-02 | LLM 空响应 | Higress→LLM upstream→chat | `HFW`: `fault_profile=empty_content`，返回合法 HTTP 200 但空 `content` | 返回可识别失败；不保存空 assistant message |
| F5-03 | structured output schema 不匹配 | Higress→LLM upstream→planner | `HFW`: `fault_profile=invalid_structured_output`，返回缺 `day_plans`/错误类型 | planner 校验失败；不保存半成品 |
| F5-04 | tool_calls 参数非法 | Higress→LLM upstream→order-assistant | `HFW`: `fault_profile=invalid_tool_args`，返回负数量/非法日期/未知 SKU | 工具拒绝；不修改草稿或订单 |

### 6.2 Planning（F5.2，4 个）

| ID | 故障 | 注入对象 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F5-05 | 行程天数与日期不一致 | planner workflow | `HFW`: `fault_profile=plan_date_mismatch`，返回多一天的 `day_plans` | 基本结构校验拒绝或修正 |
| F5-06 | 用户节奏约束遗漏 | planner prompt | `HFW`: `fault_profile=pace_violation`，固定响应超过 relaxed 活动数 | 输出带校验结果；不宣称满足约束 |
| F5-07 | 订单流程跳过草稿 | order-assistant planning | `HFW`: `fault_profile=skip_draft_submit`，直接生成 submit tool call | submit 拒绝无效 draft；不创建订单 |
| F5-08 | review 索引计划缺 target filter | review-summary index | `APP`: `FI_REVIEW_INDEX_DROP_TARGET_FILTER=1`，或删除 task context 过滤条件 | 任务失败；不写入混合索引 |

### 6.3 Memory/Context/State（F5.3，4 个）

| ID | 故障 | 注入对象 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F5-09 | Mongo session 缺失 | chat session | `DATA`: 在临时 Mongo 删除指定 session document | 新建/恢复会话行为明确；不串用户 |
| F5-10 | Mem0 返回旧记忆 | chat memory | `APP`: Mem0 adapter fixture 返回过期 user memory | 只使用当前用户上下文；日志记录 memory miss |
| F5-11 | Qdrant 跨用户过滤失效 | chat memory | `APP`: 在 retrieval adapter 测试 profile 删除 user filter | 测试必须失败；禁止输出其他用户记忆 |
| F5-12 | ORDER_DRAFTS 重启丢失 | order-assistant state | `PROC`: `docker compose restart trip-order-assistant` 后提交原 draft id | draft 明确失效；不得提交未知 draft |

### 6.4 Reasoning（F5.4，4 个）

| ID | 故障 | 注入对象 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F5-13 | 评论总结无依据事实 | review-summary answer | `HFW`: `fault_profile=ungrounded_summary`，在真实检索上下文外追加事实 | groundedness 断言失败或答案标记不确定 |
| F5-14 | 行程虚构景点 | planner answer | `HFW`: `fault_profile=hallucinated_attraction`，返回候选集外地点 | 结果校验拒绝或标注未验证 |
| F5-15 | 商品价格解释错误 | order-assistant | `HFW`: `fault_profile=wrong_price_explanation`，改写工具返回的金额 | 工具数据优先；回复与 SKU 价格一致 |
| F5-16 | 订单状态解释错误 | order-assistant | `HFW`: `fault_profile=wrong_order_status`，将 `PENDING_PAYMENT` 说成 paid | 服务端状态优先；不得执行支付后续动作 |

### 6.5 Action/Tool（F5.5，4 个）

| ID | 故障 | 注入对象 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F5-17 | get SKU 误选 get SPU | product toolset | `HFW`: `fault_profile=wrong_tool_name`，记录 get SPU tool call | 返回类型校验失败；不加入草稿 |
| F5-18 | 酒店日期参数颠倒 | order draft tool | `HFW`: `fault_profile=invalid_date_range`，生成 `end_date < start_date` | 工具 4xx；草稿不追加 |
| F5-19 | 取消订单缺确认 | order toolset | `HFW`: `fault_profile=cancel_without_confirmation`，直接生成 cancel tool call | 必须被确认门槛拦截 |
| F5-20 | itinerary 工具坐标非法 | planner tools | `APP`: geocoding/attraction fake gRPC 返回经纬度超范围 | 结构校验失败；不写入 itinerary |

### 6.6 Inter-Agent Role/Dependency（F5.6，4 个）

| ID | 故障 | 注入对象 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F5-21 | chat 发现错误 Agent | chat Nacos AI | `CFG`: Nacos AI 发布同名错误 AgentCard，或替换 AgentCard URL | 能力校验拒绝；不发送订单请求 |
| F5-22 | order-assistant 角色名不一致 | AgentCard | `CFG`: `agent.json.name` 与 Nacos AI 注册名改成不同值 | discovery 失败并可定位 |
| F5-23 | review-summary 依赖假设错误 | summary executor | `CFG`/`DATA`: 移除 Qdrant 或 Neo4j dependency fixture | task failed；不返回空摘要 |
| F5-24 | planner 误依赖已删除 POI service | planner discovery | `CFG`: 注入旧 `trip-poi-service` service name | 明确配置错误；不得恢复旧服务 |

### 6.7 Inter-Agent Instruction（F5.7，4 个）

| ID | 故障 | 注入对象 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F5-25 | 用户目的地与系统目的地冲突 | planner prompt/state | `HFW`: `fault_profile=destination_conflict`，让 state 与 prompt 使用不同城市 | 请求拒绝或要求澄清 |
| F5-26 | 取消确认语义冲突 | order-assistant instruction | `HFW`: `fault_profile=implicit_cancel_consent`，注入“默认同意取消” | 服务端仍要求显式确认 |
| F5-27 | hotel/attraction 类型冲突 | review query context | `APP`: A2A context fixture 让 `target_id` 与 `target_type` 不匹配 | 查询为空或失败，不跨类型返回 |
| F5-28 | chat 上下文与用户说法冲突 | chat session | `DATA`: 在临时 Mongo session 注入另一酒店上下文 | 以当前请求和权限为准；不泄露旧上下文 |

### 6.8 Communication/Handoff（F5.8，4 个）

| ID | 故障 | 注入对象 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F5-29 | A2A user metadata 丢失 | chat→order-assistant | `APP`: A2A metadata provider 删除 `x-user-id`/`authorization` | 下游拒绝越权操作 |
| F5-30 | A2A 消息重复 | chat→order-assistant | `TPX`: A2A proxy 重放同一 message id，或测试 client retry 同一 request | 工具调用幂等；不重复下单/取消 |
| F5-31 | review task event 丢失 | review-summary A2A | `APP`: event queue wrapper 丢弃 `working` event | 最终状态仍可查询；不报告错误完成 |
| F5-32 | stream cutoff 后重放 | chat/planner SSE | `TPX` 断流后测试 client 重发最后 event；与 F2-13 区分为重放语义 | 客户端去重；不重复保存结果 |

### 6.9 Security/Policy Boundary（F5.9，4 个）

| ID | 故障 | 注入对象 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F5-33 | 评论文本 prompt injection | review-summary RAG | `DATA`: 在 ReviewService fixture 中写入“忽略系统规则”的恶意评论文本 | 评论只作为数据；不能改变系统策略 |
| F5-34 | 越权取消他人订单 | order-assistant/order-service | contract test 使用 user A JWT 请求 user B order id | 服务端返回 permission denied |
| F5-35 | 跨用户 Mem0 检索 | chat memory | `APP`: 变异 user id/filter，再用双用户 fixture 查询 | 不返回其他用户记忆 |
| F5-36 | 恶意 AgentCard 指令 | A2A discovery | `CFG`: AgentCard instruction 字段注入外部命令/提示 | AgentCard 只用于能力描述；不执行任意指令 |

### 6.10 Recovery/Fault Attribution（F5.10，4 个）

| ID | 故障 | 注入对象 | 精确注入方法 | 预期不变量/验证 |
|---|---|---|---|---|
| F5-37 | 模型超时错误归因 | Higress→LLM upstream | `HFW`: `fault_profile=llm_timeout`，上游连接超时；不在 chat→Higress 链路注入 | 错误分类为 model timeout，不是业务无数据 |
| F5-38 | 景点工具失败降级 | planner→attraction tool result | `HFW`: `fault_profile=attraction_tool_unavailable`，LLM 生成工具失败场景；gRPC 网络故障仍归 F2 | 结果标记 attraction dependency failure |
| F5-39 | 空索引与 Qdrant 宕机区分 | review-summary retrieval | 一次用 `DATA` 空 collection，一次用 `TPX` Qdrant reset；比较两类状态 | 两种状态返回不同业务状态 |
| F5-40 | 取消后释放失败恢复 | order→inventory | `APP`: `FI_INVENTORY_RELEASE_ERROR_COUNT=1`，第一次失败、第二次成功 | 首次不假报；重试后状态和库存最终一致 |

## 7. 执行顺序

建议按以下批次落地：

1. 先实现 `APP`、`HFW`、`CFG` 三类控制开关并完成 F3/F4。
2. 再用 Compose `PROC` 完成 F1-17–F1-20。
3. 引入代理后完成 F2；优先延迟、reset、SSE cutoff，再做局部不可达。
4. 最后执行 F5；先做接口/工具/权限边界，再做推理和恢复归因。

每个样本执行后必须恢复配置、清理临时数据卷、确认健康检查恢复，并在 Loki、Prometheus、Tempo 中用同一个 `request_id/trace_id` 验证故障可定位。
