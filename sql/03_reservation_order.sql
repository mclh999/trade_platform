-- 校园二手书交易平台：下单预留订单表
-- 业务规则：买家不能是发布者本人；该跨表规则由业务层/服务层在创建订单前校验。
-- 事务边界：创建订单和更新书籍状态应在同一事务中由业务层/服务层完成；数据库层不使用触发器。
-- active_book_key 仅为 ACTIVE 订单生成书籍编号；CANCELLED 订单生成 NULL，利用唯一索引允许多个 NULL 保留取消历史。

CREATE TABLE IF NOT EXISTS reservation_order (
    order_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '订单编号',
    buyer_id BIGINT UNSIGNED NOT NULL COMMENT '买家用户编号',
    book_id BIGINT UNSIGNED NOT NULL COMMENT '书籍编号',
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' COMMENT '订单状态',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '下单时间',
    cancelled_at DATETIME NULL COMMENT '取消时间',
    active_book_key BIGINT UNSIGNED
        GENERATED ALWAYS AS (
            CASE
                WHEN status = 'ACTIVE' THEN book_id
                ELSE NULL
            END
        ) STORED COMMENT '仅 ACTIVE 订单生成书籍编号，用于唯一约束',
    PRIMARY KEY (order_id),
    UNIQUE KEY uk_reservation_order_active_book (active_book_key),
    KEY idx_reservation_order_buyer (buyer_id),
    KEY idx_reservation_order_book_and_status (book_id, status),
    KEY idx_reservation_order_created_at (created_at),
    CONSTRAINT fk_reservation_order_buyer
        FOREIGN KEY (buyer_id)
        REFERENCES user_account (user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_reservation_order_book
        FOREIGN KEY (book_id)
        REFERENCES book_listing (book_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_reservation_status_values
        CHECK (status IN ('ACTIVE', 'CANCELLED')),
    CONSTRAINT chk_reservation_order_cancel_time
        CHECK (
            (status = 'ACTIVE' AND cancelled_at IS NULL)
            OR (status = 'CANCELLED' AND cancelled_at IS NOT NULL)
        )
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = '下单预留订单';
