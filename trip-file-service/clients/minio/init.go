package minio

import (
	"context"
	"fmt"
	"time"

	"trip-file-service/config"
)

var (
	MinIO *Client
)

func Init() {
	ctx := context.Background()
	var err error

	MinIO, err = NewClient(ctx, Config{
		Endpoint:        config.MinIOEndpoint,
		AccessKeyID:     config.MinIOAccessKeyID,
		SecretAccessKey: config.MinIOSecretAccessKey,
		UseSSL:          config.MinIOUseSSL,
		Timeout:         30 * time.Second,
	})
	if err != nil {
		panic(fmt.Errorf("failed to initialize minio client: %w", err))
	}
}
