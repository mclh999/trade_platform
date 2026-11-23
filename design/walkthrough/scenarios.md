# 实验三 场景走查汇总（C 部分）

> 主责：C（32406300079 王伟锋，软件243）  
> 范围：发布书籍、检索与查看、下单预留、取消订单、取消后重新预留  
> 方法：按指导书要求逐个场景写出初始条件、操作、预期结果和模型依据，核对需求、数据库、顺序图、协作图以及（待提交的）状态图/活动图。  
> 限制：当前仓库没有可运行程序，以下结论均为**设计推演**，不代表已运行或已执行数据库事务。

---

## 1. 走查基线

### 1.1 需求基线

| 编号 | 规则 | 来源 |
|---|---|---|
| RQ-01 | 卖家可以发布书籍；一条发布记录代表一本实体书 | 实验一系统概述；`design/README.md` |
| RQ-02 | 校园用户可以按关键词/分类检索并查看书籍详情和当前状态 | 实验一用例 UC-02 |
| RQ-03 | 买家可以为可售书籍提交预留请求；下单只表示预留，不涉及支付 | 实验一基本约定 |
| RQ-04 | 买家不能预留自己发布的书籍 | 实验一基本约定；`sequence/01` 异常分支 |
| RQ-05 | 同一本书同一时刻最多一条有效订单 | 实验一基本约定；`sql/03_reservation_order.sql` |
| RQ-06 | 仅订单买家本人可以取消；取消后书籍恢复可售、历史保留 | 实验一用例 UC-04 |
| RQ-07 | `book_listing` 只有 `AVAILABLE`、`RESERVED`；订单只有 `ACTIVE`、`CANCELLED` | 实验三共享设计口径 |
| RQ-08 | 检索与查看只读，不修改书籍状态 | `sequence/05`；`design/README.md` |

### 1.2 涉及模型

- 顺序图：`design/sequence/01`～`05`（B）
- 协作图：`design/collaboration/01`～`05`（C）
- 类/对象基线：`design/README.md` 第 2.2 节、`design/collaboration/README.md` 第 3 节
- 数据库：`database/README.md`、`database/design.md`、`database/data-dictionary.md`、`sql/01`～`03`
- 状态图/活动图：D 尚未提交；期望模型见 `design/cross-check/state-activity-check.md`

### 1.3 判定口径

- **通过**：需求、消息、状态迁移和数据库约束相互支持，未发现矛盾。
- **通过但待同步**：设计推演成立，但顺序图/协作图/类图之间有一处文字或步骤需要组内同步。
- **待核验**：依赖 D 的状态图/活动图，当前只能核对期望迁移，不能核对图形本身。

---

## 2. 走查场景总表

| 编号 | 类型 | 场景 | 初始条件摘要 | 预期结果摘要 | 模型依据 | 结论 |
|---|---|---|---|---|---|---|
| N-01 | 正常 | 发布书籍成功 | 卖家存在；必填齐全；价格 ≥ 0 | 新增 `AVAILABLE` 记录；返回 `bookId` | C-04；`sequence/04`；`BookService.createListing`；`book_listing.status` | 通过 |
| N-02 | 正常 | 检索并查看 | 已有书籍；含 `AVAILABLE`/`RESERVED` | 返回带状态的列表和详情；不修改状态 | C-05；`sequence/05`；`SearchService`；`BookListing.status` | 通过 |
| N-03 | 正常 | 下单预留 | 书籍 `AVAILABLE`；买家 ≠ 卖家；无 `ACTIVE` 订单 | 新建 `ACTIVE` 订单；书籍 `RESERVED` | C-01；`sequence/01`；`ReservationService`；唯一索引 | 通过 |
| N-04 | 正常 | 取消订单 | 订单 `ACTIVE`；请求者 = 买家；无其他有效订单 | 订单 `CANCELLED`；书籍 `AVAILABLE`；历史保留 | C-02；`sequence/02`；`CancellationService`；状态守卫 | 通过 |
| E-01 | 输入校验 | 发布信息不合法 | 缺少必填字段，或价格为负/格式错误，或卖家不存在 | 拒绝提交；不创建发布记录 | C-04 `E1`～`E3`；`sequence/04` `alt`；`CHECK`/`NOT NULL`/`FK` | 通过 |
| E-02 | 异常 | 买家预留自己的书 | `buyerId == sellerId`；书籍 `AVAILABLE` | `reject(SELF_RESERVATION)`；不建订单；书籍不变 | C-01 `E1`；`sequence/01` `alt`；应用层跨表校验 | 通过 |
| E-03 | 异常/并发 | 重复请求或并发下单 | 书籍已 `RESERVED`，或已有 `ACTIVE` 订单，或并发请求同时到达 | 只允许一个成功；其余 `reject(BOOK_RESERVED)`；不新增有效订单 | C-01 `E2`/`E3`；`sequence/01` `alt`；`active_book_key` 唯一索引 | 通过 |
| E-04 | 异常 | 越权取消 | 订单 `ACTIVE`；请求者 ≠ 订单买家 | `reject(FORBIDDEN)`；订单 `ACTIVE`；书籍 `RESERVED` | C-02 `E1`；`sequence/02` `alt`；`CancellationService` 守卫 | 通过 |
| E-05 | 异常 | 重复取消 | 订单已 `CANCELLED` | `reject(ALREADY_CANCELLED)`；不重复修改书籍 | C-02 `E2`；`sequence/02` `alt`；状态图禁止 `CANCELLED → CANCELLED` | 通过 |
| B-01 | 边界 | 取消后重订，旧请求晚到 | 订单 A `ACTIVE`，书籍 `RESERVED`；A 取消后 B 重订；A 的旧取消请求晚到 | A 保留 `CANCELLED`；B 为唯一 `ACTIVE` 订单；书籍 `RESERVED`；旧请求被拒绝 | C-03；`sequence/03`；唯一索引；状态守卫 | 通过但待同步 |

---

## 3. 场景展开

### N-01 发布书籍成功

**初始条件**

- 卖家账号 `sellerId` 存在；
- 书名、作者、分类、成色非空，价格 `price >= 0`；
- 分类字段按当前 `book_listing.category` 字符串取值。

**操作与输入**

`submitBook(sellerId, title, author, category, condition, price)`。

**预期结果**

1. 发布界面调用 `BookService.createListing(bookInfo)`；
2. `UserAccount.checkSeller(sellerId)` 返回存在；
3. `validateRequiredAndPrice(bookInfo)` 返回合法；
4. 事务内插入一条 `book_listing`，`status = AVAILABLE`；
5. 提交事务，返回 `PublishResult(bookId, AVAILABLE)`；
6. 失败时不留下部分记录。

**模型依据**

- 协作图 C-04：`1 → 1.1 → 1.1.1 → 1.1.2 → 1.1.3 → 1.1.4/1.1.4.1 → 1.1.5 → 1.2`；
- 顺序图 `sequence/04` 的正常流程；
- 数据库：`book_listing.status` 默认 `AVAILABLE`，`price >= 0`、书名/作者 `NOT NULL`；
- 状态图期望：`BookListing` 初始状态为 `AVAILABLE`。

**核对结论**

通过。发布成功只创建一条 `AVAILABLE` 记录，不涉及订单表；与数据库默认值和顺序图一致。

---

### N-02 检索并查看

**初始条件**

- 数据库中存在至少一条 `AVAILABLE` 书籍，可能还存在 `RESERVED` 书籍；
- 用户输入关键词 `数据结构`，分类 `计算机`。

**操作与输入**

`search(keyword, category)`，再对结果中的 `bookId` 调用 `viewDetails(bookId)`。

**预期结果**

1. `SearchService.searchBooks` 返回匹配的 `BookSummary[]`；
2. 每条结果携带 `book_listing.status`，`AVAILABLE` 与 `RESERVED` 必须区分显示；
3. 查看详情返回 `BookDetails + current status`；
4. 全流程不调用 `markReserved`、`markAvailable`，不修改任何状态；
5. 无匹配时提示未找到，不把空结果当成异常崩溃。

**模型依据**

- 协作图 C-05：`1.x` 检索、`2.x` 详情；
- 顺序图 `sequence/05` 的正常流程和 `alt` 边界；
- 数据库：`book_listing.status` 的 `CHECK` 只允许两个值；
- 活动图期望：检索→判断有结果→展示列表→选择详情→判断存在→展示详情；无结果和详情不存在分别走向提示出口。

**核对结论**

通过。检索与查看是只读业务；`RESERVED` 只能作为状态展示，不能显示为可售，也不能触发下单。该约束需要在界面文案和类方法返回值中都体现。

---

### N-03 正常下单预留

**初始条件**

- 书籍 `bookId` 的 `status = AVAILABLE`；
- `buyerId != book.seller_id`；
- 该书籍不存在 `ACTIVE` 订单；
- 买家账号存在。

**操作与输入**

`submitReservation(buyerId, bookId)`。

**预期结果**

1. `ReservationService.reserveBook` 读取书籍，得到 `sellerId` 和 `status`；
2. 查询 `reservation_order` 的有效订单，得到 `null`；
3. 开启事务；
4. 新建 `reservation_order`，`status = ACTIVE`；
5. `book_listing.status` 更新为 `RESERVED`；
6. 提交事务，返回 `ReservationResult(orderId, ACTIVE)`；
7. 订单与书籍状态在同一事务中生效，不出现“订单已建、书籍仍可售”的中间结果。

**模型依据**

- 协作图 C-01：`1 → 1.1 → 1.1.1 → 1.1.2 → 1.1.3 → 1.1.4/1.1.4.1 → 1.1.5/1.1.5.1 → 1.1.6 → 1.2 → 1.3`；
- 顺序图 `sequence/01` 的正常流程；
- 数据库：`active_book_key` 唯一索引保证同一书籍最多一个 `ACTIVE` 订单；
- 状态图期望：`BookListing.AVAILABLE → RESERVED`，`ReservationOrder` 初始 `ACTIVE`；
- 活动图期望：正常路径经过“校验自购→校验状态/有效订单→开启事务→建单→改书籍→提交”。

**核对结论**

通过。关键是事务边界和唯一索引同时存在：唯一索引防止并发插入两条有效订单，事务保证订单与书籍状态一起提交或一起回滚。

---

### N-04 正常取消订单

**初始条件**

- 订单 `orderId` 的 `status = ACTIVE`；
- `requesterId == order.buyer_id`；
- 对应书籍 `status = RESERVED`；
- 该书籍没有其他 `ACTIVE` 订单。

**操作与输入**

`cancel(orderId, requesterId)`。

**预期结果**

1. `CancellationService.cancelOrder` 读取订单，确认买家与状态；
2. 开启事务；
3. 将订单改为 `CANCELLED`，写入 `cancelled_at`；
4. 查询该书籍是否还有新的 `ACTIVE` 订单（排除本订单）；
5. 没有其他有效订单时，书籍 `RESERVED → AVAILABLE`；
6. 提交事务，返回 `CancelResult(success)`；
7. 订单记录不删除，保留历史。

**模型依据**

- 协作图 C-02：`1 → 1.1 → 1.1.1 → 1.1.2 → 1.1.3 → 1.1.4 → 1.1.5/1.1.5.1 → 1.1.6 → 1.1.7 → 1.2 → 1.3`；
- 顺序图 `sequence/02` 的正常流程；
- 数据库：`chk_reservation_order_cancel_time` 要求 `CANCELLED` 时 `cancelled_at` 非空；
- 状态图期望：`ReservationOrder.ACTIVE → CANCELLED`；`BookListing.RESERVED → AVAILABLE` 的守卫是“无其他有效订单”；
- 活动图期望：取消流程先改订单，再判断书籍是否可恢复。

**核对结论**

通过。取消流程的顺序不能反过来：如果先把书籍改成 `AVAILABLE`，再判断是否还有新订单，就可能把已被新订单占用的书籍错误释放。协作图在 `1.1.6` 上标注了 `[activeOrder == null]` 守卫。

---

### E-01 发布信息不合法

**初始条件与输入**

- 缺少书名/作者/分类/成色/价格之一；
- 或 `price < 0` / 不是合法数字；
- 或 `sellerId` 在 `user_account` 中不存在。

**预期结果**

- 分别返回 `reject(MISSING_FIELD)`、`reject(INVALID_PRICE)`、`reject(SELLER_NOT_FOUND)`；
- 不创建 `book_listing`；
- 不产生部分写入；已有发布记录不受影响。

**模型依据**

- 协作图 C-04 `E1`～`E3`；
- 顺序图 `sequence/04` `alt` 三个分支；
- 数据库：`NOT NULL`、`CHECK price >= 0`、外键 `fk_book_listing_seller`；
- 活动图期望：校验失败走向异常出口，不进入插入节点。

**核对结论**

通过。数据库能兜底 `NOT NULL`、价格和卖家存在性；缺字段的具体提示由应用层负责。数据库外键不能区分“用户存在但已禁用”，因此若要求账号状态，需额外校验（见 R-03）。

---

### E-02 买家预留自己的书

**初始条件与输入**

- `buyerId == book.seller_id`；
- 书籍 `AVAILABLE`；
- 买家提交预留请求。

**预期结果**

- 返回 `reject(SELF_RESERVATION)`；
- 不创建订单；
- 书籍保持 `AVAILABLE`；
- 不改变其他订单。

**模型依据**

- 协作图 C-01 `E1`；
- 顺序图 `sequence/01` `alt` 第一个分支；
- 数据库无法用普通外键表达“买家 ≠ 卖家”，必须由 `ReservationService` 在创建订单前比较 `buyerId` 与 `book.seller_id`；
- 活动图期望：在“查询书籍”之后有一个“买家是否为卖家”的判定，true 走拒绝出口。

**核对结论**

通过。该规则是跨表规则，不能误写成数据库 `CHECK`；应在服务层校验，并保留明确错误码。

---

### E-03 重复请求或并发下单

**初始条件与输入**

- 场景 A：书籍已经 `RESERVED`，或已存在 `ACTIVE` 订单；
- 场景 B：两个请求几乎同时到达，都通过了前置查询；
- 操作：再次 `submitReservation`。

**预期结果**

- 前置查询发现 `status != AVAILABLE` 或存在 `ACTIVE` 订单时，返回 `reject(BOOK_RESERVED)`，不新增订单；
- 前置查询都通过但并发写入冲突时，数据库唯一约束/条件更新失败，事务回滚，返回 `BOOK_RESERVED`；
- 最终最多一条 `ACTIVE` 订单，书籍保持 `RESERVED`；
- 失败请求不改变原订单和书籍状态。

**模型依据**

- 协作图 C-01 `E2`/`E3`；
- 顺序图 `sequence/01` `alt` 第二、第三个分支；
- 数据库：`active_book_key` 生成列只在 `status = 'ACTIVE'` 时等于 `book_id`，`uk_reservation_order_active_book` 唯一索引允许多个 `NULL`、只允许一个 `ACTIVE`；
- 状态图期望：没有 `RESERVED → RESERVED` 或 `ACTIVE → ACTIVE` 的新增迁移，失败停留在原状态；
- 活动图期望：并发失败走回滚出口，不进入“更新书籍”节点。

**核对结论**

通过。该场景是“应用校验 + 数据库唯一约束 + 事务回滚”三层配合的典型例子；只靠先查后写不能防止并发。

---

### E-04 越权取消

**初始条件与输入**

- 订单 `ACTIVE`；
- `requesterId != order.buyer_id`；
- 操作：`cancel(orderId, requesterId)`。

**预期结果**

- 返回 `reject(FORBIDDEN)`；
- 订单保持 `ACTIVE`，`cancelled_at` 仍为 `NULL`；
- 书籍保持 `RESERVED`；
- 不泄露订单是否存在的额外信息（可选的安全要求）。

**模型依据**

- 协作图 C-02 `E1`；
- 顺序图 `sequence/02` `alt` 第一个分支；
- 数据库外键只保证 `buyer_id` 存在，不能保证“请求者就是买家”；
- 状态图期望：`ACTIVE → CANCELLED` 的守卫包含 `requesterId == buyerId`；
- 活动图期望：读取订单后先判断请求者，再判断订单状态。

**核对结论**

通过。越权取消不应进入事务；即使进入，也必须在更新前拒绝，避免产生 `cancelled_at` 或书籍状态变化。

---

### E-05 重复取消

**初始条件与输入**

- 订单已经是 `CANCELLED`；
- 同一买家再次提交 `cancel(orderId, buyerId)`。

**预期结果**

- 返回 `reject(ALREADY_CANCELLED)`；
- 不重复写 `cancelled_at`；
- 不再次修改书籍状态；
- 若书籍已被新订单占用，保持 `RESERVED`。

**模型依据**

- 协作图 C-02 `E2`；
- 顺序图 `sequence/02` `alt` 第二个分支；
- 数据库：`chk_reservation_order_cancel_time` 约束状态与取消时间一致，重复更新会违反“CANCELLED 时 cancelled_at 非空”以外的业务语义，但不会自动阻止重复请求；
- 状态图期望：`CANCELLED` 是终止状态，不允许 `CANCELLED → CANCELLED` 或重新激活；
- 活动图期望：读到 `CANCELLED` 后直接走“已取消”提示出口。

**核对结论**

通过。重复取消是幂等性要求：第二次请求不能因为“订单已取消”就顺带把书籍改成 `AVAILABLE`，否则可能释放已被新订单占用的书籍。

---

### B-01 取消后重订，旧请求晚到

**初始条件**

1. 买家 A 对书籍 `book` 创建订单 A，订单 A 为 `ACTIVE`，书籍为 `RESERVED`；
2. 买家 A 取消订单 A，订单 A 变为 `CANCELLED`，书籍恢复 `AVAILABLE`；
3. 买家 B 重新预留同一书籍，创建订单 B，订单 B 为 `ACTIVE`，书籍变为 `RESERVED`；
4. 此时买家 A 的旧取消请求（针对订单 A）晚到。

**操作与输入**

- 依次执行：`cancel(orderA, buyerA)`、`reserve(book, buyerB)`、`cancel(orderA, buyerA)`（旧请求）；
- 旧请求的 `orderId` 仍是订单 A。

**预期结果**

1. 订单 A 保留 `CANCELLED`，历史不删除；
2. 订单 B 为唯一 `ACTIVE` 订单；
3. 书籍保持 `RESERVED`；
4. 旧请求检测到订单 A 已非 `ACTIVE`，返回 `reject(OLD_REQUEST)`；
5. 旧请求不得修改订单 B，也不得把书籍改成 `AVAILABLE`；
6. 并发情况下同样由唯一索引和事务保证最多一个 `ACTIVE`。

**模型依据**

- 协作图 C-03：`1.x` 取消 A、`2.x` 重订 B、`3.x` 旧请求晚到；
- 顺序图 `sequence/03` 的正常流程和“旧取消请求晚到”`alt`；
- 数据库：`active_book_key` 唯一索引；`reservation_order.status` 的 `CHECK`；
- 状态图期望：`CANCELLED` 为终止状态；`RESERVED → AVAILABLE` 只在无其他 `ACTIVE` 订单时发生；
- 活动图期望：取消流程查询“当前有效订单”时排除本订单；旧请求在状态判断处直接拒绝。

**核对结论**

通过但待同步。协作图已把顺序图只用注释表示的“旧请求晚到”展开为 `3`、`3.1`、`3.1.1`、`3.2` 四条消息；建议 B 在顺序图 03 中补画这组消息，或明确说明该分支以注释为准。另，顺序图 03 第二次预留只画了 `commit()`，协作图补了 `2.2 beginTransaction()`，需要 B 确认事务边界。

---

## 4. 跨模型一致性问题与修订

| 编号 | 位置 | 发现 | 处理/修订 | 状态 |
|---|---|---|---|---|
| R-01 | 实验二发布模块与实验三共享模型 | 实验二使用 `book`、`book_status=ON_SALE/RESERVED`；实验三顺序图使用 `book_listing`、`status=AVAILABLE/RESERVED` | 实验三统一采用 `book_listing`/`AVAILABLE`，与 B 的顺序图和 `sql/02` 一致；正式建库前由小组决定是否把实验二脚本改为同一命名 | 待组内确认 |
| R-02 | `sequence/02` 取消顺序 | 先改订单状态，再查询其他有效订单；查询必须排除本订单，但顺序图未写出该条件 | 协作图在 `findCurrentActiveOrder` 说明中写“排除本订单”，在 `markAvailable` 上加守卫 `[activeOrder == null]`；建议 B 在顺序图补守卫文字 | 待同步 |
| R-03 | `sequence/04` 发布校验 | 只校验 `seller exists`；`user_account` 当前没有账号状态字段，无法校验 `ACTIVE` | 本次按“发布者存在”作为基线；若课程/小组要求 `ACTIVE`，需给 `user_account` 增加状态字段并修改 `checkSeller`、顺序图和数据库脚本 | 待组内确认 |
| R-04 | `sequence/03` 旧请求晚到 | 只用 `alt` 文字描述，没有画出买家 A 的第二次取消消息 | 协作图补充 `3`、`3.1`、`3.1.1`、`3.2`；建议 B 同步 | 待同步 |
| R-05 | `sequence/03` 第二次预留 | 只画 `commit()`，未画 `beginTransaction()` | 协作图补充 `2.2 beginTransaction()`；若事务由外层统一管理，应在顺序图注明 | 待同步 |
| R-06 | 分类字段 | 实验二使用 `book_category` 字典表 + `category_id`；实验三 `book_listing.category` 是字符串 | 实验三按 B 的顺序图和 `sql/02` 使用字符串；若小组决定规范化，需要同时修改五类图、SQL 和界面输入 | 待组内确认 |
| R-07 | 状态范围 | 实验二曾出现 `SOLD`，实验三顺序图只使用 `AVAILABLE/RESERVED` | 实验三不设 `SOLD`；D 的状态图/活动图不得新增交易完成状态 | 已按当前基线执行 |

---

## 5. 走查结论

1. **正常路径**：发布、检索、下单、取消四个正常场景均能在协作图、顺序图和数据库约束之间闭环；订单与书籍状态的同步更新是下单/取消的关键事务边界。
2. **异常路径**：自购、重复/并发下单、越权取消、重复取消都能在协作图 `alt` 面板和服务层守卫中找到对应处理；数据库唯一索引是并发场景的最后防线。
3. **边界路径**：取消后重订的关键不是“取消”本身，而是“旧取消请求晚到”不能影响新订单；协作图 03 用显式消息表达了这一点。
4. **跨图一致性**：当前发现的主要问题不是业务规则冲突，而是命名和图形表达差异（`book`/`book_listing`、`ON_SALE`/`AVAILABLE`、分类字典/字符串、旧请求晚到未画出）。这些问题已记录在 R-01～R-07，需在最终合并前由组内确认。
5. **待核验**：D 的状态图/活动图尚未提交，B-01、E-03、E-05 等场景的“状态迁移是否合法、活动图是否有对应异常出口”只能按期望模型核对，待 D 提交后在 `design/cross-check/state-activity-check.md` 补充实际检查结论。

---

*以上结论为设计推演，未运行程序，未执行数据库建表或事务测试。*
