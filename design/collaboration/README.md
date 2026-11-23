# 协作图（通信图）与消息对应说明

> 主责：C（32406300079 王伟锋，软件243）  
> 输入：`design/sequence/` 下 B 提交的五张顺序图  
> 输出：五张通信图、对象与消息对应表、与顺序图的逐项核对结论  
> 相关文件：[场景走查汇总](../walkthrough/scenarios.md)、[D 状态图/活动图检查清单](../cross-check/state-activity-check.md)  
> 说明：本次未运行程序，交互结论为设计推演；图由 `tools/generate_communication.py` 生成。

---

## 1. 为什么画五张协作图

实验要求至少 1 张协作图，并附对象与消息对应说明。由于 B 已经为发布、检索、下单、取消、取消后重订五个场景各画了一张顺序图，本部分对五个场景逐一转换，目的是：

1. 保证协作图与顺序图的对象集合、消息方向、分支条件完全对应；
2. 让 C 负责的“消息对应说明”可以直接作为五张图的公共索引；
3. 为后续 D 的状态图/活动图交叉检查提供消息级证据；
4. 避免只画一张核心图时，其他场景的对象职责无法被检查。

五张图都以正常流程为主线，异常/备选分支放在图下方的 `alt` 面板中，与顺序图的 `alt` 面板一一对应。异常分支不进入正常序号，避免把“失败路径”误读为必经步骤。

---

## 2. 转换方法

### 2.1 转换步骤

1. **抽取对象**：读取顺序图的生命线，按 Actor、Boundary、Control、Entity、Infra 分类，保留同名对象。
2. **抽取消息**：按顺序图自上而下的消息顺序抽取调用与返回；返回消息用虚线箭头表示。
3. **建立连接**：只保留实际发生消息的对象对；没有消息的对象之间不画连线，避免出现“有关联但无交互”的误导。
4. **编号**：采用分层序号。顶层请求为 `1`，服务层调用为 `1.1`，实体/数据库子调用为 `1.1.1`；返回消息使用“被调用消息的编号 + `.1`”并标注 `«return»`。
5. **分支**：顺序图 `alt` 中的守卫条件和消息放入协作图 `alt` 面板；同一守卫在图中不重复画箭头，避免与正常路径混淆。
6. **核对**：逐项核对对象集合、消息方向、参数、返回、守卫条件和状态结果，记录差异。

### 2.2 编号规则示例（下单预留）

```text
1        买家 → 预留界面      submitReservation(buyerId, bookId)
1.1      预留界面 → 预留服务  reserveBook(buyerId, bookId)
1.1.1    预留服务 → book_listing  findBook(bookId)
1.1.1.1  book_listing → 预留服务  «return» BookInfo(sellerId, status)
1.1.2    预留服务 → reservation_order  findActiveOrder(bookId)
1.1.3    预留服务 → 事务/数据库  beginTransaction()
1.1.4    预留服务 → reservation_order  createActive(buyerId, bookId)
1.1.4.1  reservation_order → 事务/数据库  INSERT reservation_order
1.1.5    预留服务 → book_listing  markReserved(bookId)
1.1.5.1  book_listing → 事务/数据库  UPDATE book_listing
1.1.6    预留服务 → 事务/数据库  commit()
1.2      预留服务 → 预留界面  «return» ReservationResult(orderId, ACTIVE)
1.3      预留界面 → 买家      reservation confirmed
```

### 2.3 图上元素说明

- 图上每个箭头旁只放**序号徽标**，完整消息名放在右侧“消息序号对照”图例和 [`message-mapping.md`](message-mapping.md) 中；
- 蓝色实线箭头为调用，灰色虚线箭头为返回，绿色为创建类消息；
- 右侧图例按序号列出简名，保证图脱离表格也能读懂交互顺序；
- 下方 `alt` 面板中的 `E1`、`E2`……与 [`message-mapping.md`](message-mapping.md) 的分支表对应。

> 转换方式为“手工抽取 + 脚本绘图”，不是建模工具的自动转换。这样可以在脚本中固定对象、消息和序号，避免手工改图后图、表不一致。

---

## 3. 对象与类对应

| 协作图对象 | 类/构件 | 角色 | 主要职责 | 顺序图生命线 | 数据落点 |
|---|---|---|---|---|---|
| 买家 | Actor | 参与者 | 发起预留、取消请求 | 买家 | 不持久化 |
| 卖家 | Actor | 参与者 | 发起发布请求 | 卖家 | 不持久化 |
| 校园用户 | Actor | 参与者 | 检索和查看书籍 | 校园用户 | 不持久化 |
| 预留界面 | `ReservationUI` | Boundary | 接收下单参数、展示结果 | 预留界面 | — |
| 订单界面 | `OrderUI` | Boundary | 接收取消请求、展示结果 | 订单界面 | — |
| 发布界面 | `PublishUI` | Boundary | 接收发布表单、展示结果 | 发布界面 | — |
| 检索界面 | `SearchUI` | Boundary | 接收检索/详情请求、展示结果 | 检索界面 | — |
| 预留服务 | `ReservationService` | Control | 校验自购、书籍状态和有效订单，组织下单事务 | 预留服务 | 服务层 |
| 取消服务 | `CancellationService` | Control | 校验订单归属和状态，组织取消事务 | 取消服务 | 服务层 |
| 订单服务 | `OrderService` | Control | 取消后重订场景的协调入口，委托取消/预留服务 | 订单服务 | 服务层 |
| 书籍服务 | `BookService` | Control | 校验发布字段并创建发布记录 | 书籍服务 | 服务层 |
| 检索服务 | `SearchService` | Control | 执行检索、详情查询和状态展示 | 检索服务 | 服务层 |
| `book_listing` | `BookListing` | Entity | 书籍发布记录，维护 `AVAILABLE/RESERVED` | `book_listing` | `book_listing` |
| `reservation_order` | `ReservationOrder` | Entity | 预留订单，维护 `ACTIVE/CANCELLED` 与历史 | `reservation_order` | `reservation_order` |
| `user_account` | `UserAccount` | Entity | 用户账号，校验发布者存在 | `user_account` | `user_account` |
| 事务 / 数据库 | `TransactionManager` | Infra | 事务控制与 SQL 执行 | 事务 / 数据库 | InnoDB |

> `OrderService` 是场景 03 中 B 使用的生命线名。为了避免与 `CancellationService`、`ReservationService` 的职责混淆，本设计把它定位为“重订场景的协调入口”，实际取消/预留仍分别委托给对应服务；A 的类图若采用其他拆分方式，以 A 的最终版本为准并同步本表。

完整的逐条消息表（含参数、返回、类方法、顺序图对应）见 [`message-mapping.md`](message-mapping.md)。

---

## 4. 与顺序图的逐项核对

### 4.1 对象集合

| 场景 | 顺序图生命线 | 协作图对象 | 结论 |
|---|---|---|---|
| C-01 下单预留 | 买家、预留界面、预留服务、`book_listing`、`reservation_order`、事务/数据库 | 同左 | 一致 |
| C-02 取消订单 | 买家、订单界面、取消服务、`reservation_order`、`book_listing`、事务/数据库 | 同左 | 一致 |
| C-03 取消后重订 | 买家 A、订单服务、`reservation_order`、`book_listing`、买家 B、事务/数据库 | 同左 | 一致 |
| C-04 发布书籍 | 卖家、发布界面、书籍服务、`user_account`、`book_listing`、事务/数据库 | 同左 | 一致 |
| C-05 检索与查看 | 校园用户、检索界面、检索服务、`book_listing`、数据库 | 同左 | 一致 |

### 4.2 消息与分支

| 场景 | 顺序图消息 | 协作图正常消息 | 差异说明 |
|---|---|---|---|
| C-01 | 14 条（含返回） | 14 条 | 全部保留；异常分支 E1～E3 放入 `alt` 面板 |
| C-02 | 13 条（含返回） | 13 条 | 全部保留；异常分支 E1～E3 放入 `alt` 面板 |
| C-03 | 顺序图 14 条（含返回） | 22 条 | 补充 `3`、`3.1`、`3.1.1`、`3.2` 四条晚到消息；补充 `1.4.1`、`2.1.1` 两条显式返回、`1.7` 取消成功通知和 `2.2` 重新预留的 `beginTransaction`；正常调用与顺序图一致 |
| C-04 | 10 条（含自消息和返回） | 10 条 | 自消息 `validateRequiredAndPrice` 用自环表示；异常分支 E1～E3 放入 `alt` 面板 |
| C-05 | 14 条（含返回） | 14 条 | 全部保留；无结果、`RESERVED` 展示、详情无记录放入 `alt` 面板 |

### 4.3 核对中发现的问题

| 编号 | 位置 | 发现 | 处理 |
|---|---|---|---|
| Q-01 | `sequence/01` 与 `sequence/02` 的返回消息 | 返回消息未统一标注 `«return»`，与调用消息混排 | 协作图用灰色虚线箭头和 `«return»` 前缀区分；建议 B 在顺序图中统一返回符号 |
| Q-02 | `sequence/03` 旧请求晚到 | 顺序图只用 `alt` 文字描述“旧取消请求晚到”，没有画出买家 A 再次提交取消的消息 | 协作图补充 `3`、`3.1`、`3.1.1`、`3.2`，使边界场景可逐消息核对；建议 B 同步补画或明确说明该分支为注释 |
| Q-03 | `sequence/02` 取消顺序 | 先 `UPDATE status = CANCELLED`，再 `findCurrentActiveOrder(bookId)`；顺序正确，但图中未写出“排除本订单”的条件 | 协作图在 `findCurrentActiveOrder` 的说明中写明“排除本订单后查询”；`markAvailable` 增加守卫 `[activeOrder == null]` |
| Q-04 | `sequence/04` 发布校验 | 只校验 `seller exists`，未校验账号是否 `ACTIVE`；`user_account` 当前也没有状态字段 | 本次按“发布者存在”基线核对；若小组要求校验 `ACTIVE`，需同步修改 `user_account` 表、`checkSeller` 和顺序图；已记入 R-03 |
| Q-05 | `sequence/05` 检索与查看 | 顺序图同时出现 `book_listing` 和“数据库”生命线，`SELECT` 的归属略有重复 | 协作图按“检索服务调用 `BookListing` 匹配，再由数据库执行查询”表达；不改变只读语义 |
| Q-06 | `sequence/03` 重新预留 | 第二次预留只画了 `commit()`，没有画 `beginTransaction()`；从原子性看应有事务起点 | 协作图补充 `2.2 beginTransaction()`；建议 B 在顺序图中补上，或说明事务边界由外层统一管理 |

---

## 5. 五张协作图的阅读顺序

1. **C-01 下单预留**：先看 `1 → 1.1 → 1.1.1/1.1.2` 的校验，再看 `1.1.3` 开启事务、`1.1.4/1.1.4.1` 创建订单、`1.1.5/1.1.5.1` 更新书籍，最后 `1.1.6` 提交。
2. **C-02 取消订单**：先看 `1.1.1` 读取订单，再看 `1.1.3/1.1.4` 改订单，`1.1.5/1.1.5.1` 查询其他有效订单，最后 `1.1.6` 才恢复书籍。
3. **C-03 取消后重订**：上半段 `1.x` 是订单 A 取消，下半段 `2.x` 是买家 B 重新预留，最上方 `3.x` 是旧取消请求晚到；三者共用同一书籍记录。
4. **C-04 发布书籍**：`1.1.1` 校验卖家，`1.1.2` 自消息校验字段/价格，`1.1.4/1.1.4.1` 创建 `AVAILABLE` 记录。
5. **C-05 检索与查看**：`1.x` 是检索列表，`2.x` 是查看详情；两条路径都不修改 `book_listing.status`。

---

## 6. 复现与修改

```powershell
py design/collaboration/tools/generate_communication.py
py design/collaboration/tools/generate_communication.py --png
```

- 修改 `tools/generate_communication.py` 中 `build_scenarios()` 的节点、消息或分支后，重新运行即可同步 SVG、PNG 和 `message-mapping.md`；
- PNG 由本机 Edge/Chrome 无头模式导出，脚本会自动查找常见安装路径；若未找到浏览器，只生成 SVG，不影响仓库内容；
- 图形坐标和序号均由脚本固定，修改后应重新检查标签是否遮挡，并在个人报告中注明实际使用的工具与版本。
- B 对 C 的交叉检查（对象与消息是否匹配顺序图）尚未记录；本文件第 4.1、4.2 节是 C 的自查，不替代 B 的核验记录。B 核验后应在本节补充“位置、发现、处理/确认依据”。

## 7. 工具与 AI 使用

- 绘图与导出：Python 3.12.5 标准库生成 SVG；Microsoft Edge 无头模式导出 PNG。未使用第三方绘图库，也没有使用收费建模工具。
- AI 使用：使用 DeepSeek（OpenCode 环境）辅助生成初版布局脚本、整理消息表和文字；对象集合、消息方向、参数、异常分支和状态结果由本人对照 `design/sequence/` 与 `sql/01`～`03` 逐项核对。核对中发现的问题见第 4.3 节 Q-01～Q-06 和走查 R-01～R-07。
- 未运行程序，未执行数据库建表或事务测试；本文件中的“通过”均为设计推演结论。

---

*本文件中的“一致”“通过”均指设计推演层面的核对，不代表已运行程序或已执行数据库事务。*
