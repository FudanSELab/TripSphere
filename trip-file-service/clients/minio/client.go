package minio

import (
	"context"
	"fmt"
	"time"

	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
)

// Config MinIO client configuration
type Config struct {
	Endpoint        string        // MinIO server address, format: "localhost:9000"
	AccessKeyID     string        // Access key ID
	SecretAccessKey string        // Secret access key
	UseSSL          bool          // Whether to use SSL
	Region          string        // Region (optional)
	Timeout         time.Duration // Timeout duration
}

// Client MinIO client
type Client struct {
	client *minio.Client
	config Config
}

// NewClient creates a new MinIO client
func NewClient(ctx context.Context, config Config) (*Client, error) {
	if config.Timeout == 0 {
		config.Timeout = 30 * time.Second
	}

	// Create MinIO client
	client, err := minio.New(config.Endpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(config.AccessKeyID, config.SecretAccessKey, ""),
		Secure: config.UseSSL,
		Region: config.Region,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create minio client: %w", err)
	}

	// Test connection
	ctx, cancel := context.WithTimeout(ctx, config.Timeout)
	defer cancel()

	_, err = client.ListBuckets(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to minio: %w", err)
	}

	return &Client{
		client: client,
		config: config,
	}, nil
}

// EnsureBucket ensures the bucket exists, creates it if it doesn't
func (c *Client) EnsureBucket(ctx context.Context, bucketName string, location string) error {
	ctx, cancel := context.WithTimeout(ctx, c.config.Timeout)
	defer cancel()

	exists, err := c.client.BucketExists(ctx, bucketName)
	if err != nil {
		return fmt.Errorf("failed to check bucket existence: %w", err)
	}

	if !exists {
		err = c.client.MakeBucket(ctx, bucketName, minio.MakeBucketOptions{Region: location})
		if err != nil {
			return fmt.Errorf("failed to create bucket: %w", err)
		}
	}

	return nil
}

// GetObject retrieves an object
func (c *Client) GetObject(ctx context.Context, bucketName, objectName string, opts minio.GetObjectOptions) (*minio.Object, error) {
	ctx, cancel := context.WithTimeout(ctx, c.config.Timeout)
	defer cancel()

	object, err := c.client.GetObject(ctx, bucketName, objectName, opts)
	if err != nil {
		return nil, fmt.Errorf("failed to get object: %w", err)
	}
	return object, nil
}

// StatObject gets object information
func (c *Client) StatObject(ctx context.Context, bucketName, objectName string, opts minio.StatObjectOptions) (minio.ObjectInfo, error) {
	ctx, cancel := context.WithTimeout(ctx, c.config.Timeout)
	defer cancel()

	info, err := c.client.StatObject(ctx, bucketName, objectName, opts)
	if err != nil {
		return minio.ObjectInfo{}, fmt.Errorf("failed to stat object: %w", err)
	}
	return info, nil
}

// RemoveObject deletes an object
func (c *Client) RemoveObject(ctx context.Context, bucketName, objectName string, opts minio.RemoveObjectOptions) error {
	ctx, cancel := context.WithTimeout(ctx, c.config.Timeout)
	defer cancel()

	err := c.client.RemoveObject(ctx, bucketName, objectName, opts)
	if err != nil {
		return fmt.Errorf("failed to remove object: %w", err)
	}
	return nil
}

// RemoveObjects deletes multiple objects
func (c *Client) RemoveObjects(ctx context.Context, bucketName string, objectsCh <-chan minio.ObjectInfo, opts minio.RemoveObjectsOptions) <-chan minio.RemoveObjectError {
	ctx, cancel := context.WithTimeout(ctx, c.config.Timeout)
	defer cancel()

	errorCh := c.client.RemoveObjects(ctx, bucketName, objectsCh, opts)
	return errorCh
}

// CopyObject copies an object
func (c *Client) CopyObject(ctx context.Context, dst minio.CopyDestOptions, src minio.CopySrcOptions) (minio.UploadInfo, error) {
	ctx, cancel := context.WithTimeout(ctx, c.config.Timeout)
	defer cancel()

	info, err := c.client.CopyObject(ctx, dst, src)
	if err != nil {
		return minio.UploadInfo{}, fmt.Errorf("failed to copy object: %w", err)
	}
	return info, nil
}

// PresignedGetObject generates a presigned URL for downloading
func (c *Client) PresignedGetObject(ctx context.Context, bucketName, objectName string, expiry time.Duration, reqParams map[string][]string) (string, error) {
	ctx, cancel := context.WithTimeout(ctx, c.config.Timeout)
	defer cancel()

	url, err := c.client.PresignedGetObject(ctx, bucketName, objectName, expiry, reqParams)
	if err != nil {
		return "", fmt.Errorf("failed to generate presigned get url: %w", err)
	}
	return url.String(), nil
}

// PresignedPutObject generates a presigned URL for uploading
func (c *Client) PresignedPutObject(ctx context.Context, bucketName, objectName string, expiry time.Duration) (string, error) {
	ctx, cancel := context.WithTimeout(ctx, c.config.Timeout)
	defer cancel()

	url, err := c.client.PresignedPutObject(ctx, bucketName, objectName, expiry)
	if err != nil {
		return "", fmt.Errorf("failed to generate presigned put url: %w", err)
	}
	return url.String(), nil
}

// ListObjects lists objects
func (c *Client) ListObjects(ctx context.Context, bucketName string, opts minio.ListObjectsOptions) <-chan minio.ObjectInfo {
	ctx, cancel := context.WithTimeout(ctx, c.config.Timeout)
	defer cancel()

	objectCh := c.client.ListObjects(ctx, bucketName, opts)
	return objectCh
}

// GetClient returns the underlying MinIO client (for advanced operations)
func (c *Client) GetClient() *minio.Client {
	return c.client
}

var (
	MinIO *Client
)

func Init() {
	client, err := NewClient(context.Background(), Config{
		Endpoint:        "localhost:9000",
		AccessKeyID:     "minioadmin",
		SecretAccessKey: "minioadmin",
		UseSSL:          false,
		Region:          "us-east-1",
		Timeout:         30 * time.Second,
	})
	if err != nil {
		panic(err)
	}
	MinIO = client
}
