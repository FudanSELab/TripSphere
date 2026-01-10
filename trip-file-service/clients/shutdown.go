package clients

import (
	"context"
	"trip-file-service/clients/nacos"
)

// Shutdown performs graceful shutdown of all clients
func Shutdown(ctx context.Context) {
	nacos.Shutdown(ctx)
}
