package service

import (
	"context"
	"log/slog"
	"time"

	"github.com/google/uuid"
	"golang.org/x/sync/errgroup"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/timestamppb"

	pb "trip-review-service/api/grpc/generated/tripsphere/review/v1"
	"trip-review-service/internal/domain"
)

const (
	// Metadata keys for user authentication
	metadataKeyUserID = "x-user-id"
)

// ReviewService implements the gRPC ReviewServiceServer
type ReviewService struct {
	pb.UnimplementedReviewServiceServer
	repo domain.ReviewRepository
}

// NewReviewService creates a new ReviewService with the given repository
func NewReviewService(repo domain.ReviewRepository) *ReviewService {
	return &ReviewService{repo: repo}
}

// extractUserID extracts the user ID from gRPC metadata.
// Returns empty string if user is not authenticated.
func extractUserID(ctx context.Context) string {
	md, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		return ""
	}

	values := md.Get(metadataKeyUserID)
	if len(values) == 0 {
		return ""
	}

	return values[0]
}

// CreateReview creates a new review
func (s *ReviewService) CreateReview(ctx context.Context, req *pb.CreateReviewRequest) (*pb.CreateReviewResponse, error) {
	if req.Review == nil {
		return nil, status.Error(codes.InvalidArgument, "review is required")
	}

	review := req.Review

	// Input validation
	if review.UserId == "" {
		return nil, status.Error(codes.InvalidArgument, "user_id is required")
	}
	if review.EntityId == "" {
		return nil, status.Error(codes.InvalidArgument, "entity_id is required")
	}
	if review.EntityType == pb.EntityType_ENTITY_TYPE_UNSPECIFIED {
		return nil, status.Error(codes.InvalidArgument, "entity_type is required")
	}
	if review.Rating < 1 || review.Rating > 5 {
		return nil, status.Error(codes.InvalidArgument, "rating must be between 1 and 5")
	}

	id := uuid.New().String()
	now := time.Now()

	domainReview := &domain.Review{
		ID:         id,
		UserID:     review.UserId,
		EntityType: domain.EntityType(review.EntityType),
		EntityID:   review.EntityId,
		Rating:     review.Rating,
		Content:    review.Content,
		Images:     review.Images,
		Dimensions: review.Dimensions,
		CreatedAt:  now,
		UpdatedAt:  now,
	}

	if err := s.repo.Create(ctx, domainReview); err != nil {
		slog.ErrorContext(ctx, "failed to create review",
			"error", err,
			"user_id", review.UserId,
			"entity_id", review.EntityId,
		)
		return nil, status.Errorf(codes.Internal, "failed to create review: %v", err)
	}

	slog.InfoContext(ctx, "review created",
		"id", id,
		"user_id", review.UserId,
		"entity_id", review.EntityId,
	)

	return &pb.CreateReviewResponse{
		Review: domainToProto(domainReview),
	}, nil
}

// UpdateReview updates an existing review
func (s *ReviewService) UpdateReview(ctx context.Context, req *pb.UpdateReviewRequest) (*pb.UpdateReviewResponse, error) {
	if req.Review == nil {
		return nil, status.Error(codes.InvalidArgument, "review is required")
	}

	review := req.Review

	// Input validation
	if review.Id == "" {
		return nil, status.Error(codes.InvalidArgument, "id is required")
	}
	if review.Rating < 1 || review.Rating > 5 {
		return nil, status.Error(codes.InvalidArgument, "rating must be between 1 and 5")
	}

	// Fetch existing review first
	existingReview, err := s.repo.GetByID(ctx, review.Id)
	if err != nil {
		slog.ErrorContext(ctx, "failed to get review for update",
			"error", err,
			"id", review.Id,
		)
		return nil, status.Errorf(codes.Internal, "failed to get review: %v", err)
	}
	if existingReview == nil {
		return nil, status.Error(codes.NotFound, "review not found")
	}

	// Update fields
	existingReview.Rating = review.Rating
	existingReview.Content = review.Content
	existingReview.Images = review.Images
	existingReview.Dimensions = review.Dimensions
	existingReview.UpdatedAt = time.Now()

	if err := s.repo.Update(ctx, existingReview); err != nil {
		slog.ErrorContext(ctx, "failed to update review",
			"error", err,
			"id", review.Id,
		)
		return nil, status.Errorf(codes.Internal, "failed to update review: %v", err)
	}

	slog.InfoContext(ctx, "review updated", "id", review.Id)

	return &pb.UpdateReviewResponse{
		Review: domainToProto(existingReview),
	}, nil
}

// DeleteReview deletes a review by ID
func (s *ReviewService) DeleteReview(ctx context.Context, req *pb.DeleteReviewRequest) (*pb.DeleteReviewResponse, error) {
	if req.Id == "" {
		return nil, status.Error(codes.InvalidArgument, "id is required")
	}

	if err := s.repo.Delete(ctx, req.Id); err != nil {
		if domain.IsNotFoundError(err) {
			return nil, status.Error(codes.NotFound, "review not found")
		}
		slog.ErrorContext(ctx, "failed to delete review",
			"error", err,
			"id", req.Id,
		)
		return nil, status.Errorf(codes.Internal, "failed to delete review: %v", err)
	}

	slog.InfoContext(ctx, "review deleted", "id", req.Id)

	return &pb.DeleteReviewResponse{}, nil
}

// ListReviewsByEntity lists reviews for an entity with cursor-based pagination.
// If the user is logged in and this is the first page (no page_token),
// the user's own review will be returned separately in user_review field,
// and excluded from the reviews list to avoid duplication.
func (s *ReviewService) ListReviewsByEntity(ctx context.Context, req *pb.ListReviewsByEntityRequest) (*pb.ListReviewsByEntityResponse, error) {
	// Input validation
	if req.EntityId == "" {
		return nil, status.Error(codes.InvalidArgument, "entity_id is required")
	}
	if req.EntityType == pb.EntityType_ENTITY_TYPE_UNSPECIFIED {
		return nil, status.Error(codes.InvalidArgument, "entity_type is required")
	}

	// Extract user ID from metadata
	userID := extractUserID(ctx)
	isFirstPage := req.PageToken == ""
	shouldFetchUserReview := userID != "" && isFirstPage

	var (
		userReview *domain.Review
		result     *domain.ListReviewsResult
	)

	// Build list options
	opts := domain.ListReviewsOptions{
		EntityType: domain.EntityType(req.EntityType),
		EntityID:   req.EntityId,
		PageSize:   req.PageSize,
		PageToken:  req.PageToken,
		OrderBy:    req.OrderBy,
	}

	// If user is logged in, exclude their review from the list to avoid duplication
	if userID != "" {
		opts.ExcludeUserID = userID
	}

	if shouldFetchUserReview {
		// Run both queries concurrently
		g, gCtx := errgroup.WithContext(ctx)

		// Query 1: Fetch the current user's review
		g.Go(func() error {
			var err error
			userReview, err = s.repo.GetByEntityAndUser(gCtx, opts.EntityType, opts.EntityID, userID)
			if err != nil {
				slog.ErrorContext(gCtx, "failed to get user review",
					"error", err,
					"entity_type", req.EntityType,
					"entity_id", req.EntityId,
					"user_id", userID,
				)
				return err
			}
			return nil
		})

		// Query 2: Fetch the paginated review list (excluding current user)
		g.Go(func() error {
			var err error
			result, err = s.repo.ListByEntity(gCtx, opts)
			if err != nil {
				slog.ErrorContext(gCtx, "failed to list reviews by entity",
					"error", err,
					"entity_type", req.EntityType,
					"entity_id", req.EntityId,
				)
				return err
			}
			return nil
		})

		if err := g.Wait(); err != nil {
			if err == domain.ErrInvalidPageToken {
				return nil, status.Error(codes.InvalidArgument, "invalid page_token")
			}
			return nil, status.Errorf(codes.Internal, "failed to list reviews: %v", err)
		}
	} else {
		// Not first page or user not logged in - just fetch the list
		var err error
		result, err = s.repo.ListByEntity(ctx, opts)
		if err != nil {
			if err == domain.ErrInvalidPageToken {
				return nil, status.Error(codes.InvalidArgument, "invalid page_token")
			}
			slog.ErrorContext(ctx, "failed to list reviews by entity",
				"error", err,
				"entity_type", req.EntityType,
				"entity_id", req.EntityId,
			)
			return nil, status.Errorf(codes.Internal, "failed to list reviews: %v", err)
		}
	}

	// Build response
	pbReviews := make([]*pb.Review, 0, len(result.Reviews))
	for _, review := range result.Reviews {
		pbReviews = append(pbReviews, domainToProto(&review))
	}

	resp := &pb.ListReviewsByEntityResponse{
		Reviews:       pbReviews,
		NextPageToken: result.NextPageToken,
	}

	// Include user_review only on first page if user has reviewed this entity
	if userReview != nil {
		resp.UserReview = domainToProto(userReview)
	}

	return resp, nil
}

// domainToProto converts a domain.Review to a protobuf Review
func domainToProto(review *domain.Review) *pb.Review {
	return &pb.Review{
		Id:         review.ID,
		UserId:     review.UserID,
		EntityType: pb.EntityType(review.EntityType),
		EntityId:   review.EntityID,
		Rating:     review.Rating,
		Content:    review.Content,
		Images:     review.Images,
		Dimensions: review.Dimensions,
		CreatedAt:  timestamppb.New(review.CreatedAt),
		UpdatedAt:  timestamppb.New(review.UpdatedAt),
	}
}
