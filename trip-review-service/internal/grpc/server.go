package grpc

import (
	"context"
	"fmt"
	"log/slog"
	"net"

	"google.golang.org/grpc"
	"google.golang.org/grpc/health"
	"google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc/reflection"

	pd "trip-review-service/api/grpc/generated/tripsphere/review/v1"
)

// Server wraps a gRPC server
type Server struct {
	server   *grpc.Server
	listener net.Listener
	port     int
}

// NewServer creates a new gRPC server with the given service and options
func NewServer(reviewService pd.ReviewServiceServer, port int) (*Server, error) {
	listener, err := net.Listen("tcp", fmt.Sprintf(":%d", port))
	if err != nil {
		return nil, fmt.Errorf("failed to listen on port %d: %w", port, err)
	}

	// Create gRPC server with interceptors
	grpcServer := grpc.NewServer(
		grpc.ChainUnaryInterceptor(
			RecoveryUnaryInterceptor(),
			LoggingUnaryInterceptor(),
		),
	)

	// Register services
	pd.RegisterReviewServiceServer(grpcServer, reviewService)

	// Register health check service
	healthServer := health.NewServer()
	healthServer.SetServingStatus("", grpc_health_v1.HealthCheckResponse_SERVING)
	healthServer.SetServingStatus("trip-review-service", grpc_health_v1.HealthCheckResponse_SERVING)
	grpc_health_v1.RegisterHealthServer(grpcServer, healthServer)

	// Register reflection service for debugging (disable in production if needed)
	reflection.Register(grpcServer)

	return &Server{
		server:   grpcServer,
		listener: listener,
		port:     port,
	}, nil
}

// Start starts the gRPC server (blocking)
func (s *Server) Start() error {
	slog.Info("starting gRPC server", "port", s.port)
	return s.server.Serve(s.listener)
}

// GracefulStop gracefully stops the server
func (s *Server) GracefulStop(ctx context.Context) {
	done := make(chan struct{})
	go func() {
		s.server.GracefulStop()
		close(done)
	}()

	select {
	case <-done:
		slog.Info("gRPC server stopped gracefully")
	case <-ctx.Done():
		slog.Warn("graceful shutdown timeout, forcing stop")
		s.server.Stop()
	}
}

// Port returns the server port
func (s *Server) Port() int {
	return s.port
}
