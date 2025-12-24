package nacos

import (
	"context"
	"fmt"
	"time"

	"github.com/nacos-group/nacos-sdk-go/v2/clients"
	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
	"github.com/nacos-group/nacos-sdk-go/v2/common/constant"
	"github.com/nacos-group/nacos-sdk-go/v2/model"
	"github.com/nacos-group/nacos-sdk-go/v2/vo"
)

// Config Nacos 客户端配置
type Config struct {
	ServerHosts []string      // Nacos 服务器地址列表，格式: ["127.0.0.1:8848"]
	NamespaceID string        // 命名空间ID
	GroupName   string        // 分组名称，默认为 "DEFAULT_GROUP"
	Username    string        // 用户名（可选）
	Password    string        // 密码（可选）
	Timeout     time.Duration // 超时时间
}

// Client Nacos 客户端
type Client struct {
	namingClient naming_client.INamingClient
	config       Config
}

// NewClient 创建新的 Nacos 客户端
func NewClient(ctx context.Context, config Config) (*Client, error) {
	if config.GroupName == "" {
		config.GroupName = "DEFAULT_GROUP"
	}
	if config.Timeout == 0 {
		config.Timeout = 5 * time.Second
	}

	// 构建服务器配置
	serverConfigs := make([]constant.ServerConfig, 0, len(config.ServerHosts))
	for _, host := range config.ServerHosts {
		serverConfigs = append(serverConfigs, constant.ServerConfig{
			IpAddr:      host,
			Port:        8848,
			Scheme:      "http",
			ContextPath: "/nacos",
		})
	}

	// 客户端配置
	clientConfig := constant.ClientConfig{
		NamespaceId:         config.NamespaceID,
		TimeoutMs:           uint64(config.Timeout.Milliseconds()),
		NotLoadCacheAtStart: true,
		LogDir:              "/tmp/nacos/log",
		CacheDir:            "/tmp/nacos/cache",
		LogLevel:            "info",
	}

	// 如果有用户名和密码，设置认证
	if config.Username != "" {
		clientConfig.Username = config.Username
		clientConfig.Password = config.Password
	}

	// 创建命名客户端
	namingClient, err := clients.NewNamingClient(
		vo.NacosClientParam{
			ClientConfig:  &clientConfig,
			ServerConfigs: serverConfigs,
		},
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create nacos naming client: %w", err)
	}

	return &Client{
		namingClient: namingClient,
		config:       config,
	}, nil
}

// RegisterInstance 注册服务实例
func (c *Client) RegisterInstance(ctx context.Context, param vo.RegisterInstanceParam) error {
	param.GroupName = c.config.GroupName
	success, err := c.namingClient.RegisterInstance(param)
	if err != nil {
		return fmt.Errorf("failed to register instance: %w", err)
	}
	if !success {
		return fmt.Errorf("register instance failed: service may already exist")
	}
	return nil
}

// DeregisterInstance 注销服务实例
func (c *Client) DeregisterInstance(ctx context.Context, param vo.DeregisterInstanceParam) error {
	param.GroupName = c.config.GroupName
	success, err := c.namingClient.DeregisterInstance(param)
	if err != nil {
		return fmt.Errorf("failed to deregister instance: %w", err)
	}
	if !success {
		return fmt.Errorf("deregister instance failed")
	}
	return nil
}

// GetService 获取服务实例列表
func (c *Client) GetService(ctx context.Context, param vo.GetServiceParam) (model.Service, error) {
	param.GroupName = c.config.GroupName
	service, err := c.namingClient.GetService(param)
	if err != nil {
		return model.Service{}, fmt.Errorf("failed to get service: %w", err)
	}
	return service, nil
}

// SelectInstances 选择健康的服务实例
func (c *Client) SelectInstances(ctx context.Context, param vo.SelectInstancesParam) ([]model.Instance, error) {
	param.GroupName = c.config.GroupName
	instances, err := c.namingClient.SelectInstances(param)
	if err != nil {
		return nil, fmt.Errorf("failed to select instances: %w", err)
	}
	return instances, nil
}

// SelectOneHealthyInstance 选择一个健康的服务实例
func (c *Client) SelectOneHealthyInstance(ctx context.Context, param vo.SelectOneHealthInstanceParam) (*model.Instance, error) {
	param.GroupName = c.config.GroupName
	instance, err := c.namingClient.SelectOneHealthyInstance(param)
	if err != nil {
		return nil, fmt.Errorf("failed to select one healthy instance: %w", err)
	}
	return instance, nil
}

// Subscribe 订阅服务变化
func (c *Client) Subscribe(param *vo.SubscribeParam) error {
	param.GroupName = c.config.GroupName
	return c.namingClient.Subscribe(param)
}

// Unsubscribe 取消订阅服务变化
func (c *Client) Unsubscribe(param *vo.SubscribeParam) error {
	param.GroupName = c.config.GroupName
	return c.namingClient.Unsubscribe(param)
}

// GetAllServicesInfo 获取所有服务信息
func (c *Client) GetAllServicesInfo(ctx context.Context, param vo.GetAllServiceInfoParam) (model.ServiceList, error) {
	param.GroupName = c.config.GroupName
	serviceList, err := c.namingClient.GetAllServicesInfo(param)
	if err != nil {
		return model.ServiceList{}, fmt.Errorf("failed to get all services info: %w", err)
	}
	return serviceList, nil
}

var Nacos *Client

func Init() {
	client, err := NewClient(context.Background(), Config{
		ServerHosts: []string{"localhost:8848"},
		NamespaceID: "public",
		GroupName:   "DEFAULT_GROUP",
		Username:    "nacos",
		Password:    "nacos",
	})
	if err != nil {
		panic(err)
	}
	Nacos = client
}
