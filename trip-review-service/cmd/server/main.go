package main

import (
	"flag"
	"fmt"
	"google.golang.org/grpc"
	"log"
	"net"
	pd "trip-review-service/api/grpc"
	"trip-review-service/internal/service"
)

func main() {
	flag.String("config", "configs/config.yaml", "配置文件路径")
	flag.String("port", "50052", "服务端口")
	flag.Parse()
	port := 50051
	lis, err := net.Listen("tcp", fmt.Sprintf("localhost:%d", port))
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	var opts []grpc.ServerOption
	grpcServer := grpc.NewServer(opts...)
	pd.RegisterTripReviewServiceServer(grpcServer, service.GetReviewService())
	err = grpcServer.Serve(lis)
	if err != nil {
		return
	}
}
