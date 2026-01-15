# Build stage
FROM golang:1.24-alpine AS builder

# Set working directory
WORKDIR /build

# Install necessary build tools
RUN apk add --no-cache git ca-certificates tzdata

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build application
# CGO_ENABLED=0 disables CGO, generates statically linked binary
# GOOS=linux specifies target operating system
# GOARCH=amd64 specifies target architecture
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -o trip-file-service \
    ./cmd/main.go


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
COPY --from=builder /build/trip-file-service .

# Change file ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 50051

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD nc -z localhost 50051 || exit 1

# Run application
CMD ["./trip-file-service"]

