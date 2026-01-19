package nacos

import (
	"context"
	"log"
)

var (
	// Nacos global nacos client
	Nacos *Client
)

// Init initializes the Nacos client
func Init(ctx context.Context, config Config) error {
	client, err := NewClient(ctx, config)
	if err != nil {
		log.Printf("Warning: failed to create nacos client: %v", err)
		return err
	}
	Nacos = client
	log.Println("Nacos client initialized successfully")
	return nil
}

// Shutdown closes the Nacos client
func Shutdown(ctx context.Context) error {
	// Nacos SDK doesn't require explicit shutdown
	// but we keep this for consistency
	if Nacos != nil {
		log.Println("Nacos client shutdown")
	}
	return nil
}
