# D 状态图 / 活动图交叉检查清单与当前结论

> 主责：C（32406300079 王伟锋，软件243）  
> 检查对象：D 负责的状态图、活动图及相关规则  
> 当前状态：**待 D 提交图形后逐项核验**。截至本文件编写时，仓库 `main`（`eb20144`）只有顺序图和协作图，没有状态图/活动图文件，因此不能声称已完成“图形本身”的核对。  
> 本文件先给出检查依据、期望状态迁移、期望活动流程和检查表；D 提交后直接按表逐项填写“位置、发现、处理/确认依据”。

---

## 1. 检查依据

1. `design/README.md` 第 2.3 节的统一业务规则；
2. `design/sequence/01`～`05` 的调用顺序、守卫和异常分支；
3. `design/collaboration/01`～`05` 的消息序号与 `alt` 面板；
4. `database/README.md`、`database/design.md`、`database/data-dictionary.md`；
5. `sql/01_user_account.sql`、`sql/02_book_listing.sql`、`sql/03_reservation_order.sql`；
6. 实验一需求基线：发布、检索、下单预留、取消订单；不包含支付、退款、物流、交易完成。

---

## 2. 期望状态模型（用于比对 D 的图）

### 2.1 `BookListing`（书籍发布记录）

| 项目 | 期望内容 | 依据 |
|---|---|---|
| 初始状态 | `AVAILABLE` | `sequence/04` 发布成功；`book_listing.status` 默认值 |
| 合法状态 | `AVAILABLE`、`RESERVED` | `sql/02` 的 `chk_book_listing_status` |
| 终态 | 无（交易完成不在范围；记录不因取消删除） | 实验一范围；`design/README.md` |
| 非法状态 | `SOLD`、`CANCELLED`、`DELETED` 等 | 当前范围不包含交易完成/删除 |
| 迁移 1 | 创建 → `AVAILABLE` [卖家存在、必填齐全、价格 ≥ 0] / 创建记录 | `sequence/04`；`BookService.createListing` |
| 迁移 2 | `AVAILABLE → RESERVED` [买家 ≠ 卖家；无 `ACTIVE` 订单；下单事务成功] / 更新状态 | `sequence/01`；`BookListing.markReserved` |
| 迁移 3 | `RESERVED → AVAILABLE` [取消订单成功；无其他 `ACTIVE` 订单] / 更新状态 | `sequence/02`；`BookListing.markAvailable` |
| 禁止迁移 | `RESERVED → RESERVED`（重复下单不改变状态）、`AVAILABLE → AVAILABLE`（取消已取消订单不重复恢复） | `sequence/01`、`sequence/02` 异常分支 |
| 持久化约束 | `status IN ('AVAILABLE','RESERVED')`；`price >= 0`；书名/作者非空 | `sql/02` |

### 2.2 `ReservationOrder`（预留订单）

| 项目 | 期望内容 | 依据 |
|---|---|---|
| 初始状态 | `ACTIVE` | `sequence/01` 创建订单；`reservation_order.status` 默认值 |
| 合法状态 | `ACTIVE`、`CANCELLED` | `sql/03` 的 `chk_reservation_status_values` |
| 终态 | `CANCELLED`（不可重新激活；历史保留） | 实验一取消约定；状态不可逆设计 |
| 非法状态 | `PAID`、`COMPLETED`、`EXPIRED`、`DELETED` 等 | 支付/交易完成不在范围 |
| 迁移 1 | 创建 → `ACTIVE` [书籍 `AVAILABLE`；买家 ≠ 卖家；唯一有效订单约束满足] / 插入订单 | `sequence/01`；`ReservationOrder.createActive` |
| 迁移 2 | `ACTIVE → CANCELLED` [请求者 = 买家；订单仍 `ACTIVE`] / 更新状态并写 `cancelled_at` | `sequence/02`；`ReservationOrder.markCancelled` |
| 禁止迁移 | `CANCELLED → ACTIVE`（重新激活旧订单）、`CANCELLED → CANCELLED`（重复取消） | `sequence/02`、`sequence/03` 异常分支 |
| 持久化约束 | `status IN ('ACTIVE','CANCELLED')`；`ACTIVE` 时 `cancelled_at IS NULL`，`CANCELLED` 时非空；`active_book_key` 唯一 | `sql/03` |

### 2.3 状态与消息的对应

| 状态迁移/动作 | 对应协作图消息 | 对应顺序图 | 检查点 |
|---|---|---|---|
| 创建书籍为 `AVAILABLE` | C-04 `1.1.4` / `1.1.4.1` | `sequence/04` `insert listing(status=AVAILABLE)` | 状态图是否有“创建→AVAILABLE”的初始迁移 |
| 订单创建为 `ACTIVE` | C-01 `1.1.4` / `1.1.4.1` | `sequence/01` `create ACTIVE order` | 状态图是否把 `ACTIVE` 标为初始状态 |
| 书籍 `AVAILABLE → RESERVED` | C-01 `1.1.5` / `1.1.5.1` | `sequence/01` `mark status = RESERVED` | 迁移守卫是否包含“买家 ≠ 卖家、无有效订单” |
| 订单 `ACTIVE → CANCELLED` | C-02 `1.1.3` / `1.1.4` | `sequence/02` `UPDATE status = CANCELLED`、`set cancelled_at` | 迁移动作是否同时写 `cancelled_at` |
| 书籍 `RESERVED → AVAILABLE` | C-02 `1.1.5` / `1.1.5.1` / `1.1.6` | `sequence/02` `findCurrentActiveOrder`、`UPDATE status = AVAILABLE` | 迁移守卫是否包含“无其他 `ACTIVE` 订单” |
| 旧请求晚到拒绝 | C-02 `E3`；C-03 `3.x` | `sequence/02` `alt`；`sequence/03` `alt` | 状态图是否允许 `CANCELLED` 再次迁移；活动图是否有拒绝出口 |
| 重复/并发下单拒绝 | C-01 `E2` / `E3` | `sequence/01` `alt` | 状态图是否有失败停留；活动图是否有回滚出口 |

---

## 3. 期望活动流程（用于比对 D 的图）

### 3.1 发布书籍

```text
开始
→ 接收发布表单
→ 校验卖家存在？ ──否──→ 提示 SELLER_NOT_FOUND → 结束（不创建记录）
→ 校验必填字段和价格？ ──否──→ 提示缺失字段/INVALID_PRICE → 结束（不创建记录）
→ 开启事务
→ 插入 book_listing(status=AVAILABLE)
→ 提交事务
→ 返回 PublishResult
→ 结束
```

活动图检查点：开始/结束、两个判定、异常出口、事务活动、插入活动是否齐全。

### 3.2 下单预留

```text
开始
→ 接收 buyerId、bookId
→ 查询书籍
→ 买家 == 卖家？ ──是──→ 拒绝 SELF_RESERVATION → 结束（不建单）
→ 书籍 AVAILABLE 且无 ACTIVE 订单？ ──否──→ 拒绝 BOOK_RESERVED → 结束（不建单）
→ 开启事务
→ 创建 reservation_order(ACTIVE)
→ 更新 book_listing.status = RESERVED
→ 提交事务
→ 返回 ReservationResult
→ 结束

并发冲突：唯一约束/条件更新失败 → 回滚 → 返回 BOOK_RESERVED → 结束
```

活动图检查点：两个判定、事务、创建/更新两个活动、并发回滚出口。

### 3.3 取消订单

```text
开始
→ 接收 orderId、requesterId
→ 查询订单
→ requesterId == buyerId？ ──否──→ 拒绝 FORBIDDEN → 结束（不改状态）
→ 订单 ACTIVE？ ──否──→ 拒绝 ALREADY_CANCELLED/OLD_REQUEST → 结束（不改状态）
→ 开启事务
→ 订单 status = CANCELLED，写 cancelled_at
→ 查询该书籍其他 ACTIVE 订单（排除本订单）
→ 存在其他 ACTIVE 订单？ ──是──→ 保持书籍 RESERVED
                              └─否──→ 书籍 status = AVAILABLE
→ 提交事务
→ 返回 CancelResult
→ 结束
```

活动图检查点：顺序必须是“先改订单、再查其他订单、最后按条件恢复书籍”；不能先恢复书籍再查询；必须有越权、重复取消、旧请求晚到三个拒绝出口。

### 3.4 取消后重订

```text
开始
→ 订单 A 取消（按 3.3）
→ 书籍恢复 AVAILABLE
→ 买家 B 预留（按 3.2）
→ 订单 B ACTIVE，书籍 RESERVED
→ 订单 A 的旧取消请求晚到
→ 订单 A 已 CANCELLED？ ──是──→ 拒绝 OLD_REQUEST → 结束
→ 不修改订单 B，不修改书籍状态
```

活动图检查点：是否表达“旧请求晚到”是独立的异常出口；是否明确不影响新订单。

### 3.5 检索与查看

```text
开始
→ 接收关键词/分类
→ 查询匹配书籍
→ 有匹配？ ──否──→ 提示无结果 → 结束
→ 展示列表（带 AVAILABLE/RESERVED 状态）
→ 选择书籍查看详情
→ 记录存在？ ──否──→ 提示详情不可用 → 结束
→ 展示详情和当前状态
→ 结束
```

活动图检查点：只读；没有更新状态的 activity；`RESERVED` 必须原样展示。

---

## 4. 检查表（D 提交后填写）

| 编号 | 检查项 | 判定标准 | 位置（D 的图/文字） | 发现（D 提交后填） | 处理/确认依据 | 当前结论 |
|---|---|---|---|---|---|---|
| SA-01 | `BookListing` 初始状态 | 必须是 `AVAILABLE`，不能是 `ON_SALE`/`SOLD` | 待填 | 待填 | 待填 | 待 D 提交 |
| SA-02 | `BookListing` 状态集合 | 只允许 `AVAILABLE`、`RESERVED` | 待填 | 待填 | 待填 | 待 D 提交 |
| SA-03 | 下单迁移守卫 | `AVAILABLE → RESERVED` 必须包含“买家 ≠ 卖家、无 `ACTIVE` 订单、事务成功” | 待填 | 待填 | 待填 | 待 D 提交 |
| SA-04 | 取消迁移守卫 | `RESERVED → AVAILABLE` 必须包含“无其他 `ACTIVE` 订单” | 待填 | 待填 | 待填 | 待 D 提交 |
| SA-05 | 订单初始状态 | `ReservationOrder` 必须是 `ACTIVE` | 待填 | 待填 | 待填 | 待 D 提交 |
| SA-06 | 订单状态集合 | 只允许 `ACTIVE`、`CANCELLED`；`CANCELLED` 为终态 | 待填 | 待填 | 待填 | 待 D 提交 |
| SA-07 | 取消动作 | `ACTIVE → CANCELLED` 必须同时写 `cancelled_at` | 待填 | 待填 | 待填 | 待 D 提交 |
| SA-08 | 非法迁移 | 重复取消、重复下单、旧请求晚到不得产生新状态 | 待填 | 待填 | 待填 | 待 D 提交 |
| SA-09 | 活动图起止 | 发布/下单/取消/重订/检索均有开始和结束节点 | 待填 | 待填 | 待填 | 待 D 提交 |
| SA-10 | 活动图判定 | 自购、越权、重复、无结果、详情不存在均有判定和异常出口 | 待填 | 待填 | 待填 | 待 D 提交 |
| SA-11 | 活动图事务顺序 | 先建单/改单，再改书籍；回滚出口存在 | 待填 | 待填 | 待填 | 待 D 提交 |
| SA-12 | 只读业务 | 检索与查看活动图没有 `markReserved`/`markAvailable` 等写操作 | 待填 | 待填 | 待填 | 待 D 提交 |
| SA-13 | 与需求一致 | 不出现支付、退款、物流、交易完成、评价等范围外状态/活动 | 待填 | 待填 | 待填 | 待 D 提交 |
| SA-14 | 与数据库一致 | 状态值、`CHECK`、`cancelled_at`、`active_book_key` 与 `sql/02`、`sql/03` 一致 | 待填 | 待填 | 待填 | 待 D 提交 |
| SA-15 | 与顺序图/协作图一致 | 每条迁移/活动都能对应 C-01～C-05 中的消息或 `alt` 分支 | 待填 | 待填 | 待填 | 待 D 提交 |

> “位置、发现、处理/确认依据”按指导书要求填写；D 提交前统一为“待填/待 D 提交”。D 提交后应改为“一致 / 不一致（已记录并修改）+ 具体位置”，不能只写“看过”。

---

## 5. 提交后重点核对的高风险点

1. **状态名分叉**：D 若沿用实验二的 `ON_SALE`，会与 B/C 的 `AVAILABLE` 冲突；必须统一。
2. **取消顺序画反**：先 `book → AVAILABLE` 再查询其他订单，会把已被新订单占用的书籍错误释放。
3. **缺少守卫**：`RESERVED → AVAILABLE` 如果没有“无其他 `ACTIVE` 订单”守卫，B-01 边界场景不成立。
4. **重复取消**：若把 `CANCELLED` 画成可再次进入取消活动，会违反“历史保留、不可重复修改”的约定。
5. **旧请求晚到**：活动图若没有独立拒绝出口，无法解释订单 A 的旧请求为何不影响订单 B。
6. **只读业务被画成写操作**：检索/查看活动图若出现状态更新，违反 RQ-08。
7. **缺少异常出口**：发布缺字段/负价、自购、重复下单、越权取消、重复取消都应有异常结束或返回节点。
8. **事务边界缺失**：下单/取消活动图若没有“开启事务/提交/回滚”，无法与顺序图的 `beginTransaction/commit/rollback` 对应。

---

## 6. 交叉检查记录（D 提交后填写）

| 日期 | 检查人 | D 的提交版本/链接 | 发现问题数 | 处理结果 | 复核人 |
|---|---|---|---|---|---|
| 待填 | 王伟锋（C） | 待填 | 待填 | 待填 | 待填 |

---

*本文件当前只完成检查依据、期望模型和检查表；未对 D 的实际图形作出“已通过”结论。*
