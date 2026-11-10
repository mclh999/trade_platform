-- 校园二手书交易平台：书籍发布表

CREATE TABLE IF NOT EXISTS book_listing (
    book_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '书籍编号',
    seller_id BIGINT UNSIGNED NOT NULL COMMENT '卖家用户编号',
    title VARCHAR(255) NOT NULL COMMENT '书名',
    author VARCHAR(255) NOT NULL COMMENT '作者',
    category VARCHAR(100) NOT NULL COMMENT '类别',
    book_condition VARCHAR(32) NOT NULL COMMENT '成色',
    price DECIMAL(10, 2) NOT NULL COMMENT '价格',
    description TEXT NULL COMMENT '书籍描述',
    cover_url VARCHAR(1024) NULL COMMENT '封面地址',
    status VARCHAR(16) NOT NULL DEFAULT 'AVAILABLE' COMMENT '书籍状态',
    PRIMARY KEY (book_id),
    KEY idx_book_listing_seller (seller_id),
    KEY idx_book_listing_status (status),
    CONSTRAINT fk_book_listing_seller
        FOREIGN KEY (seller_id)
        REFERENCES user_account (user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_book_listing_price_nonnegative
        CHECK (price >= 0),
    CONSTRAINT chk_book_listing_status
        CHECK (status IN ('AVAILABLE', 'RESERVED'))
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = '书籍发布';
