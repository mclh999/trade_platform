# 发布书籍模块数据字典

> 版本：v1.0 · 2026-11-10  
> 数据库类型：MySQL 8.0 语法（未执行 SQL）  
> 字符集建议：`utf8mb4`；排序规则：`utf8mb4_0900_ai_ci`（或以小组数据库统一配置为准）  
> 存储引擎：InnoDB（支持事务和外键）

---

## 1. `app_user`（用户表）

用途：保存预置账号、显示名和账号状态；发布书籍时作为卖家身份来源。

| 字段名 | 中文含义 | 数据类型（长度） | 可空/默认 | 键与约束 | 说明 |
|---|---|---|---|---|---|
| `user_id` | 用户标识 | `BIGINT UNSIGNED` | 否 / 自增 | PK | 代理主键 |
| `login_name` | 登录名 | `VARCHAR(32)` | 否 | UNIQUE | 预置账号登录名 |
| `display_name` | 显示名 | `VARCHAR(50)` | 否 | — | 卖家显示名 |
| `password_hash` | 口令散列 | `VARCHAR(100)` | 否 | — | 预置账号凭据；不存明文 |
| `user_status` | 账号状态 | `ENUM('ACTIVE','DISABLED')` | 否 / `ACTIVE` | — | 发布时应用校验 `ACTIVE` |
| `created_at` | 创建时间 | `DATETIME` | 否 / 当前时间 | — | 账号建立时间 |

说明：

- `password_hash` 的长度按常见 BCrypt/Argon2 输出预留；本设计不保存明文口令。若小组统一采用其他认证方式，可删除该列或改为认证服务引用。
- 注册、找回密码不在本实验范围；`app_user` 仅覆盖预置测试账号和发布/下单所需的身份信息。

---

## 2. `book_category`（书籍分类表）

用途：保存分类名称、排序和启用状态，供发布选择和检索筛选。

| 字段名 | 中文含义 | 数据类型（长度） | 可空/默认 | 键与约束 | 说明 |
|---|---|---|---|---|---|
| `category_id` | 分类标识 | `TINYINT UNSIGNED` | 否 / 自增 | PK | 分类少，用 `TINYINT` |
| `category_name` | 分类名称 | `VARCHAR(30)` | 否 | UNIQUE | 教材、文学、考研等 |
| `sort_order` | 显示顺序 | `SMALLINT UNSIGNED` | 否 / 0 | — | 越小越靠前 |
| `is_active` | 是否启用 | `TINYINT(1)` | 否 / 1 | — | 0 停用；历史书籍仍显示原分类 |
| `created_at` | 创建时间 | `DATETIME` | 否 / 当前时间 | — | 分类建立时间 |

说明：分类使用字典表而不是 `book` 表中的字符串列，原因是分类名会在检索筛选、排序和页面展示中复用；集中存储可以避免改名时多行更新和拼写不一致。分类停用（`is_active = 0`）后不再用于新发布，但历史书籍仍可显示原分类；分类不物理删除。

---

## 3. `book`（书籍表）

用途：保存发布书籍的字段、售价、品相、状态和归属；一条记录对应一本实体书。

| 字段名 | 中文含义 | 数据类型（长度） | 可空/默认 | 键与约束 | 说明 |
|---|---|---|---|---|---|
| `book_id` | 书籍标识 | `BIGINT UNSIGNED` | 否 / 自增 | PK | 一条记录 = 一本实体书 |
| `seller_id` | 发布者 | `BIGINT UNSIGNED` | 否 | FK → `app_user.user_id` | 发布者；删除受限 |
| `category_id` | 分类 | `TINYINT UNSIGNED` | 否 | FK → `book_category.category_id` | 分类；删除受限 |
| `title` | 书名 | `VARCHAR(120)` | 否 | CHECK 非空 | 必填 |
| `author` | 作者 | `VARCHAR(80)` | 否 | CHECK 非空 | 必填 |
| `isbn` | ISBN | `VARCHAR(20)` | 是 / NULL | — | 旧书可能没有 |
| `publisher` | 出版社 | `VARCHAR(100)` | 是 / NULL | — | 可选 |
| `condition_level` | 成色 | `ENUM` | 否 | — | `NEW`=全新 / `LIKE_NEW`=九成新 / `GOOD`=七成新 / `FAIR`=五成新及以下 |
| `selling_price` | 售价（元） | `DECIMAL(8,2)` | 否 | CHECK ≥ 0 | 0 元表示赠送 |
| `description` | 描述 | `VARCHAR(500)` | 是 / NULL | — | 书况、瑕疵等 |
| `cover_url` | 封面地址 | `VARCHAR(255)` | 是 / NULL | — | URL 或对象存储键 |
| `book_status` | 书籍状态 | `ENUM('ON_SALE','RESERVED')` | 否 / `ON_SALE` | — | 初始可售；订单事务更新 |
| `created_at` | 发布时间 | `DATETIME` | 否 / 当前时间 | — | 发布记录创建时间 |
| `updated_at` | 更新时间 | `DATETIME` | 否 / 当前时间 | 更新时刷新 | 字段/状态变化时刷新 |

说明：

- `book` 表不设置 `quantity/stock` 列。若未来需要同一卖家发布多本同款书，应增加多条 `book` 记录，或另建“实体副本”表；当前范围按一条记录一本实体书处理。
- `book_status` 不设 `SOLD`；交易完成、支付、物流不在系统范围，订单取消后书籍回到 `ON_SALE`。
- 成色枚举映射：`NEW` = 全新，`LIKE_NEW` = 九成新，`GOOD` = 七成新，`FAIR` = 五成新及以下。
- `cover_url` 可存完整 URL 或对象存储键；若需要多张图片，应增加 `book_image` 子表，不在 `book` 中存逗号分隔的图片列表。
- `created_at` 默认 `CURRENT_TIMESTAMP`；`updated_at` 使用 `ON UPDATE CURRENT_TIMESTAMP` 自动刷新。

---

## 4. 主外键与检查约束汇总

| 约束名 | 类型 | 涉及表/列 | 规则 | 说明 |
|---|---|---|---|---|
| `pk_app_user` | 主键 | `app_user.user_id` | 唯一、非空 | 代理键 |
| `uk_app_user_login` | 唯一 | `app_user.login_name` | 唯一、非空 | 业务键 |
| `pk_book_category` | 主键 | `book_category.category_id` | 唯一、非空 | 代理键 |
| `uk_category_name` | 唯一 | `book_category.category_name` | 唯一、非空 | 防重复分类 |
| `pk_book` | 主键 | `book.book_id` | 唯一、非空 | 代理键 |
| `fk_book_seller` | 外键 | `book.seller_id` → `app_user.user_id` | 引用存在用户；删除受限、更新级联 | `ON DELETE RESTRICT` / `ON UPDATE CASCADE` |
| `fk_book_category` | 外键 | `book.category_id` → `book_category.category_id` | 引用存在分类；删除受限、更新级联 | `ON DELETE RESTRICT` / `ON UPDATE CASCADE` |
| `chk_book_price` | 检查 | `book.selling_price` | `>= 0` | 允许 0 元赠送 |
| `chk_book_title` | 检查 | `book.title` | `TRIM` 后长度 > 0 | 防空字符串 |
| `chk_book_author` | 检查 | `book.author` | `TRIM` 后长度 > 0 | 防空字符串 |

---

## 5. 索引建议

| 索引名 | 列 | 用途 |
|---|---|---|
| `idx_book_seller_status` | `(seller_id, book_status)` | 卖家查看自己的在售书籍 |
| `idx_book_category_status` | `(category_id, book_status)` | 按分类浏览可售书籍 |
| `idx_book_created_at` | `(created_at)` | 按发布时间排序 |

索引不属于业务约束，但应在建表时一并定义。

---

## 6. 约束责任边界

数据库约束能保证：

- 实体完整性：主键；
- 引用完整性：外键；
- 域完整性：`ENUM`、`DECIMAL`、`CHECK`；
- 默认值：`ON_SALE`、当前时间等。

数据库约束不能保证、必须由应用/事务负责：

- `seller_id` 对应用户必须为 `ACTIVE`；
- `category_id` 对应分类必须 `is_active = 1`；
- 当前登录用户是否为书籍发布者/订单买家；
- 下单时书籍必须为 `ON_SALE`；
- 订单与 `book_status` 的同步更新必须原子完成；
- 同一本书同一时刻最多一条有效订单（由订单模块使用部分唯一索引、生成列唯一索引或事务锁落实）。

---

## 7. 备注

- 本数据字典只覆盖本人主责的发布书籍模块；`book_order` 由组内下单模块负责人补充。
- 未执行 SQL，选做部分按小组要求忽略；实际建表后应使用虚构数据验证约束。
- 完整设计说明见 [`design.md`](design.md)；图表见 [`diagrams/`](diagrams/)。
