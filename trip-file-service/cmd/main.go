package main

import (
	"context"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"google.golang.org/grpc"

	"trip-file-service/clients"
	pb "trip-file-service/clients/grpc/gen/tripsphere/file"
	"trip-file-service/clients/nacos"
	"trip-file-service/config"
	server "trip-file-service/services"
)

const (
	port = ":50051"
)

func main() {
	config.Init()
	clients.Init()

	// Listen on port
	lis, err := net.Listen("tcp", port)
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	// Create gRPC server
	s := grpc.NewServer()

	// Register FileService
	fileServer := server.NewFileServer()
	pb.RegisterFileServiceServer(s, fileServer)

	log.Printf("FileService gRPC server listening on %s", port)

	// Start service in a goroutine
	go func() {
		if err := s.Serve(lis); err != nil {
			log.Fatalf("failed to serve: %v", err)
		}
	}()

	// Register service to Nacos after 100ms
	go func() {
		time.Sleep(100 * time.Millisecond)
		ctx := context.Background()
		if err := nacos.Register(ctx); err != nil {
			log.Panicf("failed to register to nacos: %v", err)
		}
		log.Printf("Service registered to Nacos")
	}()

	// Wait for interrupt signal to gracefully shutdown the server
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	log.Println("Shutting down server...")

	// Graceful shutdown
	gracefulStop := make(chan struct{})
	go func() {
		s.GracefulStop()
		close(gracefulStop)
	}()

	// Wait for graceful stop with timeout
	select {
	case <-gracefulStop:
		log.Println("Server stopped gracefully")
	case <-time.After(10 * time.Second):
		log.Println("Graceful shutdown timeout, forcing stop")
		s.Stop()
	}

	// Shutdown clients
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	clients.Shutdown(shutdownCtx)

	log.Println("Server exited")
}
