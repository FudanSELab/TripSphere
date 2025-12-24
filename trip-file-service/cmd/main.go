package main

import (
	"log"
	"net"

	"google.golang.org/grpc"

	"trip-file-service/clients"
	pb "trip-file-service/clients/grpc/gen/file"
	server "trip-file-service/servies"
)

const (
	port = ":50051"
)

func main() {
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

	// Start service
	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
