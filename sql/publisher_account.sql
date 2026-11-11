-- 实验二：校园二手书交易平台：查询管理模块（MySQL 8.0）
-- 执行sql顺序：publisher_account->book_category->book

CREATE DATABASE IF NOT EXISTS campus_book
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE campus_book;

-- 1. 用户表：保存图书发布者信息
CREATE TABLE publisher_account (
    user_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户编号',
    username VARCHAR(50) NOT NULL COMMENT '用户姓名/昵称',
    phone VARCHAR(20) NULL COMMENT '联系方式',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    UNIQUE KEY uk_user_phone (phone)
) ENGINE=InnoDB COMMENT='用户表';