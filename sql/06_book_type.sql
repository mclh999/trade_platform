-- 2. 图书类别表：为类别筛选提供标准类别值
CREATE TABLE book_type (
    type_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '类别编号',
    type_name VARCHAR(50) NOT NULL COMMENT '类别名称',
    type_description VARCHAR(200) NULL COMMENT '类别说明',
    UNIQUE KEY uk_type_name (type_name)
) ENGINE=InnoDB COMMENT='图书类别表';noDB COMMENT='图书类别表';
