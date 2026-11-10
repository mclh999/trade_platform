-- 校园二手书交易平台：用户账户表
-- 执行顺序：01_user_account.sql -> 02_book_listing.sql -> 03_reservation_order.sql

CREATE TABLE IF NOT EXISTS user_account (
    user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户编号',
    username VARCHAR(100) NOT NULL COMMENT '用户名',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (user_id),
    UNIQUE KEY uk_user_account_username (username)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = '用户账户';
