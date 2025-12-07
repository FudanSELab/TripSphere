package domain

import (
	"context"
	"time"
	"trip-review-service/internal/repository/model"
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
	Rating     int              `json:"rating"`

	Text   string   `json:"text"`
	Images []string `json:"images"`

	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

func (review *Review) ToModel() *model.ReviewModel {
	return &model.ReviewModel{
		ID:         review.ID,
		UserID:     review.UserID,
		TargetType: string(review.TargetType),
		TargetID:   review.TargetID,
		Rating:     review.Rating,
		Text:       review.Text,
		// 直接转换类型，因为底层都是 []string
		Images: review.Images,
	}
}

type ReviewRepository interface {
	Create(ctx context.Context, review *Review) error
	GetByID(ctx context.Context, id string) (*Review, error)
	FindByTarget(ctx context.Context, targetType ReviewTargetType, targetID string, offset, limit int) ([]*Review, error)
	Update(ctx context.Context, review *Review) error
	Delete(ctx context.Context, id string, userID string) error
}
