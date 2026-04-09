package mock

import (
	"context"

	"github.com/stretchr/testify/mock"

	"trip-review-service/internal/domain"
)

// MockReviewRepository is a mock implementation of the ReviewRepository interface
type MockReviewRepository struct {
	mock.Mock
}

// NewMockReviewRepository creates a new MockReviewRepository
func NewMockReviewRepository() *MockReviewRepository {
	return &MockReviewRepository{}
}

// Create mock implementation
func (m *MockReviewRepository) Create(ctx context.Context, review *domain.Review) error {
	args := m.Called(ctx, review)
	return args.Error(0)
}

// GetByID mock implementation
func (m *MockReviewRepository) GetByID(ctx context.Context, id string) (*domain.Review, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Review), args.Error(1)
}

// GetByEntityAndUser mock implementation
func (m *MockReviewRepository) GetByEntityAndUser(ctx context.Context, entityType domain.EntityType, entityID, userID string) (*domain.Review, error) {
	args := m.Called(ctx, entityType, entityID, userID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Review), args.Error(1)
}

// Update mock implementation
func (m *MockReviewRepository) Update(ctx context.Context, review *domain.Review) error {
	args := m.Called(ctx, review)
	return args.Error(0)
}

// Delete mock implementation
func (m *MockReviewRepository) Delete(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

// ListByEntity mock implementation
func (m *MockReviewRepository) ListByEntity(ctx context.Context, opts domain.ListReviewsOptions) (*domain.ListReviewsResult, error) {
	args := m.Called(ctx, opts)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.ListReviewsResult), args.Error(1)
}

// Ensure MockReviewRepository implements the domain.ReviewRepository interface
var _ domain.ReviewRepository = (*MockReviewRepository)(nil)
