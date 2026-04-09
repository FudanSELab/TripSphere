package domain

import (
	"context"
	"time"
)

// EntityType represents the type of entity being reviewed
type EntityType int32

const (
	EntityTypeUnspecified EntityType = 0
	EntityTypeHotel       EntityType = 1
	EntityTypeAttraction  EntityType = 2
)

// Review represents a user review for an entity (hotel, attraction, etc.)
type Review struct {
	ID         string            `json:"id" bson:"_id"`
	UserID     string            `json:"user_id" bson:"user_id"`
	EntityType EntityType        `json:"entity_type" bson:"entity_type"`
	EntityID   string            `json:"entity_id" bson:"entity_id"`
	Rating     int32             `json:"rating" bson:"rating"`
	Content    string            `json:"content" bson:"content"`
	Images     []string          `json:"images" bson:"images"`
	Dimensions map[string]uint32 `json:"dimensions" bson:"dimensions"`
	CreatedAt  time.Time         `json:"created_at" bson:"created_at"`
	UpdatedAt  time.Time         `json:"updated_at" bson:"updated_at"`
}

// ListReviewsOptions contains options for listing reviews
type ListReviewsOptions struct {
	EntityType    EntityType
	EntityID      string
	PageSize      int32
	PageToken     string
	OrderBy       string // e.g. "created_at", "updated_at desc"
	ExcludeUserID string // Exclude reviews from this user (for deduplication)
}

// ListReviewsResult contains the result of listing reviews
type ListReviewsResult struct {
	Reviews       []Review
	NextPageToken string
}

// ReviewRepository defines the interface for review data access
type ReviewRepository interface {
	Create(ctx context.Context, review *Review) error
	GetByID(ctx context.Context, id string) (*Review, error)
	Update(ctx context.Context, review *Review) error
	Delete(ctx context.Context, id string) error
	ListByEntity(ctx context.Context, opts ListReviewsOptions) (*ListReviewsResult, error)
	// GetByEntityAndUser retrieves a user's review for a specific entity.
	// Returns nil if the user has not reviewed the entity.
	GetByEntityAndUser(ctx context.Context, entityType EntityType, entityID, userID string) (*Review, error)
}
