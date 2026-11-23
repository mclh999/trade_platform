# 图形源文件

本目录保存实验二发布书籍模块的两张图及其生成脚本：

| 文件 | 内容 |
|---|---|
| `concept-er.png` | 概念 ER 图（Chen 表示法，关键属性） |
| `table-relationship.png` | 表间关系图（鸦脚表示法） |
| `draw_diagrams.py` | 生成脚本（Python 3.12 + Pillow 13） |

重新生成：

```bash
py -3 draw_diagrams.py
```

脚本默认使用 Windows 字体（`C:\Windows\Fonts` 下的微软雅黑、Consolas）；如在其他系统运行，请修改脚本顶部的 `FONT_DIR` 和字体文件名。

图形内容与 `../design.md`、`../data-dictionary.md` 及个人报告保持一致。若修改表名、字段名或基数，请同时修改脚本并重新生成两张 PNG。
