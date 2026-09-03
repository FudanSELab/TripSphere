# TripSphere Phase 5 订单闭环设计

**日期：** 2026-08-30
**状态：** 已批准并完成代码级实施
**范围：** `docs/服务改造清单.md` 中的 Phase 5，不包含 Phase 6 部署与可观测性工作

## 1. 目标

完成“酒店房型 SKU -> 前端或订单助手创建订单 -> 锁定库存 -> 模拟支付或取消”的订单闭环，并修复当前实现中会返回错误业务结果或允许跨用户操作的缺口。

完成后的用户行为为：

1. 用户在酒店详情页选择 SKU，填写入住日期、退房日期、数量和联系人后创建订单。
2. 新订单以 `PENDING_PAYMENT` 状态出现在“我的订单”页面。
3. 用户可以模拟支付自己的待支付订单，订单进入 `PAID`，库存锁进入已确认状态。
4. 用户可以取消自己的待支付订单，订单进入 `CANCELLED`，库存锁释放。
5. 用户也可以通过 chat 委派给 order-assistant 创建草稿、补联系人、确认草稿、提交、查询、取消和模拟支付。
6. 相同用户使用相同 `request_id` 重试时只能得到原订单，不能创建重复订单。

## 2. 范围边界

### 2.1 本阶段实现

- 酒店详情页 SKU 预订弹窗和前端创建订单 Server Action。
- “我的订单”模拟支付入口以及取消/支付错误反馈。
- order-assistant 联系人、草稿确认、稳定幂等键、提交后清理和支付工具。
- order-assistant 对下游订单调用的认证 metadata 转发。
- order-service 基于现有 `x-user-id` metadata 的用户身份和订单归属校验。
- 订单幂等键的数据库事实记录，Redis 继续作为快速命中缓存。
- SKU、SPU、联系人、日期和库存实际价格校验。
- 取消与支付的状态预检，以及库存操作失败时的真实失败返回。

### 2.2 本阶段不实现

- 真实支付渠道、退款、订单 `COMPLETED` 后续履约。
- order-assistant 草稿迁移到 Redis 或 MongoDB；单实例进程内草稿满足本阶段要求。
- 新的认证体系、JWT 验证架构或 protobuf 身份字段重构。
- Attraction 详情页新建商品展示模块；景点 SKU 仍可由 order-assistant 下单。
- Compose、健康检查、遥测、日志、指标和 trace；这些属于 Phase 6。
- 高可用、跨实例一致性、Outbox、完整 Saga 补偿或新消息系统。
- 新增或运行自动化测试。按用户要求，本阶段只编码并进行静态代码审查。

## 3. 架构与身份边界

保留现有 Next.js Server Actions、静态 gRPC 客户端、order-assistant A2A、Nacos 服务发现以及 Product/Inventory/Order 三服务边界，不修改 protobuf 接口。

order-service 增加与 itinerary-service 同类的轻量 gRPC 请求上下文：全局拦截器读取 `x-user-id`、`x-user-roles` 和 `authorization`，业务入口只使用 `x-user-id` 作为当前仓库既有的可信用户标识。本阶段不在 order-service 内重复验证 JWT。

身份规则如下：

- `CreateOrderRequest.user_id` 必须与 metadata 中的当前用户一致；持久化时使用当前用户 ID。
- `ListUserOrdersRequest.user_id` 必须与当前用户一致。
- Get、GetByNo、Cancel 和 ConfirmPayment 在返回或执行操作前必须确认订单属于当前用户。
- order-assistant 从 A2A metadata 获取当前用户身份，并在调用 order-service 时转发原有认证 metadata。
- order-assistant 的每个草稿读取、修改、确认、删除和提交操作都校验草稿 owner。

## 4. 前端下单与订单管理

酒店详情页保留当前房型和 SKU 表格。每个可售 SKU 的“预订”按钮打开客户端弹窗，字段包括：

- 入住日期，默认今天。
- 退房日期，默认明天，必须晚于入住日期。
- 房间数量，必须为正整数。
- 联系人姓名，登录时使用 session 姓名作为默认值。
- 联系电话，必填。
- 联系邮箱，登录时使用 session 邮箱作为默认值，且必须是合法邮箱。

客户端为一次提交生成 UUID `request_id`，提交期间禁用按钮。Server Action 重新校验所有输入，从服务端 session 获取用户 ID，显式覆盖 metadata 中的 `x-user-id`，并以 `channel=web` 创建订单。成功后关闭弹窗并跳转 `/orders`；失败时保留表单并显示服务端错误。

订单卡片仅对 `PENDING_PAYMENT` 展示“取消订单”和“去支付”。“去支付”调用 `ConfirmPayment(payment_method="mock")`，成功后刷新订单页；取消和支付失败时在卡片内显示错误，不以无反馈方式吞掉失败。

## 5. order-assistant 草稿与工具

进程内草稿结构增加：

- `user_id`：草稿 owner。
- `request_id`：创建草稿时生成，所有提交重试复用。
- `contact`：姓名、电话和邮箱。
- `confirmed`：草稿是否已由用户确认。
- `items` 和 `source`：沿用现有结构。

工具行为：

1. `create_order_draft` 创建未确认草稿。
2. `set_order_draft_contact` 校验并设置联系人，随后将草稿重置为未确认。
3. 添加酒店或景点 SKU 时校验日期格式、日期关系、数量和 SKU 可用状态，并将草稿重置为未确认。
4. `confirm_order_draft` 只在联系人完整且至少包含一个商品时将草稿标记为已确认。
5. `submit_order_draft` 只提交已确认草稿，并复用草稿的 `request_id`；成功后删除草稿，失败时保留草稿供重试。
6. Get、GetByNo、Cancel 和新增的 `confirm_payment` 都转发当前用户 metadata，由 order-service 做最终归属校验。

Agent instruction 和 AgentCard 同步声明创建、查询、取消和模拟支付能力。取消仍要求对话层先向用户确认；最终不可绕过的安全边界由 order-service 的身份和状态校验承担。

## 6. order-service 正确性

### 6.1 持久化幂等

Order 领域对象和数据库实体记录 `request_id`。数据库以 `(user_id, request_id)` 作为唯一业务键，并提供按该组合查询的方法。

创建订单时先查询数据库；存在则返回原订单。Redis 可以缓存该映射以减少数据库查询，但 Redis 不可用、缓存过期或服务重启不得导致同一用户和 request id 创建第二笔订单。没有 request id 的旧调用继续使用短窗口指纹去重。

### 6.2 商品与输入校验

- 联系人姓名、电话和邮箱必须非空；邮箱格式必须合法。
- SKU 必须存在且为 `ACTIVE`。
- SKU 对应 SPU 必须存在且为 `ON_SHELF`。
- 仅接受 `HOTEL_ROOM` 和 `ATTRACTION` 资源类型。
- 下单日期不得早于当前日期；酒店退房日期必须晚于入住日期；景点订单不得带退房日期。
- 数量必须为正整数。
- Inventory 的每日价格是实际成交价事实源。任一日期缺少库存价格或价格查询失败时，建单失败；不能退回 Product base price 并继续成功。

### 6.3 库存与状态顺序

创建订单继续先锁库存、再持久化订单；持久化或实际价格装配失败时释放本次库存锁。

取消流程先确认订单属于当前用户且状态为 `PENDING_PAYMENT`，再释放全部库存锁。任一释放失败时返回失败并保留订单原状态，不能记录日志后返回取消成功。

支付流程先确认订单属于当前用户、状态为 `PENDING_PAYMENT` 且未过期，再确认全部库存锁。库存确认失败时返回失败并保留订单原状态；全部成功后才写入 `PAID`。

本阶段订单当前只产生一个库存锁，因此不存在多个锁之间的部分成功路径；代码仍按 distinct lock id 处理现有模型。

## 7. 错误处理

- 缺少认证 metadata 返回 `UNAUTHENTICATED`。
- 请求用户与当前用户不一致、访问其他用户订单返回 `PERMISSION_DENIED`。
- 非法联系人、日期、数量、资源类型和缺失实际价格返回 `INVALID_ARGUMENT`。
- 订单不存在返回 `NOT_FOUND`。
- 非待支付订单的取消/支付、过期订单支付和库存状态冲突返回 `FAILED_PRECONDITION`。
- 前端和 order-assistant 保留后端错误语义并向用户显示失败，不把依赖失败转换为空订单或成功消息。

## 8. 文件职责规划

预计修改范围：

- `trip-next-frontend/actions/order.ts`：创建、取消和模拟支付 Server Actions。
- `trip-next-frontend/components/hotel-detail/*`：SKU 预订弹窗接入。
- `trip-next-frontend/components/orders/order-card.tsx`：支付和错误反馈。
- `trip-order-assistant/src/order_assistant/tools/order.py`：认证 metadata、查询/取消/支付工具。
- `trip-order-assistant/src/order_assistant/tools/order_draft.py`：草稿 owner、联系人、确认、幂等提交和清理。
- `trip-order-assistant/src/order_assistant/agent.py` 与 `agent.json`：能力和使用顺序。
- `trip-order-service` 的 gRPC 接入、安全上下文、领域模型、应用服务和持久化适配器：身份、归属、幂等和状态/库存顺序。

仅当代码审计发现库存服务自身违背锁定、确认或释放契约时才修改 `trip-inventory-service`；当前审计未发现 Phase 5 必须修改的库存实现。

## 9. 审查与完成标准

按用户要求不新增、不修改、不运行测试。编码完成后执行以下非测试审查：

- 逐文件静态审查身份边界、状态转换顺序和失败传播。
- 检查 protobuf 生成代码没有不必要变更。
- 检查 Phase 5 diff 未包含 Compose、可观测性或删除服务工作。
- 执行格式检查或格式化，以及 `git diff --check`；不执行编译、lint、单元测试、集成测试或 smoke test。

代码层完成判定：前端和 order-assistant 均具有完整订单入口；order-service 能静态证明同一用户 request id 幂等、订单归属受限、库存失败不会产生虚假成功，且 Phase 5 范围外代码未被修改。
