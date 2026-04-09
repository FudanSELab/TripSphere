package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"
	"time"

	"trip-review-service/config"
	grpcserver "trip-review-service/internal/grpc"
	"trip-review-service/internal/repository"
	"trip-review-service/internal/service"
	"trip-review-service/pkg/nacos"
)

func main() {
	// Setup structured logging
	setupLogger()

	// Run the application
	if err := run(); err != nil {
		slog.Error("application failed", "error", err)
		os.Exit(1)
	}
}

func run() error {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		return err
	}

	slog.Info("configuration loaded",
		"app_name", cfg.App.Name,
		"env", cfg.App.Env,
		"port", cfg.App.Port,
	)

	// Initialize MongoDB
	db, mongoClient, err := repository.NewMongoDB(ctx, cfg.MongoDB)
	if err != nil {
		return err
	}
	defer func() {
		shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer shutdownCancel()
		if err := repository.CloseMongoDB(shutdownCtx, mongoClient); err != nil {
			slog.Error("failed to close MongoDB connection", "error", err)
		}
	}()

	// Initialize repository
	reviewRepo := repository.NewReviewRepo(db)

	// Ensure indexes are created
	if err := reviewRepo.EnsureIndexes(ctx); err != nil {
		slog.Warn("failed to create indexes", "error", err)
	}

	// Initialize service
	reviewService := service.NewReviewService(reviewRepo)

	// Initialize gRPC server
	server, err := grpcserver.NewServer(reviewService, cfg.App.Port)
	if err != nil {
		return err
	}

	// Initialize Nacos client (optional)
	var nacosClient *nacos.Client
	if cfg.Nacos.Host != "" {
		nacosClient, err = nacos.NewClient(ctx, nacos.Config{
			Host:        cfg.Nacos.Host,
			Port:        cfg.Nacos.Port,
			NamespaceID: cfg.Nacos.Namespace,
			GroupName:   cfg.Nacos.Group,
			Username:    cfg.Nacos.Username,
			Password:    cfg.Nacos.Password,
		})
		if err != nil {
			slog.Warn("failed to initialize nacos client, service discovery disabled", "error", err)
		}
	}

	// Start gRPC server in goroutine
	errChan := make(chan error, 1)
	go func() {
		if err := server.Start(); err != nil {
			errChan <- err
		}
	}()

	// Register to Nacos after server starts
	if nacosClient != nil {
		time.Sleep(100 * time.Millisecond)
		if err := nacosClient.Register(ctx, cfg.App.Name, uint64(cfg.App.Port)); err != nil {
			slog.Warn("failed to register to nacos", "error", err)
		} else {
			slog.Info("service registered to Nacos", "service_name", cfg.App.Name)
		}
	}

	// Wait for interrupt signal or server error
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	select {
	case <-quit:
		slog.Info("received shutdown signal")
	case err := <-errChan:
		slog.Error("server error", "error", err)
		return err
	}

	// Graceful shutdown
	slog.Info("shutting down server...")

	// Deregister from Nacos
	if nacosClient != nil {
		deregisterCtx, deregisterCancel := context.WithTimeout(context.Background(), 5*time.Second)
		if err := nacosClient.Deregister(deregisterCtx, cfg.App.Name, uint64(cfg.App.Port)); err != nil {
			slog.Warn("failed to deregister from nacos", "error", err)
		} else {
			slog.Info("service deregistered from Nacos")
		}
		deregisterCancel()
	}

	// Stop gRPC server
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer shutdownCancel()
	server.GracefulStop(shutdownCtx)

	slog.Info("server exited")
	return nil
}

func setupLogger() {
	// Use JSON handler in production, text handler in development
	var handler slog.Handler
	env := os.Getenv("APP_ENV")
	if env == "prod" || env == "production" {
		handler = slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
			Level: slog.LevelInfo,
		})
	} else {
		handler = slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
			Level: slog.LevelDebug,
		})
	}
	slog.SetDefault(slog.New(handler))
}
