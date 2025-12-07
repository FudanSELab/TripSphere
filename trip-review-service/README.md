# trip-review-service
## architecture
```
your-service/
├── api/                          # 协议定义层
│   ├── protobuf/                 # Protobuf文件
│   │   ├── v1/                   # API版本
│   │   │   ├── your_service.proto
│   │   │   ├── messages.proto
│   │   │   └── enums.proto
│   │   └── v2/                   # 未来版本
│   └── grpc/                     # 生成的Go代码
│       └── v1/
│           ├── your_service.pb.go
│           └── your_service_grpc.pb.go
├── cmd/                          # 应用程序入口
│   └── server/
│       └── main.go               # 主函数入口
├── internal/                     # 私有代码（外部项目不可导入）
│   ├── config/                   # 配置相关
│   │   ├── config.go
│   │   ├── server.go
│   │   └── database.go
│   ├── handler/                  # gRPC处理器
│   │   ├── your_service.go
│   │   └── middleware/           # gRPC中间件
│   │       ├── auth.go
│   │       ├── logging.go
│   │       └── recovery.go
│   ├── service/                  # 业务逻辑层
│   │   ├── user_service.go
│   │   └── order_service.go
│   ├── repository/               # 数据访问层
│   │   ├── user_repository.go
│   │   ├── order_repository.go
│   │   └── models/               # 数据模型
│   │       ├── user.go
│   │       └── order.go
│   ├── domain/                   # 领域模型
│   │   ├── user.go
│   │   └── value_objects.go
│   └── pkg/                      # 内部公共包
│       ├── logger/
│       ├── validator/
│       └── utils/
├── pkg/                          # 可导出的公共包
│   ├── grpcclient/               # gRPC客户端封装
│   ├── health/                   # 健康检查
│   └── errors/                   # 错误定义
├── deployments/                  # 部署配置
│   ├── docker/
│   │   └── Dockerfile
│   ├── k8s/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   └── docker-compose.yaml
├── scripts/                      # 构建和辅助脚本
│   ├── generate.sh               # 生成proto代码
│   ├── build.sh
│   └── migration/
├── configs/                      # 配置文件
│   ├── config.yaml
│   ├── config.dev.yaml
│   └── config.prod.yaml
├── migrations/                   # 数据库迁移文件
│   ├── 001_create_users.sql
│   └── 002_create_orders.sql
├── tests/                        # 测试文件
│   ├── integration/              # 集成测试
│   │   └── handler_test.go
│   ├── unit/                     # 单元测试
│   │   └── service_test.go
│   └── mocks/                    # Mock对象
│       └── repository_mock.go
├── go.mod
├── go.sum
├── Makefile                      # 构建命令
├── .env.example                  # 环境变量示例
├── .gitignore
└── README.md
```