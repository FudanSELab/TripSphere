package minio

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"trip-file-service/clients/nacos"

	"github.com/nacos-group/nacos-sdk-go/v2/model"
	"github.com/nacos-group/nacos-sdk-go/v2/vo"
)

var (
	MinIO *Client
	mu    sync.RWMutex
)

// GetClient returns the MinIO client
func GetClient() *Client {
	mu.RLock()
	defer mu.RUnlock()
	return MinIO
}

// updateClient updates the MinIO client with a new instance
func updateClient(instance *model.Instance) error {
	ctx := context.Background()

	// Build endpoint: "ip:port"
	endpoint := fmt.Sprintf("%s:%d", instance.Ip, instance.Port)

	client, err := NewClient(ctx, Config{
		Endpoint:        endpoint,
		AccessKeyID:     "minioadmin",
		SecretAccessKey: "minioadmin",
		UseSSL:          false,
		Timeout:         30 * time.Second,
	})
	if err != nil {
		return fmt.Errorf("failed to create minio client: %w", err)
	}

	mu.Lock()
	MinIO = client
	mu.Unlock()

	return nil
}

func Init() {
	ctx := context.Background()

	// Get MinIO service instance from Nacos
	instance, err := nacos.Nacos.SelectOneHealthyInstance(ctx, vo.SelectOneHealthInstanceParam{
		ServiceName: "minio",
	})
	if err != nil {
		panic(fmt.Errorf("failed to get minio instance from nacos: %w", err))
	}

	// Initialize client with the first instance
	if err := updateClient(instance); err != nil {
		panic(fmt.Errorf("failed to initialize minio client: %w", err))
	}

	// Subscribe to service changes
	err = nacos.Nacos.Subscribe(&vo.SubscribeParam{
		ServiceName: "minio",
		SubscribeCallback: func(instances []model.Instance, err error) {
			if err != nil {
				log.Printf("failed to subscribe to minio service changes: %v", err)
				return
			}

			for _, inst := range instances {
				if inst.Healthy {
					if err := updateClient(&inst); err != nil {
						log.Printf("failed to update minio client: %v", err)
						return
					}
					log.Printf("updated minio client to %s:%d", inst.Ip, inst.Port)
					break
				}
			}
		},
	})
	if err != nil {
		panic(fmt.Errorf("failed to subscribe to minio service changes: %w", err))
	}
}
