# TripSphere 每服务调用方式清单

审计日期：2026-08-10

## 0. 阅读口径

本文件按服务逐一罗列：

- 这个服务对外暴露什么入口。
- 当前仓库中谁在调用它、通过什么协议调用、调用了哪些方法。
- 这个服务自身又调用了哪些外部服务或基础设施。
- 哪些接口虽然实现或生成了代码，但没有发现业务调用方。

“没有发现调用方”指在当前仓库源码、前端入口、Agent、服务间适配器和 Compose 配置中没有发现业务调用；不等于运行环境外部一定没有调用。

潜在 bug 和运行风险细项见 [tripsphere-service-potential-bug-audit.md](./tripsphere-service-potential-bug-audit.md)。
后续业务接入行动清单见 [tripsphere-service-business-integration-action-plan.md](./tripsphere-service-business-integration-action-plan.md)。

## 1. 全局调用方式分类

当前仓库里主要有五类调用方式：

| 类型 | 说明 | 典型调用方 |
| --- | --- | --- |
| Next 静态 gRPC | `trip-next-frontend` 直接通过环境变量地址创建 gRPC 客户端，不走 Nacos | 用户、景点、酒店、商品、行程、订单 |
| Java 服务间 gRPC | Java 服务通过 `@GrpcClient("service-name")` 走服务发现 | 订单服务调用商品、库存 |
| Python 手动 Nacos + gRPC | Python 服务从 Nacos Naming 找实例，再拼 `ip:gRPC_port` 调 gRPC | 行程规划器、订单助手 |
| Copilot/AG-UI HTTP | 前端 Copilot Runtime 通过 `HttpAgent` 调 Python Agent HTTP 服务 | Chat、行程规划器、订单助手配置项 |
| A2A + Nacos AI | AgentCard 发布到 Nacos AI，另一个 Agent 发现后远程调用 | Chat 调订单助手；评论总结可发布但未接入主链路 |

前端 gRPC 地址定义在 `trip-next-frontend/lib/env.ts`，客户端工厂在 `trip-next-frontend/lib/grpc/client.ts`。前端会从请求头构造 gRPC metadata，传递 `authorization`、`x-user-id`、`x-user-roles`。

## 2. `trip-next-frontend`

虽然它不是后端服务，但它是当前用户流量入口。

### 对外入口

- Next.js 页面、Server Actions、API Route。
- CopilotKit API route：`app/api/v1/copilotkit/route.ts`。

### 它调用的服务

| 目标服务 | 调用方式 | 当前调用的方法 |
| --- | --- | --- |
| `trip-user-service` | 静态 gRPC | `SignUp`、`SignIn` |
| `trip-attraction-service` | 静态 gRPC | `ListAttractionsByCity`、`GetAttractionById`、`GetAttractionsNearby` |
| `trip-hotel-service` | 静态 gRPC | `ListHotels`、`GetHotelById`、`GetRoomTypesByHotelId` |
| `trip-product-service` | 静态 gRPC | `ListSpusByResource` |
| `trip-itinerary-planner` | HTTP | `POST /api/v1/itineraries/plannings` |
| `trip-itinerary-service` | 静态 gRPC | `ListUserItineraries`、`GetItinerary`、`ReplaceItinerary`、`DeleteItinerary` |
| `trip-order-service` | 静态 gRPC | `ListUserOrders`、`CancelOrder` |
| `trip-chat-service` | Copilot `HttpAgent` | `agentId="default"` |
| `trip-itinerary-planner` | Copilot `HttpAgent` | `agentId="itinerary_planner"` |
| `trip-order-assistant` | Copilot `HttpAgent` 配置存在 | 没有发现可见页面直接使用 |

### 声明过但已清理的入口

- 前端已移除 `POI_SERVICE_ADDR` 和 `getPoiService()`；POI 只保留为共享类型和历史数据概念。
- `INVENTORY_SERVICE_ADDR` 存在，但没有 `getInventoryService()`，库存只通过订单服务间接使用。
- Review、File、Note、Review Summary 没有前端客户端。
- 酒店详情页评论 Tab 是占位内容。
- `/notes` 页面是占位内容。
- 没有发现前端常规下单和支付确认流程。

## 3. `trip-user-service`

### 对外入口

gRPC `UserService`：

- `SignUp`
- `SignIn`
- `GetCurrentUser`

实现入口：`trip-user-service/src/main/java/org/tripsphere/user/infrastructure/adapter/inbound/grpc/UserGrpcService.java`。

### 当前被调用方式

| 调用方 | 协议 | 方法 | 业务入口 |
| --- | --- | --- | --- |
| `trip-next-frontend` | 静态 gRPC | `SignUp` | 注册 action |
| `trip-next-frontend` | 静态 gRPC | `SignIn` | 登录 action |

### 未发现业务调用的方法

- `GetCurrentUser` 没有发现前端或其他服务调用。
- 前端鉴权主要由 cookie/JWT 和 `proxy.ts` 处理，不会每次请求都回查 UserService。

### 它调用或依赖

- PostgreSQL 用户数据。
- JWT 签发/校验相关配置。
- 没有发现调用其他业务服务。

## 4. `trip-attraction-service`

### 对外入口

gRPC `AttractionService`：

- `GetAttractionById`
- `BatchGetAttractions`
- `GetAttractionsNearby`
- `ListAttractionsByCity`

另有 `MetadataService.GetVersion`。

实现入口：`trip-attraction-service/src/main/java/org/tripsphere/attraction/infrastructure/adapter/inbound/grpc/AttractionGrpcService.java`。

### 当前被调用方式

| 调用方 | 协议 | 方法 | 用途 |
| --- | --- | --- | --- |
| `trip-next-frontend` | 静态 gRPC | `ListAttractionsByCity` | 景点列表页、城市筛选 |
| `trip-next-frontend` | 静态 gRPC | `GetAttractionById` | 景点详情页 |
| `trip-next-frontend` | 静态 gRPC | `GetAttractionsNearby` | 附近景点数据 |
| `trip-itinerary-planner` | Nacos Naming + gRPC | `GetAttractionsNearby` | 规划行程时搜索目的地附近景点 |

### 未发现业务调用的方法

- `BatchGetAttractions` 没有发现当前业务调用方。
- `MetadataService.GetVersion` 只适合健康检查或版本检查，未发现业务调用。

### 它调用或依赖

- MongoDB 景点数据。
- Nacos 注册由 Spring Cloud Alibaba 负责，但前端不会通过 Nacos 调它。

### 风险点

- Python 行程规划器直接读取 Nacos 实例 metadata 中的 `gRPC_port`；该服务配置文件里没有统一显式声明这个字段，部署时要验证是否由框架自动补齐。

## 5. `trip-hotel-service`

### 对外入口

gRPC `HotelService`：

- `GetHotelById`
- `BatchGetHotels`
- `GetHotelsNearby`
- `ListHotels`
- `GetRoomTypesByHotelId`

另有 `MetadataService.GetVersion`。

实现入口：`trip-hotel-service/src/main/java/org/tripsphere/hotel/infrastructure/adapter/inbound/grpc/HotelGrpcService.java`。

### 当前被调用方式

| 调用方 | 协议 | 方法 | 用途 |
| --- | --- | --- | --- |
| `trip-next-frontend` | 静态 gRPC | `ListHotels` | 酒店列表页 |
| `trip-next-frontend` | 静态 gRPC | `GetHotelById` | 酒店详情页 |
| `trip-next-frontend` | 静态 gRPC | `GetRoomTypesByHotelId` | 酒店详情页房型列表 |
| `trip-itinerary-planner` | Nacos Naming + gRPC | `GetHotelsNearby` | 规划行程时搜索附近酒店 |

### 未发现业务调用的方法

- `BatchGetHotels` 没有发现当前业务调用方。
- 酒店评论没有接入 ReviewService，前端仍是占位。

### 它调用或依赖

- MongoDB 酒店和房型数据。
- 不调用 ProductService；房型对应的可售商品由前端再调用 ProductService 查询。

### 相关但不是直接调用

`trip-chat-service` 的酒店查看工具只读取前端 AG-UI 上下文里的酒店和房型数据，不直接调用 HotelService。

## 6. `trip-product-service`

### 对外入口

gRPC `ProductService`：

- `GetSpuById`
- `BatchGetSpus`
- `ListSpusByResource`
- `CreateSpu`
- `BatchCreateSpus`
- `UpdateSpu`
- `GetSkuById`
- `BatchGetSkus`

另有 `MetadataService.GetVersion`。

实现入口：`trip-product-service/src/main/java/org/tripsphere/product/infrastructure/adapter/inbound/grpc/ProductGrpcService.java`。

### 当前被调用方式

| 调用方 | 协议 | 方法 | 用途 |
| --- | --- | --- | --- |
| `trip-next-frontend` | 静态 gRPC | `ListSpusByResource` | 酒店房型展示价格和 SKU/SPU 信息 |
| `trip-order-service` | Java `@GrpcClient` | `BatchGetSkus` | 创建订单时校验 SKU |
| `trip-order-service` | Java `@GrpcClient` | `BatchGetSpus` | 创建订单时校验 SPU 和资源类型 |
| `trip-order-assistant` | Nacos Naming + gRPC | `GetSpuById` | Agent 查询商品详情 |
| `trip-order-assistant` | Nacos Naming + gRPC | `GetSkuById` | Agent 查询 SKU，加入订单草稿 |

### 未发现业务调用的方法

- `CreateSpu`
- `BatchCreateSpus`
- `UpdateSpu`

这些更像运营/初始化接口，当前没有前端后台或其他服务调用。

### 它调用或依赖

- 商品数据库。
- 没有发现调用其他业务服务。

### 接入缺口

- 前端展示了酒店房型商品，但没有从商品展示进入创建订单的常规页面流程。

## 7. `trip-inventory-service`

### 对外入口

gRPC `InventoryService`：

- `SetDailyInventory`
- `BatchSetDailyInventory`
- `GetDailyInventory`
- `QueryInventoryCalendar`
- `CheckAvailability`
- `LockInventory`
- `ConfirmLock`
- `ReleaseLock`

另有 `MetadataService.GetVersion`。

实现入口：`trip-inventory-service/src/main/java/org/tripsphere/inventory/infrastructure/adapter/inbound/grpc/InventoryGrpcService.java`。

### 当前被调用方式

| 调用方 | 协议 | 方法 | 用途 |
| --- | --- | --- | --- |
| `trip-order-service` | Java `@GrpcClient` | `QueryInventoryCalendar` | 创建订单时查询日期价格 |
| `trip-order-service` | Java `@GrpcClient` | `LockInventory` | 创建订单时锁库存 |
| `trip-order-service` | Java `@GrpcClient` | `ConfirmLock` | 支付确认后确认库存 |
| `trip-order-service` | Java `@GrpcClient` | `ReleaseLock` | 取消订单或订单过期后释放库存 |

### 内部调度

- `LockExpiryScheduler` 每 30 秒扫描过期库存锁，直接调用应用层 `ReleaseLockUseCase`，不是通过 gRPC 调自己。

### 未发现业务调用的方法

- `SetDailyInventory`
- `BatchSetDailyInventory`
- `GetDailyInventory`
- `CheckAvailability`

这些像运营配置和查询接口，当前没有前端或后台入口。

### 它调用或依赖

- 库存数据库。
- Redis：维护库存锁过期索引。
- 没有发现调用其他业务服务。

### 接入缺口

- 前端声明了 `INVENTORY_SERVICE_ADDR`，但没有 Inventory 客户端和页面调用。
- 库存价格只在订单创建链路中被使用，酒店详情页展示仍主要依赖 Product 的 base price 或商品数据。

## 8. `trip-order-service`

### 对外入口

gRPC `OrderService`：

- `CreateOrder`
- `GetOrder`
- `GetOrderByNo`
- `ListUserOrders`
- `CancelOrder`
- `ConfirmPayment`

另有 `MetadataService.GetVersion`。

实现入口：`trip-order-service/src/main/java/org/tripsphere/order/infrastructure/adapter/inbound/grpc/OrderGrpcService.java`。

### 当前被调用方式

| 调用方 | 协议 | 方法 | 用途 |
| --- | --- | --- | --- |
| `trip-next-frontend` | 静态 gRPC | `ListUserOrders` | 我的订单列表 |
| `trip-next-frontend` | 静态 gRPC | `CancelOrder` | 订单页取消订单 |
| `trip-order-assistant` | Nacos Naming + gRPC | `CreateOrder` | 提交 Agent 订单草稿 |
| `trip-order-assistant` | Nacos Naming + gRPC | `GetOrder` | Agent 按订单 ID 查询 |
| `trip-order-assistant` | Nacos Naming + gRPC | `GetOrderByNo` | Agent 按订单号查询 |
| `trip-order-assistant` | Nacos Naming + gRPC | `CancelOrder` | Agent 取消订单 |

### 内部调度

- `OrderExpiryScheduler` 每 30 秒扫描 Redis 中的过期订单，直接调用应用层 `CancelOrderUseCase`，不是通过 gRPC 调自己。

### 未发现业务调用的方法

- `ConfirmPayment` 已实现，但没有发现前端、Agent 或支付回调调用。
- `CreateOrder` 没有常规前端页面调用，目前主要由订单助手提交草稿时调用。

### 它调用或依赖

| 目标 | 调用方式 | 方法 | 触发场景 |
| --- | --- | --- | --- |
| `trip-product-service` | Java `@GrpcClient` | `BatchGetSkus`、`BatchGetSpus` | 创建订单校验商品 |
| `trip-inventory-service` | Java `@GrpcClient` | `QueryInventoryCalendar` | 计算日期价格 |
| `trip-inventory-service` | Java `@GrpcClient` | `LockInventory` | 创建订单锁库存 |
| `trip-inventory-service` | Java `@GrpcClient` | `ConfirmLock` | 支付确认 |
| `trip-inventory-service` | Java `@GrpcClient` | `ReleaseLock` | 取消或过期释放 |

还依赖订单数据库和 Redis 订单过期索引。

### 接入缺口和风险

- 前端没有下单、确认订单、支付确认业务闭环。
- gRPC 入站接口主要信任请求里的 `user_id` 或 `order_id`，当前没有完整的用户所有权校验。

## 9. `trip-itinerary-service`

### 对外入口

gRPC `ItineraryService`：

- `CreateItinerary`
- `GetItinerary`
- `ListUserItineraries`
- `DeleteItinerary`
- `UpdateItinerary`
- `ReplaceItinerary`
- `AddDayPlan`
- `DeleteDayPlan`
- `AddActivity`
- `UpdateActivity`
- `DeleteActivity`

另有 `MetadataService.GetVersion`。

实现入口：`trip-itinerary-service/src/main/java/org/tripsphere/itinerary/infrastructure/adapter/inbound/grpc/ItineraryGrpcService.java`。

### 当前被调用方式

| 调用方 | 协议 | 方法 | 用途 |
| --- | --- | --- | --- |
| `trip-next-frontend` | 静态 gRPC | `ListUserItineraries` | 我的行程列表 |
| `trip-next-frontend` | 静态 gRPC | `GetItinerary` | 打开已保存行程 |
| `trip-next-frontend` | 静态 gRPC | `ReplaceItinerary` | 规划页编辑后整份替换保存 |
| `trip-next-frontend` | 静态 gRPC | `DeleteItinerary` | 删除行程 |
| `trip-itinerary-planner` | Nacos Naming + gRPC | `CreateItinerary` | HTTP 规划完成后持久化新行程 |

### 封装存在但当前未进入业务入口的方法

`trip-itinerary-planner` 的 gRPC client wrapper 封装了 `get_itinerary`、`list_user_itineraries`、`replace_itinerary`、`delete_itinerary`，但当前规划 HTTP 入口只实际调用 `create_itinerary`。

### 未发现业务调用的方法

- `UpdateItinerary`
- `AddDayPlan`
- `DeleteDayPlan`
- `AddActivity`
- `UpdateActivity`
- `DeleteActivity`

前端现在采取整份 `ReplaceItinerary` 保存，而不是调用细粒度 RPC。

### 它调用或依赖

- 行程数据库。
- 认证上下文来自 gRPC metadata 中的 `x-user-id`，服务端会基于该用户做读取和所有权判断。
- 没有发现调用其他业务服务。

## 10. `trip-poi-service`

### 对外入口

gRPC `PoiService`：

- `GetPoiById`
- `BatchGetPois`
- `GetPoisNearby`
- `GetPoisInBounds`
- `CreatePoi`
- `BatchCreatePois`

另有 `MetadataService.GetVersion`。

实现入口：`trip-poi-service/src/main/java/org/tripsphere/poi/infrastructure/adapter/inbound/grpc/PoiGrpcService.java`。

### 当前被调用方式

当前没有发现业务调用方。

### 相关但不是调用

- `trip-next-frontend` 不再保留 POI 客户端入口。
- `Itinerary` proto 使用了 `tripsphere.poi.v1.Poi` 类型作为目的地结构，但这不是对 POI 服务的运行时调用。
- 行程规划器当前用目的地名称和地理坐标工作，没有发现调用 POI 服务。

### 它调用或依赖

- MongoDB POI 数据。
- 没有发现调用其他业务服务。

### 接入缺口

- 推荐部署 Compose 未纳入该服务。
- Attraction 和 POI 的职责边界还没有通过调用链体现出来。

## 11. `trip-file-service`

### 对外入口

gRPC `FileService`：

- `GetUploadSignedUrl`
- `GetTempUploadSignedUrl`
- `GetDownloadSignedUrls`
- `CopyFiles`
- `DeleteFiles`
- `CopyToPermanent`

实现入口：`trip-file-service/services/file.go`。

### 当前被调用方式

当前没有发现前端或其他业务服务调用。

已有调用只出现在手工测试工具中：

- `trip-file-service/cmd/test_client/main.go`
- `trip-file-service/scripts/test-grpc.sh`
- `trip-file-service/scripts/test-grpc.ps1`

### 它调用或依赖

- MinIO：生成上传/下载签名 URL，复制、删除对象。
- Nacos：服务启动后注册实例。
- gRPC server 固定监听 `:50051`。

### 接入缺口

- 没有用户头像、酒店图片、评论图片、笔记图片等业务链路接入。
- 推荐部署 Compose 没有纳入 FileService 和完整 MinIO 依赖。

## 12. `trip-review-service`

### 对外入口

gRPC `ReviewService`：

- `CreateReview`
- `UpdateReview`
- `DeleteReview`
- `ListReviewsByEntity`

实现入口：`trip-review-service/internal/service/review_service.go`。

### 当前被调用方式

当前没有发现前端或其他业务服务调用。

已有调用主要是测试：

- 单元测试：`trip-review-service/internal/service/review_service_test.go`
- MongoDB 集成测试：`trip-review-service/internal/repository/review_repo_integration_test.go`

### 相关但不是调用

- `trip-next-frontend` 生成了 Review proto 代码，但没有 Review gRPC 客户端工厂。
- 酒店详情页评论 Tab 没有调用 ReviewService。
- `trip-review-summary` 没有从 ReviewService 拉取评论，当前不是 ReviewService 的下游。

### 它调用或依赖

- MongoDB 评论数据。
- Nacos 可选注册。
- 没有发现调用其他业务服务。

### 接入缺口和风险

- 没有前端评论创建、编辑、删除、列表展示。
- 创建/更新/删除的用户所有权校验需要补强。

## 13. `trip-note-service`

### 对外入口

当前只有 gRPC `MetadataService.GetVersion`。

实现入口：`trip-note-service/src/main/java/org/tripsphere/note/infrastructure/adapter/inbound/grpc/MetadataGrpcService.java`。

### 当前被调用方式

没有发现业务调用方。

### 相关但不是调用

- 前端侧边栏和首页有 `/notes` 入口。
- `/notes` 页面是占位页面，没有调用 NoteService。

### 它调用或依赖

- 没有发现 Note 领域数据库访问或其他业务服务调用。

### 接入缺口

- 没有 NoteService proto。
- 没有笔记创建、查询、更新、删除等领域实现。

## 14. `trip-chat-service`

### 对外入口

- FastAPI 应用。
- AG-UI/ADK endpoint，由 `add_adk_fastapi_endpoint` 挂载。
- 健康检查：`/api/v1/health`。
- Nacos Naming 服务注册。

### 当前被调用方式

| 调用方 | 协议 | 方式 | 用途 |
| --- | --- | --- | --- |
| `trip-next-frontend` | Copilot `HttpAgent` | `agentId="default"` | 主站默认聊天助手 |

### 它调用或依赖

| 目标 | 调用方式 | 用途 |
| --- | --- | --- |
| Nacos AI | `get_agent_card("order_assistant")` | 发现远程订单助手 Agent |
| `trip-order-assistant` | A2A remote agent | 把订单相关请求委派给订单助手 |
| MongoDB | 会话存储 | 保存 ADK session |
| Mem0 / 向量记忆配置 | Memory service | 长期记忆 |
| OpenAI/Higress | LLM | 默认聊天推理 |

### 相关但不是业务服务调用

- 酒店查看工具只读取 AG-UI context 中的酒店和房型数据，不直接调用 HotelService。

### 接入缺口和风险

- `review_summary` 通过 MCP 直连，不再参与远程 A2A Agent 发现；远程 Agent 列表默认只有 `order_assistant`。
- 健康检查逻辑目前是固定成功值。
- 缺少有效业务测试。

## 15. `trip-itinerary-planner`

### 对外入口

- FastAPI 应用。
- HTTP 规划接口：`POST /api/v1/itineraries/plannings`。
- AG-UI/ADK endpoint，前端以 `agentId="itinerary_planner"` 使用。
- Nacos Naming 服务注册。

### 当前被调用方式

| 调用方 | 协议 | 方式 | 用途 |
| --- | --- | --- | --- |
| `trip-next-frontend` | HTTP | `POST /api/v1/itineraries/plannings` | 表单提交后生成并保存行程 |
| `trip-next-frontend` | Copilot `HttpAgent` | `agentId="itinerary_planner"` | 规划页对话式编辑和再生成 |

### 它调用或依赖

| 目标 | 调用方式 | 方法 | 用途 |
| --- | --- | --- | --- |
| Nacos Naming | SDK | 查找服务实例 | 发现景点、酒店、行程服务 |
| `trip-attraction-service` | Nacos + gRPC | `GetAttractionsNearby` | 搜索景点候选 |
| `trip-hotel-service` | Nacos + gRPC | `GetHotelsNearby` | 搜索酒店候选 |
| `trip-itinerary-service` | Nacos + gRPC | `CreateItinerary` | HTTP 规划完成后持久化 |
| OpenAI/Higress | HTTP SDK | LLM 调用 | 生成行程内容 |

### 封装存在但当前不等于业务调用

- 行程 gRPC client 封装了 `GetItinerary`、`ListUserItineraries`、`ReplaceItinerary`、`DeleteItinerary`，但当前规划 HTTP 入口只调用 `CreateItinerary`。
- 对话式编辑主要改前端/Agent 状态；持久化由前端后续调用 `ReplaceItinerary` 完成。

### 没有调用的服务

- 没有调用 POI 服务。
- 没有调用 Product、Inventory、Order。

### 风险点

- 搜索景点、酒店时直接读取 Nacos metadata 的 `gRPC_port`。
- 景点候选有固定抽样逻辑，候选数量不足时可能失败。

## 16. `trip-order-assistant`

### 对外入口

- A2A Starlette 应用。
- AgentCard 发布到 Nacos AI。
- 可被其他 Agent 通过 Nacos AI 发现。

### 当前被调用方式

| 调用方 | 协议 | 方式 | 用途 |
| --- | --- | --- | --- |
| `trip-chat-service` | A2A + Nacos AI | 远程 Agent `order_assistant` | 处理订单相关对话 |
| `trip-next-frontend` | Copilot `HttpAgent` 配置存在 | `order_assistant` agent 注册在 runtime 中 | 未发现可见页面直接使用，且 Compose 缺少 `COPILOT_ORDER_AGENT_URL` |

### 它调用或依赖

| 目标 | 调用方式 | 方法 | 用途 |
| --- | --- | --- | --- |
| Nacos Naming | SDK | 查找服务实例 | 发现 ProductService、OrderService |
| `trip-product-service` | Nacos + gRPC | `GetSpuById` | 查询 SPU |
| `trip-product-service` | Nacos + gRPC | `GetSkuById` | 查询 SKU、加入订单草稿 |
| `trip-order-service` | Nacos + gRPC | `CreateOrder` | 提交订单草稿 |
| `trip-order-service` | Nacos + gRPC | `GetOrder` | 按 ID 查订单 |
| `trip-order-service` | Nacos + gRPC | `GetOrderByNo` | 按订单号查订单 |
| `trip-order-service` | Nacos + gRPC | `CancelOrder` | 取消订单 |
| OpenAI/Higress | LLM | Agent 推理 |

### 内部使用方式

- 订单草稿保存在进程内 `ORDER_DRAFTS`。
- 草稿工具包括创建草稿、查看草稿、删除草稿、加入酒店房型 SKU、加入景点票 SKU、提交订单。

### 没有调用的服务

- 不直接调用 InventoryService；库存由 OrderService 负责。
- 不调用 UserService；用户身份来自上游转发的 header/state。

### 接入缺口和风险

- 草稿不是持久化数据，服务重启会丢失。
- 联系人信息仍是 TODO。
- 提交订单时通过请求体传 `user_id`，没有向 OrderService 转发完整 auth metadata。

## 17. `trip-review-summary`

### 对外入口

- FastAPI 应用。
- HTTP 索引接口：`POST /api/v1/indices`。
- HTTP 删除索引接口：`DELETE /api/v1/indices/{target_id}`，当前未实现。
- HTTP 评论问答接口：`POST /api/v1/review-summaries`。
- MCP Streamable HTTP 接口：`/mcp`，提供 `summarize_reviews` 工具。
- Nacos Naming 服务注册。

### 当前被调用方式

| 调用方 | 协议 | 方式 | 用途 |
| --- | --- | --- | --- |
| `trip-chat-service` | MCP Streamable HTTP | `summarize_reviews` | 回答当前页面酒店或景点的评论问题 |
| 外部或人工 | HTTP | `POST /api/v1/indices` | 触发索引构建 |

### 它调用或依赖

| 目标 | 调用方式 | 用途 |
| --- | --- | --- |
| Celery | task chain | 执行图索引流程 |
| Qdrant | vector store | 文本单元、实体向量检索 |
| Neo4j | graph store | 图查询和上下文构建 |
| OpenAI/Higress | LLM/embedding | 图抽取、摘要、向量 |
| `trip-review-service` | Nacos + gRPC | 拉取目标评论作为查询事实来源 |
| Nacos Naming | SDK | 服务注册 |
| MinIO/文件存储相关配置 | 任务链依赖配置 | 存储或读取索引中间产物 |

### 没有调用的服务

- 不再使用 A2A 或 Nacos AI 发布/发现评论总结 Agent。
- 没有接入酒店详情页或评论展示页。

### 未完整实现点

- 删除索引接口未实现。
- 图嵌入相关流程存在未实现分支。

## 18. `trip-note-creator`

### 对外入口

没有发现对外 HTTP、gRPC、A2A 或 CLI 入口。

### 当前被调用方式

没有发现业务调用方。

### 它调用或依赖

没有发现业务逻辑和外部依赖调用。

### 当前状态

只有空初始化模块和项目配置，属于脚手架。

## 19. 服务调用速查表

| 被调用服务 | 当前真实调用方 |
| --- | --- |
| `trip-user-service` | `trip-next-frontend` |
| `trip-attraction-service` | `trip-next-frontend`、`trip-itinerary-planner` |
| `trip-hotel-service` | `trip-next-frontend`、`trip-itinerary-planner` |
| `trip-product-service` | `trip-next-frontend`、`trip-order-service`、`trip-order-assistant` |
| `trip-inventory-service` | `trip-order-service` |
| `trip-order-service` | `trip-next-frontend`、`trip-order-assistant`、内部过期调度 |
| `trip-itinerary-service` | `trip-next-frontend`、`trip-itinerary-planner` |
| `trip-poi-service` | 未发现业务调用方 |
| `trip-file-service` | 未发现业务调用方，只有手工测试客户端 |
| `trip-review-service` | 未发现业务调用方，主要是测试 |
| `trip-note-service` | 未发现业务调用方 |
| `trip-chat-service` | `trip-next-frontend` |
| `trip-itinerary-planner` | `trip-next-frontend` |
| `trip-order-assistant` | `trip-chat-service`，前端有配置但没有自然业务入口 |
| `trip-review-summary` | `trip-chat-service`（MCP），以及人工/运维 HTTP 索引入口 |
| `trip-note-creator` | 未发现业务调用方 |
