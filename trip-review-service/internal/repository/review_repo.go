package repository

import (
	"context"
	"encoding/base64"
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"

	"trip-review-service/internal/domain"
)

const (
	// reviewCollection is the MongoDB collection name for reviews
	reviewCollection = "reviews"

	// cursorSeparator is the delimiter used in cursor token encoding
	cursorSeparator = "|"

	// defaultPageSize is the default number of items per page
	defaultPageSize = 10

	// maxPageSize is the maximum allowed page size
	maxPageSize = 100
)

// ReviewRepo implements domain.ReviewRepository using MongoDB
type ReviewRepo struct {
	collection *mongo.Collection
}

// NewReviewRepo creates a new ReviewRepo
func NewReviewRepo(db *mongo.Database) *ReviewRepo {
	return &ReviewRepo{
		collection: db.Collection(reviewCollection),
	}
}

// Ensure ReviewRepo implements domain.ReviewRepository
var _ domain.ReviewRepository = (*ReviewRepo)(nil)

// Create inserts a new review into MongoDB
func (r *ReviewRepo) Create(ctx context.Context, review *domain.Review) error {
	_, err := r.collection.InsertOne(ctx, review)
	if err != nil {
		return fmt.Errorf("failed to insert review: %w", err)
	}
	return nil
}

// GetByID retrieves a review by its ID
func (r *ReviewRepo) GetByID(ctx context.Context, id string) (*domain.Review, error) {
	var review domain.Review
	err := r.collection.FindOne(ctx, bson.M{"_id": id}).Decode(&review)
	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to get review: %w", err)
	}
	return &review, nil
}

// GetByEntityAndUser retrieves a user's review for a specific entity.
// Returns nil if the user has not reviewed the entity.
func (r *ReviewRepo) GetByEntityAndUser(ctx context.Context, entityType domain.EntityType, entityID, userID string) (*domain.Review, error) {
	filter := bson.M{
		"entity_type": entityType,
		"entity_id":   entityID,
		"user_id":     userID,
	}

	var review domain.Review
	err := r.collection.FindOne(ctx, filter).Decode(&review)
	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to get user review: %w", err)
	}
	return &review, nil
}

// Update updates an existing review
func (r *ReviewRepo) Update(ctx context.Context, review *domain.Review) error {
	update := bson.M{
		"$set": bson.M{
			"rating":     review.Rating,
			"content":    review.Content,
			"images":     review.Images,
			"dimensions": review.Dimensions,
			"updated_at": review.UpdatedAt,
		},
	}

	result, err := r.collection.UpdateOne(ctx, bson.M{"_id": review.ID}, update)
	if err != nil {
		return fmt.Errorf("failed to update review: %w", err)
	}

	if result.MatchedCount == 0 {
		return domain.ErrReviewNotFound
	}

	return nil
}

// Delete removes a review by its ID
func (r *ReviewRepo) Delete(ctx context.Context, id string) error {
	result, err := r.collection.DeleteOne(ctx, bson.M{"_id": id})
	if err != nil {
		return fmt.Errorf("failed to delete review: %w", err)
	}

	if result.DeletedCount == 0 {
		return domain.ErrReviewNotFound
	}

	return nil
}

// ListByEntity retrieves reviews for an entity with cursor-based pagination.
// If ExcludeUserID is set, reviews from that user will be excluded from the result.
func (r *ReviewRepo) ListByEntity(ctx context.Context, opts domain.ListReviewsOptions) (*domain.ListReviewsResult, error) {
	// Normalize page size
	pageSize := opts.PageSize
	if pageSize <= 0 {
		pageSize = defaultPageSize
	}
	if pageSize > maxPageSize {
		pageSize = maxPageSize
	}

	// Parse order_by field: default to "updated_at desc"
	sortField, sortOrder := parseSortOptions(opts.OrderBy)

	// Build filter
	filter := bson.M{
		"entity_type": opts.EntityType,
		"entity_id":   opts.EntityID,
	}

	// Exclude specific user's reviews (for deduplication when user_review is shown separately)
	if opts.ExcludeUserID != "" {
		filter["user_id"] = bson.M{"$ne": opts.ExcludeUserID}
	}

	// Apply cursor condition if page_token is provided
	if opts.PageToken != "" {
		cursorTime, cursorID, err := decodeCursorToken(opts.PageToken)
		if err != nil {
			return nil, domain.ErrInvalidPageToken
		}

		// Cursor-based pagination filter:
		// For descending order: (sortField < cursorTime) OR (sortField == cursorTime AND _id < cursorID)
		// For ascending order: (sortField > cursorTime) OR (sortField == cursorTime AND _id > cursorID)
		var compareOp, idCompareOp string
		if sortOrder == -1 {
			compareOp = "$lt"
			idCompareOp = "$lt"
		} else {
			compareOp = "$gt"
			idCompareOp = "$gt"
		}

		filter["$or"] = []bson.M{
			{sortField: bson.M{compareOp: cursorTime}},
			{
				sortField: cursorTime,
				"_id":     bson.M{idCompareOp: cursorID},
			},
		}
	}

	// Build sort options: primary sort field + _id as tiebreaker
	sortOpts := bson.D{
		{Key: sortField, Value: sortOrder},
		{Key: "_id", Value: sortOrder},
	}

	// Fetch one extra item to determine if there's a next page
	findOpts := options.Find().
		SetSort(sortOpts).
		SetLimit(int64(pageSize + 1))

	cursor, err := r.collection.Find(ctx, filter, findOpts)
	if err != nil {
		return nil, fmt.Errorf("failed to query reviews: %w", err)
	}
	defer cursor.Close(ctx)

	var reviews []domain.Review
	if err := cursor.All(ctx, &reviews); err != nil {
		return nil, fmt.Errorf("failed to decode reviews: %w", err)
	}

	// Determine next page token
	var nextPageToken string
	if len(reviews) > int(pageSize) {
		// Remove the extra item and generate next cursor
		reviews = reviews[:pageSize]
		lastReview := reviews[len(reviews)-1]

		// Encode cursor based on sort field
		var cursorTime time.Time
		if sortField == "created_at" {
			cursorTime = lastReview.CreatedAt
		} else {
			cursorTime = lastReview.UpdatedAt
		}
		nextPageToken = encodeCursorToken(cursorTime, lastReview.ID)
	}

	return &domain.ListReviewsResult{
		Reviews:       reviews,
		NextPageToken: nextPageToken,
	}, nil
}

// parseSortOptions parses the order_by string and returns the sort field and order.
// Format follows Google AIP-132: "field_name" for ascending, "field_name desc" for descending.
// Default: "updated_at desc" (latest reviews first)
func parseSortOptions(orderBy string) (field string, order int) {
	// Default values
	field = "updated_at"
	order = -1 // descending

	if orderBy == "" {
		return
	}

	parts := strings.Fields(orderBy)
	if len(parts) >= 1 {
		// Validate field name
		switch parts[0] {
		case "created_at", "updated_at":
			field = parts[0]
		default:
			// Invalid field, use default
			return "updated_at", -1
		}
	}

	if len(parts) >= 2 && strings.ToLower(parts[1]) == "desc" {
		order = -1
	} else {
		order = 1 // ascending by default if field is specified without "desc"
	}

	return
}

// encodeCursorToken encodes cursor values into a Base64 page token.
// Format: "epochMillis|id" encoded in URL-safe Base64 without padding.
// This follows the same pattern as the Java implementation in ItineraryServiceImpl.
func encodeCursorToken(t time.Time, id string) string {
	raw := strconv.FormatInt(t.UnixMilli(), 10) + cursorSeparator + id
	return base64.URLEncoding.WithPadding(base64.NoPadding).EncodeToString([]byte(raw))
}

// decodeCursorToken decodes a Base64 page token into cursor values.
// Returns the timestamp and ID extracted from the token.
func decodeCursorToken(token string) (time.Time, string, error) {
	decoded, err := base64.URLEncoding.WithPadding(base64.NoPadding).DecodeString(token)
	if err != nil {
		return time.Time{}, "", fmt.Errorf("failed to decode token: %w", err)
	}

	parts := strings.SplitN(string(decoded), cursorSeparator, 2)
	if len(parts) != 2 {
		return time.Time{}, "", fmt.Errorf("invalid token format")
	}

	epochMillis, err := strconv.ParseInt(parts[0], 10, 64)
	if err != nil {
		return time.Time{}, "", fmt.Errorf("invalid timestamp in token: %w", err)
	}

	return time.UnixMilli(epochMillis), parts[1], nil
}

// EnsureIndexes creates the necessary indexes for the reviews collection
func (r *ReviewRepo) EnsureIndexes(ctx context.Context) error {
	indexes := []mongo.IndexModel{
		{
			Keys: bson.D{
				{Key: "entity_type", Value: 1},
				{Key: "entity_id", Value: 1},
				{Key: "updated_at", Value: -1},
				{Key: "_id", Value: -1},
			},
			Options: options.Index().SetName("idx_entity_updated"),
		},
		{
			Keys: bson.D{
				{Key: "entity_type", Value: 1},
				{Key: "entity_id", Value: 1},
				{Key: "created_at", Value: -1},
				{Key: "_id", Value: -1},
			},
			Options: options.Index().SetName("idx_entity_created"),
		},
		{
			Keys: bson.D{
				{Key: "user_id", Value: 1},
			},
			Options: options.Index().SetName("idx_user_id"),
		},
		// Index for looking up a user's review for a specific entity
		{
			Keys: bson.D{
				{Key: "entity_type", Value: 1},
				{Key: "entity_id", Value: 1},
				{Key: "user_id", Value: 1},
			},
			Options: options.Index().SetName("idx_entity_user").SetUnique(true),
		},
	}

	_, err := r.collection.Indexes().CreateMany(ctx, indexes)
	if err != nil {
		return fmt.Errorf("failed to create indexes: %w", err)
	}

	return nil
}
