package correlation

import (
	"context"
	"strings"
	"unicode"

	"github.com/google/uuid"
	"google.golang.org/grpc/metadata"
)

const MetadataKey = "x-request-id"

type requestIDContextKey struct{}

func FromIncomingContext(ctx context.Context) string {
	md, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		return NewRequestID()
	}

	values := md.Get(MetadataKey)
	if len(values) == 0 {
		return NewRequestID()
	}
	return Normalize(values[0])
}

func WithRequestID(ctx context.Context, requestID string) context.Context {
	return context.WithValue(ctx, requestIDContextKey{}, Normalize(requestID))
}

func RequestID(ctx context.Context) string {
	requestID, _ := ctx.Value(requestIDContextKey{}).(string)
	return requestID
}

func NewRequestID() string {
	return uuid.NewString()
}

func Normalize(requestID string) string {
	value := strings.TrimSpace(requestID)
	if value == "" || len(value) > 128 {
		return NewRequestID()
	}
	for _, char := range value {
		if unicode.IsControl(char) {
			return NewRequestID()
		}
	}
	return value
}
