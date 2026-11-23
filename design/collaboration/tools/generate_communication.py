#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成实验三 C 部分的协作图（通信图）。

设计约束：
1. 图形只使用标准库生成 SVG，便于在仓库中审阅和复现；
2. 对象名、消息名与 design/sequence/ 下的顺序图保持一致；
3. 每条消息带分层序号，异常/备选分支单独列在 alt 面板中；
4. 运行 --png 时调用本机 Edge/Chrome 将 SVG 导出为 PNG，便于插入 Word。

用法：
    py design/collaboration/tools/generate_communication.py
    py design/collaboration/tools/generate_communication.py --png
"""

from __future__ import annotations

import argparse
import html
import math
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "design" / "collaboration"

FONT = "'Microsoft YaHei', 'DengXian', 'SimHei', Arial, sans-serif"
CALL = "#2F6B9A"
RETURN = "#5B6B7A"
BRANCH = "#B33A3A"
LINK = "#90A4AE"
INK = "#243447"
MUTED = "#5B6B7A"

KIND_STYLE = {
    "actor": ("#F2F4F6", "#687783"),
    "boundary": ("#DDEBF7", "#2F6B9A"),
    "control": ("#DDF3EE", "#1B7F6B"),
    "book": ("#FFF4DC", "#B56B00"),
    "order": ("#EFE7F7", "#6B4C9A"),
    "user": ("#E8F5E9", "#3D7A2E"),
    "infra": ("#ECEFF1", "#546E7A"),
}


@dataclass(frozen=True)
class Node:
    key: str
    name: str
    stereotype: str
    kind: str
    x: float
    y: float
    w: float = 220
    h: float = 66


@dataclass(frozen=True)
class Message:
    seq: str
    src: str
    dst: str
    short: str
    full: str
    kind: str = "call"          # call / return / create
    io: str = ""
    op: str = ""
    seq_ref: str = ""
    note: str = ""


@dataclass(frozen=True)
class Branch:
    guard: str
    text: str
    result: str


@dataclass
class Scenario:
    key: str
    filename: str
    title: str
    subtitle: str
    nodes: list[Node]
    messages: list[Message]
    branches: list[Branch]
    caption: str
    width: int = 1840
    height: int = 1250
    extra_links: list[tuple[str, str]] = field(default_factory=list)


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def estimate_width(text: str, size: float = 15.5) -> float:
    """按中日韩字符与西文字符的近似宽度估算，用于给标签留白。"""
    total = 0.0
    for ch in text:
        total += size if ord(ch) > 0x2E80 else size * 0.54
    return total


def center(node: Node) -> tuple[float, float]:
    return node.x + node.w / 2, node.y + node.h / 2


def clip_rect(cx: float, cy: float, dx: float, dy: float, node: Node, pad: float = 6) -> tuple[float, float]:
    """从节点中心沿方向 (dx, dy) 求与矩形边界的交点。"""
    hw, hh = node.w / 2 + pad, node.h / 2 + pad
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return cx, cy
    tx = hw / abs(dx) if abs(dx) > 1e-9 else float("inf")
    ty = hh / abs(dy) if abs(dy) > 1e-9 else float("inf")
    t = min(tx, ty)
    return cx + dx * t, cy + dy * t


class Svgs:
    def __init__(self) -> None:
        self.parts: list[str] = []

    def add(self, text: str) -> None:
        self.parts.append(text)

    def text(
        self,
        x: float,
        y: float,
        content: str,
        size: float = 16,
        color: str = INK,
        weight: int = 400,
        anchor: str = "start",
        opacity: float = 1.0,
    ) -> None:
        self.add(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}" dominant-baseline="middle" '
            f'opacity="{opacity}">{esc(content)}</text>'
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        color: str = LINK,
        width: float = 1.8,
        dash: str = "",
        arrow: bool = False,
    ) -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{width}"{dash_attr} stroke-linecap="round"/>'
        )
        if arrow:
            angle = math.atan2(y2 - y1, x2 - x1)
            length = 11.0
            spread = 0.42
            p1 = (x2 - length * math.cos(angle - spread), y2 - length * math.sin(angle - spread))
            p2 = (x2 - length * math.cos(angle + spread), y2 - length * math.sin(angle + spread))
            self.add(
                f'<path d="M{x2:.1f},{y2:.1f} L{p1[0]:.1f},{p1[1]:.1f} L{p2[0]:.1f},{p2[1]:.1f} Z" '
                f'fill="{color}"/>'
            )

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str,
        stroke: str,
        radius: float = 12,
        dash: str = "",
        width: float = 2,
    ) -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"{dash_attr}/>'
        )


def svg_header(width: int, height: int, title: str, desc: str) -> Svgs:
    s = Svgs()
    s.add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    s.add(f"<title>{esc(title)}</title><desc>{esc(desc)}</desc>")
    s.add(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#FFFFFF"/>')
    s.add(f'<g font-family="{FONT}">')
    return s


def svg_footer(s: Svgs) -> None:
    s.add("</g></svg>")


def draw_node(s: Svgs, node: Node) -> None:
    fill, stroke = KIND_STYLE[node.kind]
    s.rect(node.x, node.y, node.w, node.h, fill, stroke, radius=12, width=2)
    cx = node.x + node.w / 2
    s.text(cx, node.y + node.h / 2 - 9, node.name, 18, INK, 700, "middle")
    s.text(cx, node.y + node.h / 2 + 16, node.stereotype, 12.5, MUTED, 400, "middle")


def draw_self_message(s: Svgs, node: Node, message: Message, side: int = 1) -> None:
    color = RETURN if message.kind == "return" else CALL
    dash = "7 6" if message.kind == "return" else ""
    x_right = node.x + node.w
    y_mid = node.y + node.h * 0.45
    out = 58
    up = 46
    # 从右边缘出发，向右、向上、再回到右边缘，形成自消息环
    s.add(
        f'<path d="M{x_right:.1f},{y_mid + 18:.1f} H{x_right + out:.1f} V{y_mid - up:.1f} H{x_right + 12:.1f}" '
        f'fill="none" stroke="{color}" stroke-width="2" '
        f'{("stroke-dasharray=\"" + dash + "\"") if dash else ""}/>'
    )
    s.line(x_right + 22, y_mid - up, x_right + 2, y_mid - up, color=color, width=2, arrow=True)
    label = message.seq
    label_w = max(34, estimate_width(label, 13) + 16)
    lx = x_right + out + 10
    ly = y_mid - up - 10
    s.rect(lx, ly, label_w, 21, "#FFFFFF", color, radius=5, width=1.2)
    s.text(lx + label_w / 2, ly + 10.5, label, 13, color, 700, "middle")


def draw_message(
    s: Svgs,
    message: Message,
    p1: tuple[float, float],
    p2: tuple[float, float],
    pair: tuple[str, str],
    t: float,
    side: int,
) -> None:
    ax, ay = p1
    bx, by = p2
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    if length < 1:
        return
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux

    cx = ax + dx * t
    cy = ay + dy * t

    color = {"call": CALL, "return": RETURN, "create": "#3D7A2E"}.get(message.kind, CALL)
    dash = "7 6" if message.kind == "return" else ""

    # 连线按首次出现的消息方向建立；若当前消息方向相反，则箭头反向。
    direction = 1 if (message.src, message.dst) == pair else -1
    arrow_len = min(62.0, max(26.0, length * 0.16))
    half = arrow_len / 2
    sx, sy = cx - ux * half * direction, cy - uy * half * direction
    ex, ey = cx + ux * half * direction, cy + uy * half * direction

    s.line(sx, sy, ex, ey, color=color, width=2.1, dash=dash, arrow=True)

    # 图上只放序号徽标，完整消息名见右侧图例和 message-mapping.md
    label = message.seq
    label_size = 13.0
    label_w = max(34.0, estimate_width(label, label_size) + 16)
    label_h = 21.0
    off = 24.0
    lx = cx + nx * side * off - label_w / 2
    ly = cy + ny * side * off - label_h / 2
    lx = max(6, min(lx, SCENARIO_WIDTH - label_w - 6))
    s.rect(lx, ly, label_w, label_h, "#FFFFFF", color, radius=5, width=1.2)
    s.text(lx + label_w / 2, ly + label_h / 2 + 0.5, label, label_size, color, 700, "middle")


_link_order_key: dict[tuple[str, str], tuple[str, str]] = {}
SCENARIO_WIDTH = 1600


def draw_legend(s: Svgs, sc: Scenario) -> None:
    """右侧消息图例：保证图上只有序号时仍能直接读懂交互。"""
    x = 1500
    y = 118
    w = sc.width - x - 44
    rows = sc.messages
    h = 54 + len(rows) * 23 + 14
    s.text(x, y - 12, "实线 = 调用　虚线 = 返回　绿色 = 创建", 12.5, MUTED, 400)
    s.rect(x, y, w, h, "#FBFCFD", "#C7D1D8", radius=12, width=1.4)
    s.text(x + 18, y + 27, "消息序号对照", 17, INK, 700)
    s.text(x + w - 18, y + 27, f"共 {len(rows)} 条", 12.5, MUTED, 400, "end")
    ry = y + 52
    for i, m in enumerate(rows):
        color = {"call": CALL, "return": RETURN, "create": "#3D7A2E"}.get(m.kind, CALL)
        if i % 2 == 1:
            s.rect(x + 10, ry - 9, w - 20, 22, "#F2F4F6", "#F2F4F6", radius=4, width=0)
        s.text(x + 18, ry, m.seq, 12.5, color, 700)
        s.text(x + 82, ry, m.short, 12.5, INK, 400)
        ry += 23


def layout_scenario(sc: Scenario) -> str:
    global _link_order_key, SCENARIO_WIDTH
    SCENARIO_WIDTH = sc.width
    by_key = {n.key: n for n in sc.nodes}
    s = svg_header(sc.width, sc.height, sc.title, sc.subtitle)

    s.text(56, 42, sc.title, 29, INK, 700)
    s.text(56, 76, sc.subtitle, 16, MUTED, 400)

    # 连线去重；方向统一为“从上到下、从左到右”，使序号沿着阅读方向递增
    links: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    for m in sc.messages:
        if m.src == m.dst:
            continue
        key = frozenset((m.src, m.dst))
        if key in seen:
            continue
        seen.add(key)
        na, nb = by_key[m.src], by_key[m.dst]
        if (na.y, na.x) <= (nb.y, nb.x):
            links.append((m.src, m.dst))
        else:
            links.append((m.dst, m.src))
    for pair in sc.extra_links:
        key = frozenset(pair)
        if key not in seen:
            seen.add(key)
            na, nb = by_key[pair[0]], by_key[pair[1]]
            links.append(pair if (na.y, na.x) <= (nb.y, nb.x) else (pair[1], pair[0]))

    _link_order_key = {pair: pair for pair in links}
    _link_order_key.update({(b, a): (a, b) for a, b in links})
    for a, b in links:
        na, nb = by_key[a], by_key[b]
        ax, ay = center(na)
        bx, by = center(nb)
        dx, dy = bx - ax, by - ay
        norm = math.hypot(dx, dy)
        if norm < 1:
            continue
        sx, sy = clip_rect(ax, ay, dx / norm, dy / norm, na)
        ex, ey = clip_rect(bx, by, -dx / norm, -dy / norm, nb)
        s.line(sx, sy, ex, ey, color=LINK, width=1.8)

    # 按无向连线分组，确定消息沿线位置
    grouped: dict[frozenset[str], list[Message]] = {}
    for m in sc.messages:
        if m.src == m.dst:
            continue
        grouped.setdefault(frozenset((m.src, m.dst)), []).append(m)

    for m in sc.messages:
        if m.src == m.dst:
            continue
        canonical = _link_order_key[(m.src, m.dst)]
        na, nb = by_key[canonical[0]], by_key[canonical[1]]
        ax, ay = center(na)
        bx, by = center(nb)
        dx, dy = bx - ax, by - ay
        norm = math.hypot(dx, dy)
        sx, sy = clip_rect(ax, ay, dx / norm, dy / norm, na)
        ex, ey = clip_rect(bx, by, -dx / norm, -dy / norm, nb)
        group = grouped[frozenset((m.src, m.dst))]
        idx = group.index(m)
        t = (idx + 1) / (len(group) + 1)
        side = 1 if idx % 2 == 0 else -1
        draw_message(s, m, (sx, sy), (ex, ey), canonical, t, side)

    for m in sc.messages:
        if m.src == m.dst:
            draw_self_message(s, by_key[m.src], m)

    for node in sc.nodes:
        draw_node(s, node)

    draw_legend(s, sc)

    # 异常/备选分支面板
    panel_w = 1440
    panel_top = sc.height - 70 - (len(sc.branches) * 92 + 64)
    s.rect(50, panel_top, panel_w, len(sc.branches) * 92 + 58, "#FAFBFC", "#687783", radius=12, dash="9 7", width=2)
    s.rect(50, panel_top, 92, 34, "#FCE3E3", BRANCH, radius=5, width=1)
    s.text(96, panel_top + 17, "alt", 17, BRANCH, 700, "middle")
    s.text(160, panel_top + 17, "异常 / 备选分支（不进入正常序号）", 17, INK, 700)

    y = panel_top + 50
    for i, br in enumerate(sc.branches):
        fill = "#FCE3E3" if i % 2 == 0 else "#FFF4DC"
        stroke = BRANCH if i % 2 == 0 else "#B56B00"
        s.rect(76, y, panel_w - 52, 78, fill, stroke, radius=8, width=1)
        s.text(96, y + 21, br.guard, 16, stroke, 700)
        s.text(96, y + 47, br.text, 15, INK, 400)
        s.text(96, y + 68, br.result, 15, MUTED, 400)
        y += 92

    s.text(56, sc.height - 30, sc.caption, 15, MUTED, 400)
    svg_footer(s)
    return "\n".join(s.parts)


# ---------------------------------------------------------------------------
# 对象说明（用于生成 message-mapping.md）
# ---------------------------------------------------------------------------
OBJECTS = {
    "buyer": ("买家", "Actor（参与者）", "校园用户，发起预留/取消请求", "—", "不持久化"),
    "seller": ("卖家", "Actor（参与者）", "校园用户，发起发布请求", "—", "不持久化"),
    "user": ("校园用户", "Actor（参与者）", "检索和查看书籍", "—", "不持久化"),
    "resUI": ("预留界面", "Boundary / ReservationUI", "接收下单参数并展示结果", "预留界面", "—"),
    "orderUI": ("订单界面", "Boundary / OrderUI", "接收取消请求并展示结果", "订单界面", "—"),
    "publishUI": ("发布界面", "Boundary / PublishUI", "接收发布表单并展示结果", "发布界面", "—"),
    "searchUI": ("检索界面", "Boundary / SearchUI", "接收检索/详情请求并展示结果", "检索界面", "—"),
    "resService": ("预留服务", "Control / ReservationService", "校验身份与书籍状态，组织下单事务", "预留服务", "无（服务层）"),
    "cancelService": ("取消服务", "Control / CancellationService", "校验取消权限与订单状态，组织取消事务", "取消服务", "无（服务层）"),
    "orderService": ("订单服务", "Control / OrderService", "取消后重订场景下统一协调取消和预留", "订单服务", "无（服务层）"),
    "bookService": ("书籍服务", "Control / BookService", "校验发布字段并创建发布记录", "书籍服务", "无（服务层）"),
    "searchService": ("检索服务", "Control / SearchService", "执行检索、详情查询和状态展示", "检索服务", "无（服务层）"),
    "book": ("book_listing", "Entity / BookListing", "书籍发布记录，维护书籍状态", "book_listing", "book_listing"),
    "order": ("reservation_order", "Entity / ReservationOrder", "预留订单，维护订单状态与历史", "reservation_order", "reservation_order"),
    "account": ("user_account", "Entity / UserAccount", "用户账号，校验发布者存在", "user_account", "user_account"),
    "db": ("事务 / 数据库", "Infra / TransactionManager", "事务控制与 SQL 执行", "事务 / 数据库", "InnoDB"),
}


def message_markdown(sc: Scenario, by_key: dict[str, Node]) -> str:
    lines = [f"### {sc.key} {sc.title}", "", f"> {sc.subtitle}", ""]
    lines.append("| 序号 | 发送 → 接收 | 消息（完整签名） | 输入/返回 | 类操作 | 顺序图对应 | 说明 |")
    lines.append("|---|---|---|---|---|---|---|")
    for m in sc.messages:
        src = by_key[m.src].name
        dst = by_key[m.dst].name
        lines.append(
            f"| {m.seq} | {src} → {dst} | `{m.full}` | {m.io or '—'} | {m.op or '—'} | {m.seq_ref or '同一消息'} | {m.note or '—'} |"
        )
    lines.append("")
    if sc.branches:
        lines.append("| 分支 | 守卫条件 | 交互与结果 |")
        lines.append("|---|---|---|")
        for i, br in enumerate(sc.branches, 1):
            lines.append(f"| E{i} | {br.guard} | {br.text} {br.result} |")
        lines.append("")
    return "\n".join(lines)


def build_scenarios() -> list[Scenario]:
    # 01 下单预留
    n01 = [
        Node("buyer", "买家", "Actor", "actor", 50, 250, 200, 64),
        Node("resUI", "预留界面", "Boundary", "boundary", 400, 150, 220, 64),
        Node("resService", "预留服务", "Control", "control", 750, 410, 240, 64),
        Node("book", "book_listing", "Entity", "book", 1230, 180, 220, 64),
        Node("order", "reservation_order", "Entity", "order", 1230, 430, 220, 64),
        Node("db", "事务 / 数据库", "Infra", "infra", 900, 750, 220, 64),
    ]
    m01 = [
        Message("1", "buyer", "resUI", "submitReservation", "submitReservation(buyerId, bookId)", "call", "buyerId, bookId", "ReservationUI.submitReservation", "submitReservation", "界面接收下单请求"),
        Message("1.1", "resUI", "resService", "reserveBook", "reserveBook(buyerId, bookId)", "call", "buyerId, bookId；返回 ReservationResult", "ReservationService.reserveBook", "reserveBook", "进入服务层校验"),
        Message("1.1.1", "resService", "book", "findBook", "findBook(bookId)", "call", "bookId；返回 BookInfo(sellerId, status)", "BookListing.findBook", "findBook(bookId)", "读取发布者与状态"),
        Message("1.1.1.1", "book", "resService", "«return» BookInfo", "BookInfo(sellerId, status)", "return", "sellerId、status", "BookListing.findBook 返回", "BookInfo(sellerId, status)", "正常返回；无记录另行拒绝"),
        Message("1.1.2", "resService", "order", "findActiveOrder", "findActiveOrder(bookId)", "call", "bookId；返回订单或 null", "ReservationOrder.findActiveOrder", "findActiveOrder(bookId)", "检查是否已有有效订单"),
        Message("1.1.2.1", "order", "resService", "«return» ActiveOrder/null", "ActiveOrder or null", "return", "ACTIVE 订单或 null", "ReservationOrder.findActiveOrder 返回", "ActiveOrder or null", "存在则进入 BOOK_RESERVED 分支"),
        Message("1.1.3", "resService", "db", "beginTransaction", "beginTransaction()", "call", "—", "TransactionManager.begin", "beginTransaction()", "开启下单事务"),
        Message("1.1.4", "resService", "order", "createActive", "createActive(buyerId, bookId)", "create", "buyerId, bookId；新建 ACTIVE 订单", "ReservationOrder.createActive", "create ACTIVE order", "订单状态初始为 ACTIVE"),
        Message("1.1.4.1", "order", "db", "INSERT order", "INSERT INTO reservation_order", "create", "新订单行", "ReservationOrder.persist", "INSERT reservation_order", "唯一索引保证一书一有效订单"),
        Message("1.1.5", "resService", "book", "markReserved", "markReserved(bookId)", "call", "bookId", "BookListing.markReserved", "mark status = RESERVED", "书籍状态改为 RESERVED"),
        Message("1.1.5.1", "book", "db", "UPDATE book", "UPDATE book_listing SET status = 'RESERVED'", "call", "bookId", "BookListing.persistStatus", "UPDATE book_listing", "与订单写入同一事务"),
        Message("1.1.6", "resService", "db", "commit", "commit()", "call", "—", "TransactionManager.commit", "commit()", "成功提交"),
        Message("1.2", "resService", "resUI", "«return» ReservationResult", "ReservationResult(orderId, ACTIVE)", "return", "orderId、ACTIVE", "ReservationService.reserveBook 返回", "ReservationResult(orderId, ACTIVE)", "返回订单确认"),
        Message("1.3", "resUI", "buyer", "confirmed", "reservation confirmed", "return", "确认提示", "ReservationUI.showResult", "reservation confirmed", "界面展示成功"),
    ]
    b01 = [
        Branch("[buyerId == sellerId]", "预留服务 → 预留界面：reject(SELF_RESERVATION)", "不创建订单；书籍保持 AVAILABLE。"),
        Branch("[status != AVAILABLE 或存在 ACTIVE 订单]", "预留服务 → 预留界面：reject(BOOK_RESERVED)", "不新增订单；原订单和书籍状态不变。"),
        Branch("[并发请求导致唯一约束/条件更新失败]", "事务/数据库 → 预留服务：rollback()；预留服务 → 预留界面：reject(BOOK_RESERVED)", "只有先成功受理的请求保留 ACTIVE 订单。"),
    ]
    sc01 = Scenario(
        "C-01", "01_下单预留_通信图.svg",
        "通信图一：下单预留（正常流程）",
        "由 design/sequence/01_下单预留_正常与异常.svg 转换；序号与顺序图消息一一对应",
        n01, m01, b01,
        "状态结果：成功时 book_listing.AVAILABLE → RESERVED，reservation_order 新增 ACTIVE；异常分支不改变既有状态。",
        height=1280,
    )

    # 02 取消订单
    n02 = [
        Node("buyer", "买家", "Actor", "actor", 50, 250, 200, 64),
        Node("orderUI", "订单界面", "Boundary", "boundary", 400, 145, 220, 64),
        Node("cancelService", "取消服务", "Control", "control", 750, 330, 240, 64),
        Node("order", "reservation_order", "Entity", "order", 750, 760, 240, 64),
        Node("book", "book_listing", "Entity", "book", 1230, 300, 220, 64),
        Node("db", "事务 / 数据库", "Infra", "infra", 1230, 650, 220, 64),
    ]
    m02 = [
        Message("1", "buyer", "orderUI", "cancel", "cancel(orderId, requesterId)", "call", "orderId, requesterId", "OrderUI.cancel", "cancel(orderId, requesterId)", "提交取消请求"),
        Message("1.1", "orderUI", "cancelService", "cancelOrder", "cancelOrder(requesterId, orderId)", "call", "requesterId, orderId；返回 CancelResult", "CancellationService.cancelOrder", "cancelOrder(requesterId, orderId)", "进入取消服务"),
        Message("1.1.1", "cancelService", "order", "findOrder", "findOrder(orderId)", "call", "orderId；返回 Order(buyerId, bookId, status)", "ReservationOrder.findOrder", "findOrder(orderId)", "读取订单归属和状态"),
        Message("1.1.1.1", "order", "cancelService", "«return» Order", "Order(buyerId, bookId, status)", "return", "buyerId、bookId、status", "ReservationOrder.findOrder 返回", "Order(buyerId, bookId, status)", "正常返回；不存在另行拒绝"),
        Message("1.1.2", "cancelService", "db", "beginTransaction", "beginTransaction()", "call", "—", "TransactionManager.begin", "beginTransaction()", "开启取消事务"),
        Message("1.1.3", "cancelService", "order", "markCancelled", "markCancelled(orderId)", "call", "orderId；status = CANCELLED", "ReservationOrder.markCancelled", "UPDATE status = CANCELLED", "订单状态变更"),
        Message("1.1.4", "cancelService", "order", "setCancelledAt", "setCancelledAt(orderId, now)", "call", "orderId, 当前时间", "ReservationOrder.setCancelledAt", "set cancelled_at", "记录取消时间，保留历史"),
        Message("1.1.5", "cancelService", "order", "findCurrentActiveOrder", "findCurrentActiveOrder(bookId)", "call", "bookId；排除本订单后查询", "ReservationOrder.findCurrentActiveOrder", "findCurrentActiveOrder(bookId)", "确认书籍是否仍被新订单占用"),
        Message("1.1.5.1", "order", "cancelService", "«return» ActiveOrder/null", "ActiveOrder or null", "return", "新 ACTIVE 订单或 null", "ReservationOrder.findCurrentActiveOrder 返回", "ActiveOrder or null", "为 null 才可恢复书籍"),
        Message("1.1.6", "cancelService", "book", "markAvailable", "markAvailable(bookId) [无其他 ACTIVE 订单]", "call", "bookId；守卫：activeOrder == null", "BookListing.markAvailable", "UPDATE status = AVAILABLE", "书籍恢复可售"),
        Message("1.1.7", "cancelService", "db", "commit", "commit()", "call", "—", "TransactionManager.commit", "commit()", "提交取消结果"),
        Message("1.2", "cancelService", "orderUI", "«return» CancelResult", "CancelResult(success)", "return", "success", "CancellationService.cancelOrder 返回", "CancelResult(success)", "返回取消结果"),
        Message("1.3", "orderUI", "buyer", "confirmed", "cancel confirmed", "return", "确认提示", "OrderUI.showResult", "cancel confirmed", "界面展示成功"),
    ]
    b02 = [
        Branch("[requesterId != order.buyerId]", "取消服务 → 订单界面：reject(FORBIDDEN)", "订单保持 ACTIVE；书籍保持 RESERVED。"),
        Branch("[order.status == CANCELLED]", "取消服务 → 订单界面：reject(ALREADY_CANCELLED)", "拒绝重复取消；不重复修改书籍状态。"),
        Branch("[旧订单取消请求晚到，书籍已有新 ACTIVE 订单]", "取消服务 → 订单界面：reject(OLD_REQUEST)", "不修改新订单；书籍保持 RESERVED。"),
    ]
    sc02 = Scenario(
        "C-02", "02_取消订单_通信图.svg",
        "通信图二：取消订单（正常流程）",
        "由 design/sequence/02_取消订单_正常与异常.svg 转换；先改订单状态，再判断书籍是否可恢复",
        n02, m02, b02,
        "状态结果：成功时 reservation_order.ACTIVE → CANCELLED；仅当不存在其他 ACTIVE 订单时 book_listing.RESERVED → AVAILABLE。",
        height=1250,
    )

    # 03 取消后重订
    n03 = [
        Node("buyerA", "买家 A", "Actor", "actor", 80, 160, 190, 64),
        Node("buyerB", "买家 B", "Actor", "actor", 80, 780, 190, 64),
        Node("orderService", "订单服务", "Control", "control", 740, 500, 240, 64),
        Node("order", "reservation_order", "Entity", "order", 740, 100, 240, 64),
        Node("book", "book_listing", "Entity", "book", 740, 900, 240, 64),
        Node("db", "事务 / 数据库", "Infra", "infra", 1270, 500, 200, 64),
    ]
    m03 = [
        Message("1", "buyerA", "orderService", "cancel", "cancel(orderA, buyerA)", "call", "orderA, buyerA", "OrderService.cancel", "cancel(orderA, buyerA)", "订单 A 的买家发起取消"),
        Message("1.1", "orderService", "order", "findOrder", "findOrder(orderA)", "call", "orderA；返回 ACTIVE(orderA)", "ReservationOrder.findOrder", "findOrder(orderA)", "读取订单 A"),
        Message("1.1.1", "order", "orderService", "«return» ACTIVE", "ACTIVE(orderA)", "return", "status = ACTIVE", "ReservationOrder.findOrder 返回", "ACTIVE(orderA)", "确认订单 A 仍有效"),
        Message("1.2", "orderService", "db", "beginTransaction", "beginTransaction()", "call", "—", "TransactionManager.begin", "beginTransaction()", "开启取消事务"),
        Message("1.3", "orderService", "order", "orderA→CANCELLED", "orderA → CANCELLED", "call", "orderA；status = CANCELLED", "ReservationOrder.markCancelled", "orderA → CANCELLED", "订单 A 失效"),
        Message("1.4", "orderService", "order", "checkCurrentOrder", "check current order(book)", "call", "book；返回 null", "ReservationOrder.findCurrentActiveOrder", "check current order(book)", "排除订单 A 后查询"),
        Message("1.4.1", "order", "orderService", "«return» null", "null", "return", "无其他 ACTIVE 订单", "ReservationOrder.findCurrentActiveOrder 返回", "null", "允许恢复书籍"),
        Message("1.5", "orderService", "book", "book→AVAILABLE", "book → AVAILABLE", "call", "book", "BookListing.markAvailable", "book → AVAILABLE", "恢复可售"),
        Message("1.6", "orderService", "db", "commit", "commit()", "call", "—", "TransactionManager.commit", "commit()", "提交取消"),
        Message("1.7", "orderService", "buyerA", "success(cancelled)", "success(cancelled)", "return", "取消成功", "OrderService.cancel 返回", "—", "通知买家 A"),
        Message("2", "buyerB", "orderService", "reserve", "reserve(book)", "call", "book, buyerB", "OrderService.reserve", "reserve(book)", "买家 B 重新预留"),
        Message("2.1", "orderService", "book", "check AVAILABLE", "check AVAILABLE", "call", "book；返回 AVAILABLE", "BookListing.findBook", "check AVAILABLE", "重新读取书籍状态"),
        Message("2.1.1", "book", "orderService", "«return» AVAILABLE", "AVAILABLE", "return", "status = AVAILABLE", "BookListing.findBook 返回", "AVAILABLE", "可被预留"),
        Message("2.2", "orderService", "db", "beginTransaction", "beginTransaction()", "call", "—", "TransactionManager.begin", "—", "开启新预留事务"),
        Message("2.3", "orderService", "order", "create orderB", "create orderB ACTIVE", "create", "buyerB, book；新订单 ACTIVE", "ReservationOrder.createActive", "create orderB ACTIVE", "订单 B 建立"),
        Message("2.4", "orderService", "book", "book→RESERVED", "book → RESERVED", "call", "book", "BookListing.markReserved", "book → RESERVED", "书籍再次预留"),
        Message("2.5", "orderService", "db", "commit", "commit()", "call", "—", "TransactionManager.commit", "commit()", "提交新预留"),
        Message("2.6", "orderService", "buyerB", "success(orderB)", "success(orderB)", "return", "orderB", "OrderService.reserve 返回", "success(orderB)", "通知买家 B"),
        Message("3", "buyerA", "orderService", "cancel(orderA) 晚到", "cancel(orderA, buyerA)（旧请求晚到）", "call", "旧 orderA", "OrderService.cancel", "旧取消请求晚到", "边界：订单 A 已取消后再次请求"),
        Message("3.1", "orderService", "order", "findOrder", "findOrder(orderA)", "call", "orderA；返回 CANCELLED", "ReservationOrder.findOrder", "—", "读取订单 A 当前状态"),
        Message("3.1.1", "order", "orderService", "«return» CANCELLED", "CANCELLED", "return", "status = CANCELLED", "ReservationOrder.findOrder 返回", "—", "已非 ACTIVE"),
        Message("3.2", "orderService", "buyerA", "reject(OLD_REQUEST)", "reject(OLD_REQUEST)", "return", "拒绝原因", "OrderService.cancel 返回", "reject(OLD_REQUEST)", "不修改订单 B"),
    ]
    b03 = [
        Branch("[orderA 已 CANCELLED 且 orderB 已 ACTIVE]", "订单服务 → 买家 A：reject(OLD_REQUEST)", "不修改 orderB；book_listing 保持 RESERVED。"),
        Branch("[orderA 取消成功且当前无其他 ACTIVE 订单]", "订单服务 → book_listing：book → AVAILABLE", "订单 A 保留为 CANCELLED，历史不删除。"),
        Branch("[买家 B 预留时书籍仍被占用]", "订单服务 → 买家 B：reject(BOOK_RESERVED)", "不创建 orderB；书籍状态不变。"),
    ]
    sc03 = Scenario(
        "C-03", "03_取消后重订_通信图.svg",
        "通信图三：取消后重新预留（边界一致性）",
        "由 design/sequence/03_取消后重订_边界场景.svg 转换；补充旧取消请求晚到的消息",
        n03, m03, b03,
        "一致性结果：orderA 保留为 CANCELLED；orderB 为唯一 ACTIVE 订单；book_listing 为 RESERVED。",
        height=1450,
    )

    # 04 发布书籍
    n04 = [
        Node("seller", "卖家", "Actor", "actor", 50, 240, 190, 64),
        Node("publishUI", "发布界面", "Boundary", "boundary", 400, 140, 220, 64),
        Node("bookService", "书籍服务", "Control", "control", 750, 390, 240, 64),
        Node("account", "user_account", "Entity", "user", 1230, 160, 220, 64),
        Node("book", "book_listing", "Entity", "book", 1230, 420, 220, 64),
        Node("db", "事务 / 数据库", "Infra", "infra", 950, 720, 220, 64),
    ]
    m04 = [
        Message("1", "seller", "publishUI", "submitBook", "submitBook(sellerId, title, author, category, condition, price)", "call", "表单字段", "PublishUI.submitBook", "submitBook(...)", "接收发布表单"),
        Message("1.1", "publishUI", "bookService", "createListing", "createListing(bookInfo)", "call", "bookInfo；返回 PublishResult", "BookService.createListing", "createListing(bookInfo)", "进入书籍服务"),
        Message("1.1.1", "bookService", "account", "checkSeller", "checkSeller(sellerId)", "call", "sellerId；返回 seller exists", "UserAccount.checkSeller", "checkSeller(sellerId)", "校验发布者存在"),
        Message("1.1.1.1", "account", "bookService", "«return» seller exists", "seller exists", "return", "true/false", "UserAccount.checkSeller 返回", "seller exists", "不存在则拒绝发布"),
        Message("1.1.2", "bookService", "bookService", "validateRequiredAndPrice", "validateRequiredAndPrice(bookInfo)", "call", "bookInfo；返回 valid", "BookService.validateRequiredAndPrice", "validateRequiredAndPrice(bookInfo)", "自消息：校验必填和价格"),
        Message("1.1.3", "bookService", "db", "beginTransaction", "beginTransaction()", "call", "—", "TransactionManager.begin", "beginTransaction()", "开启发布事务"),
        Message("1.1.4", "bookService", "book", "insertListing", "insertListing(bookInfo, status=AVAILABLE)", "create", "bookInfo；初始 AVAILABLE", "BookListing.create", "insert listing(status=AVAILABLE)", "创建发布记录"),
        Message("1.1.4.1", "book", "db", "INSERT book", "INSERT INTO book_listing", "create", "新书籍行", "BookListing.persist", "INSERT book_listing", "写入数据库"),
        Message("1.1.5", "bookService", "db", "commit", "commit()", "call", "—", "TransactionManager.commit", "commit()", "提交发布"),
        Message("1.2", "bookService", "publishUI", "«return» PublishResult", "PublishResult(bookId, AVAILABLE)", "return", "bookId, status", "BookService.createListing 返回", "PublishResult(bookId, AVAILABLE)", "返回发布结果"),
    ]
    b04 = [
        Branch("[必填字段缺失]", "书籍服务 → 发布界面：reject(MISSING_FIELD)", "指出缺失字段；不创建 book_listing。"),
        Branch("[price < 0 或格式不合法]", "书籍服务 → 发布界面：reject(INVALID_PRICE)", "提示价格不得为负；不创建发布记录。"),
        Branch("[sellerId 不存在]", "书籍服务 → 发布界面：reject(SELLER_NOT_FOUND)", "不写入书籍发布记录。"),
    ]
    sc04 = Scenario(
        "C-04", "04_发布书籍_通信图.svg",
        "通信图四：发布书籍（正常流程）",
        "由 design/sequence/04_发布书籍_正常与异常.svg 转换；发布成功初始状态为 AVAILABLE",
        n04, m04, b04,
        "状态结果：成功时新增 book_listing 记录且 status = AVAILABLE；异常分支不产生发布记录。",
        height=1300,
    )

    # 05 检索与查看
    n05 = [
        Node("user", "校园用户", "Actor", "actor", 300, 150, 200, 64),
        Node("searchUI", "检索界面", "Boundary", "boundary", 300, 470, 220, 64),
        Node("searchService", "检索服务", "Control", "control", 820, 470, 240, 64),
        Node("book", "book_listing", "Entity", "book", 1240, 260, 220, 64),
        Node("db", "数据库", "Infra", "infra", 1240, 650, 220, 64),
    ]
    m05 = [
        Message("1", "user", "searchUI", "search", "search(keyword, category)", "call", "keyword, category", "SearchUI.search", "search(keyword, category)", "提交检索条件"),
        Message("1.1", "searchUI", "searchService", "searchBooks", "searchBooks(keyword, category)", "call", "keyword, category；返回 BookSummary[]", "SearchService.searchBooks", "searchBooks(keyword, category)", "执行检索"),
        Message("1.1.1", "searchService", "book", "match", "match(title / author / category)", "call", "keyword, category", "BookListing.match", "match title / author / category", "匹配书名、作者或分类"),
        Message("1.1.2", "searchService", "db", "SELECT listings", "SELECT listings and current status", "call", "匹配条件", "BookListing.query", "SELECT listings and current status", "查询结果与当前状态"),
        Message("1.1.2.1", "db", "searchService", "«return» BookSummary[]", "BookSummary[]", "return", "书籍摘要列表", "BookListing.query 返回", "BookSummary[]", "返回结果集"),
        Message("1.1.3", "searchService", "searchUI", "result list", "result list with AVAILABLE / RESERVED", "return", "摘要及状态", "SearchService.searchBooks 返回", "result list with AVAILABLE / RESERVED", "状态必须随结果展示"),
        Message("1.1.4", "searchUI", "user", "display results", "display results", "return", "检索结果", "SearchUI.displayResults", "display results", "展示列表"),
        Message("2", "user", "searchUI", "viewDetails", "viewDetails(bookId)", "call", "bookId", "SearchUI.viewDetails", "viewDetails(bookId)", "打开书籍详情"),
        Message("2.1", "searchUI", "searchService", "getBookDetails", "getBookDetails(bookId)", "call", "bookId；返回 BookDetails + status", "SearchService.getBookDetails", "getBookDetails(bookId)", "查询详情"),
        Message("2.1.1", "searchService", "book", "findById", "findById(bookId)", "call", "bookId", "BookListing.findById", "findById(bookId)", "按编号查询"),
        Message("2.1.2", "searchService", "db", "SELECT details", "SELECT details + current status", "call", "bookId", "BookListing.queryOne", "BookDetails + current status", "读取详情和状态"),
        Message("2.1.2.1", "db", "searchService", "«return» BookDetails", "BookDetails + current status", "return", "详情与状态", "BookListing.queryOne 返回", "BookDetails + current status", "无记录则返回不可用"),
        Message("2.1.3", "searchService", "searchUI", "display details", "display details", "return", "详情与状态", "SearchService.getBookDetails 返回", "display details", "保留 AVAILABLE/RESERVED"),
        Message("2.1.4", "searchUI", "user", "display details", "display details", "return", "详情与状态", "SearchUI.displayDetails", "display details", "用户查看详情"),
    ]
    b05 = [
        Branch("[无匹配项]", "检索服务 → 检索界面：empty result", "界面提示未找到匹配书籍。"),
        Branch("[结果书籍为 RESERVED]", "检索界面 → 校园用户：显示 RESERVED", "仍可展示，但不得显示为可售。"),
        Branch("[详情查询无记录]", "检索服务 → 检索界面：not found", "提示详情不可用，不把不存在的书籍显示为有效结果。"),
    ]
    sc05 = Scenario(
        "C-05", "05_检索与查看_通信图.svg",
        "通信图五：检索与查看（正常流程）",
        "由 design/sequence/05_检索与查看_正常与异常.svg 转换；查询只读，不修改书籍状态",
        n05, m05, b05,
        "状态结果：不产生状态迁移；返回结果必须携带当前 book_listing.status，RESERVED 不得显示为可售。",
        height=1220,
    )

    return [sc01, sc02, sc03, sc04, sc05]


def render_png(svg_path: Path) -> None:
    candidates = [
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ]
    exe = next((p for p in candidates if p.exists()), None)
    if exe is None:
        print(f"[skip] 未找到 Edge/Chrome，无法导出 PNG：{svg_path.name}", file=sys.stderr)
        return
    png_path = svg_path.with_suffix(".png")
    # 使用 2 倍像素密度，保证 Word 中放大后仍清晰
    cmd = [
        str(exe),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=1.6",
        f"--window-size={SCENARIO_WIDTH},{_png_height}",
        f"--screenshot={png_path}",
        svg_path.as_uri(),
    ]
    subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if png_path.exists():
        print(f"[ok] {png_path.relative_to(ROOT)} ({png_path.stat().st_size} bytes)")
    else:
        print(f"[warn] PNG 未生成：{svg_path.name}", file=sys.stderr)


_png_height = 1250


def main() -> None:
    global _png_height
    parser = argparse.ArgumentParser()
    parser.add_argument("--png", action="store_true", help="同时导出 PNG")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scenarios = build_scenarios()
    mapping_parts = [
        "# 协作图对象与消息对应说明",
        "",
        "> 版本：v1.0 · 日期：2026-11-23 · 维护：C（32406300079 王伟锋，软件243）",
        "> 本文件由 `tools/generate_communication.py` 根据同一份图数据生成，避免图、表不一致。",
        "> 对象名、消息名与 `design/sequence/` 下的顺序图保持一致；消息序号采用分层编号。",
        "",
        "## 1. 对象与类对应",
        "",
        "| 协作图对象 | 类 / 构件 | 角色 | 职责 | 顺序图生命线 | 数据落点 |",
        "|---|---|---|---|---|---|",
    ]
    for key, (name, cls, resp, lifeline, table) in OBJECTS.items():
        role = "Actor" if "Actor" in cls else cls.split(" / ")[0]
        mapping_parts.append(f"| {name} | {cls} | {role} | {resp} | {lifeline} | {table} |")
    mapping_parts += ["", "## 2. 场景消息对应", ""]

    for sc in scenarios:
        by_key = {n.key: n for n in sc.nodes}
        svg = layout_scenario(sc)
        svg_path = OUT_DIR / sc.filename
        svg_path.write_text(svg, encoding="utf-8")
        print(f"[ok] {svg_path.relative_to(ROOT)}")
        mapping_parts.append(message_markdown(sc, by_key))
        if args.png:
            _png_height = sc.height
            render_png(svg_path)

    # 对象表去重：只保留本组场景实际用到的对象说明，但保留全部便于横向查询
    mapping_path = OUT_DIR / "message-mapping.md"
    mapping_path.write_text("\n".join(mapping_parts) + "\n", encoding="utf-8")
    print(f"[ok] {mapping_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
