"""程序图标生成器。

使用 QPainter 在运行时生成应用图标，无需外部图片文件。
构建时可通过 scripts/generate_assets.py 导出 PNG/ICO。
"""

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap


# FloatLedger 品牌色系
_ICON_BG_START = QColor(68, 100, 246)  # 渐变起始色
_ICON_BG_END = QColor(100, 80, 220)  # 渐变结束色
_ICON_TEXT_COLOR = QColor(255, 255, 255)


def create_app_pixmap(size: int = 256) -> QPixmap:
    """生成应用图标的 QPixmap。

    绘制圆角矩形背景 + "DS" 文字，风格简洁。
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 圆角矩形背景
    margin = max(size // 16, 1)
    radius = size // 5
    rect = QRect(margin, margin, size - 2 * margin, size - 2 * margin)
    painter.setBrush(_ICON_BG_START)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(rect, radius, radius)

    # "FL" 文字
    font_size = max(int(size * 0.35), 8)
    font = QFont("Segoe UI", font_size, QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(_ICON_TEXT_COLOR)
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "FL")

    painter.end()
    return pixmap


def create_tray_icon() -> QIcon:
    """生成系统托盘图标（多分辨率）。"""
    icon = QIcon()
    for size in (16, 24, 32, 48, 64):
        icon.addPixmap(create_app_pixmap(size))
    return icon


def save_icon_png(path: str, size: int = 256) -> None:
    """将图标保存为 PNG 文件（构建脚本使用）。"""
    pixmap = create_app_pixmap(size)
    pixmap.save(path, "PNG")
