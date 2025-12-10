package service

import (
	"context"
	"fmt"
	"github.com/google/uuid"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"log"
	"time"
	pd "trip-review-service/api/grpc"
	"trip-review-service/internal/domain"
	"trip-review-service/internal/repository"
)

type ReviewService struct {
	pd.UnimplementedTripReviewServiceServer
	db domain.ReviewRepository
}

var reviewService *ReviewService

func GetReviewService() *ReviewService {
	return reviewService
}

func NewReviewService(db domain.ReviewRepository) *ReviewService {
	return &ReviewService{db: db}
}

func (r *ReviewService) CreateReview(ctx context.Context, request *pd.CreateReviewRequest) (*pd.CreateReviewResponse, error) {
	newUUID, err := uuid.NewUUID()
	if err != nil {
		log.Println("")
		return &pd.CreateReviewResponse{Status: false, Id: ""}, status.Error(codes.Internal, fmt.Sprintf("failed to create "))
	}
	id := newUUID.String()
	review := &domain.Review{ID: id, UserID: request.UserId, TargetType: domain.ReviewTargetType(request.TargetType),
		TargetID: request.TargetId, Rating: request.Rating, Text: request.Text, Images: request.Images,
		CreatedAt: time.Now(), UpdatedAt: time.Now()}
	err = reviewService.db.Create(ctx, review)
	if err != nil {
		log.Printf("failed to create %+v\n", review)
		return &pd.CreateReviewResponse{Status: false, Id: ""}, status.Error(codes.Internal, fmt.Sprintf("failed to create "))
	}
	return &pd.CreateReviewResponse{
		Id:     id,
		Status: true,
	}, nil
}

func (r *ReviewService) UpdateReview(ctx context.Context, request *pd.UpdateReviewRequest) (*pd.UpdateReviewResponse, error) {
	review := &domain.Review{
		ID:        request.Id,
		Rating:    request.Rating,
		Text:      request.Text,
		Images:    request.Images,
		UpdatedAt: time.Now(),
	}
	err := reviewService.db.Update(ctx, review)
	if err != nil {
		log.Printf("update fail:%s\n", err.Error())
		return &pd.UpdateReviewResponse{Status: false}, status.Error(codes.Internal, fmt.Sprintf("failed to update "))
	}
	return &pd.UpdateReviewResponse{Status: true}, nil

}

func (r *ReviewService) DeleteReview(ctx context.Context, request *pd.DeleteReviewRequest) (*pd.DeleteReviewResponse, error) {
	id := request.Id
	err := reviewService.db.Delete(ctx, id)
	if err != nil {
		return &pd.DeleteReviewResponse{Status: false}, status.Error(codes.Internal, fmt.Sprintf("failed to delete"))
	}
	return &pd.DeleteReviewResponse{Status: true}, nil
}

func (r *ReviewService) GetReviewByTargetID(ctx context.Context, request *pd.GetReviewByTargetIDRequest) (*pd.GetReviewByTargetIDResponse, error) {
	reviews, err := reviewService.db.FindByTarget(ctx, domain.ReviewTargetType(request.TargetType), request.TargetId, request.PageSize*(request.PageNumber-1), request.PageSize)
	if err != nil {
		log.Printf("get reviews by target id fail\n")
		return &pd.GetReviewByTargetIDResponse{Reviews: []*pd.Review{}}, status.Error(codes.Internal, fmt.Sprintf("failed to get reviews by target id"))
	}
	var pbReviews []*pd.Review
	for _, review := range reviews {
		pbReview := &pd.Review{
			Id:         review.ID,
			UserId:     review.UserID,
			TargetType: string(review.TargetType),
			TargetId:   review.TargetID,
			Rating:     review.Rating,
			Text:       review.Text,
			Images:     review.Images,
			CreatedAt:  review.CreatedAt.Unix(),
			UpdatedAt:  review.UpdatedAt.Unix(),
		}
		pbReviews = append(pbReviews, pbReview)
	}
	return &pd.GetReviewByTargetIDResponse{Reviews: pbReviews,
		TotalReviews: int64(len(pbReviews)),
		Status:       true,
	}, nil

}

func (r *ReviewService) GetReviewByTargetIDWithCursor(ctx context.Context, request *pd.GetReviewByTargetIDWithCursorRequest) (*pd.GetReviewByTargetIDWithCursorResponse, error) {
	reviews, nextCursor, err := reviewService.db.FindByTargetWithCursor(ctx, domain.ReviewTargetType(request.TargetType), request.TargetId, request.Cursor, request.Limit)
	if err != nil {
		log.Printf("get reviews by target id with cursor fail:%s\n", err.Error())
		return &pd.GetReviewByTargetIDWithCursorResponse{Reviews: []*pd.Review{}, NextCursor: ""}, status.Error(codes.Internal, fmt.Sprintf("failed to get reviews by target id with cursor"))
	}
	var pbReviews []*pd.Review
	for _, review := range reviews {
		pbReview := &pd.Review{
			Id:         review.ID,
			UserId:     review.UserID,
			TargetType: string(review.TargetType),
			TargetId:   review.TargetID,
			Rating:     review.Rating,
			Text:       review.Text,
			Images:     review.Images,
			CreatedAt:  review.CreatedAt.Unix(),
			UpdatedAt:  review.UpdatedAt.Unix(),
		}
		pbReviews = append(pbReviews, pbReview)
	}
	return &pd.GetReviewByTargetIDWithCursorResponse{Reviews: pbReviews, TotalReviews: int64(len(pbReviews)), NextCursor: nextCursor, Status: true}, nil
}

func init() {
	reviewService = NewReviewService(repository.GetReviewRepo())
}
