-- ============================================================
-- 校园二手书交易平台 · 实验二 数据库设计
-- 发布书籍模块建表脚本（王伟锋）
--
-- 对应材料：
--   database/README.md
--   database/design.md
--   database/data-dictionary.md
--   docs/reports/实验二/32406300079_王伟锋_实验二.docx
--
-- 说明：
--   1. 本脚本按个人报告的 app_user / book_category / book 命名，
--      覆盖发布书籍模块的三张表及其主外键、检查约束和索引。
--   2. 组内下单模块脚本 01-03 使用 user_account / book_listing /
--      reservation_order 命名；两套脚本的表名和状态值不同。
--      正式合并建库前需由小组统一命名，避免同一数据库中重复建表。
--   3. 目标数据库：MySQL 8.0.16+（CHECK 约束需要 8.0.16 及以上）。
--   4. 执行前请先选择目标数据库，例如：
--        USE trade_platform;
-- ============================================================

SET NAMES utf8mb4;

-- ------------------------------------------------------------
-- 1. 用户表：保存预置账号、显示名和账号状态
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app_user (
    user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户标识',
    login_name VARCHAR(32) NOT NULL COMMENT '登录名',
    display_name VARCHAR(50) NOT NULL COMMENT '显示名',
    password_hash VARCHAR(100) NOT NULL COMMENT '口令散列，不保存明文',
    user_status ENUM('ACTIVE', 'DISABLED') NOT NULL DEFAULT 'ACTIVE' COMMENT '账号状态',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (user_id),
    UNIQUE KEY uk_app_user_login (login_name)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = '用户表';

-- ------------------------------------------------------------
-- 2. 书籍分类表：发布时选择分类，供检索筛选
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS book_category (
    category_id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '分类标识',
    category_name VARCHAR(30) NOT NULL COMMENT '分类名称',
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '显示顺序，越小越靠前',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用：1启用，0停用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (category_id),
    UNIQUE KEY uk_category_name (category_name),
    CONSTRAINT chk_category_sort_order CHECK (sort_order >= 0),
    CONSTRAINT chk_category_is_active CHECK (is_active IN (0, 1))
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = '书籍分类表';

-- ------------------------------------------------------------
-- 3. 书籍表：一条记录对应一本实体书
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS book (
    book_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '书籍标识',
    seller_id BIGINT UNSIGNED NOT NULL COMMENT '发布者用户标识',
    category_id TINYINT UNSIGNED NOT NULL COMMENT '分类标识',
    title VARCHAR(120) NOT NULL COMMENT '书名',
    author VARCHAR(80) NOT NULL COMMENT '作者',
    isbn VARCHAR(20) NULL COMMENT 'ISBN，旧书可为空',
    publisher VARCHAR(100) NULL COMMENT '出版社',
    condition_level ENUM('NEW', 'LIKE_NEW', 'GOOD', 'FAIR') NOT NULL COMMENT '成色',
    selling_price DECIMAL(8, 2) NOT NULL COMMENT '售价（元），0 元表示赠送',
    description VARCHAR(500) NULL COMMENT '描述、书况、瑕疵等',
    cover_url VARCHAR(255) NULL COMMENT '封面地址或对象存储键',
    book_status ENUM('ON_SALE', 'RESERVED') NOT NULL DEFAULT 'ON_SALE' COMMENT '书籍状态',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (book_id),
    KEY idx_book_seller_status (seller_id, book_status),
    KEY idx_book_category_status (category_id, book_status),
    KEY idx_book_created_at (created_at),
    CONSTRAINT fk_book_seller
        FOREIGN KEY (seller_id)
        REFERENCES app_user (user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_book_category
        FOREIGN KEY (category_id)
        REFERENCES book_category (category_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_book_price CHECK (selling_price >= 0),
    CONSTRAINT chk_book_title CHECK (CHAR_LENGTH(TRIM(title)) > 0),
    CONSTRAINT chk_book_author CHECK (CHAR_LENGTH(TRIM(author)) > 0)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = '书籍发布记录，一条记录对应一本实体书';

-- ------------------------------------------------------------
-- 可选：初始化分类字典（按小组实际分类调整后再执行）
-- ------------------------------------------------------------
-- INSERT INTO book_category (category_name, sort_order) VALUES
--     ('教材', 10),
--     ('文学', 20),
--     ('考研', 30),
--     ('外语', 40),
--     ('计算机', 50),
--     ('其他', 99)
-- ON DUPLICATE KEY UPDATE category_name = VALUES(category_name);
