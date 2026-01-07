package client

import (
	"context"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// ClientConfig client configuration
type ClientConfig struct {
	Address string
	Timeout time.Duration
}

// NewClientConn creates a gRPC client connection
func NewClientConn(ctx context.Context, config ClientConfig) (*grpc.ClientConn, error) {
	ctx, cancel := context.WithTimeout(ctx, config.Timeout)
	defer cancel()

	conn, err := grpc.DialContext(
		ctx,
		config.Address,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithBlock(),
	)
	if err != nil {
		return nil, err
	}

	return conn, nil
}

// CloseClientConn closes the client connection
func CloseClientConn(conn *grpc.ClientConn) error {
	if conn != nil {
		return conn.Close()
	}
	return nil
}
