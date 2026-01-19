-- Create reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id          VARCHAR(64)  NOT NULL,
    uid         VARCHAR(64)  NOT NULL,
    target_type VARCHAR(20)  NOT NULL,
    target_id   VARCHAR(64)  NOT NULL,
    rating      TINYINT      NOT NULL DEFAULT 0,
    text        TEXT         CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT 'Text with Emoji support',
    images      JSON         COMMENT 'Array of image URLs',
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX idx_target (target_type, target_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;