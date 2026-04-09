package domain

import "errors"

// Domain layer error definitions
var (
	// ErrReviewNotFound indicates the requested review does not exist
	ErrReviewNotFound = errors.New("review not found")

	// ErrInvalidRating indicates the rating value is invalid (must be between 1 and 5)
	ErrInvalidRating = errors.New("rating must be between 1 and 5")

	// ErrInvalidPageToken indicates the pagination token format is invalid
	ErrInvalidPageToken = errors.New("invalid page token format")

	// ErrEmptyUserID indicates the user ID is empty
	ErrEmptyUserID = errors.New("user_id is required")

	// ErrEmptyEntityID indicates the entity ID is empty
	ErrEmptyEntityID = errors.New("entity_id is required")

	// ErrInvalidEntityType indicates the entity type is invalid
	ErrInvalidEntityType = errors.New("entity_type is invalid")

	// ErrEmptyReviewID indicates the review ID is empty
	ErrEmptyReviewID = errors.New("review id is required")
)

// IsNotFoundError checks if the error is a "not found" type
func IsNotFoundError(err error) bool {
	return errors.Is(err, ErrReviewNotFound)
}
