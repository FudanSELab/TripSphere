package domain

import (
	"context"
	"time"
)

type ReviewTargetType string

const (
	ReviewTargetHotel      ReviewTargetType = "hotel"
	ReviewTargetAttraction ReviewTargetType = "attraction"
)

type Review struct {
	ID         string           `json:"id"`
	UserID     string           `json:"uid"`
	TargetType ReviewTargetType `json:"target_type"`
	TargetID   string           `json:"target_id"`
	Rating     int64            `json:"rating"`

	Text   string   `json:"text"`
	Images []string `json:"images"`

	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type ReviewRepository interface {
	Create(ctx context.Context, review *Review) error
	GetByID(ctx context.Context, id string) (*Review, error)
	FindByTarget(ctx context.Context, targetType ReviewTargetType, targetID string, offset, limit int64) ([]Review, error)
	Update(ctx context.Context, review *Review) error
	Delete(ctx context.Context, id string) error
	FindByTargetWithCursor(ctx context.Context, targetType ReviewTargetType, targetID string, cursor string, limit int64) ([]Review, string, error)
}
