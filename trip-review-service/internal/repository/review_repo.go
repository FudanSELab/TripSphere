package repository

import (
	"context"
	"errors"
	"gorm.io/gorm"
	"trip-review-service/internal/domain"
	"trip-review-service/internal/repository/model"
)

// ReviewRepo 定义 Repository 结构体
type ReviewRepo struct {
	db *gorm.DB
}

// NewReviewRepo 构造函数
func NewReviewRepo(db *gorm.DB) domain.ReviewRepository {
	return &ReviewRepo{
		db: db,
	}
}

// Create  - 创建点评
func (r *ReviewRepo) Create(ctx context.Context, review *domain.Review) error {
	//  将 Domain 实体转换为 DB Model
	reviewModel := review.ToModel()

	// 写入数据库
	if err := r.db.WithContext(ctx).Create(reviewModel).Error; err != nil {
		return err
	}

	return nil
}

// GetByID  - 根据 ID 查询单条
func (r *ReviewRepo) GetByID(ctx context.Context, id string) (*domain.Review, error) {
	var m model.ReviewModel

	// 查询
	if err := r.db.WithContext(ctx).Where("id = ?", id).First(&m).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			// 可以返回特定的领域错误，或者直接返回 nil, nil
			return nil, nil
		}
		return nil, err
	}

	// 转回 Domain 对象
	return m.ToDomain(), nil
}

// FindByTarget  查询列表 (例如：查询某酒店下的所有评论)
// 带有分页功能
func (r *ReviewRepo) FindByTarget(ctx context.Context, targetType domain.ReviewTargetType, targetID string, offset, limit int) ([]*domain.Review, error) {
	var models []model.ReviewModel

	// 构建查询
	// 对应索引: idx_target (target_type, target_id)
	query := r.db.WithContext(ctx).
		Where("target_type = ? AND target_id = ?", targetType, targetID).
		Order("created_at DESC"). // 通常按时间倒序
		Offset(offset).
		Limit(limit)

	if err := query.Find(&models).Error; err != nil {
		return nil, err
	}

	// 转换列表
	reviews := make([]*domain.Review, 0, len(models))
	for _, m := range models {
		temp := m
		reviews = append(reviews, temp.ToDomain())
	}

	return reviews, nil
}

// Update 更新点评 (例如：用户修改评分或内容)
func (r *ReviewRepo) Update(ctx context.Context, review *domain.Review) error {
	// 这里的 map 用于指定只更新哪些字段
	// 使用 Updates 可以避免将未赋值的零值字段更新到数据库
	updates := map[string]interface{}{
		"text":       review.Text,
		"rating":     review.Rating,
		"images":     model.StringArray(review.Images), // 强制转换类型
		"updated_at": review.UpdatedAt,
	}

	result := r.db.WithContext(ctx).
		Model(&model.ReviewModel{}).
		Where("id = ? AND uid = ?", review.ID, review.UserID). // 安全起见，带上 uid 校验所有权
		Updates(updates)

	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return errors.New("review not found or permission denied")
	}
	return nil
}

// Delete  删除点评
func (r *ReviewRepo) Delete(ctx context.Context, id string, uid string) error {
	result := r.db.WithContext(ctx).
		Where("id = ? AND uid = ?", id, uid).
		Delete(&model.ReviewModel{})

	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return errors.New("review not found")
	}
	return nil
}
