"""QSS 样式常量和主题感知样式生成。

视觉规范参考 DESIGN.md §4.2。
背景由 overlay_window.paintEvent 绘制，QSS 仅控制子控件。
支持 scale 参数，字体随窗口大小动态缩放。
"""

from ui.themes import Theme, LIGHT

# ---------------------------------------------------------------------------
# 字体
# ---------------------------------------------------------------------------

FONT_FAMILY_CN = "Microsoft YaHei"
FONT_FAMILY_NUM = "Segoe UI"
FONT_FAMILY_DEFAULT = f"{FONT_FAMILY_CN}, {FONT_FAMILY_NUM}, sans-serif"

# ---------------------------------------------------------------------------
# 尺寸（调大窗口、留足间距）
# ---------------------------------------------------------------------------

WINDOW_WIDTH = 280
WINDOW_HEIGHT = 250
WINDOW_RADIUS = 16
EDGE_MARGIN = 20  # 默认距离屏幕边缘（像素）
MIN_WINDOW_WIDTH = 200
MIN_WINDOW_HEIGHT = 180
RESIZE_EDGE_ZONE = 6  # 边缘拖拽检测区域（像素）

# 默认字号基准（scale=1.0 时的值）
_BASE_FONT_SIZES = {
    "balanceLabel": 22,
    "balanceTitle": 10,
    "balanceDetail": 8,
    "spendingLabel": 16,
    "spendingTitle": 10,
    "timestampLabel": 8,
    "actionButton": 9,
    "titleLabel": 10,
    "balanceWarning": 22,
    "balanceError": 13,
}

# 字号缩放范围
_SCALE_MIN = 0.6
_SCALE_MAX = 2.5


def calc_scale(width: int, height: int) -> float:
    """根据窗口尺寸计算字体缩放因子。"""
    scale_w = width / WINDOW_WIDTH
    scale_h = height / WINDOW_HEIGHT
    scale = min(scale_w, scale_h)
    return max(_SCALE_MIN, min(_SCALE_MAX, scale))


def _sz(base_key: str, scale: float) -> str:
    """将基准字号乘以缩放因子，返回 pt 字符串。"""
    pt = max(5, round(_BASE_FONT_SIZES[base_key] * scale))
    return f"{pt}pt"


# ---------------------------------------------------------------------------
# 主题感知 QSS 生成
# ---------------------------------------------------------------------------


def generate_main_qss(theme: Theme = LIGHT, scale: float = 1.0) -> str:
    """根据主题和缩放因子生成主窗口 QSS。"""
    return f"""
QLabel#balanceLabel {{
    color: {theme.text_primary};
    font-family: {FONT_FAMILY_DEFAULT};
    font-size: {_sz('balanceLabel', scale)};
    font-weight: bold;
}}

QLabel#balanceTitle {{
    color: {theme.text_secondary};
    font-family: {FONT_FAMILY_DEFAULT};
    font-size: {_sz('balanceTitle', scale)};
}}

QLabel#balanceDetail {{
    color: {theme.text_muted};
    font-family: {FONT_FAMILY_DEFAULT};
    font-size: {_sz('balanceDetail', scale)};
}}

QLabel#spendingLabel {{
    color: {theme.spending_color};
    font-family: {FONT_FAMILY_DEFAULT};
    font-size: {_sz('spendingLabel', scale)};
    font-weight: bold;
}}

QLabel#spendingTitle {{
    color: {theme.text_secondary};
    font-family: {FONT_FAMILY_DEFAULT};
    font-size: {_sz('spendingTitle', scale)};
}}

QLabel#timestampLabel {{
    color: {theme.text_muted};
    font-family: {FONT_FAMILY_DEFAULT};
    font-size: {_sz('timestampLabel', scale)};
}}

QPushButton#actionButton {{
    background: {theme.button_bg};
    border: none;
    border-radius: 6px;
    padding: 5px 14px;
    color: {theme.text_secondary};
    font-family: {FONT_FAMILY_DEFAULT};
    font-size: {_sz('actionButton', scale)};
}}

QPushButton#actionButton:hover {{
    background: {theme.button_bg_hover};
    color: {theme.text_primary};
}}

QLabel#titleLabel {{
    color: {theme.text_primary};
    font-family: {FONT_FAMILY_DEFAULT};
    font-size: {_sz('titleLabel', scale)};
    font-weight: bold;
}}
"""


def generate_warning_qss(theme: Theme = LIGHT, scale: float = 1.0) -> str:
    """低余额警告状态样式。"""
    return f"""
QLabel#balanceLabel {{
    color: {theme.warning_color};
    font-family: {FONT_FAMILY_DEFAULT};
    font-size: {_sz('balanceWarning', scale)};
    font-weight: bold;
}}
"""


def generate_error_qss(theme: Theme = LIGHT, scale: float = 1.0) -> str:
    """错误/不可用状态样式。"""
    return f"""
QLabel#balanceLabel {{
    color: {theme.error_color};
    font-family: {FONT_FAMILY_DEFAULT};
    font-size: {_sz('balanceError', scale)};
    font-weight: bold;
}}
"""
