package grpc

import (
	"context"
	"encoding/hex"
	"log/slog"
	"strings"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
)

// LoggingUnaryInterceptor logs unary RPC requests
func LoggingUnaryInterceptor() grpc.UnaryServerInterceptor {
	return func(
		ctx context.Context,
		req interface{},
		info *grpc.UnaryServerInfo,
		handler grpc.UnaryHandler,
	) (interface{}, error) {
		start := time.Now()

		// Call the handler
		resp, err := handler(ctx, req)

		// Log the request
		duration := time.Since(start)
		code := codes.OK
		if err != nil {
			code = status.Code(err)
		}

		level := slog.LevelInfo
		if code != codes.OK {
			level = slog.LevelError
		}

		attributes := requestCorrelationAttributes(ctx)
		attributes = append(attributes,
			"method", info.FullMethod,
			"duration", duration,
			"code", code.String(),
		)
		slog.Log(ctx, level, "gRPC request", attributes...)

		return resp, err
	}
}

// RecoveryUnaryInterceptor recovers from panics in handlers
func RecoveryUnaryInterceptor() grpc.UnaryServerInterceptor {
	return func(
		ctx context.Context,
		req interface{},
		info *grpc.UnaryServerInfo,
		handler grpc.UnaryHandler,
	) (resp interface{}, err error) {
		defer func() {
			if r := recover(); r != nil {
				attributes := requestCorrelationAttributes(ctx)
				attributes = append(attributes,
					"method", info.FullMethod,
					"panic", r,
				)
				slog.ErrorContext(ctx, "panic recovered in gRPC handler", attributes...)
				err = status.Errorf(codes.Internal, "internal server error")
			}
		}()

		return handler(ctx, req)
	}
}

func requestCorrelationAttributes(ctx context.Context) []any {
	incomingMetadata, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		return nil
	}

	attributes := make([]any, 0, 6)
	if traceID := traceIDFromTraceparent(firstMetadataValue(incomingMetadata, "traceparent")); traceID != "" {
		attributes = append(attributes, "trace_id", traceID)
	}
	if requestID := firstMetadataValue(incomingMetadata, "x-request-id", "request-id", "request_id"); requestID != "" {
		attributes = append(attributes, "request_id", requestID)
	}
	if userID := firstMetadataValue(incomingMetadata, "x-user-id"); userID != "" {
		attributes = append(attributes, "user_id", userID)
	}
	return attributes
}

func firstMetadataValue(incomingMetadata metadata.MD, keys ...string) string {
	for _, key := range keys {
		if values := incomingMetadata.Get(key); len(values) > 0 {
			if value := strings.TrimSpace(values[0]); value != "" {
				return value
			}
		}
	}
	return ""
}

func traceIDFromTraceparent(traceparent string) string {
	parts := strings.Split(traceparent, "-")
	if len(parts) != 4 || len(parts[1]) != 32 || parts[1] == strings.Repeat("0", 32) {
		return ""
	}
	if _, err := hex.DecodeString(parts[1]); err != nil {
		return ""
	}
	return strings.ToLower(parts[1])
}
