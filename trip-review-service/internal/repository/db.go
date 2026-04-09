package repository

import (
	"context"
	"fmt"
	"log/slog"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
	"go.mongodb.org/mongo-driver/mongo/readpref"

	"trip-review-service/config"
)

// NewMongoDB creates a new MongoDB client and database connection
func NewMongoDB(ctx context.Context, cfg config.MongoDBConfig) (*mongo.Database, *mongo.Client, error) {
	clientOpts := options.Client().
		ApplyURI(cfg.URI).
		SetMaxPoolSize(cfg.MaxPoolSize).
		SetMinPoolSize(cfg.MinPoolSize)

	connectCtx, cancel := context.WithTimeout(ctx, cfg.ConnectTimeout)
	defer cancel()

	client, err := mongo.Connect(connectCtx, clientOpts)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to connect to MongoDB: %w", err)
	}

	// Verify connection
	pingCtx, pingCancel := context.WithTimeout(ctx, cfg.ConnectTimeout)
	defer pingCancel()
	if err := client.Ping(pingCtx, readpref.Primary()); err != nil {
		return nil, nil, fmt.Errorf("failed to ping MongoDB: %w", err)
	}

	slog.Info("connected to MongoDB successfully",
		"database", cfg.Database,
	)

	return client.Database(cfg.Database), client, nil
}

// CloseMongoDB closes the MongoDB client connection
func CloseMongoDB(ctx context.Context, client *mongo.Client) error {
	if client == nil {
		return nil
	}
	return client.Disconnect(ctx)
}
