"""系统托盘图标与菜单。

功能:
- 双击托盘图标: 显示/隐藏主窗口
- 右键菜单: 显示/隐藏、刷新、设置、退出
- Tooltip: 显示当前余额
- 首次最小化通知
"""

import logging

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from i18n import t
from ui.icon_factory import create_tray_icon

logger = logging.getLogger(__name__)


class TrayIcon(QSystemTrayIcon):
    """FloatLedger 系统托盘图标。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._window = None
        self._has_shown_notification = False

        # 图标
        self.setIcon(create_tray_icon())
        self.setToolTip(t("tray_tooltip"))

        # 右键菜单
        self._menu = QMenu()

        self._show_action = self._menu.addAction(t("tray_show"))
        self._menu.addSeparator()
        self._refresh_action = self._menu.addAction(t("tray_refresh"))
        self._settings_action = self._menu.addAction(t("tray_settings"))
        self._menu.addSeparator()
        self._quit_action = self._menu.addAction(t("tray_quit"))
        self.setContextMenu(self._menu)

        # 信号连接
        self.activated.connect(self._on_activated)
        self._show_action.triggered.connect(self._toggle_window)
        self._refresh_action.triggered.connect(self._on_refresh)
        self._settings_action.triggered.connect(self._on_settings)
        self._quit_action.triggered.connect(self._on_quit)

    def set_window(self, window) -> None:
        """设置关联的主窗口引用。"""
        self._window = window

    def update_tooltip(self, balance: float | None = None) -> None:
        """更新托盘图标提示文字。"""
        if balance is not None:
            self.setToolTip(t("tray_balance_tooltip", balance=balance))
        else:
            self.setToolTip(t("tray_tooltip"))

    def show_minimize_notification(self) -> None:
        """最小化到托盘时不弹出通知。"""
        pass

    # ------------------------------------------------------------------
    # 语言切换
    # ------------------------------------------------------------------

    def apply_language(self) -> None:
        """切换语言后刷新菜单文本。"""
        self._show_action.setText(
            t("tray_hide") if (self._window and self._window.isVisible()) else t("tray_show")
        )
        self._refresh_action.setText(t("tray_refresh"))
        self._settings_action.setText(t("tray_settings"))
        self._quit_action.setText(t("tray_quit"))

    # ------------------------------------------------------------------
    # 信号处理
    # ------------------------------------------------------------------

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """托盘图标激活事件。"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_window()

    def _toggle_window(self) -> None:
        """切换主窗口可见性。"""
        if self._window is None:
            return
        if self._window.isVisible():
            self._window.hide()
            self._show_action.setText(t("tray_show"))
        else:
            self._window.show()
            self._window.raise_()
            self._window.activateWindow()
            self._show_action.setText(t("tray_hide"))

    def _on_refresh(self) -> None:
        """菜单 — 刷新余额。"""
        if self._window is not None:
            self._window.refresh_balance()

    def _on_settings(self) -> None:
        """菜单 — 打开设置。"""
        if self._window is not None:
            self._window.settings_requested.emit()

    def _on_quit(self) -> None:
        """菜单 — 退出应用。"""
        if self._window is not None:
            self._window.prepare_quit()
        QApplication.quit()
