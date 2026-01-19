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

// Config Nacos client configuration
type Config struct {
	Host        string        // Nacos server address
	Port        int           // Nacos server port
	NamespaceID string        // Namespace ID
	GroupName   string        // Group name, defaults to "DEFAULT_GROUP"
	Username    string        // Username (optional)
	Password    string        // Password (optional)
	Timeout     time.Duration // Timeout duration
}

// Client Nacos client
type Client struct {
	namingClient naming_client.INamingClient
	config       Config
}

// NewClient creates a new Nacos client
func NewClient(ctx context.Context, config Config) (*Client, error) {
	if config.GroupName == "" {
		config.GroupName = "DEFAULT_GROUP"
	}
	if config.Timeout == 0 {
		config.Timeout = 5 * time.Second
	}

	// Build server configuration
	serverConfigs := []constant.ServerConfig{
		{
			IpAddr:      config.Host,
			Port:        uint64(config.Port),
			Scheme:      "http",
			ContextPath: "/nacos",
		},
	}

	// Client configuration
	clientConfig := constant.ClientConfig{
		NamespaceId:         config.NamespaceID,
		TimeoutMs:           uint64(config.Timeout.Milliseconds()),
		NotLoadCacheAtStart: true,
		LogDir:              "/tmp/nacos/log",
		CacheDir:            "/tmp/nacos/cache",
		LogLevel:            "info",
	}

	// Set authentication if username and password are provided
	if config.Username != "" {
		clientConfig.Username = config.Username
		clientConfig.Password = config.Password
	}

	// Create naming client
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

// RegisterInstance registers a service instance
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

// DeregisterInstance deregisters a service instance
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

// GetService gets service instance list
func (c *Client) GetService(ctx context.Context, param vo.GetServiceParam) (model.Service, error) {
	param.GroupName = c.config.GroupName
	service, err := c.namingClient.GetService(param)
	if err != nil {
		return model.Service{}, fmt.Errorf("failed to get service: %w", err)
	}
	return service, nil
}

// SelectInstances selects healthy service instances
func (c *Client) SelectInstances(ctx context.Context, param vo.SelectInstancesParam) ([]model.Instance, error) {
	param.GroupName = c.config.GroupName
	instances, err := c.namingClient.SelectInstances(param)
	if err != nil {
		return nil, fmt.Errorf("failed to select instances: %w", err)
	}
	return instances, nil
}

// SelectOneHealthyInstance selects one healthy service instance
func (c *Client) SelectOneHealthyInstance(ctx context.Context, param vo.SelectOneHealthInstanceParam) (*model.Instance, error) {
	param.GroupName = c.config.GroupName
	instance, err := c.namingClient.SelectOneHealthyInstance(param)
	if err != nil {
		return nil, fmt.Errorf("failed to select one healthy instance: %w", err)
	}
	return instance, nil
}

// Subscribe subscribes to service changes
func (c *Client) Subscribe(param *vo.SubscribeParam) error {
	param.GroupName = c.config.GroupName
	return c.namingClient.Subscribe(param)
}

// Unsubscribe unsubscribes from service changes
func (c *Client) Unsubscribe(param *vo.SubscribeParam) error {
	param.GroupName = c.config.GroupName
	return c.namingClient.Unsubscribe(param)
}

// GetAllServicesInfo gets all service information
func (c *Client) GetAllServicesInfo(ctx context.Context, param vo.GetAllServiceInfoParam) (model.ServiceList, error) {
	param.GroupName = c.config.GroupName
	serviceList, err := c.namingClient.GetAllServicesInfo(param)
	if err != nil {
		return model.ServiceList{}, fmt.Errorf("failed to get all services info: %w", err)
	}
	return serviceList, nil
}
