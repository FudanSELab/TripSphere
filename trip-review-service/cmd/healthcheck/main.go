package main

import (
	"context"
	"log"
	"os"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	healthpb "google.golang.org/grpc/health/grpc_health_v1"
)

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	connection, err := grpc.NewClient(
		"localhost:50057",
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		log.Printf("create health check client: %v", err)
		os.Exit(1)
	}
	defer connection.Close()

	response, err := healthpb.NewHealthClient(connection).Check(
		ctx,
		&healthpb.HealthCheckRequest{Service: "trip-review-service"},
	)
	if err != nil {
		log.Printf("check gRPC health: %v", err)
		os.Exit(1)
	}
	if response.GetStatus() != healthpb.HealthCheckResponse_SERVING {
		log.Printf("unexpected gRPC health status: %s", response.GetStatus())
		os.Exit(1)
	}
}
