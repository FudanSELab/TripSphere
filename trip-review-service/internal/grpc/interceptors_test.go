package grpc

import (
	"context"
	"log/slog"
	"sync"
	"testing"

	"github.com/stretchr/testify/require"
	"go.opentelemetry.io/otel/trace"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
)

type capturedRecord struct {
	message string
	attrs   map[string]any
}

type captureHandler struct {
	mu      sync.Mutex
	records []capturedRecord
}

func (h *captureHandler) Enabled(context.Context, slog.Level) bool {
	return true
}

func (h *captureHandler) Handle(_ context.Context, record slog.Record) error {
	attrs := map[string]any{}
	record.Attrs(func(attr slog.Attr) bool {
		attrs[attr.Key] = attr.Value.Any()
		return true
	})

	h.mu.Lock()
	defer h.mu.Unlock()
	h.records = append(h.records, capturedRecord{
		message: record.Message,
		attrs:   attrs,
	})
	return nil
}

func (h *captureHandler) WithAttrs(attrs []slog.Attr) slog.Handler {
	if len(attrs) == 0 {
		return h
	}
	return h
}

func (h *captureHandler) WithGroup(string) slog.Handler {
	return h
}

func (h *captureHandler) lastRecord(t *testing.T) capturedRecord {
	t.Helper()

	h.mu.Lock()
	defer h.mu.Unlock()
	require.NotEmpty(t, h.records)
	return h.records[len(h.records)-1]
}

func TestLoggingUnaryInterceptorAddsCorrelationFields(t *testing.T) {
	logs := &captureHandler{}
	previousLogger := slog.Default()
	slog.SetDefault(slog.New(logs))
	defer slog.SetDefault(previousLogger)

	traceID := trace.TraceID{0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10}
	spanID := trace.SpanID{0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18}
	spanContext := trace.NewSpanContext(trace.SpanContextConfig{
		TraceID: traceID,
		SpanID:  spanID,
	})
	ctx := metadata.NewIncomingContext(
		trace.ContextWithSpanContext(context.Background(), spanContext),
		metadata.Pairs(metadataKeyRequestID, "request-42", metadataKeyUserID, "user-7"),
	)

	resp, err := LoggingUnaryInterceptor()(
		ctx,
		nil,
		&grpc.UnaryServerInfo{FullMethod: "/tripsphere.review.v1.ReviewService/ListReviewsByEntity"},
		func(context.Context, interface{}) (interface{}, error) {
			return "ok", nil
		},
	)

	require.NoError(t, err)
	require.Equal(t, "ok", resp)
	record := logs.lastRecord(t)
	require.Equal(t, "gRPC request", record.message)
	require.Equal(t, "/tripsphere.review.v1.ReviewService/ListReviewsByEntity", record.attrs["method"])
	require.Equal(t, codes.OK.String(), record.attrs["code"])
	require.Equal(t, "request-42", record.attrs["request_id"])
	require.Equal(t, "user-7", record.attrs["user_id"])
	require.Equal(t, traceID.String(), record.attrs["trace_id"])
	require.Equal(t, spanID.String(), record.attrs["span_id"])
	require.Contains(t, record.attrs, "duration")
}

func TestLoggingUnaryInterceptorOmitsEmptyCorrelationFields(t *testing.T) {
	logs := &captureHandler{}
	previousLogger := slog.Default()
	slog.SetDefault(slog.New(logs))
	defer slog.SetDefault(previousLogger)

	_, err := LoggingUnaryInterceptor()(
		context.Background(),
		nil,
		&grpc.UnaryServerInfo{FullMethod: "/tripsphere.review.v1.ReviewService/ListReviewsByEntity"},
		func(context.Context, interface{}) (interface{}, error) {
			return nil, nil
		},
	)

	require.NoError(t, err)
	record := logs.lastRecord(t)
	require.NotContains(t, record.attrs, "request_id")
	require.NotContains(t, record.attrs, "user_id")
	require.NotContains(t, record.attrs, "trace_id")
	require.NotContains(t, record.attrs, "span_id")
}
