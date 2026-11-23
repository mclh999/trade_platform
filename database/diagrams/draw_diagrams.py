# -*- coding: utf-8 -*-
"""
绘制实验二“发布书籍模块”的概念 ER 图与表间关系图（可读版）。
画布逻辑尺寸约 900×600，插入 Word 后文字约 6–10 pt。
依赖：Python 3.12 + Pillow 13。
"""
from __future__ import annotations

import math
import os
from PIL import Image, ImageDraw, ImageFont

SCALE = 2
FONT_DIR = r"C:\Windows\Fonts"
FONT_CN = os.path.join(FONT_DIR, "msyh.ttc")
FONT_CN_B = os.path.join(FONT_DIR, "msyhbd.ttc")
FONT_MONO = os.path.join(FONT_DIR, "consola.ttf")
FONT_MONO_B = os.path.join(FONT_DIR, "consolab.ttf")

COL_TEXT = "#1F1F1F"
COL_MUTED = "#595959"
COL_LINE = "#404040"
COL_USER_FILL, COL_USER_LINE = "#E2F0D9", "#548235"
COL_BOOK_FILL, COL_BOOK_LINE = "#DEEBF7", "#2F5597"
COL_CAT_FILL, COL_CAT_LINE = "#FFF2CC", "#BF9000"
COL_REL_FILL, COL_REL_LINE = "#FCE4D6", "#C55A11"
COL_ATTR_FILL, COL_ATTR_LINE = "#FFFFFF", "#7F7F7F"
COL_HEADER = "#2F5597"
COL_ROW_ALT = "#F2F5FA"
COL_PK = "#BF9000"
COL_FK = "#2F5597"
COL_UK = "#548235"


def F(path, size):
    return ImageFont.truetype(path, int(size * SCALE), index=0)


def canvas(w, h):
    img = Image.new("RGB", (w * SCALE, h * SCALE), "white")
    return img, ImageDraw.Draw(img)


def S(v):
    return v * SCALE


def line(draw, xy, fill=COL_LINE, width=1.6):
    draw.line([(S(x), S(y)) for x, y in xy], fill=fill, width=max(1, int(width * SCALE)))


def dashed_line(draw, xy, fill=COL_LINE, width=1.2, dash=6, gap=4):
    (x1, y1), (x2, y2) = xy
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy)
    if dist == 0:
        return
    ux, uy = dx / dist, dy / dist
    pos = 0.0
    while pos < dist:
        end = min(pos + dash, dist)
        line(draw, [(x1 + ux * pos, y1 + uy * pos), (x1 + ux * end, y1 + uy * end)],
             fill=fill, width=width)
        pos = end + gap


def dashed_rect(draw, box, fill="white", outline=COL_ATTR_LINE, width=1.2):
    x1, y1, x2, y2 = box
    draw.rectangle([S(x1), S(y1), S(x2), S(y2)], fill=fill)
    dashed_line(draw, [(x1, y1), (x2, y1)], outline, width)
    dashed_line(draw, [(x2, y1), (x2, y2)], outline, width)
    dashed_line(draw, [(x2, y2), (x1, y2)], outline, width)
    dashed_line(draw, [(x1, y2), (x1, y1)], outline, width)


def text_center(draw, box, text, fnt, fill=COL_TEXT, spacing=2):
    x1, y1, x2, y2 = box
    draw.multiline_text(((x1 + x2) / 2 * SCALE, (y1 + y2) / 2 * SCALE), text,
                        font=fnt, fill=fill, anchor="mm", align="center",
                        spacing=spacing * SCALE)


def text_left(draw, x, y, text, fnt, fill=COL_TEXT):
    draw.text((S(x), S(y)), text, font=fnt, fill=fill, anchor="lm")


def text_right(draw, x, y, text, fnt, fill=COL_TEXT):
    draw.text((S(x), S(y)), text, font=fnt, fill=fill, anchor="rm")


def rounded_box(draw, box, fill, outline, width=1.8, radius=6):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle([S(x1), S(y1), S(x2), S(y2)], radius=S(radius), fill=fill,
                           outline=outline, width=max(1, int(width * SCALE)))


def diamond(draw, cx, cy, w, h, fill, outline, width=1.6):
    pts = [(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2), (cx - w / 2, cy)]
    draw.polygon([(S(x), S(y)) for x, y in pts], fill=fill, outline=outline,
                 width=max(1, int(width * SCALE)))


def ellipse(draw, cx, cy, w, h, fill, outline, width=1.2):
    draw.ellipse([S(cx - w / 2), S(cy - h / 2), S(cx + w / 2), S(cy + h / 2)],
                 fill=fill, outline=outline, width=max(1, int(width * SCALE)))


def draw_attr(draw, cx, cy, w, h, name, key=False):
    ellipse(draw, cx, cy, w, h, COL_ATTR_FILL, COL_ATTR_LINE, width=1.3)
    fnt = F(FONT_CN_B if key else FONT_CN, 14.0)
    draw.text((S(cx), S(cy)), name, font=fnt, fill=COL_TEXT, anchor="mm")
    if key:
        bbox = draw.textbbox((0, 0), name, font=fnt)
        tw = (bbox[2] - bbox[0]) / SCALE
        line(draw, [(cx - tw / 2, cy + 9), (cx + tw / 2, cy + 9)], fill=COL_TEXT, width=1.1)


# ---------------------------------------------------------------------------
# 图 1：概念 ER 图（精简为关键属性，完整属性见表3）
# ---------------------------------------------------------------------------
def concept_er(path):
    W, H = 900, 600
    img, draw = canvas(W, H)

    text_center(draw, (0, 10, W, 34), "概念 ER 图 · 发布书籍模块", F(FONT_CN_B, 20))
    text_center(draw, (0, 36, W, 52), "Chen 表示法（关键属性；完整属性见表3）", F(FONT_CN, 11), COL_MUTED)

    # 连接线
    line(draw, [(210, 285), (250, 285)])
    line(draw, [(310, 285), (350, 285)])
    line(draw, [(590, 285), (630, 285)])
    line(draw, [(690, 285), (720, 285)])

    # 属性连接线
    links = [
        ((105, 180), (135, 240)), ((225, 180), (185, 240)),
        ((100, 390), (135, 330)), ((230, 390), (195, 330)),
        ((390, 170), (415, 230)), ((500, 170), (475, 230)),
        ((380, 400), (415, 340)), ((510, 400), (475, 340)),
        ((760, 180), (785, 240)), ((820, 390), (800, 330)),
    ]
    for a, b in links:
        line(draw, [a, b], fill="#A6A6A6", width=1.0)

    # 实体
    rounded_box(draw, (40, 240, 210, 330), COL_USER_FILL, COL_USER_LINE)
    draw.text((S(125), S(273)), "USER 用户", font=F(FONT_CN_B, 18), fill=COL_TEXT, anchor="mm")
    draw.text((S(125), S(300)), "卖家 / 买家", font=F(FONT_CN, 11), fill=COL_MUTED, anchor="mm")

    rounded_box(draw, (350, 230, 590, 340), COL_BOOK_FILL, COL_BOOK_LINE)
    draw.text((S(470), S(268)), "BOOK 书籍", font=F(FONT_CN_B, 18), fill=COL_TEXT, anchor="mm")
    draw.text((S(470), S(296)), "一条记录 = 一本实体书", font=F(FONT_CN, 11), fill=COL_MUTED, anchor="mm")

    rounded_box(draw, (720, 240, 870, 330), COL_CAT_FILL, COL_CAT_LINE)
    draw.text((S(795), S(273)), "BOOK_CATEGORY", font=F(FONT_CN_B, 13), fill=COL_TEXT, anchor="mm")
    draw.text((S(795), S(300)), "书籍分类", font=F(FONT_CN, 12), fill=COL_MUTED, anchor="mm")

    # 联系
    diamond(draw, 280, 285, 60, 42, COL_REL_FILL, COL_REL_LINE)
    text_center(draw, (250, 264, 310, 306), "发布", F(FONT_CN_B, 15))
    diamond(draw, 660, 285, 60, 42, COL_REL_FILL, COL_REL_LINE)
    text_center(draw, (630, 264, 690, 306), "分类", F(FONT_CN_B, 15))

    # 关键/主要属性
    draw_attr(draw, 105, 180, 95, 42, "user_id", key=True)
    draw_attr(draw, 225, 180, 125, 42, "login_name")
    draw_attr(draw, 100, 390, 120, 42, "display_name")
    draw_attr(draw, 230, 390, 120, 42, "user_status")

    draw_attr(draw, 390, 170, 100, 42, "book_id", key=True)
    draw_attr(draw, 500, 170, 90, 42, "title")
    draw_attr(draw, 380, 400, 120, 42, "selling_price")
    draw_attr(draw, 510, 400, 120, 42, "book_status")

    draw_attr(draw, 760, 180, 120, 42, "category_id", key=True)
    draw_attr(draw, 820, 390, 140, 42, "category_name")

    # 基数与可选性
    text_left(draw, 218, 264, "1", F(FONT_CN_B, 15))
    text_left(draw, 318, 264, "N", F(FONT_CN_B, 15))
    text_left(draw, 312, 352, "0..N", F(FONT_CN, 11), COL_MUTED)
    text_left(draw, 215, 352, "1 位卖家", F(FONT_CN, 11), COL_MUTED)

    text_left(draw, 595, 264, "N", F(FONT_CN_B, 15))
    text_right(draw, 700, 264, "1", F(FONT_CN_B, 15))
    text_left(draw, 595, 352, "0..N", F(FONT_CN, 11), COL_MUTED)
    text_right(draw, 705, 352, "1 个分类", F(FONT_CN, 11), COL_MUTED)

    # 图例
    ly = 485
    text_left(draw, 40, ly, "图例：", F(FONT_CN_B, 12), COL_TEXT)
    rounded_box(draw, (95, ly - 8, 120, ly + 8), COL_BOOK_FILL, COL_BOOK_LINE, width=1.0, radius=2)
    text_left(draw, 126, ly, "实体", F(FONT_CN, 11), COL_MUTED)
    ellipse(draw, 185, ly, 28, 16, COL_ATTR_FILL, COL_ATTR_LINE, width=1.0)
    text_left(draw, 202, ly, "属性", F(FONT_CN, 11), COL_MUTED)
    diamond(draw, 260, ly, 28, 16, COL_REL_FILL, COL_REL_LINE, width=1.0)
    text_left(draw, 278, ly, "联系", F(FONT_CN, 11), COL_MUTED)
    line(draw, [(330, ly + 5), (356, ly + 5)], fill=COL_TEXT, width=1.1)
    text_left(draw, 362, ly, "标识（下划线）", F(FONT_CN, 11), COL_MUTED)
    text_left(draw, 470, ly, "1:N = 一个实体对应零个或多个实体", F(FONT_CN, 11), COL_MUTED)

    text_left(draw, 40, 555,
              "说明：订单实体由下单模块负责；本图只画发布书籍模块。可空属性 isbn、publisher、description、cover_url 见表3。",
              F(FONT_CN, 10.5), COL_MUTED)

    img = img.resize((W * SCALE, H * SCALE), Image.LANCZOS)
    img.save(path, dpi=(300, 300))
    print("saved", path, img.size)


# ---------------------------------------------------------------------------
# 图 2：表间关系图
# ---------------------------------------------------------------------------
def table_box(draw, x, y, w, title, rows):
    header_h = 34
    row_h = 21
    h = header_h + row_h * len(rows)
    draw.rectangle([S(x), S(y), S(x + w), S(y + h)], fill="white", outline="#8EA9DB",
                   width=max(1, int(1.3 * SCALE)))
    draw.rectangle([S(x), S(y), S(x + w), S(y + header_h)], fill=COL_HEADER)
    text_left(draw, x + 8, y + header_h / 2, title, F(FONT_CN_B, 14), "white")
    for i, (key, name, nullable) in enumerate(rows):
        ry = y + header_h + i * row_h
        if i % 2 == 1:
            draw.rectangle([S(x), S(ry), S(x + w), S(ry + row_h)], fill=COL_ROW_ALT)
        draw.line([S(x), S(ry), S(x + w), S(ry)], fill="#D9E2F3", width=max(1, int(0.5 * SCALE)))
        bx = x + 6
        if key in ("PK", "FK", "UK"):
            color = {"PK": COL_PK, "FK": COL_FK, "UK": COL_UK}[key]
            draw.rounded_rectangle([S(bx), S(ry + 4), S(bx + 24), S(ry + row_h - 4)],
                                   radius=S(2), fill=color)
            text_center(draw, (bx, ry + 3, bx + 24, ry + row_h - 3), key, F(FONT_MONO_B, 9), "white")
        nx = x + 34
        draw.text((S(nx), S(ry + row_h / 2)), name, font=F(FONT_MONO, 13), fill=COL_TEXT, anchor="lm")
        if nullable:
            draw.text((S(x + w - 6), S(ry + row_h / 2)), "NULL", font=F(FONT_MONO, 9),
                      fill="#A6A6A6", anchor="rm")
    return x, y, x + w, y + h


def crow_foot(draw, x, y, direction="right", size=8):
    if direction == "right":
        apex = (x - 7, y)
        pts = [(x, y - size), (x, y), (x, y + size)]
    else:
        apex = (x + 7, y)
        pts = [(x, y - size), (x, y), (x, y + size)]
    for p in pts:
        line(draw, [apex, p], fill=COL_LINE, width=1.4)


def one_bar(draw, x, y, direction="right", gap=4):
    if direction == "right":
        for dx in (0, gap):
            line(draw, [(x - dx, y - 9), (x - dx, y + 9)], fill=COL_LINE, width=1.4)
    else:
        for dx in (0, gap):
            line(draw, [(x + dx, y - 9), (x + dx, y + 9)], fill=COL_LINE, width=1.4)


def zero_circle(draw, x, y, direction="right", r=4):
    cx = x - 15 if direction == "right" else x + 15
    draw.ellipse([S(cx - r), S(y - r), S(cx + r), S(y + r)], fill="white", outline=COL_LINE,
                 width=max(1, int(1.2 * SCALE)))


def table_relationship(path):
    W, H = 900, 620
    img, draw = canvas(W, H)

    text_center(draw, (0, 10, W, 34), "表间关系图 · 发布书籍模块", F(FONT_CN_B, 20))
    text_center(draw, (0, 36, W, 52), "鸦脚表示法（Crow's Foot）：实际表名、关键字段与主外键", F(FONT_CN, 11), COL_MUTED)

    user_rows = [
        ("PK", "user_id", False),
        ("UK", "login_name", False),
        ("", "display_name", False),
        ("", "password_hash", False),
        ("", "user_status", False),
        ("", "created_at", False),
    ]
    book_rows = [
        ("PK", "book_id", False),
        ("FK", "seller_id", False),
        ("FK", "category_id", False),
        ("", "title", False),
        ("", "author", False),
        ("", "isbn", True),
        ("", "publisher", True),
        ("", "condition_level", False),
        ("", "selling_price", False),
        ("", "description", True),
        ("", "cover_url", True),
        ("", "book_status", False),
        ("", "created_at", False),
        ("", "updated_at", False),
    ]
    cat_rows = [
        ("PK", "category_id", False),
        ("UK", "category_name", False),
        ("", "sort_order", False),
        ("", "is_active", False),
        ("", "created_at", False),
    ]

    ub = table_box(draw, 35, 210, 200, "app_user（用户）", user_rows)
    bb = table_box(draw, 325, 120, 260, "book（书籍）", book_rows)
    cb = table_box(draw, 700, 225, 170, "book_category（分类）", cat_rows)

    y1 = 300
    line(draw, [(ub[2], y1), (bb[0], y1)], fill=COL_LINE, width=1.8)
    one_bar(draw, ub[2], y1, direction="right")
    zero_circle(draw, bb[0], y1, direction="right")
    crow_foot(draw, bb[0], y1, direction="right")
    text_left(draw, ub[2] + 8, y1 - 14, "1", F(FONT_CN_B, 13), COL_TEXT)
    text_left(draw, bb[0] - 38, y1 - 14, "0..N", F(FONT_CN_B, 13), COL_TEXT)
    text_center(draw, (ub[2] + 4, y1 + 2, bb[0] - 4, y1 + 20), "发布", F(FONT_CN, 11), COL_MUTED)

    y2 = 305
    line(draw, [(bb[2], y2), (cb[0], y2)], fill=COL_LINE, width=1.8)
    crow_foot(draw, bb[2], y2, direction="left")
    zero_circle(draw, bb[2], y2, direction="left")
    one_bar(draw, cb[0], y2, direction="left")
    text_left(draw, bb[2] + 14, y2 - 14, "0..N", F(FONT_CN_B, 13), COL_TEXT)
    text_right(draw, cb[0] - 14, y2 - 14, "1", F(FONT_CN_B, 13), COL_TEXT)
    text_center(draw, (bb[2] + 4, y2 + 2, cb[0] - 4, y2 + 20), "分类", F(FONT_CN, 11), COL_MUTED)

    # 图例
    ly = 505
    text_left(draw, 35, ly, "图例：", F(FONT_CN_B, 12), COL_TEXT)
    one_bar(draw, 90, ly, direction="right", gap=4)
    text_left(draw, 100, ly, "1（有且仅有一个）", F(FONT_CN, 11), COL_MUTED)
    zero_circle(draw, 225, ly, direction="right")
    crow_foot(draw, 225, ly, direction="right")
    text_left(draw, 238, ly, "0..N（零个或多个）", F(FONT_CN, 11), COL_MUTED)
    draw.rounded_rectangle([S(370), S(ly - 7), S(390), S(ly + 7)], radius=S(2), fill=COL_PK)
    text_left(draw, 396, ly, "PK 主键", F(FONT_CN, 11), COL_MUTED)
    draw.rounded_rectangle([S(470), S(ly - 7), S(490), S(ly + 7)], radius=S(2), fill=COL_FK)
    text_left(draw, 496, ly, "FK 外键", F(FONT_CN, 11), COL_MUTED)
    text_left(draw, 575, ly, "NULL = 可空", F(FONT_CN, 11), COL_MUTED)

    text_left(draw, 35, 555,
              "说明：book.seller_id → app_user.user_id，book.category_id → book_category.category_id；两列 NOT NULL。",
              F(FONT_CN, 10.5), COL_MUTED)
    text_left(draw, 35, 580,
              "完整字段类型、默认值和检查约束见表6～表9；本图只列关键字段。",
              F(FONT_CN, 10.5), COL_MUTED)

    img = img.resize((W * SCALE, H * SCALE), Image.LANCZOS)
    img.save(path, dpi=(300, 300))
    print("saved", path, img.size)


if __name__ == "__main__":
    out = os.path.dirname(os.path.abspath(__file__))
    concept_er(os.path.join(out, "concept-er.png"))
    table_relationship(os.path.join(out, "table-relationship.png"))
