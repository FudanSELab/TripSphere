package model

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
	"time"
	"trip-review-service/internal/domain"
)

type ReviewModel struct {
	ID         string `gorm:"primaryKey;column:id;type:varchar(64)"`
	UserID     string `gorm:"column:uid;type:varchar(64);not null"`
	TargetType string `gorm:"column:target_type;type:varchar(20);not null"`
	TargetID   string `gorm:"column:target_id;type:varchar(64);not null"`
	Rating     int    `gorm:"column:rating;type:tinyint;not null"`

	// GORM 默认处理 string 为 utf8，但在建表时需确保 DB 层面是 utf8mb4
	Text string `gorm:"column:text;type:text"`

	// 自定义类型处理 []string <-> JSON
	Images StringArray `gorm:"column:images;type:json"`

	CreatedAt time.Time `gorm:"autoCreateTime"`
	UpdatedAt time.Time `gorm:"autoUpdateTime"`
}

func (reviewModel *ReviewModel) TableName() string {
	return "reviews"
}

func (reviewModel *ReviewModel) ToDomain() *domain.Review {
	return &domain.Review{
		ID:         reviewModel.ID,
		UserID:     reviewModel.UserID,
		TargetType: domain.ReviewTargetType(reviewModel.TargetType),
		TargetID:   reviewModel.TargetID,
		Rating:     reviewModel.Rating,
		Text:       reviewModel.Text,
		// 强转回 []string
		Images:    reviewModel.Images,
		CreatedAt: reviewModel.CreatedAt,
		UpdatedAt: reviewModel.UpdatedAt,
	}
}

// ==========================================================
// 自定义类型: StringArray (用于处理 JSON 字符串数组)
// ==========================================================

type StringArray []string

// Value  Go Struct -> DB (序列化为 JSON 字符串)
// 存入数据库时，会变成 ["url1", "url2"]
func (s StringArray) Value() (driver.Value, error) {
	if len(s) == 0 {
		// 也可以存 nil 或 "[]"，视业务需求而定，这里建议存空数组字符串
		return "[]", nil
	}
	return json.Marshal(s)
}

// Scan  DB -> Go Struct (反序列化)
func (s *StringArray) Scan(value interface{}) error {
	if value == nil {
		*s = []string{}
		return nil
	}

	bytes, ok := value.([]byte)
	if !ok {
		// 兼容某些驱动可能返回 string 的情况
		if str, ok := value.(string); ok {
			bytes = []byte(str)
		} else {
			return errors.New("failed to scan StringArray: value is not []byte or string")
		}
	}

	return json.Unmarshal(bytes, s)
}
