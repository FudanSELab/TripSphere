package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"google.golang.org/grpc"

	pd "trip-review-service/api/grpc/gen/tripsphere/review"
	"trip-review-service/config"
	"trip-review-service/internal/service"
	"trip-review-service/pkg/nacos"
)

func main() {
	// Initialize configuration
	config.Init()

	// Get service name and port from config
	serviceName := config.AppName
	port := int(config.PortInt)

	// Initialize Nacos client
	ctx := context.Background()
	if config.NacosHost != "" {
		err := nacos.Init(ctx, nacos.Config{
			Host:        config.NacosHost,
			Port:        int(config.NacosPortInt),
			NamespaceID: config.NacosNamespace,
			GroupName:   config.NacosGroup,
			Username:    config.NacosUsername,
			Password:    config.NacosPassword,
		})
		if err != nil {
			log.Printf("Warning: failed to initialize nacos client: %v", err)
		}
	}

	// Listen on port
	lis, err := net.Listen("tcp", fmt.Sprintf(":%d", port))
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	// Create gRPC server
	var opts []grpc.ServerOption
	grpcServer := grpc.NewServer(opts...)
	pd.RegisterReviewServiceServer(grpcServer, service.GetReviewService())

	log.Printf("ReviewService gRPC server listening on port %d", port)

	// Start service in a goroutine
	go func() {
		if err := grpcServer.Serve(lis); err != nil {
			log.Fatalf("failed to serve: %v", err)
		}
	}()

	// Register service to Nacos after 100ms
	go func() {
		time.Sleep(100 * time.Millisecond)
		if nacos.Nacos != nil {
			if err := nacos.Nacos.Register(ctx, serviceName, uint64(port)); err != nil {
				log.Printf("Warning: failed to register to nacos: %v", err)
			} else {
				log.Printf("Service registered to Nacos")
			}
		}
	}()

	// Wait for interrupt signal to gracefully shutdown the server
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	log.Println("Shutting down server...")

	// Deregister from Nacos
	if nacos.Nacos != nil {
		deregisterCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		if err := nacos.Nacos.Deregister(deregisterCtx, serviceName, uint64(port)); err != nil {
			log.Printf("Warning: failed to deregister from nacos: %v", err)
		} else {
			log.Println("Service deregistered from Nacos")
		}
		cancel()
	}

	// Graceful shutdown
	gracefulStop := make(chan struct{})
	go func() {
		grpcServer.GracefulStop()
		close(gracefulStop)
	}()

	// Wait for graceful stop with timeout
	select {
	case <-gracefulStop:
		log.Println("Server stopped gracefully")
	case <-time.After(10 * time.Second):
		log.Println("Graceful shutdown timeout, forcing stop")
		grpcServer.Stop()
	}

	// Shutdown Nacos client
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	nacos.Shutdown(shutdownCtx)

	log.Println("Server exited")
}
