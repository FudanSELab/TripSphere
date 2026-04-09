//go:build integration

package repository

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"trip-review-service/internal/domain"
	"trip-review-service/internal/repository/testutil"
)

// ============================================================
// TestMain - Setup shared MongoDB container for all tests
// ============================================================

func TestMain(m *testing.M) {
	// Start shared MongoDB container
	cleanup, err := testutil.SetupSharedMongoDB()
	if err != nil {
		panic("failed to setup MongoDB: " + err.Error())
	}

	// Run all tests
	code := m.Run()

	// Cleanup container
	cleanup()

	os.Exit(code)
}

// ============================================================
// Integration Test Setup
// ============================================================

// setupIntegrationTest creates a ReviewRepo connected to the shared MongoDB container.
// Each test gets its own database for isolation.
func setupIntegrationTest(t *testing.T) (*ReviewRepo, context.Context) {
	t.Helper()

	ctx := context.Background()

	// Get shared container
	container := testutil.GetSharedMongoDB()
	require.NotNil(t, container, "shared MongoDB container not initialized - did TestMain run?")

	// Get unique database for this test
	db := container.GetTestDatabase(t)

	// Create repository
	repo := NewReviewRepo(db)

	// Create indexes
	err := repo.EnsureIndexes(ctx)
	require.NoError(t, err, "failed to create indexes")

	return repo, ctx
}

// newTestReviewWithID creates a test review with specified ID
func newTestReviewWithID(id, userID, entityID string) *domain.Review {
	now := time.Now()
	return &domain.Review{
		ID:         id,
		UserID:     userID,
		EntityType: domain.EntityTypeHotel,
		EntityID:   entityID,
		Rating:     4,
		Content:    "Great hotel!",
		Images:     []string{"img1.jpg", "img2.jpg"},
		Dimensions: map[string]uint32{"view": 4, "service": 5},
		CreatedAt:  now,
		UpdatedAt:  now,
	}
}

// ============================================================
// Create Tests
// ============================================================

func TestIntegration_Create(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	review := newTestReviewWithID(uuid.NewString(), "user-123", "hotel-456")

	err := repo.Create(ctx, review)
	require.NoError(t, err)

	// Verify the review was created
	got, err := repo.GetByID(ctx, review.ID)
	require.NoError(t, err)
	require.NotNil(t, got)
	assert.Equal(t, review.ID, got.ID)
	assert.Equal(t, review.UserID, got.UserID)
	assert.Equal(t, review.Rating, got.Rating)
	assert.Equal(t, review.Content, got.Content)
}

func TestIntegration_Create_DuplicateEntityUser(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	// Create first review
	review1 := newTestReviewWithID(uuid.NewString(), "user-123", "hotel-456")
	err := repo.Create(ctx, review1)
	require.NoError(t, err)

	// Try to create another review for the same entity by the same user
	review2 := newTestReviewWithID(uuid.NewString(), "user-123", "hotel-456")
	err = repo.Create(ctx, review2)

	// Should fail due to unique index
	assert.Error(t, err)
}

// ============================================================
// GetByID Tests
// ============================================================

func TestIntegration_GetByID_Found(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	review := newTestReviewWithID(uuid.NewString(), "user-123", "hotel-456")
	err := repo.Create(ctx, review)
	require.NoError(t, err)

	got, err := repo.GetByID(ctx, review.ID)
	require.NoError(t, err)
	require.NotNil(t, got)
	assert.Equal(t, review.ID, got.ID)
}

func TestIntegration_GetByID_NotFound(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	got, err := repo.GetByID(ctx, "non-existent-id")
	require.NoError(t, err)
	assert.Nil(t, got)
}

// ============================================================
// GetByEntityAndUser Tests
// ============================================================

func TestIntegration_GetByEntityAndUser_Found(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	review := newTestReviewWithID(uuid.NewString(), "user-123", "hotel-456")
	err := repo.Create(ctx, review)
	require.NoError(t, err)

	got, err := repo.GetByEntityAndUser(ctx, domain.EntityTypeHotel, "hotel-456", "user-123")
	require.NoError(t, err)
	require.NotNil(t, got)
	assert.Equal(t, review.ID, got.ID)
}

func TestIntegration_GetByEntityAndUser_NotFound(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	got, err := repo.GetByEntityAndUser(ctx, domain.EntityTypeHotel, "hotel-456", "user-999")
	require.NoError(t, err)
	assert.Nil(t, got)
}

// ============================================================
// Update Tests
// ============================================================

func TestIntegration_Update(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	review := newTestReviewWithID(uuid.NewString(), "user-123", "hotel-456")
	err := repo.Create(ctx, review)
	require.NoError(t, err)

	// Update the review
	review.Rating = 4
	review.Content = "Updated content"
	review.UpdatedAt = time.Now()
	err = repo.Update(ctx, review)
	require.NoError(t, err)

	// Verify the update
	got, err := repo.GetByID(ctx, review.ID)
	require.NoError(t, err)
	require.NotNil(t, got)
	assert.Equal(t, int32(4), got.Rating)
	assert.Equal(t, "Updated content", got.Content)
}

func TestIntegration_Update_NotFound(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	review := newTestReviewWithID("non-existent-id", "user-123", "hotel-456")
	err := repo.Update(ctx, review)
	assert.ErrorIs(t, err, domain.ErrReviewNotFound)
}

// ============================================================
// Delete Tests
// ============================================================

func TestIntegration_Delete(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	review := newTestReviewWithID(uuid.NewString(), "user-123", "hotel-456")
	err := repo.Create(ctx, review)
	require.NoError(t, err)

	err = repo.Delete(ctx, review.ID)
	require.NoError(t, err)

	// Verify deletion
	got, err := repo.GetByID(ctx, review.ID)
	require.NoError(t, err)
	assert.Nil(t, got)
}

func TestIntegration_Delete_NotFound(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	err := repo.Delete(ctx, "non-existent-id")
	assert.ErrorIs(t, err, domain.ErrReviewNotFound)
}

// ============================================================
// ListByEntity Tests
// ============================================================

func TestIntegration_ListByEntity_Empty(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	result, err := repo.ListByEntity(ctx, domain.ListReviewsOptions{
		EntityType: domain.EntityTypeHotel,
		EntityID:   "hotel-123",
		PageSize:   10,
	})
	require.NoError(t, err)
	assert.Empty(t, result.Reviews)
	assert.Empty(t, result.NextPageToken)
}

func TestIntegration_ListByEntity_WithReviews(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	// Create multiple reviews
	for i := 0; i < 5; i++ {
		review := newTestReviewWithID(uuid.NewString(), "user-"+uuid.NewString(), "hotel-123")
		review.CreatedAt = time.Now().Add(time.Duration(i) * time.Minute)
		review.UpdatedAt = review.CreatedAt
		err := repo.Create(ctx, review)
		require.NoError(t, err)
	}

	result, err := repo.ListByEntity(ctx, domain.ListReviewsOptions{
		EntityType: domain.EntityTypeHotel,
		EntityID:   "hotel-123",
		PageSize:   10,
	})
	require.NoError(t, err)
	assert.Len(t, result.Reviews, 5)
	assert.Empty(t, result.NextPageToken) // No more pages
}

func TestIntegration_ListByEntity_Pagination(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	// Create 15 reviews
	for i := 0; i < 15; i++ {
		review := newTestReviewWithID(uuid.NewString(), "user-"+uuid.NewString(), "hotel-123")
		review.CreatedAt = time.Now().Add(time.Duration(i) * time.Minute)
		review.UpdatedAt = review.CreatedAt
		err := repo.Create(ctx, review)
		require.NoError(t, err)
	}

	// First page
	result, err := repo.ListByEntity(ctx, domain.ListReviewsOptions{
		EntityType: domain.EntityTypeHotel,
		EntityID:   "hotel-123",
		PageSize:   10,
	})
	require.NoError(t, err)
	assert.Len(t, result.Reviews, 10)
	assert.NotEmpty(t, result.NextPageToken)

	// Second page
	result2, err := repo.ListByEntity(ctx, domain.ListReviewsOptions{
		EntityType: domain.EntityTypeHotel,
		EntityID:   "hotel-123",
		PageSize:   10,
		PageToken:  result.NextPageToken,
	})
	require.NoError(t, err)
	assert.Len(t, result2.Reviews, 5)
	assert.Empty(t, result2.NextPageToken) // No more pages
}

func TestIntegration_ListByEntity_ExcludeUser(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	// Create reviews from different users
	userToExclude := "user-exclude"
	for i := 0; i < 3; i++ {
		review := newTestReviewWithID(uuid.NewString(), "user-"+uuid.NewString(), "hotel-123")
		err := repo.Create(ctx, review)
		require.NoError(t, err)
	}

	// Create a review from the user to exclude
	excludedReview := newTestReviewWithID(uuid.NewString(), userToExclude, "hotel-123")
	err := repo.Create(ctx, excludedReview)
	require.NoError(t, err)

	// List with exclusion
	result, err := repo.ListByEntity(ctx, domain.ListReviewsOptions{
		EntityType:    domain.EntityTypeHotel,
		EntityID:      "hotel-123",
		PageSize:      10,
		ExcludeUserID: userToExclude,
	})
	require.NoError(t, err)
	assert.Len(t, result.Reviews, 3)

	// Verify excluded user's review is not in the result
	for _, r := range result.Reviews {
		assert.NotEqual(t, userToExclude, r.UserID)
	}
}

func TestIntegration_ListByEntity_SortByCreatedAt(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	// Create reviews with different timestamps
	var reviewIDs []string
	baseTime := time.Now()
	for i := 0; i < 5; i++ {
		review := newTestReviewWithID(uuid.NewString(), "user-"+uuid.NewString(), "hotel-123")
		review.CreatedAt = baseTime.Add(time.Duration(i) * time.Minute)
		review.UpdatedAt = review.CreatedAt
		err := repo.Create(ctx, review)
		require.NoError(t, err)
		reviewIDs = append(reviewIDs, review.ID)
	}

	// List with ascending order
	result, err := repo.ListByEntity(ctx, domain.ListReviewsOptions{
		EntityType: domain.EntityTypeHotel,
		EntityID:   "hotel-123",
		PageSize:   10,
		OrderBy:    "created_at",
	})
	require.NoError(t, err)
	assert.Len(t, result.Reviews, 5)

	// Verify ascending order (oldest first)
	for i := 1; i < len(result.Reviews); i++ {
		assert.True(t, result.Reviews[i].CreatedAt.After(result.Reviews[i-1].CreatedAt) ||
			result.Reviews[i].CreatedAt.Equal(result.Reviews[i-1].CreatedAt))
	}

	// List with descending order
	result, err = repo.ListByEntity(ctx, domain.ListReviewsOptions{
		EntityType: domain.EntityTypeHotel,
		EntityID:   "hotel-123",
		PageSize:   10,
		OrderBy:    "created_at desc",
	})
	require.NoError(t, err)
	assert.Len(t, result.Reviews, 5)

	// Verify descending order (newest first)
	for i := 1; i < len(result.Reviews); i++ {
		assert.True(t, result.Reviews[i].CreatedAt.Before(result.Reviews[i-1].CreatedAt) ||
			result.Reviews[i].CreatedAt.Equal(result.Reviews[i-1].CreatedAt))
	}
}

func TestIntegration_ListByEntity_InvalidPageToken(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	_, err := repo.ListByEntity(ctx, domain.ListReviewsOptions{
		EntityType: domain.EntityTypeHotel,
		EntityID:   "hotel-123",
		PageSize:   10,
		PageToken:  "invalid-token",
	})
	assert.ErrorIs(t, err, domain.ErrInvalidPageToken)
}

// ============================================================
// EnsureIndexes Tests
// ============================================================

func TestIntegration_EnsureIndexes(t *testing.T) {
	repo, ctx := setupIntegrationTest(t)

	// Indexes should already be created in setupIntegrationTest
	// Creating them again should be idempotent
	err := repo.EnsureIndexes(ctx)
	require.NoError(t, err)
}
