# 协作图对象与消息对应说明

> 版本：v1.0 · 日期：2026-11-23 · 维护：C（32406300079 王伟锋，软件243）
> 本文件由 `tools/generate_communication.py` 根据同一份图数据生成，避免图、表不一致。
> 对象名、消息名与 `design/sequence/` 下的顺序图保持一致；消息序号采用分层编号。

## 1. 对象与类对应

| 协作图对象 | 类 / 构件 | 角色 | 职责 | 顺序图生命线 | 数据落点 |
|---|---|---|---|---|---|
| 买家 | Actor（参与者） | Actor | 校园用户，发起预留/取消请求 | — | 不持久化 |
| 卖家 | Actor（参与者） | Actor | 校园用户，发起发布请求 | — | 不持久化 |
| 校园用户 | Actor（参与者） | Actor | 检索和查看书籍 | — | 不持久化 |
| 预留界面 | Boundary / ReservationUI | Boundary | 接收下单参数并展示结果 | 预留界面 | — |
| 订单界面 | Boundary / OrderUI | Boundary | 接收取消请求并展示结果 | 订单界面 | — |
| 发布界面 | Boundary / PublishUI | Boundary | 接收发布表单并展示结果 | 发布界面 | — |
| 检索界面 | Boundary / SearchUI | Boundary | 接收检索/详情请求并展示结果 | 检索界面 | — |
| 预留服务 | Control / ReservationService | Control | 校验身份与书籍状态，组织下单事务 | 预留服务 | 无（服务层） |
| 取消服务 | Control / CancellationService | Control | 校验取消权限与订单状态，组织取消事务 | 取消服务 | 无（服务层） |
| 订单服务 | Control / OrderService | Control | 取消后重订场景下统一协调取消和预留 | 订单服务 | 无（服务层） |
| 书籍服务 | Control / BookService | Control | 校验发布字段并创建发布记录 | 书籍服务 | 无（服务层） |
| 检索服务 | Control / SearchService | Control | 执行检索、详情查询和状态展示 | 检索服务 | 无（服务层） |
| book_listing | Entity / BookListing | Entity | 书籍发布记录，维护书籍状态 | book_listing | book_listing |
| reservation_order | Entity / ReservationOrder | Entity | 预留订单，维护订单状态与历史 | reservation_order | reservation_order |
| user_account | Entity / UserAccount | Entity | 用户账号，校验发布者存在 | user_account | user_account |
| 事务 / 数据库 | Infra / TransactionManager | Infra | 事务控制与 SQL 执行 | 事务 / 数据库 | InnoDB |

## 2. 场景消息对应

### C-01 通信图一：下单预留（正常流程）

> 由 design/sequence/01_下单预留_正常与异常.svg 转换；序号与顺序图消息一一对应

| 序号 | 发送 → 接收 | 消息（完整签名） | 输入/返回 | 类操作 | 顺序图对应 | 说明 |
|---|---|---|---|---|---|---|
| 1 | 买家 → 预留界面 | `submitReservation(buyerId, bookId)` | buyerId, bookId | ReservationUI.submitReservation | submitReservation | 界面接收下单请求 |
| 1.1 | 预留界面 → 预留服务 | `reserveBook(buyerId, bookId)` | buyerId, bookId；返回 ReservationResult | ReservationService.reserveBook | reserveBook | 进入服务层校验 |
| 1.1.1 | 预留服务 → book_listing | `findBook(bookId)` | bookId；返回 BookInfo(sellerId, status) | BookListing.findBook | findBook(bookId) | 读取发布者与状态 |
| 1.1.1.1 | book_listing → 预留服务 | `BookInfo(sellerId, status)` | sellerId、status | BookListing.findBook 返回 | BookInfo(sellerId, status) | 正常返回；无记录另行拒绝 |
| 1.1.2 | 预留服务 → reservation_order | `findActiveOrder(bookId)` | bookId；返回订单或 null | ReservationOrder.findActiveOrder | findActiveOrder(bookId) | 检查是否已有有效订单 |
| 1.1.2.1 | reservation_order → 预留服务 | `ActiveOrder or null` | ACTIVE 订单或 null | ReservationOrder.findActiveOrder 返回 | ActiveOrder or null | 存在则进入 BOOK_RESERVED 分支 |
| 1.1.3 | 预留服务 → 事务 / 数据库 | `beginTransaction()` | — | TransactionManager.begin | beginTransaction() | 开启下单事务 |
| 1.1.4 | 预留服务 → reservation_order | `createActive(buyerId, bookId)` | buyerId, bookId；新建 ACTIVE 订单 | ReservationOrder.createActive | create ACTIVE order | 订单状态初始为 ACTIVE |
| 1.1.4.1 | reservation_order → 事务 / 数据库 | `INSERT INTO reservation_order` | 新订单行 | ReservationOrder.persist | INSERT reservation_order | 唯一索引保证一书一有效订单 |
| 1.1.5 | 预留服务 → book_listing | `markReserved(bookId)` | bookId | BookListing.markReserved | mark status = RESERVED | 书籍状态改为 RESERVED |
| 1.1.5.1 | book_listing → 事务 / 数据库 | `UPDATE book_listing SET status = 'RESERVED'` | bookId | BookListing.persistStatus | UPDATE book_listing | 与订单写入同一事务 |
| 1.1.6 | 预留服务 → 事务 / 数据库 | `commit()` | — | TransactionManager.commit | commit() | 成功提交 |
| 1.2 | 预留服务 → 预留界面 | `ReservationResult(orderId, ACTIVE)` | orderId、ACTIVE | ReservationService.reserveBook 返回 | ReservationResult(orderId, ACTIVE) | 返回订单确认 |
| 1.3 | 预留界面 → 买家 | `reservation confirmed` | 确认提示 | ReservationUI.showResult | reservation confirmed | 界面展示成功 |

| 分支 | 守卫条件 | 交互与结果 |
|---|---|---|
| E1 | [buyerId == sellerId] | 预留服务 → 预留界面：reject(SELF_RESERVATION) 不创建订单；书籍保持 AVAILABLE。 |
| E2 | [status != AVAILABLE 或存在 ACTIVE 订单] | 预留服务 → 预留界面：reject(BOOK_RESERVED) 不新增订单；原订单和书籍状态不变。 |
| E3 | [并发请求导致唯一约束/条件更新失败] | 事务/数据库 → 预留服务：rollback()；预留服务 → 预留界面：reject(BOOK_RESERVED) 只有先成功受理的请求保留 ACTIVE 订单。 |

### C-02 通信图二：取消订单（正常流程）

> 由 design/sequence/02_取消订单_正常与异常.svg 转换；先改订单状态，再判断书籍是否可恢复

| 序号 | 发送 → 接收 | 消息（完整签名） | 输入/返回 | 类操作 | 顺序图对应 | 说明 |
|---|---|---|---|---|---|---|
| 1 | 买家 → 订单界面 | `cancel(orderId, requesterId)` | orderId, requesterId | OrderUI.cancel | cancel(orderId, requesterId) | 提交取消请求 |
| 1.1 | 订单界面 → 取消服务 | `cancelOrder(requesterId, orderId)` | requesterId, orderId；返回 CancelResult | CancellationService.cancelOrder | cancelOrder(requesterId, orderId) | 进入取消服务 |
| 1.1.1 | 取消服务 → reservation_order | `findOrder(orderId)` | orderId；返回 Order(buyerId, bookId, status) | ReservationOrder.findOrder | findOrder(orderId) | 读取订单归属和状态 |
| 1.1.1.1 | reservation_order → 取消服务 | `Order(buyerId, bookId, status)` | buyerId、bookId、status | ReservationOrder.findOrder 返回 | Order(buyerId, bookId, status) | 正常返回；不存在另行拒绝 |
| 1.1.2 | 取消服务 → 事务 / 数据库 | `beginTransaction()` | — | TransactionManager.begin | beginTransaction() | 开启取消事务 |
| 1.1.3 | 取消服务 → reservation_order | `markCancelled(orderId)` | orderId；status = CANCELLED | ReservationOrder.markCancelled | UPDATE status = CANCELLED | 订单状态变更 |
| 1.1.4 | 取消服务 → reservation_order | `setCancelledAt(orderId, now)` | orderId, 当前时间 | ReservationOrder.setCancelledAt | set cancelled_at | 记录取消时间，保留历史 |
| 1.1.5 | 取消服务 → reservation_order | `findCurrentActiveOrder(bookId)` | bookId；排除本订单后查询 | ReservationOrder.findCurrentActiveOrder | findCurrentActiveOrder(bookId) | 确认书籍是否仍被新订单占用 |
| 1.1.5.1 | reservation_order → 取消服务 | `ActiveOrder or null` | 新 ACTIVE 订单或 null | ReservationOrder.findCurrentActiveOrder 返回 | ActiveOrder or null | 为 null 才可恢复书籍 |
| 1.1.6 | 取消服务 → book_listing | `markAvailable(bookId) [无其他 ACTIVE 订单]` | bookId；守卫：activeOrder == null | BookListing.markAvailable | UPDATE status = AVAILABLE | 书籍恢复可售 |
| 1.1.7 | 取消服务 → 事务 / 数据库 | `commit()` | — | TransactionManager.commit | commit() | 提交取消结果 |
| 1.2 | 取消服务 → 订单界面 | `CancelResult(success)` | success | CancellationService.cancelOrder 返回 | CancelResult(success) | 返回取消结果 |
| 1.3 | 订单界面 → 买家 | `cancel confirmed` | 确认提示 | OrderUI.showResult | cancel confirmed | 界面展示成功 |

| 分支 | 守卫条件 | 交互与结果 |
|---|---|---|
| E1 | [requesterId != order.buyerId] | 取消服务 → 订单界面：reject(FORBIDDEN) 订单保持 ACTIVE；书籍保持 RESERVED。 |
| E2 | [order.status == CANCELLED] | 取消服务 → 订单界面：reject(ALREADY_CANCELLED) 拒绝重复取消；不重复修改书籍状态。 |
| E3 | [旧订单取消请求晚到，书籍已有新 ACTIVE 订单] | 取消服务 → 订单界面：reject(OLD_REQUEST) 不修改新订单；书籍保持 RESERVED。 |

### C-03 通信图三：取消后重新预留（边界一致性）

> 由 design/sequence/03_取消后重订_边界场景.svg 转换；补充旧取消请求晚到的消息

| 序号 | 发送 → 接收 | 消息（完整签名） | 输入/返回 | 类操作 | 顺序图对应 | 说明 |
|---|---|---|---|---|---|---|
| 1 | 买家 A → 订单服务 | `cancel(orderA, buyerA)` | orderA, buyerA | OrderService.cancel | cancel(orderA, buyerA) | 订单 A 的买家发起取消 |
| 1.1 | 订单服务 → reservation_order | `findOrder(orderA)` | orderA；返回 ACTIVE(orderA) | ReservationOrder.findOrder | findOrder(orderA) | 读取订单 A |
| 1.1.1 | reservation_order → 订单服务 | `ACTIVE(orderA)` | status = ACTIVE | ReservationOrder.findOrder 返回 | ACTIVE(orderA) | 确认订单 A 仍有效 |
| 1.2 | 订单服务 → 事务 / 数据库 | `beginTransaction()` | — | TransactionManager.begin | beginTransaction() | 开启取消事务 |
| 1.3 | 订单服务 → reservation_order | `orderA → CANCELLED` | orderA；status = CANCELLED | ReservationOrder.markCancelled | orderA → CANCELLED | 订单 A 失效 |
| 1.4 | 订单服务 → reservation_order | `check current order(book)` | book；返回 null | ReservationOrder.findCurrentActiveOrder | check current order(book) | 排除订单 A 后查询 |
| 1.4.1 | reservation_order → 订单服务 | `null` | 无其他 ACTIVE 订单 | ReservationOrder.findCurrentActiveOrder 返回 | null | 允许恢复书籍 |
| 1.5 | 订单服务 → book_listing | `book → AVAILABLE` | book | BookListing.markAvailable | book → AVAILABLE | 恢复可售 |
| 1.6 | 订单服务 → 事务 / 数据库 | `commit()` | — | TransactionManager.commit | commit() | 提交取消 |
| 1.7 | 订单服务 → 买家 A | `success(cancelled)` | 取消成功 | OrderService.cancel 返回 | — | 通知买家 A |
| 2 | 买家 B → 订单服务 | `reserve(book)` | book, buyerB | OrderService.reserve | reserve(book) | 买家 B 重新预留 |
| 2.1 | 订单服务 → book_listing | `check AVAILABLE` | book；返回 AVAILABLE | BookListing.findBook | check AVAILABLE | 重新读取书籍状态 |
| 2.1.1 | book_listing → 订单服务 | `AVAILABLE` | status = AVAILABLE | BookListing.findBook 返回 | AVAILABLE | 可被预留 |
| 2.2 | 订单服务 → 事务 / 数据库 | `beginTransaction()` | — | TransactionManager.begin | — | 开启新预留事务 |
| 2.3 | 订单服务 → reservation_order | `create orderB ACTIVE` | buyerB, book；新订单 ACTIVE | ReservationOrder.createActive | create orderB ACTIVE | 订单 B 建立 |
| 2.4 | 订单服务 → book_listing | `book → RESERVED` | book | BookListing.markReserved | book → RESERVED | 书籍再次预留 |
| 2.5 | 订单服务 → 事务 / 数据库 | `commit()` | — | TransactionManager.commit | commit() | 提交新预留 |
| 2.6 | 订单服务 → 买家 B | `success(orderB)` | orderB | OrderService.reserve 返回 | success(orderB) | 通知买家 B |
| 3 | 买家 A → 订单服务 | `cancel(orderA, buyerA)（旧请求晚到）` | 旧 orderA | OrderService.cancel | 旧取消请求晚到 | 边界：订单 A 已取消后再次请求 |
| 3.1 | 订单服务 → reservation_order | `findOrder(orderA)` | orderA；返回 CANCELLED | ReservationOrder.findOrder | — | 读取订单 A 当前状态 |
| 3.1.1 | reservation_order → 订单服务 | `CANCELLED` | status = CANCELLED | ReservationOrder.findOrder 返回 | — | 已非 ACTIVE |
| 3.2 | 订单服务 → 买家 A | `reject(OLD_REQUEST)` | 拒绝原因 | OrderService.cancel 返回 | reject(OLD_REQUEST) | 不修改订单 B |

| 分支 | 守卫条件 | 交互与结果 |
|---|---|---|
| E1 | [orderA 已 CANCELLED 且 orderB 已 ACTIVE] | 订单服务 → 买家 A：reject(OLD_REQUEST) 不修改 orderB；book_listing 保持 RESERVED。 |
| E2 | [orderA 取消成功且当前无其他 ACTIVE 订单] | 订单服务 → book_listing：book → AVAILABLE 订单 A 保留为 CANCELLED，历史不删除。 |
| E3 | [买家 B 预留时书籍仍被占用] | 订单服务 → 买家 B：reject(BOOK_RESERVED) 不创建 orderB；书籍状态不变。 |

### C-04 通信图四：发布书籍（正常流程）

> 由 design/sequence/04_发布书籍_正常与异常.svg 转换；发布成功初始状态为 AVAILABLE

| 序号 | 发送 → 接收 | 消息（完整签名） | 输入/返回 | 类操作 | 顺序图对应 | 说明 |
|---|---|---|---|---|---|---|
| 1 | 卖家 → 发布界面 | `submitBook(sellerId, title, author, category, condition, price)` | 表单字段 | PublishUI.submitBook | submitBook(...) | 接收发布表单 |
| 1.1 | 发布界面 → 书籍服务 | `createListing(bookInfo)` | bookInfo；返回 PublishResult | BookService.createListing | createListing(bookInfo) | 进入书籍服务 |
| 1.1.1 | 书籍服务 → user_account | `checkSeller(sellerId)` | sellerId；返回 seller exists | UserAccount.checkSeller | checkSeller(sellerId) | 校验发布者存在 |
| 1.1.1.1 | user_account → 书籍服务 | `seller exists` | true/false | UserAccount.checkSeller 返回 | seller exists | 不存在则拒绝发布 |
| 1.1.2 | 书籍服务 → 书籍服务 | `validateRequiredAndPrice(bookInfo)` | bookInfo；返回 valid | BookService.validateRequiredAndPrice | validateRequiredAndPrice(bookInfo) | 自消息：校验必填和价格 |
| 1.1.3 | 书籍服务 → 事务 / 数据库 | `beginTransaction()` | — | TransactionManager.begin | beginTransaction() | 开启发布事务 |
| 1.1.4 | 书籍服务 → book_listing | `insertListing(bookInfo, status=AVAILABLE)` | bookInfo；初始 AVAILABLE | BookListing.create | insert listing(status=AVAILABLE) | 创建发布记录 |
| 1.1.4.1 | book_listing → 事务 / 数据库 | `INSERT INTO book_listing` | 新书籍行 | BookListing.persist | INSERT book_listing | 写入数据库 |
| 1.1.5 | 书籍服务 → 事务 / 数据库 | `commit()` | — | TransactionManager.commit | commit() | 提交发布 |
| 1.2 | 书籍服务 → 发布界面 | `PublishResult(bookId, AVAILABLE)` | bookId, status | BookService.createListing 返回 | PublishResult(bookId, AVAILABLE) | 返回发布结果 |

| 分支 | 守卫条件 | 交互与结果 |
|---|---|---|
| E1 | [必填字段缺失] | 书籍服务 → 发布界面：reject(MISSING_FIELD) 指出缺失字段；不创建 book_listing。 |
| E2 | [price < 0 或格式不合法] | 书籍服务 → 发布界面：reject(INVALID_PRICE) 提示价格不得为负；不创建发布记录。 |
| E3 | [sellerId 不存在] | 书籍服务 → 发布界面：reject(SELLER_NOT_FOUND) 不写入书籍发布记录。 |

### C-05 通信图五：检索与查看（正常流程）

> 由 design/sequence/05_检索与查看_正常与异常.svg 转换；查询只读，不修改书籍状态

| 序号 | 发送 → 接收 | 消息（完整签名） | 输入/返回 | 类操作 | 顺序图对应 | 说明 |
|---|---|---|---|---|---|---|
| 1 | 校园用户 → 检索界面 | `search(keyword, category)` | keyword, category | SearchUI.search | search(keyword, category) | 提交检索条件 |
| 1.1 | 检索界面 → 检索服务 | `searchBooks(keyword, category)` | keyword, category；返回 BookSummary[] | SearchService.searchBooks | searchBooks(keyword, category) | 执行检索 |
| 1.1.1 | 检索服务 → book_listing | `match(title / author / category)` | keyword, category | BookListing.match | match title / author / category | 匹配书名、作者或分类 |
| 1.1.2 | 检索服务 → 数据库 | `SELECT listings and current status` | 匹配条件 | BookListing.query | SELECT listings and current status | 查询结果与当前状态 |
| 1.1.2.1 | 数据库 → 检索服务 | `BookSummary[]` | 书籍摘要列表 | BookListing.query 返回 | BookSummary[] | 返回结果集 |
| 1.1.3 | 检索服务 → 检索界面 | `result list with AVAILABLE / RESERVED` | 摘要及状态 | SearchService.searchBooks 返回 | result list with AVAILABLE / RESERVED | 状态必须随结果展示 |
| 1.1.4 | 检索界面 → 校园用户 | `display results` | 检索结果 | SearchUI.displayResults | display results | 展示列表 |
| 2 | 校园用户 → 检索界面 | `viewDetails(bookId)` | bookId | SearchUI.viewDetails | viewDetails(bookId) | 打开书籍详情 |
| 2.1 | 检索界面 → 检索服务 | `getBookDetails(bookId)` | bookId；返回 BookDetails + status | SearchService.getBookDetails | getBookDetails(bookId) | 查询详情 |
| 2.1.1 | 检索服务 → book_listing | `findById(bookId)` | bookId | BookListing.findById | findById(bookId) | 按编号查询 |
| 2.1.2 | 检索服务 → 数据库 | `SELECT details + current status` | bookId | BookListing.queryOne | BookDetails + current status | 读取详情和状态 |
| 2.1.2.1 | 数据库 → 检索服务 | `BookDetails + current status` | 详情与状态 | BookListing.queryOne 返回 | BookDetails + current status | 无记录则返回不可用 |
| 2.1.3 | 检索服务 → 检索界面 | `display details` | 详情与状态 | SearchService.getBookDetails 返回 | display details | 保留 AVAILABLE/RESERVED |
| 2.1.4 | 检索界面 → 校园用户 | `display details` | 详情与状态 | SearchUI.displayDetails | display details | 用户查看详情 |

| 分支 | 守卫条件 | 交互与结果 |
|---|---|---|
| E1 | [无匹配项] | 检索服务 → 检索界面：empty result 界面提示未找到匹配书籍。 |
| E2 | [结果书籍为 RESERVED] | 检索界面 → 校园用户：显示 RESERVED 仍可展示，但不得显示为可售。 |
| E3 | [详情查询无记录] | 检索服务 → 检索界面：not found 提示详情不可用，不把不存在的书籍显示为有效结果。 |

