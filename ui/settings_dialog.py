"""设置对话框 — API Key、刷新间隔、窗口行为、外观、语言、主题。

完整实现 DESIGN.md §5 中描述的所有设置项。
"""

import logging

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from api.deepseek_client import DeepSeekAPIError, DeepSeekClient
from core.config import ConfigManager
from i18n import t
from i18n.translations import LANGUAGES
from ui.themes import THEMES
from utils.autostart import is_auto_start_enabled, set_auto_start

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 连接测试工作线程
# ---------------------------------------------------------------------------


class _TestConnectionWorker(QThread):
    """API 连接测试工作线程，避免阻塞 UI。"""

    result_ready = pyqtSignal(bool, str)  # (success, message)

    def __init__(self, api_key: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._api_key = api_key

    def run(self) -> None:
        try:
            client = DeepSeekClient(self._api_key)
            info = client.get_balance()
            self.result_ready.emit(True, t("test_success", balance=info.total_balance))
        except DeepSeekAPIError as exc:
            self.result_ready.emit(False, str(exc))
        except Exception as exc:
            self.result_ready.emit(False, f"Unknown error: {exc}")


# ---------------------------------------------------------------------------
# 设置对话框
# ---------------------------------------------------------------------------


class SettingsDialog(QDialog):
    """FloatLedger 设置对话框。"""

    settings_saved = pyqtSignal()  # 设置已保存，需要应用变更

    def __init__(
        self, config_manager: ConfigManager, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._config = config_manager
        self._test_worker: _TestConnectionWorker | None = None

        self._init_ui()
        self._load_values()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        """构建对话框界面。"""
        self.setWindowTitle(t("settings_title"))
        self.setFixedSize(400, 560)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 12)

        layout.addWidget(self._create_api_key_group())
        layout.addWidget(self._create_refresh_group())
        layout.addWidget(self._create_behavior_group())
        layout.addWidget(self._create_appearance_group())

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        restore_btn = QPushButton(t("restore_defaults"))
        restore_btn.clicked.connect(self._restore_defaults)
        btn_layout.addWidget(restore_btn)

        save_btn = QPushButton(t("save"))
        save_btn.setDefault(True)
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self._save_and_close)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _create_api_key_group(self) -> QGroupBox:
        """创建 API Key 设置区域。"""
        group = QGroupBox(t("api_key_group"))
        layout = QVBoxLayout()

        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_input.setPlaceholderText(t("api_key_placeholder"))
        layout.addWidget(self._api_key_input)

        # 显示/隐藏 + 测试连接
        row = QHBoxLayout()
        self._toggle_key_btn = QPushButton(t("show_key"))
        self._toggle_key_btn.setFixedWidth(55)
        self._toggle_key_btn.clicked.connect(self._toggle_key_visibility)
        row.addWidget(self._toggle_key_btn)

        self._test_btn = QPushButton(t("test_connection"))
        self._test_btn.clicked.connect(self._test_connection)
        row.addWidget(self._test_btn)

        self._test_status = QLabel("")
        self._test_status.setStyleSheet("font-size: 9pt;")
        row.addWidget(self._test_status)
        row.addStretch()

        layout.addLayout(row)
        group.setLayout(layout)
        return group

    def _create_refresh_group(self) -> QGroupBox:
        """创建刷新间隔设置区域。"""
        group = QGroupBox(t("refresh_interval"))
        layout = QVBoxLayout()

        self._interval_group = QButtonGroup(self)
        intervals = [
            (1, t("interval_1min")),
            (5, t("interval_5min")),
            (10, t("interval_10min")),
            (30, t("interval_30min")),
        ]
        grid = QGridLayout()
        grid.setSpacing(6)

        for i, (minutes, label) in enumerate(intervals):
            radio = QRadioButton(label)
            self._interval_group.addButton(radio, minutes)
            grid.addWidget(radio, i // 2, i % 2)

        # 自定义
        self._custom_radio = QRadioButton(t("custom"))
        self._interval_group.addButton(self._custom_radio, -1)
        self._custom_input = QLineEdit()
        self._custom_input.setFixedWidth(55)
        self._custom_input.setValidator(QIntValidator(1, 1440))
        self._custom_input.setPlaceholderText(t("minutes"))

        custom_row = QHBoxLayout()
        custom_row.addWidget(self._custom_radio)
        custom_row.addWidget(self._custom_input)
        custom_row.addStretch()
        grid.addLayout(custom_row, 2, 0, 1, 2)

        layout.addLayout(grid)
        group.setLayout(layout)
        return group

    def _create_behavior_group(self) -> QGroupBox:
        """创建窗口行为设置区域。"""
        group = QGroupBox(t("window_behavior"))
        layout = QVBoxLayout()

        self._always_on_top_cb = QCheckBox(t("always_on_top"))
        self._show_tray_cb = QCheckBox(t("show_tray_icon"))
        self._auto_start_cb = QCheckBox(t("auto_start"))

        layout.addWidget(self._always_on_top_cb)
        layout.addWidget(self._show_tray_cb)
        layout.addWidget(self._auto_start_cb)

        group.setLayout(layout)
        return group

    def _create_appearance_group(self) -> QGroupBox:
        """创建外观设置区域（语言 + 透明度 + 主题）。"""
        group = QGroupBox(t("appearance"))
        layout = QVBoxLayout()

        # 语言
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel(t("language_label")))
        self._lang_combo = QComboBox()
        for code, display_name in LANGUAGES:
            self._lang_combo.addItem(display_name, code)
        lang_row.addWidget(self._lang_combo)
        lang_row.addStretch()
        layout.addLayout(lang_row)

        # 透明度
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel(t("opacity")))
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(30, 100)
        self._opacity_slider.setValue(100)
        self._opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._opacity_slider.setTickInterval(10)
        opacity_row.addWidget(self._opacity_slider)
        self._opacity_label = QLabel("100%")
        self._opacity_label.setFixedWidth(36)
        opacity_row.addWidget(self._opacity_label)
        self._opacity_slider.valueChanged.connect(
            lambda v: self._opacity_label.setText(f"{v}%")
        )
        layout.addLayout(opacity_row)

        # 主题
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel(t("theme_label")))
        self._theme_btn_group = QButtonGroup(self)
        self._theme_keys = list(THEMES.keys())  # ["light", "dark"]
        for idx, theme in enumerate(THEMES.values()):
            label = t("theme_light") if theme.name == "light" else t("theme_dark")
            radio = QRadioButton(label)
            self._theme_btn_group.addButton(radio, idx)
            theme_row.addWidget(radio)
        theme_row.addStretch()
        layout.addLayout(theme_row)

        group.setLayout(layout)
        return group

    # ------------------------------------------------------------------
    # 加载与保存
    # ------------------------------------------------------------------

    def _load_values(self) -> None:
        """从配置加载当前值到各控件。"""
        cfg = self._config.config
        api_key = self._config.api_key_plain
        self._api_key_input.setText(api_key)

        # 刷新间隔
        interval = cfg.refresh_interval_minutes
        btn = self._interval_group.button(interval)
        if btn:
            btn.setChecked(True)
        else:
            self._custom_radio.setChecked(True)
            self._custom_input.setText(str(interval))

        # 窗口行为
        self._always_on_top_cb.setChecked(cfg.always_on_top)
        self._show_tray_cb.setChecked(cfg.show_tray_icon)
        self._auto_start_cb.setChecked(is_auto_start_enabled())

        # 语言
        lang_code = getattr(cfg, "language", "zh_CN")
        for i in range(self._lang_combo.count()):
            if self._lang_combo.itemData(i) == lang_code:
                self._lang_combo.setCurrentIndex(i)
                break

        # 透明度
        self._opacity_slider.setValue(int(cfg.window_opacity * 100))

        # 主题
        theme_name = getattr(cfg, "theme", "light")
        theme_keys = list(THEMES.keys())
        if theme_name in theme_keys:
            idx = theme_keys.index(theme_name)
            btn = self._theme_btn_group.button(idx)
            if btn:
                btn.setChecked(True)

    def _save_and_close(self) -> None:
        """保存设置并关闭对话框。"""
        # API Key（仅当用户修改了内容时更新）
        new_key = self._api_key_input.text().strip()
        if new_key and new_key != self._config.api_key_plain:
            self._config.set_api_key(new_key)

        # 刷新间隔
        interval = self._interval_group.checkedId()
        if interval == -1:  # 自定义
            try:
                interval = int(self._custom_input.text())
                interval = max(1, interval)
            except ValueError:
                interval = 5
        self._config.update_config(refresh_interval_minutes=interval)

        # 窗口行为
        self._config.update_config(
            always_on_top=self._always_on_top_cb.isChecked(),
            show_tray_icon=self._show_tray_cb.isChecked(),
            auto_start=self._auto_start_cb.isChecked(),
        )

        # 语言
        lang_code = self._lang_combo.currentData()
        self._config.update_config(language=lang_code)

        # 主题
        theme_keys = list(THEMES.keys())
        theme_idx = self._theme_btn_group.checkedId()
        theme_name = theme_keys[theme_idx] if 0 <= theme_idx < len(theme_keys) else "light"
        self._config.update_config(theme=theme_name)

        # 开机自启
        set_auto_start(self._auto_start_cb.isChecked())

        # 透明度
        opacity = self._opacity_slider.value() / 100.0
        self._config.update_config(window_opacity=opacity)

        self.settings_saved.emit()
        self.accept()

    def _restore_defaults(self) -> None:
        """恢复默认设置。"""
        from core.config import DEFAULT_REFRESH_INTERVAL, DEFAULT_WINDOW_OPACITY

        self._api_key_input.setText(self._config.api_key_plain)

        btn = self._interval_group.button(DEFAULT_REFRESH_INTERVAL)
        if btn:
            btn.setChecked(True)

        self._always_on_top_cb.setChecked(True)
        self._show_tray_cb.setChecked(True)
        self._auto_start_cb.setChecked(False)
        self._opacity_slider.setValue(int(DEFAULT_WINDOW_OPACITY * 100))

        # 默认语言：简体中文
        for i in range(self._lang_combo.count()):
            if self._lang_combo.itemData(i) == "zh_CN":
                self._lang_combo.setCurrentIndex(i)
                break

        # 默认浅色主题
        btn = self._theme_btn_group.button(0)
        if btn:
            btn.setChecked(True)

    # ------------------------------------------------------------------
    # 交互
    # ------------------------------------------------------------------

    def _toggle_key_visibility(self) -> None:
        """切换 API Key 显示/隐藏。"""
        if self._api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self._api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._toggle_key_btn.setText(t("hide_key"))
        else:
            self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._toggle_key_btn.setText(t("show_key"))

    def _test_connection(self) -> None:
        """测试 API Key 连接。"""
        key = self._api_key_input.text().strip()
        if not key:
            self._test_status.setText(t("test_enter_key"))
            self._test_status.setStyleSheet("color: #e74c3c; font-size: 9pt;")
            return

        self._test_btn.setEnabled(False)
        self._test_status.setText(t("testing"))
        self._test_status.setStyleSheet("color: #666; font-size: 9pt;")

        self._test_worker = _TestConnectionWorker(key, parent=self)
        self._test_worker.result_ready.connect(self._on_test_result)
        self._test_worker.finished.connect(lambda: self._test_btn.setEnabled(True))
        self._test_worker.start()

    def _on_test_result(self, success: bool, message: str) -> None:
        """连接测试结果回调。"""
        color = "#27ae60" if success else "#e74c3c"
        self._test_status.setStyleSheet(f"color: {color}; font-size: 9pt;")
        self._test_status.setText(message)
