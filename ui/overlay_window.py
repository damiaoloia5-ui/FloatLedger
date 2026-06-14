"""主弹窗 — 透明毛玻璃桌面卡片。

窗口特性：
- 无边框 + 半透明背景
- 始终置顶（可配置）
- 可拖拽移动 + 边缘拖拽缩放
- 异步 API 查询（不阻塞 UI）
- 关闭按钮最小化到系统托盘
- 主题切换（浅色/深色）+ 多语言支持
"""

import logging
from datetime import datetime

from PyQt6.QtCore import QObject, QPoint, QRect, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from api.deepseek_client import BalanceInfo, DeepSeekAPIError, DeepSeekClient
from core.calculator import calculate_today_spending
from core.config import ConfigManager
from core.scheduler import RefreshScheduler
from i18n import set_language, t
from ui.styles import (
    EDGE_MARGIN,
    calc_scale,
    generate_error_qss,
    generate_main_qss,
    generate_warning_qss,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    RESIZE_EDGE_ZONE,
    WINDOW_RADIUS,
    WINDOW_WIDTH,
)
from ui.themes import get_theme

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 边缘拖拽缩放 — 边缘标记（可用 | 组合）
# ---------------------------------------------------------------------------

_EDGE_NONE = 0
_EDGE_LEFT = 1
_EDGE_RIGHT = 2
_EDGE_TOP = 4
_EDGE_BOTTOM = 8


# ---------------------------------------------------------------------------
# 异步 API 工作线程
# ---------------------------------------------------------------------------


class _BalanceWorker(QThread):
    """余额查询工作线程，避免阻塞 UI 主线程。"""

    result_ready = pyqtSignal(object)  # BalanceInfo | DeepSeekAPIError

    def __init__(
        self, client: DeepSeekClient, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._client = client

    def run(self) -> None:
        try:
            info = self._client.get_balance()
            self.result_ready.emit(info)
        except DeepSeekAPIError as exc:
            self.result_ready.emit(exc)
        except Exception as exc:
            self.result_ready.emit(DeepSeekAPIError(f"未预期的错误: {exc}"))


# ---------------------------------------------------------------------------
# 主窗口
# ---------------------------------------------------------------------------


class OverlayWindow(QWidget):
    """DeepSeek 余额监控桌面弹窗。"""

    # 信号
    settings_requested = pyqtSignal()  # 请求打开设置
    balance_updated = pyqtSignal(float)  # 余额更新通知（传给托盘 tooltip）

    def __init__(
        self,
        config_manager: ConfigManager,
        api_client: DeepSeekClient | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._config = config_manager
        self._api_client = api_client
        self._drag_pos: QPoint = QPoint()
        self._is_refreshing = False
        self._resize_edge: int = _EDGE_NONE
        self._resize_start_geo: QRect = QRect()
        self._resize_start_pos: QPoint = QPoint()
        self._current_worker: _BalanceWorker | None = None
        self._scheduler: RefreshScheduler | None = None
        self._really_quit = False  # False=隐藏到托盘, True=真正退出
        self._tray_icon = None  # 由外部注入

        # 加载主题
        theme_name = getattr(self._config.config, "theme", "light")
        self._theme = get_theme(theme_name)

        self._init_window()
        self._init_ui()
        self._apply_styles()
        self._load_initial_data()

    # ------------------------------------------------------------------
    # 窗口初始化
    # ------------------------------------------------------------------

    def _init_window(self) -> None:
        """配置窗口属性。"""
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # 不在任务栏显示
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAutoFillBackground(False)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.setMouseTracking(True)

        cfg = self._config.config

        # 恢复或使用默认尺寸
        w = cfg.window_width if cfg.window_width is not None else WINDOW_WIDTH
        h = cfg.window_height if cfg.window_height is not None else 250
        self.resize(w, h)

        # 强制透明背景色
        from PyQt6.QtGui import QPalette
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 0))
        self.setPalette(palette)

        # 裁剪窗口为圆角形状
        self._apply_window_mask()

        # 恢复窗口位置
        if cfg.window_x is not None and cfg.window_y is not None:
            self.move(cfg.window_x, cfg.window_y)
        else:
            self._move_to_top_right()

        # 应用窗口透明度
        self.setWindowOpacity(cfg.window_opacity)

    def _move_to_top_right(self) -> None:
        """将窗口移动到屏幕右上角。"""
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.right() - WINDOW_WIDTH - EDGE_MARGIN
            y = geo.top() + EDGE_MARGIN
            self.move(x, y)

    def _apply_window_mask(self) -> None:
        """将窗口裁剪为圆角形状，消除四角白边。"""
        from PyQt6.QtCore import QRectF
        from PyQt6.QtGui import QPainterPath, QRegion

        path = QPainterPath()
        path.addRoundedRect(
            QRectF(0, 0, self.width(), self.height()),
            WINDOW_RADIUS,
            WINDOW_RADIUS,
        )
        polygon = path.toFillPolygon().toPolygon()
        self.setMask(QRegion(polygon))

    def resizeEvent(self, event) -> None:  # noqa: N802
        """窗口尺寸变化时更新圆角蒙版和字体缩放。"""
        self._apply_window_mask()
        self._apply_styles()
        super().resizeEvent(event)

    # ------------------------------------------------------------------
    # 绘制（主题感知）
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802
        """绘制半透明毛玻璃背景和边框。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 清空为全透明（覆盖 Qt 默认背景）
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # 半透明圆角背景 — 100% 不透明度 = alpha 255
        cfg_opacity = self._config.config.window_opacity
        bg = self._theme.bg_color
        bg_alpha = int(255 * cfg_opacity)
        painter.setBrush(QColor(bg[0], bg[1], bg[2], bg_alpha))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), WINDOW_RADIUS, WINDOW_RADIUS)

        bd = self._theme.border_color
        border_alpha = int(self._theme.border_alpha * cfg_opacity)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(bd[0], bd[1], bd[2], border_alpha), 1))
        painter.drawRoundedRect(self.rect(), WINDOW_RADIUS, WINDOW_RADIUS)

        painter.end()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        """构建界面布局。"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 14, 20, 12)
        main_layout.setSpacing(3)

        # 标题栏（固定在顶部）
        main_layout.addLayout(self._create_title_bar())

        # 上方弹性空间 — 内容垂直居中
        main_layout.addStretch(1)

        # 余额区域
        main_layout.addLayout(self._create_balance_section())

        # 分割线
        divider = QLabel()
        divider.setFixedHeight(1)
        divider.setStyleSheet(
            f"background: {self._theme.divider_color}; margin: 8px 0;"
        )
        self._divider = divider
        main_layout.addWidget(divider)

        # 今日消费区域
        main_layout.addLayout(self._create_spending_section())

        # 下方弹性空间 — 内容垂直居中
        main_layout.addStretch(1)

        # 时间戳
        self._timestamp_label = QLabel(t("not_updated"))
        self._timestamp_label.setObjectName("timestampLabel")
        self._timestamp_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(self._timestamp_label)

        # 操作栏
        main_layout.addLayout(self._create_action_bar())

    def _create_title_bar(self) -> QHBoxLayout:
        """创建标题栏。"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 4)

        title = QLabel("🔷 DeepSeek")
        title.setObjectName("titleLabel")

        layout.addWidget(title)
        layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; "
            f"color: {self._theme.close_normal}; font-size: 12pt; }} "
            f"QPushButton:hover {{ color: {self._theme.close_hover}; }}"
        )
        close_btn.clicked.connect(self._on_close)
        close_btn.setToolTip(t("close_tooltip"))
        self._close_btn = close_btn

        layout.addWidget(close_btn)
        return layout

    def _create_balance_section(self) -> QVBoxLayout:
        """创建余额显示区域。"""
        layout = QVBoxLayout()
        layout.setSpacing(3)

        title = QLabel(t("balance_title"))
        title.setObjectName("balanceTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._balance_label = QLabel("—")
        self._balance_label.setObjectName("balanceLabel")
        self._balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._detail_label = QLabel("")
        self._detail_label.setObjectName("balanceDetail")
        self._detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(self._balance_label)
        layout.addWidget(self._detail_label)
        return layout

    def _create_spending_section(self) -> QVBoxLayout:
        """创建今日消费显示区域。"""
        layout = QVBoxLayout()
        layout.setSpacing(3)

        title = QLabel(t("spending_title"))
        title.setObjectName("spendingTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._spending_label = QLabel("¥ 0.00")
        self._spending_label.setObjectName("spendingLabel")
        self._spending_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(self._spending_label)
        return layout

    def _create_action_bar(self) -> QHBoxLayout:
        """创建底部操作栏。"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 4, 0, 0)

        self._refresh_btn = QPushButton(t("refresh_btn"))
        self._refresh_btn.setObjectName("actionButton")
        self._refresh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._refresh_btn.clicked.connect(self._on_refresh)

        settings_btn = QPushButton(t("settings_btn"))
        settings_btn.setObjectName("actionButton")
        settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        settings_btn.clicked.connect(self.settings_requested.emit)

        layout.addWidget(self._refresh_btn)
        layout.addStretch()
        layout.addWidget(settings_btn)
        return layout

    # ------------------------------------------------------------------
    # 样式 & 语言
    # ------------------------------------------------------------------

    def _apply_styles(self) -> None:
        """根据当前主题和窗口尺寸应用样式表。"""
        scale = calc_scale(self.width(), self.height())
        self.setStyleSheet(generate_main_qss(self._theme, scale))

    def apply_theme(self, theme_name: str) -> None:
        """切换主题并刷新 UI。"""
        self._theme = get_theme(theme_name)
        self._apply_styles()
        self._close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; "
            f"color: {self._theme.close_normal}; font-size: 12pt; }} "
            f"QPushButton:hover {{ color: {self._theme.close_hover}; }}"
        )
        self._divider.setStyleSheet(
            f"background: {self._theme.divider_color}; margin: 6px 0;"
        )
        self.update()

    def apply_language(self) -> None:
        """切换语言并刷新所有 UI 文本。"""
        lang = getattr(self._config.config, "language", "zh_CN")
        set_language(lang)

        self._close_btn.setToolTip(t("close_tooltip"))
        self._refresh_btn.setText(t("refresh_btn"))
        self._timestamp_label.setText(t("not_updated"))

        for label in self.findChildren(QLabel):
            if label.objectName() == "balanceTitle":
                label.setText(t("balance_title"))
            elif label.objectName() == "spendingTitle":
                label.setText(t("spending_title"))

        if self._tray_icon is not None and hasattr(self._tray_icon, "apply_language"):
            self._tray_icon.apply_language()

    # ------------------------------------------------------------------
    # 数据加载
    # ------------------------------------------------------------------

    def _load_initial_data(self) -> None:
        """从本地快照加载初始数据（不触发 API 调用）。"""
        state = self._config.state

        if not self._config.api_key_plain:
            self._show_no_api_key()
            return

        if state.last_balance > 0:
            self._update_display(
                total_balance=state.last_balance,
                topped_up=0.0,
                granted=0.0,
                is_available=True,
                today_spending=0.0,
            )
            if state.last_updated:
                self._timestamp_label.setText(
                    t("last_updated", time=self._format_time(state.last_updated))
                )

    def _show_no_api_key(self) -> None:
        """显示 API Key 未配置状态。"""
        self._balance_label.setText(t("no_api_key"))
        scale = calc_scale(self.width(), self.height())
        self._balance_label.setStyleSheet(generate_error_qss(self._theme, scale))
        self._detail_label.setText(t("click_settings"))
        self._spending_label.setText("—")

    # ------------------------------------------------------------------
    # 刷新逻辑（异步）
    # ------------------------------------------------------------------

    def _on_refresh(self) -> None:
        """手动刷新按钮点击。"""
        if self._is_refreshing:
            return
        self.refresh_balance()

    def refresh_balance(self) -> None:
        """异步刷新余额数据。"""
        if self._is_refreshing:
            return

        if not self._api_client:
            self._show_no_api_key()
            return

        self._is_refreshing = True
        self._refresh_btn.setText(t("refreshing_btn"))
        self._refresh_btn.setEnabled(False)

        self._current_worker = _BalanceWorker(self._api_client, parent=self)
        self._current_worker.result_ready.connect(self._on_balance_result)
        self._current_worker.finished.connect(self._on_worker_finished)
        self._current_worker.start()

    def _on_balance_result(self, result: object) -> None:
        """工作线程返回结果的处理。"""
        if isinstance(result, BalanceInfo):
            self._on_balance_fetched(result)
        elif isinstance(result, DeepSeekAPIError):
            self._on_balance_error(str(result))
        else:
            self._on_balance_error("未知错误")

    def _on_balance_fetched(self, info: BalanceInfo) -> None:
        """余额查询成功后的处理。"""
        current_balance = info.total_balance
        spending_result = calculate_today_spending(
            self._config.state, current_balance, info
        )

        # 持久化更新
        self._config.update_state(
            today_first_balance=spending_result.new_first_balance,
            today_first_time=spending_result.new_first_time,
            last_balance=current_balance,
            last_updated=datetime.now().isoformat(timespec="seconds"),
        )
        self._config.add_balance_record(current_balance)

        # 更新 UI
        self._update_display(
            total_balance=info.total_balance,
            topped_up=info.topped_up_balance,
            granted=info.granted_balance,
            is_available=info.is_available,
            today_spending=spending_result.today_spending,
        )

        now = datetime.now().strftime("%H:%M:%S")
        self._timestamp_label.setText(t("last_updated", time=now))

        # 通知托盘更新 tooltip
        self.balance_updated.emit(current_balance)

        logger.info(
            "余额刷新成功: ¥%.2f, 今日消费: ¥%.2f",
            current_balance,
            spending_result.today_spending,
        )

    def _on_balance_error(self, error_msg: str) -> None:
        """余额查询失败后的处理。"""
        self._balance_label.setText(t("cannot_connect"))
        scale = calc_scale(self.width(), self.height())
        self._balance_label.setStyleSheet(generate_error_qss(self._theme, scale))
        self._detail_label.setText(error_msg[:40])
        self._timestamp_label.setText(t("connection_failed"))
        logger.warning("余额查询失败: %s", error_msg)

    def _on_worker_finished(self) -> None:
        """工作线程结束 — 恢复按钮状态。"""
        self._is_refreshing = False
        self._refresh_btn.setText(t("refresh_btn"))
        self._refresh_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # 显示更新
    # ------------------------------------------------------------------

    def _update_display(
        self,
        total_balance: float,
        topped_up: float,
        granted: float,
        is_available: bool,
        today_spending: float,
    ) -> None:
        """更新界面数据。"""
        self._balance_label.setText(f"¥ {total_balance:.2f}")
        self._balance_label.setStyleSheet("")

        if not is_available:
            scale = calc_scale(self.width(), self.height())
            self._balance_label.setStyleSheet(generate_warning_qss(self._theme, scale))

        self._detail_label.setText(
            f"{t('topped_up')} ¥{topped_up:.2f}  |  {t('granted')} ¥{granted:.2f}"
        )
        self._spending_label.setText(f"¥ {today_spending:.2f}")

    # ------------------------------------------------------------------
    # 窗口交互
    # ------------------------------------------------------------------

    def _on_close(self) -> None:
        """关闭按钮点击。"""
        self.close()

    def prepare_quit(self) -> None:
        """准备真正退出应用（由托盘 "退出" 菜单调用）。"""
        self._really_quit = True

        if self._current_worker is not None and self._current_worker.isRunning():
            self._current_worker.quit()
            self._current_worker.wait(3000)

        if self._scheduler is not None:
            self._scheduler.stop()

        self._config.update_config(
            window_x=self.x(), window_y=self.y(),
            window_width=self.width(), window_height=self.height(),
        )

    def closeEvent(self, event) -> None:  # noqa: N802
        """窗口关闭事件。

        - _really_quit=True → 真正关闭
        - 有托盘图标 → 隐藏到托盘
        - 无托盘图标 → 直接退出
        """
        self._config.update_config(
            window_x=self.x(), window_y=self.y(),
            window_width=self.width(), window_height=self.height(),
        )

        if self._really_quit:
            if self._current_worker is not None and self._current_worker.isRunning():
                self._current_worker.quit()
                self._current_worker.wait(3000)
            if self._scheduler is not None:
                self._scheduler.stop()
            super().closeEvent(event)
            return

        if self._tray_icon is not None and self._tray_icon.isVisible():
            event.ignore()
            self.hide()
            self._tray_icon.show_minimize_notification()
            return

        super().closeEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        """鼠标按下 — 判断边缘缩放或整体拖拽。"""
        if event is None:
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return

        pos = event.position().toPoint()
        edge = self._detect_edge(pos)

        if edge != _EDGE_NONE:
            self._resize_edge = edge
            self._resize_start_geo = self.geometry()
            self._resize_start_pos = event.globalPosition().toPoint()
        else:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        """鼠标移动 — 处理缩放、拖拽或悬停光标。"""
        if event is None:
            return

        if event.buttons() & Qt.MouseButton.LeftButton and self._resize_edge != _EDGE_NONE:
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            geo = QRect(self._resize_start_geo)

            if self._resize_edge & _EDGE_LEFT:
                new_width = geo.right() - (geo.left() + delta.x()) + 1
                if new_width >= self.minimumWidth():
                    geo.setLeft(geo.left() + delta.x())
            if self._resize_edge & _EDGE_RIGHT:
                new_width = geo.width() + delta.x()
                if new_width >= self.minimumWidth():
                    geo.setWidth(new_width)
            if self._resize_edge & _EDGE_TOP:
                new_height = geo.bottom() - (geo.top() + delta.y()) + 1
                if new_height >= self.minimumHeight():
                    geo.setTop(geo.top() + delta.y())
            if self._resize_edge & _EDGE_BOTTOM:
                new_height = geo.height() + delta.y()
                if new_height >= self.minimumHeight():
                    geo.setHeight(new_height)

            self.setGeometry(geo)
            self._apply_window_mask()
            return

        if event.buttons() & Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            return

        # 悬停 — 更新光标形状
        edge = self._detect_edge(event.position().toPoint())
        if edge != _EDGE_NONE:
            self.setCursor(self._edge_cursor(edge))
        else:
            self.unsetCursor()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        """鼠标释放 — 结束缩放或拖拽，保存位置和尺寸。"""
        if self._resize_edge != _EDGE_NONE:
            self._resize_edge = _EDGE_NONE
            self._config.update_config(
                window_x=self.x(), window_y=self.y(),
                window_width=self.width(), window_height=self.height(),
            )
        if not self._drag_pos.isNull():
            self._config.update_config(
                window_x=self.x(), window_y=self.y(),
                window_width=self.width(), window_height=self.height(),
            )
        self._drag_pos = QPoint()

    # ------------------------------------------------------------------
    # 边缘缩放辅助
    # ------------------------------------------------------------------

    def _detect_edge(self, pos: QPoint) -> int:
        """判断位置靠近哪些边缘，返回边缘标记组合。"""
        edge = _EDGE_NONE
        w, h = self.width(), self.height()
        if pos.x() < RESIZE_EDGE_ZONE:
            edge |= _EDGE_LEFT
        elif pos.x() > w - RESIZE_EDGE_ZONE:
            edge |= _EDGE_RIGHT
        if pos.y() < RESIZE_EDGE_ZONE:
            edge |= _EDGE_TOP
        elif pos.y() > h - RESIZE_EDGE_ZONE:
            edge |= _EDGE_BOTTOM
        return edge

    @staticmethod
    def _edge_cursor(edge: int) -> QCursor:
        """根据边缘组合返回对应的光标形状。"""
        if edge in (_EDGE_LEFT | _EDGE_TOP, _EDGE_RIGHT | _EDGE_BOTTOM):
            return QCursor(Qt.CursorShape.SizeFDiagCursor)
        if edge in (_EDGE_RIGHT | _EDGE_TOP, _EDGE_LEFT | _EDGE_BOTTOM):
            return QCursor(Qt.CursorShape.SizeBDiagCursor)
        if edge in (_EDGE_LEFT, _EDGE_RIGHT):
            return QCursor(Qt.CursorShape.SizeHorCursor)
        if edge in (_EDGE_TOP, _EDGE_BOTTOM):
            return QCursor(Qt.CursorShape.SizeVerCursor)
        return QCursor(Qt.CursorShape.ArrowCursor)

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def set_api_client(self, client: DeepSeekClient) -> None:
        """设置/更新 API 客户端（支持延迟注入）。"""
        self._api_client = client

    def set_tray_icon(self, tray_icon) -> None:
        """注入系统托盘图标引用。"""
        self._tray_icon = tray_icon

    def get_scheduler(self) -> RefreshScheduler:
        """获取定时刷新调度器（需在事件循环启动后调用 start）。"""
        if self._scheduler is None:
            self._scheduler = RefreshScheduler(
                interval_minutes=self._config.config.refresh_interval_minutes,
                parent=self,
            )
            self._scheduler.refresh_requested.connect(self.refresh_balance)
        return self._scheduler

    def apply_config_changes(self) -> None:
        """应用配置变更（设置对话框保存后调用）。"""
        cfg = self._config.config

        # 刷新间隔
        if self._scheduler is not None:
            self._scheduler.set_interval(cfg.refresh_interval_minutes)

        # 置顶
        if cfg.always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(
                self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint
            )
        self.show()

        # 主题 + 透明度 + 语言
        self.apply_theme(getattr(cfg, "theme", "light"))
        self.setWindowOpacity(cfg.window_opacity)
        self.apply_language()

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _format_time(iso_str: str) -> str:
        """将 ISO 时间格式化为 HH:MM:SS。"""
        try:
            dt = datetime.fromisoformat(iso_str)
            return dt.strftime("%H:%M:%S")
        except (ValueError, TypeError):
            return iso_str
