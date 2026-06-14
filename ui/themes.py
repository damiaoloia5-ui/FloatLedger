"""主题定义 — 浅色/深色双主题。

每个主题定义完整的颜色体系，供 overlay_window 和 styles 使用。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """主题颜色方案（不可变）。"""

    name: str
    display_name: str  # UI 显示名
    bg_color: tuple[int, int, int]  # 背景填充 RGB
    bg_alpha: int  # 背景透明度 0-255
    border_color: tuple[int, int, int]  # 边框 RGB
    border_alpha: int  # 边框透明度 0-255
    text_primary: str
    text_secondary: str
    text_muted: str
    spending_color: str
    warning_color: str
    error_color: str
    divider_color: str
    button_bg: str
    button_bg_hover: str
    close_normal: str
    close_hover: str


LIGHT = Theme(
    name="light",
    display_name="浅色",
    bg_color=(255, 255, 255),
    bg_alpha=int(0.78 * 255),
    border_color=(255, 255, 255),
    border_alpha=int(0.4 * 255),
    text_primary="#1a1a1a",
    text_secondary="#666666",
    text_muted="#999999",
    spending_color="#e74c3c",
    warning_color="#f39c12",
    error_color="#95a5a6",
    divider_color="rgba(0, 0, 0, 0.08)",
    button_bg="rgba(0, 0, 0, 0.04)",
    button_bg_hover="rgba(0, 0, 0, 0.08)",
    close_normal="#999999",
    close_hover="#e74c3c",
)

DARK = Theme(
    name="dark",
    display_name="深色",
    bg_color=(30, 30, 30),
    bg_alpha=int(0.85 * 255),
    border_color=(255, 255, 255),
    border_alpha=int(0.1 * 255),
    text_primary="#e0e0e0",
    text_secondary="#a0a0a0",
    text_muted="#707070",
    spending_color="#ff6b6b",
    warning_color="#ffd43b",
    error_color="#707070",
    divider_color="rgba(255, 255, 255, 0.06)",
    button_bg="rgba(255, 255, 255, 0.06)",
    button_bg_hover="rgba(255, 255, 255, 0.12)",
    close_normal="#707070",
    close_hover="#ff6b6b",
)

THEMES: dict[str, Theme] = {
    "light": LIGHT,
    "dark": DARK,
}

DEFAULT_THEME = "light"


def get_theme(name: str) -> Theme:
    """获取指定主题，名称无效时返回默认浅色主题。"""
    return THEMES.get(name, LIGHT)
