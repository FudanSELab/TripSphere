package minio

import (
	"context"
	"fmt"
	"time"

	"trip-file-service/clients/nacos"

	"github.com/nacos-group/nacos-sdk-go/v2/vo"
)

var (
	MinIO *Client
)

func Init() {
	ctx := context.Background()

	// Get MinIO service instance from Nacos
	instance, err := nacos.Nacos.SelectOneHealthyInstance(ctx, vo.SelectOneHealthInstanceParam{
		ServiceName: "minio",
	})
	if err != nil {
		panic(fmt.Errorf("failed to get minio instance from nacos: %w", err))
	}

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
		panic(err)
	}
	MinIO = client
}
