package nacos

import (
	"context"
	"log"
)

// Shutdown performs graceful shutdown of Nacos client
func Shutdown(ctx context.Context) {
	if Nacos == nil {
		return
	}
	if err := Deregister(ctx); err != nil {
		log.Printf("failed to deregister from nacos: %v", err)
	}
}
