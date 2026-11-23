-- 实验二：校园二手书交易平台：查询管理模块
-- 三张表：publisher_account（发布者）、book_type（图书类别）、book_info（图书检索信息）

CREATE DATABASE IF NOT EXISTS campus_book
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE campus_book;

-- 1. 发布者信息表：只保存查询结果需要展示的发布者信息
CREATE TABLE publisher_account (
    publisher_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '发布者编号',
    publisher_name VARCHAR(50) NOT NULL COMMENT '发布者名称',
    contact_phone VARCHAR(20) NULL COMMENT '联系号码',
    account_status TINYINT NOT NULL DEFAULT 1 COMMENT '账号状态：1正常，0停用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    UNIQUE KEY uk_publisher_phone (contact_phone),
    KEY idx_publisher_name (publisher_name)
) ENGINE=InnoDB COMMENT='发布者信息表';