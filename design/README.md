# 实验三 软件设计（共享设计）

> 课程：软件工程导论实验 · 实验三 软件设计  
> 范围：校园二手书交易平台的发布书籍、检索与查看、下单预留、取消订单四项核心业务  
> 说明：本目录只保存共享设计模型与说明，个人报告和答辩记录另行提交。

---

## 1. 当前完成情况

| 分工 | 主责模型 | 当前状态 | 入口 |
|---|---|---|---|
| A（组长） | 类图、关键操作说明 | 待提交 | — |
| B | 顺序图、正常与异常交互 | 已提交 5 张顺序图 | [`sequence/`](sequence/) |
| C（本人） | 协作图、消息对应说明、场景走查汇总 | 已完成 5 张通信图、消息对应表、10 个场景走查 | [`collaboration/`](collaboration/)、[`walkthrough/`](walkthrough/) |
| D | 状态图、活动图 | 待提交 | — |

C 同时负责交叉检查 D 的状态图与活动图。当前仓库版本尚未包含 D 的成果，因此 [`cross-check/`](cross-check/) 先给出检查清单、期望状态迁移和活动流程；待 D 提交后再逐项核验并补充结论。

---

## 2. 设计范围与基线

### 2.1 业务范围

1. **发布书籍**：卖家提交书籍信息，系统校验后创建发布记录，初始状态为 `AVAILABLE`。
2. **检索与查看**：校园用户按关键词/分类检索，查看书籍详情和当前状态；本业务只读。
3. **下单预留**：买家为可售书籍提交预留请求；成功后创建 `ACTIVE` 订单，书籍变为 `RESERVED`。
4. **取消订单**：仅订单买家本人可取消 `ACTIVE` 订单；成功后订单变为 `CANCELLED`，在没有其他有效订单时书籍恢复 `AVAILABLE`，历史保留。

不包含支付、退款、物流、交易完成、评价和推荐。

### 2.2 命名基线

实验二的两套数据库材料存在命名差异：发布模块使用 `book` / `ON_SALE`，下单模块使用 `book_listing` / `AVAILABLE`。实验三的共享顺序图已经采用下单模块的命名，为避免五类图之间再次分叉，本次设计统一采用下表口径：

| 模型元素 | 类名 | 持久化表/字段 | 状态值 |
|---|---|---|---|
| 用户账号 | `UserAccount` | `user_account(user_id, username, created_at)` | — |
| 书籍发布记录 | `BookListing` | `book_listing`（`book_id`、`seller_id`、`title`、`author`、`category`、`book_condition`、`price`、`description`、`cover_url`、`status`） | `AVAILABLE` / `RESERVED` |
| 预留订单 | `ReservationOrder` | `reservation_order`（`order_id`、`buyer_id`、`book_id`、`status`、`created_at`、`cancelled_at`、`active_book_key`） | `ACTIVE` / `CANCELLED` |

界面类：`PublishUI`、`SearchUI`、`ReservationUI`、`OrderUI`。  
服务类：`BookService`、`SearchService`、`ReservationService`、`CancellationService`、`OrderService`（取消后重订场景的协调入口）。  
基础设施：`TransactionManager`（事务/数据库）。

> 该口径是实验三的共享设计口径，不表示实验二的建表脚本已经合并。正式建库前仍需组内统一 `book` / `book_listing`、`ON_SALE` / `AVAILABLE`、分类字典 / 分类字符串等差异；该问题已记录在场景走查的 R-01。

### 2.3 统一业务规则

| 编号 | 规则 | 主要落实位置 |
|---|---|---|
| BR-01 | 一条 `book_listing` 记录代表一本实体书，不设数量字段 | 类图属性；数据库表 |
| BR-02 | 发布必填书名、作者、分类、成色、价格；价格不得为负 | `BookService.validateRequiredAndPrice`；`CHECK price >= 0` |
| BR-03 | 买家不能预留自己发布的书籍 | `ReservationService.reserveBook`；应用层校验 |
| BR-04 | 同一本书同一时刻最多一条 `ACTIVE` 订单 | `chk_reservation_status_values`；`active_book_key` 唯一索引；事务 |
| BR-05 | 下单成功：订单 `ACTIVE`，书籍 `RESERVED`，两者同一事务提交 | `ReservationService`；`TransactionManager` |
| BR-06 | 仅订单买家本人可以取消 | `CancellationService.cancelOrder`；状态图守卫 |
| BR-07 | 取消成功：订单 `CANCELLED` 并记录 `cancelled_at`；仅当没有其他 `ACTIVE` 订单时书籍恢复 `AVAILABLE` | `CancellationService`；状态图/活动图守卫 |
| BR-08 | 取消不删除订单；重复取消、越权取消、旧请求晚到均不得改变当前有效订单和书籍状态 | `CancellationService`；异常分支 |
| BR-09 | 检索与查看只读，返回结果必须携带当前状态，`RESERVED` 不得显示为可售 | `SearchService`；`book_listing.status` |
| BR-10 | 不设 `SOLD` 状态；交易完成不在系统范围 | 状态图；数据库 `CHECK` |

---

## 3. 图与说明索引

### 3.1 顺序图（B 已提交）

- [`sequence/01_下单预留_正常与异常.svg`](sequence/01_下单预留_正常与异常.svg)
- [`sequence/02_取消订单_正常与异常.svg`](sequence/02_取消订单_正常与异常.svg)
- [`sequence/03_取消后重订_边界场景.svg`](sequence/03_取消后重订_边界场景.svg)
- [`sequence/04_发布书籍_正常与异常.svg`](sequence/04_发布书籍_正常与异常.svg)
- [`sequence/05_检索与查看_正常与异常.svg`](sequence/05_检索与查看_正常与异常.svg)

### 3.2 协作图（C 主责）

| 协作图 | 对应顺序图 | SVG | PNG |
|---|---|---|---|
| 下单预留 | `sequence/01` | [`collaboration/01_下单预留_通信图.svg`](collaboration/01_下单预留_通信图.svg) | [`collaboration/01_下单预留_通信图.png`](collaboration/01_下单预留_通信图.png) |
| 取消订单 | `sequence/02` | [`collaboration/02_取消订单_通信图.svg`](collaboration/02_取消订单_通信图.svg) | [`collaboration/02_取消订单_通信图.png`](collaboration/02_取消订单_通信图.png) |
| 取消后重订 | `sequence/03` | [`collaboration/03_取消后重订_通信图.svg`](collaboration/03_取消后重订_通信图.svg) | [`collaboration/03_取消后重订_通信图.png`](collaboration/03_取消后重订_通信图.png) |
| 发布书籍 | `sequence/04` | [`collaboration/04_发布书籍_通信图.svg`](collaboration/04_发布书籍_通信图.svg) | [`collaboration/04_发布书籍_通信图.png`](collaboration/04_发布书籍_通信图.png) |
| 检索与查看 | `sequence/05` | [`collaboration/05_检索与查看_通信图.svg`](collaboration/05_检索与查看_通信图.svg) | [`collaboration/05_检索与查看_通信图.png`](collaboration/05_检索与查看_通信图.png) |

- 协作图转换方法、对象与消息对应说明：[`collaboration/README.md`](collaboration/README.md)
- 完整消息表（含参数、返回、类方法和顺序图对应）：[`collaboration/message-mapping.md`](collaboration/message-mapping.md)

### 3.3 走查与交叉检查

- 10 个场景走查（4 个正常、4 个异常、1 个输入校验、1 个边界）：[`walkthrough/scenarios.md`](walkthrough/scenarios.md)
- D 状态图/活动图检查清单：[`cross-check/state-activity-check.md`](cross-check/state-activity-check.md)

---

## 4. 跨图一致性约定

1. **对象名一致**：五类图统一使用 `BookListing` / `book_listing`、`ReservationOrder` / `reservation_order`、`UserAccount` / `user_account`。
2. **操作名一致**：顺序图消息、协作图消息、类图方法采用同一英文动词，例如 `reserveBook`、`findActiveOrder`、`markCancelled`、`markAvailable`、`createListing`。
3. **状态名一致**：书籍只用 `AVAILABLE` / `RESERVED`；订单只用 `ACTIVE` / `CANCELLED`。
4. **状态迁移一致**：状态图的每条迁移都必须能对应一条协作图消息或一个明确的守卫条件；活动图的每个判定必须能对应业务规则或异常分支。
5. **分支一致**：顺序图 `alt` 面板、协作图 `alt` 面板、活动图异常出口、状态图非法迁移拒绝必须一一对应。
6. **数据一致**：跨表规则（买家不能是卖家、仅买家可取消、一书一有效订单）不能只靠外键；必须在服务层/事务中校验，并在走查中注明责任层。

---

## 5. 复现方式

协作图由 Python 3.12 标准库生成，不依赖第三方绘图库：

```powershell
py design/collaboration/tools/generate_communication.py
py design/collaboration/tools/generate_communication.py --png
```

- 第一条命令只更新 SVG 和 `message-mapping.md`；
- 第二条命令额外调用本机 Edge/Chrome 导出 PNG，便于插入 Word；
- 脚本 `build_scenarios()` 中的节点、消息、分支与 `message-mapping.md` 来自同一份数据，避免图、表不一致。

---

## 6. 待组内确认

1. A 的类图方法签名是否与本文第 2.2 节的对象/操作名一致；若不一致，以 A 最终类图为准并同步协作图与映射表。
2. D 的状态图/活动图是否采用 `AVAILABLE/RESERVED` 与 `ACTIVE/CANCELLED`；是否包含自购、越权、重复取消、旧请求晚到等异常出口。
3. 实验二 `book` / `ON_SALE` 与实验三 `book_listing` / `AVAILABLE` 的命名合并方案；正式建库前必须统一。
4. `user_account` 是否增加账号状态字段。当前 `user_account` 只有 `user_id`、`username`、`created_at`，发布顺序图只校验发布者存在；若要求校验 `ACTIVE`，需同步修改表结构和 `checkSeller`。

---

*本目录中的走查结论为设计推演；当前仓库不包含可运行程序，未执行数据库建表和运行时测试。*
