package grpc

import (
	"context"
	"log/slog"
	"time"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"

	"trip-review-service/internal/correlation"
)

const metadataKeyUserID = "x-user-id"

// CorrelationUnaryInterceptor makes the external request ID available to logs
// and adds it to the active server span.
func CorrelationUnaryInterceptor() grpc.UnaryServerInterceptor {
	return func(
		ctx context.Context,
		req interface{},
		info *grpc.UnaryServerInfo,
		handler grpc.UnaryHandler,
	) (interface{}, error) {
		requestID := correlation.FromIncomingContext(ctx)
		ctx = correlation.WithRequestID(ctx, requestID)

		span := trace.SpanFromContext(ctx)
		if span.IsRecording() {
			span.SetAttributes(attribute.String("request.id", requestID))
		}

		return handler(ctx, req)
	}
}

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

		attrs := []slog.Attr{
			slog.String("method", info.FullMethod),
			slog.Duration("duration", duration),
			slog.String("code", code.String()),
		}
		if userID := incomingMetadataValue(ctx, metadataKeyUserID); userID != "" {
			attrs = append(attrs, slog.String("user_id", userID))
		}
		spanContext := trace.SpanContextFromContext(ctx)
		if spanContext.IsValid() {
			attrs = append(attrs,
				slog.String("trace_id", spanContext.TraceID().String()),
				slog.String("span_id", spanContext.SpanID().String()),
			)
		}

		slog.LogAttrs(ctx, level, "gRPC request", attrs...)

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
				slog.ErrorContext(ctx, "panic recovered in gRPC handler",
					"method", info.FullMethod,
					"panic", r,
				)
				err = status.Errorf(codes.Internal, "internal server error")
			}
		}()

		return handler(ctx, req)
	}
}

func incomingMetadataValue(ctx context.Context, key string) string {
	md, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		return ""
	}
	values := md.Get(key)
	if len(values) == 0 {
		return ""
	}
	return values[0]
}
