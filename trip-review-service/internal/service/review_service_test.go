package service

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"

	pb "trip-review-service/api/grpc/generated/tripsphere/review/v1"
	"trip-review-service/internal/domain"
	domainmock "trip-review-service/internal/domain/mock"
)

// ============================================================
// Test Helpers
// ============================================================

func setupTest(_ *testing.T) (*ReviewService, *domainmock.MockReviewRepository) {
	mockRepo := domainmock.NewMockReviewRepository()
	service := NewReviewService(mockRepo)
	return service, mockRepo
}

func assertGRPCErrorCode(t *testing.T, err error, expectedCode codes.Code) {
	t.Helper()
	assert.Error(t, err)
	st, ok := status.FromError(err)
	assert.True(t, ok, "error should be a gRPC status error")
	assert.Equal(t, expectedCode, st.Code())
}

// contextWithUserID creates a context with user ID in metadata
func contextWithUserID(userID string) context.Context {
	md := metadata.Pairs("x-user-id", userID)
	return metadata.NewIncomingContext(context.Background(), md)
}

// ============================================================
// extractUserID Tests
// ============================================================

func TestExtractUserID(t *testing.T) {
	tests := []struct {
		name           string
		ctx            context.Context
		expectedUserID string
	}{
		{
			name:           "with user id in metadata",
			ctx:            contextWithUserID("user-123"),
			expectedUserID: "user-123",
		},
		{
			name:           "without metadata",
			ctx:            context.Background(),
			expectedUserID: "",
		},
		{
			name:           "with empty metadata",
			ctx:            metadata.NewIncomingContext(context.Background(), metadata.MD{}),
			expectedUserID: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			userID := extractUserID(tt.ctx)
			assert.Equal(t, tt.expectedUserID, userID)
		})
	}
}

// ============================================================
// CreateReview Tests
// ============================================================

func TestCreateReview(t *testing.T) {
	tests := []struct {
		name          string
		request       *pb.CreateReviewRequest
		setupMock     func(*domainmock.MockReviewRepository)
		expectedCode  codes.Code
		expectedError bool
		checkResponse func(*testing.T, *pb.CreateReviewResponse)
	}{
		{
			name: "successfully create review",
			request: &pb.CreateReviewRequest{
				Review: &pb.Review{
					UserId:     "user-123",
					EntityId:   "hotel-456",
					EntityType: pb.EntityType_ENTITY_TYPE_HOTEL,
					Rating:     4,
					Content:    "Great hotel!",
					Images:     []string{"img1.jpg", "img2.jpg"},
					Dimensions: map[string]uint32{"view": 4, "service": 5},
				},
			},
			setupMock: func(m *domainmock.MockReviewRepository) {
				m.On("Create", mock.Anything, mock.MatchedBy(func(r *domain.Review) bool {
					return r.UserID == "user-123" &&
						r.EntityID == "hotel-456" &&
						r.EntityType == domain.EntityTypeHotel &&
						r.Rating == 4
				})).Return(nil)
			},
			expectedError: false,
			checkResponse: func(t *testing.T, resp *pb.CreateReviewResponse) {
				assert.NotNil(t, resp.Review)
				assert.NotEmpty(t, resp.Review.Id)
				assert.Equal(t, "user-123", resp.Review.UserId)
			},
		},
		{
			name: "nil review",
			request: &pb.CreateReviewRequest{
				Review: nil,
			},
			setupMock:     func(m *domainmock.MockReviewRepository) {},
			expectedCode:  codes.InvalidArgument,
			expectedError: true,
		},
		{
			name: "empty user ID",
			request: &pb.CreateReviewRequest{
				Review: &pb.Review{
					UserId:     "",
					EntityId:   "hotel-456",
					EntityType: pb.EntityType_ENTITY_TYPE_HOTEL,
					Rating:     4,
				},
			},
			setupMock:     func(m *domainmock.MockReviewRepository) {},
			expectedCode:  codes.InvalidArgument,
			expectedError: true,
		},
		{
			name: "empty entity ID",
			request: &pb.CreateReviewRequest{
				Review: &pb.Review{
					UserId:     "user-123",
					EntityId:   "",
					EntityType: pb.EntityType_ENTITY_TYPE_HOTEL,
					Rating:     4,
				},
			},
			setupMock:     func(m *domainmock.MockReviewRepository) {},
			expectedCode:  codes.InvalidArgument,
			expectedError: true,
		},
		{
			name: "unspecified entity type",
			request: &pb.CreateReviewRequest{
				Review: &pb.Review{
					UserId:     "user-123",
					EntityId:   "hotel-456",
					EntityType: pb.EntityType_ENTITY_TYPE_UNSPECIFIED,
					Rating:     4,
				},
			},
			setupMock:     func(m *domainmock.MockReviewRepository) {},
			expectedCode:  codes.InvalidArgument,
			expectedError: true,
		},
		{
			name: "rating less than 1",
			request: &pb.CreateReviewRequest{
				Review: &pb.Review{
					UserId:     "user-123",
					EntityId:   "hotel-456",
					EntityType: pb.EntityType_ENTITY_TYPE_HOTEL,
					Rating:     0,
				},
			},
			setupMock:     func(m *domainmock.MockReviewRepository) {},
			expectedCode:  codes.InvalidArgument,
			expectedError: true,
		},
		{
			name: "rating greater than 5",
			request: &pb.CreateReviewRequest{
				Review: &pb.Review{
					UserId:     "user-123",
					EntityId:   "hotel-456",
					EntityType: pb.EntityType_ENTITY_TYPE_HOTEL,
					Rating:     6,
				},
			},
			setupMock:     func(m *domainmock.MockReviewRepository) {},
			expectedCode:  codes.InvalidArgument,
			expectedError: true,
		},
		{
			name: "database error",
			request: &pb.CreateReviewRequest{
				Review: &pb.Review{
					UserId:     "user-123",
					EntityId:   "hotel-456",
					EntityType: pb.EntityType_ENTITY_TYPE_HOTEL,
					Rating:     4,
				},
			},
			setupMock: func(m *domainmock.MockReviewRepository) {
				m.On("Create", mock.Anything, mock.Anything).Return(errors.New("database error"))
			},
			expectedCode:  codes.Internal,
			expectedError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			service, mockRepo := setupTest(t)
			tt.setupMock(mockRepo)

			resp, err := service.CreateReview(context.Background(), tt.request)

			if tt.expectedError {
				assertGRPCErrorCode(t, err, tt.expectedCode)
				assert.Nil(t, resp)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, resp)
				if tt.checkResponse != nil {
					tt.checkResponse(t, resp)
				}
			}

			mockRepo.AssertExpectations(t)
		})
	}
}

// ============================================================
// UpdateReview Tests
// ============================================================

func TestUpdateReview(t *testing.T) {
	now := time.Now()
	existingReview := &domain.Review{
		ID:         "review-123",
		UserID:     "user-123",
		EntityType: domain.EntityTypeHotel,
		EntityID:   "hotel-456",
		Rating:     3,
		Content:    "Original content",
		CreatedAt:  now.Add(-time.Hour),
		UpdatedAt:  now.Add(-time.Hour),
	}

	tests := []struct {
		name          string
		request       *pb.UpdateReviewRequest
		setupMock     func(*domainmock.MockReviewRepository)
		expectedCode  codes.Code
		expectedError bool
	}{
		{
			name: "successfully update review",
			request: &pb.UpdateReviewRequest{
				Review: &pb.Review{
					Id:      "review-123",
					Rating:  4,
					Content: "Updated content",
					Images:  []string{"new-img.jpg"},
				},
			},
			setupMock: func(m *domainmock.MockReviewRepository) {
				m.On("GetByID", mock.Anything, "review-123").Return(existingReview, nil)
				m.On("Update", mock.Anything, mock.MatchedBy(func(r *domain.Review) bool {
					return r.ID == "review-123" && r.Rating == 4
				})).Return(nil)
			},
			expectedError: false,
		},
		{
			name: "nil review",
			request: &pb.UpdateReviewRequest{
				Review: nil,
			},
			setupMock:     func(m *domainmock.MockReviewRepository) {},
			expectedCode:  codes.InvalidArgument,
			expectedError: true,
		},
		{
			name: "empty review ID",
			request: &pb.UpdateReviewRequest{
				Review: &pb.Review{
					Id:     "",
					Rating: 4,
				},
			},
			setupMock:     func(m *domainmock.MockReviewRepository) {},
			expectedCode:  codes.InvalidArgument,
			expectedError: true,
		},
		{
			name: "invalid rating - less than 1",
			request: &pb.UpdateReviewRequest{
				Review: &pb.Review{
					Id:     "review-123",
					Rating: 0,
				},
			},
			setupMock:     func(m *domainmock.MockReviewRepository) {},
			expectedCode:  codes.InvalidArgument,
			expectedError: true,
		},
		{
			name: "invalid rating - greater than 5",
			request: &pb.UpdateReviewRequest{
				Review: &pb.Review{
					Id:     "review-123",
					Rating: 6,
				},
			},
			setupMock:     func(m *domainmock.MockReviewRepository) {},
			expectedCode:  codes.InvalidArgument,
			expectedError: true,
		},
		{
			name: "review not found",
			request: &pb.UpdateReviewRequest{
				Review: &pb.Review{
					Id:     "non-existent",
					Rating: 4,
				},
			},
			setupMock: func(m *domainmock.MockReviewRepository) {
				m.On("GetByID", mock.Anything, "non-existent").Return(nil, nil)
			},
			expectedCode:  codes.NotFound,
			expectedError: true,
		},
		{
			name: "database error on get",
			request: &pb.UpdateReviewRequest{
				Review: &pb.Review{
					Id:     "review-123",
					Rating: 4,
				},
			},
			setupMock: func(m *domainmock.MockReviewRepository) {
				m.On("GetByID", mock.Anything, "review-123").Return(nil, errors.New("database error"))
			},
			expectedCode:  codes.Internal,
			expectedError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			service, mockRepo := setupTest(t)
			tt.setupMock(mockRepo)

			resp, err := service.UpdateReview(context.Background(), tt.request)

			if tt.expectedError {
				assertGRPCErrorCode(t, err, tt.expectedCode)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, resp)
				assert.NotNil(t, resp.Review)
			}

			mockRepo.AssertExpectations(t)
		})
	}
}

// ============================================================
// DeleteReview Tests
// ============================================================

func TestDeleteReview(t *testing.T) {
	tests := []struct {
		name          string
		request       *pb.DeleteReviewRequest
		setupMock     func(*domainmock.MockReviewRepository)
		expectedCode  codes.Code
		expectedError bool
	}{
		{
			name: "successfully delete review",
			request: &pb.DeleteReviewRequest{
				Id: "review-123",
			},
			setupMock: func(m *domainmock.MockReviewRepository) {
				m.On("Delete", mock.Anything, "review-123").Return(nil)
			},
			expectedError: false,
		},
		{
			name: "empty review ID",
			request: &pb.DeleteReviewRequest{
				Id: "",
			},
			setupMock:     func(m *domainmock.MockReviewRepository) {},
			expectedCode:  codes.InvalidArgument,
			expectedError: true,
		},
		{
			name: "review not found",
			request: &pb.DeleteReviewRequest{
				Id: "non-existent",
			},
			setupMock: func(m *domainmock.MockReviewRepository) {
				m.On("Delete", mock.Anything, "non-existent").Return(domain.ErrReviewNotFound)
			},
			expectedCode:  codes.NotFound,
			expectedError: true,
		},
		{
			name: "database error",
			request: &pb.DeleteReviewRequest{
				Id: "review-123",
			},
			setupMock: func(m *domainmock.MockReviewRepository) {
				m.On("Delete", mock.Anything, "review-123").Return(errors.New("database error"))
			},
			expectedCode:  codes.Internal,
			expectedError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			service, mockRepo := setupTest(t)
			tt.setupMock(mockRepo)

			resp, err := service.DeleteReview(context.Background(), tt.request)

			if tt.expectedError {
				assertGRPCErrorCode(t, err, tt.expectedCode)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, resp)
			}

			mockRepo.AssertExpectations(t)
		})
	}
}

// ============================================================
// ListReviewsByEntity Tests
// ============================================================

func TestListReviewsByEntity(t *testing.T) {
	now := time.Now()

	userReview := &domain.Review{
		ID:         "user-review-1",
		UserID:     "current-user",
		EntityType: domain.EntityTypeHotel,
		EntityID:   "hotel-123",
		Rating:     4,
		Content:    "My review",
		CreatedAt:  now,
		UpdatedAt:  now,
	}

	otherReviews := []domain.Review{
		{
			ID:         "review-1",
			UserID:     "other-user-1",
			EntityType: domain.EntityTypeHotel,
			EntityID:   "hotel-123",
			Rating:     4,
			Content:    "Great!",
			CreatedAt:  now.Add(-time.Hour),
			UpdatedAt:  now.Add(-time.Hour),
		},
		{
			ID:         "review-2",
			UserID:     "other-user-2",
			EntityType: domain.EntityTypeHotel,
			EntityID:   "hotel-123",
			Rating:     3,
			Content:    "Good",
			CreatedAt:  now.Add(-2 * time.Hour),
			UpdatedAt:  now.Add(-2 * time.Hour),
		},
	}

	tests := []struct {
		name              string
		ctx               context.Context
		request           *pb.ListReviewsByEntityRequest
		setupMock         func(*domainmock.MockReviewRepository)
		expectedCode      codes.Code
		expectedError     bool
		expectedLength    int
		expectUserReview  bool
		expectedNextToken string
	}{
		{
			name: "first page with logged in user - returns user_review separately",
			ctx:  contextWithUserID("current-user"),
			request: &pb.ListReviewsByEntityRequest{
				EntityId:   "hotel-123",
				EntityType: pb.EntityType_ENTITY_TYPE_HOTEL,
				PageSize:   10,
			},
			setupMock: func(m *domainmock.MockReviewRepository) {
				m.On("GetByEntityAndUser", mock.Anything, domain.EntityTypeHotel, "hotel-123", "current-user").
					Return(userReview, nil)
				m.On("ListByEntity", mock.Anything, mock.MatchedBy(func(opts domain.ListReviewsOptions) bool {
					return opts.ExcludeUserID == "current-user"
				})).Return(&domain.ListReviewsResult{
					Reviews:       otherReviews,
					NextPageToken: "next-token",
				}, nil)
			},
			expectedError:     false,
			expectedLength:    2,
			expectUserReview:  true,
			expectedNextToken: "next-token",
		},
		{
			name: "first page with logged in user - user has no review",
			ctx:  contextWithUserID("new-user"),
			request: &pb.ListReviewsByEntityRequest{
				EntityId:   "hotel-123",
				EntityType: pb.EntityType_ENTITY_TYPE_HOTEL,
				PageSize:   10,
			},
			setupMock: func(m *domainmock.MockReviewRepository) {
				m.On("GetByEntityAndUser", mock.Anything, domain.EntityTypeHotel, "hotel-123", "new-user").
					Return(nil, nil)
				m.On("ListByEntity", mock.Anything, mock.MatchedBy(func(opts domain.ListReviewsOptions) bool {
					return opts.ExcludeUserID == "new-user"
				})).Return(&domain.ListReviewsResult{
					Reviews: otherReviews,
				}, nil)
			},
			expectedError:    false,
			expectedLength:   2,
			expectUserReview: false,
		},
		{
			name: "second page with logged in user - no user_review",
			ctx:  contextWithUserID("current-user"),
			request: &pb.ListReviewsByEntityRequest{
				EntityId:   "hotel-123",
				EntityType: pb.EntityType_ENTITY_TYPE_HOTEL,
				PageSize:   10,
				PageToken:  "some-token",
			},
			setupMock: func(m *domainmock.MockReviewRepository) {
				// Should NOT call GetByEntityAndUser on non-first page
				m.On("ListByEntity", mock.Anything, mock.MatchedBy(func(opts domain.ListReviewsOptions) bool {
					return opts.PageToken == "some-token" && opts.ExcludeUserID == "current-user"
				})).Return(&domain.ListReviewsResult{
					Reviews: otherReviews,
				}, nil)
			},
			expectedError:    false,
			expectedLength:   2,
			expectUserReview: false, // No user_review on non-first page
		},
		{
			name: "not logged in - normal list without user_review",
			ctx:  context.Background(),
			request: &pb.ListReviewsByEntityRequest{
				EntityId:   "hotel-123",
				EntityType: pb.EntityType_ENTITY_TYPE_HOTEL,
				PageSize:   10,
			},
			setupMock: func(m *domainmock.MockReviewRepository) {
				// Should NOT call GetByEntityAndUser when not logged in
				m.On("ListByEntity", mock.Anything, mock.MatchedBy(func(opts domain.ListReviewsOptions) bool {
					return opts.ExcludeUserID == "" // No exclusion when not logged in
				})).Return(&domain.ListReviewsResult{
					Reviews: otherReviews,
				}, nil)
			},
			expectedError:    false,
			expectedLength:   2,
			expectUserReview: false,
		},
		{
			name: "empty entity ID",
			ctx:  context.Background(),
			request: &pb.ListReviewsByEntityRequest{
				EntityId:   "",
				EntityType: pb.EntityType_ENTITY_TYPE_HOTEL,
			},
			setupMock:     func(m *domainmock.MockReviewRepository) {},
			expectedCode:  codes.InvalidArgument,
			expectedError: true,
		},
		{
			name: "unspecified entity type",
			ctx:  context.Background(),
			request: &pb.ListReviewsByEntityRequest{
				EntityId:   "hotel-123",
				EntityType: pb.EntityType_ENTITY_TYPE_UNSPECIFIED,
			},
			setupMock:     func(m *domainmock.MockReviewRepository) {},
			expectedCode:  codes.InvalidArgument,
			expectedError: true,
		},
		{
			name: "invalid page token",
			ctx:  context.Background(),
			request: &pb.ListReviewsByEntityRequest{
				EntityId:   "hotel-123",
				EntityType: pb.EntityType_ENTITY_TYPE_HOTEL,
				PageToken:  "invalid-token",
			},
			setupMock: func(m *domainmock.MockReviewRepository) {
				m.On("ListByEntity", mock.Anything, mock.Anything).Return(nil, domain.ErrInvalidPageToken)
			},
			expectedCode:  codes.InvalidArgument,
			expectedError: true,
		},
		{
			name: "database error",
			ctx:  context.Background(),
			request: &pb.ListReviewsByEntityRequest{
				EntityId:   "hotel-123",
				EntityType: pb.EntityType_ENTITY_TYPE_HOTEL,
				PageSize:   10,
			},
			setupMock: func(m *domainmock.MockReviewRepository) {
				m.On("ListByEntity", mock.Anything, mock.Anything).Return(nil, errors.New("database error"))
			},
			expectedCode:  codes.Internal,
			expectedError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			service, mockRepo := setupTest(t)
			tt.setupMock(mockRepo)

			resp, err := service.ListReviewsByEntity(tt.ctx, tt.request)

			if tt.expectedError {
				assertGRPCErrorCode(t, err, tt.expectedCode)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, resp)
				assert.Len(t, resp.Reviews, tt.expectedLength)

				if tt.expectUserReview {
					assert.NotNil(t, resp.UserReview)
					assert.Equal(t, "user-review-1", resp.UserReview.Id)
				} else {
					assert.Nil(t, resp.UserReview)
				}

				if tt.expectedNextToken != "" {
					assert.Equal(t, tt.expectedNextToken, resp.NextPageToken)
				}
			}

			mockRepo.AssertExpectations(t)
		})
	}
}

// ============================================================
// domainToProto Tests
// ============================================================

func TestDomainToProto(t *testing.T) {
	now := time.Now()
	review := &domain.Review{
		ID:         "review-123",
		UserID:     "user-456",
		EntityType: domain.EntityTypeHotel,
		EntityID:   "hotel-789",
		Rating:     4,
		Content:    "Great experience!",
		Images:     []string{"img1.jpg", "img2.jpg"},
		Dimensions: map[string]uint32{"view": 4, "service": 5},
		CreatedAt:  now,
		UpdatedAt:  now,
	}

	proto := domainToProto(review)

	assert.Equal(t, review.ID, proto.Id)
	assert.Equal(t, review.UserID, proto.UserId)
	assert.Equal(t, pb.EntityType(review.EntityType), proto.EntityType)
	assert.Equal(t, review.EntityID, proto.EntityId)
	assert.Equal(t, review.Rating, proto.Rating)
	assert.Equal(t, review.Content, proto.Content)
	assert.Equal(t, review.Images, proto.Images)
	assert.Equal(t, review.Dimensions, proto.Dimensions)
	assert.NotNil(t, proto.CreatedAt)
	assert.NotNil(t, proto.UpdatedAt)
}

// ============================================================
// Benchmark Tests
// ============================================================

func BenchmarkCreateReview(b *testing.B) {
	mockRepo := domainmock.NewMockReviewRepository()
	mockRepo.On("Create", mock.Anything, mock.Anything).Return(nil)
	service := NewReviewService(mockRepo)

	req := &pb.CreateReviewRequest{
		Review: &pb.Review{
			UserId:     "user-123",
			EntityId:   "hotel-456",
			EntityType: pb.EntityType_ENTITY_TYPE_HOTEL,
			Rating:     4,
			Content:    "Great hotel!",
		},
	}

	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = service.CreateReview(ctx, req)
	}
}

func BenchmarkDomainToProto(b *testing.B) {
	now := time.Now()
	review := &domain.Review{
		ID:         "review-123",
		UserID:     "user-456",
		EntityType: domain.EntityTypeHotel,
		EntityID:   "hotel-789",
		Rating:     4,
		Content:    "Great experience!",
		Images:     []string{"img1.jpg", "img2.jpg"},
		Dimensions: map[string]uint32{"view": 4, "service": 5},
		CreatedAt:  now,
		UpdatedAt:  now,
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = domainToProto(review)
	}
}
