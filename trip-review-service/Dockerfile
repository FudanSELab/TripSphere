# Build stage
FROM golang:1.25-alpine AS builder

RUN go env -w GO111MODULE=on
ARG GOPROXY
RUN if [ -n "$GOPROXY" ]; then go env -w GOPROXY="$GOPROXY"; fi

# Set working directory
WORKDIR /build

ARG ALPINE_MIRROR
RUN if [ -n "$ALPINE_MIRROR" ]; then \
        sed -i "$ALPINE_MIRROR" /etc/apk/repositories; \
    fi

# Install necessary build tools
RUN --mount=type=cache,target=/var/cache/apk \
    apk add git ca-certificates tzdata

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go mod download

# Copy source code
COPY . .

# Build application
# CGO_ENABLED=0 disables CGO, generates statically linked binary
# GOOS=linux specifies target operating system
# GOARCH=amd64 specifies target architecture
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -o trip-review-service \
    ./cmd/server/main.go


# Runtime stage
FROM alpine:latest

# Install ca-certificates and netcat for HTTPS connections and health checks
RUN apk --no-cache add ca-certificates tzdata netcat-openbsd

# Set timezone
ENV TZ=Asia/Shanghai

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# Set working directory
WORKDIR /app

# Copy binary from build stage
COPY --from=builder /build/trip-review-service .

# Create directories for RocketMQ and Nacos logs with proper permissions
RUN mkdir -p /logs /tmp/nacos/log /tmp/nacos/cache && \
    chown -R appuser:appuser /logs /tmp/nacos

# Change file ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 50057

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD nc -z localhost 50057 || exit 1

# Run application
CMD ["./trip-review-service"]
