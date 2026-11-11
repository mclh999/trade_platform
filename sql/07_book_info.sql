-- 3. 图书检索信息表：查询管理模块的核心表
CREATE TABLE book_info (
    book_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '图书编号',
    publisher_id BIGINT NOT NULL COMMENT '发布者编号',
    type_id INT NOT NULL COMMENT '图书类别编号',
    book_name VARCHAR(150) NOT NULL COMMENT '书名',
    author_name VARCHAR(80) NOT NULL COMMENT '作者',
    book_condition VARCHAR(20) NOT NULL COMMENT '图书成色',
    price DECIMAL(10,2) NOT NULL COMMENT '价格',
    book_status VARCHAR(10) NOT NULL DEFAULT '可售' COMMENT '状态：可售/已预留',
    description VARCHAR(500) NULL COMMENT '图书简介',
    publish_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
    CONSTRAINT fk_book_publisher FOREIGN KEY (publisher_id)
      REFERENCES publisher_account(publisher_id)
      ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_book_type FOREIGN KEY (type_id)
      REFERENCES book_type(type_id)
      ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ck_book_price CHECK (price >= 0),
    CONSTRAINT ck_book_status CHECK (book_status IN ('可售', '已预留')),
    KEY idx_book_name (book_name),
    KEY idx_author_name (author_name),
    KEY idx_type_status_time (type_id, book_status, publish_time),
    KEY idx_status_price (book_status, price),
    FULLTEXT KEY ft_book_search (book_name, author_name, description)
) ENGINE=InnoDB COMMENT='图书检索信息表';