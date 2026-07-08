"""配置管理器 — 读写 snapshot.json。

文件位置: %APPDATA%\\FloatLedger\\snapshot.json
首次运行时自动创建默认配置。
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.crypto_utils import decode_key, encode_key

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 默认值
# ---------------------------------------------------------------------------

DEFAULT_REFRESH_INTERVAL = 5  # 分钟
DEFAULT_WINDOW_OPACITY = 1.0
DEFAULT_ALWAYS_ON_TOP = True
DEFAULT_SHOW_TRAY_ICON = True
MAX_BALANCE_HISTORY = 30


# ---------------------------------------------------------------------------
# 数据模型（不可变）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AppConfig:
    """用户配置。"""

    api_key: str = ""  # Base64 编码存储
    refresh_interval_minutes: int = DEFAULT_REFRESH_INTERVAL
    window_opacity: float = DEFAULT_WINDOW_OPACITY
    always_on_top: bool = DEFAULT_ALWAYS_ON_TOP
    show_tray_icon: bool = DEFAULT_SHOW_TRAY_ICON
    auto_start: bool = False
    theme: str = "light"  # "light" | "dark"
    language: str = "zh_CN"  # 语言代码，见 i18n.translations.LANGUAGES
    window_x: int | None = None
    window_y: int | None = None
    window_width: int | None = None
    window_height: int | None = None


@dataclass(frozen=True)
class AppState:
    """运行时状态。"""

    today_first_balance: float = 0.0
    today_first_time: str | None = None  # ISO 格式
    last_balance: float = 0.0
    last_updated: str | None = None  # ISO 格式
    balance_history: tuple[dict[str, Any], ...] = ()


# ---------------------------------------------------------------------------
# 配置管理器
# ---------------------------------------------------------------------------


def _get_config_dir() -> Path:
    """获取配置文件目录（%APPDATA%\\FloatLedger）。"""
    app_data = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
    return Path(app_data) / "FloatLedger"


class ConfigManager:
    """配置读写管理器。

    所有修改操作通过 update_config / update_state 生成新的不可变对象，
    并自动持久化到磁盘。
    """

    def __init__(self) -> None:
        self._config_dir = _get_config_dir()
        self._config_path = self._config_dir / "snapshot.json"
        self._config: AppConfig = AppConfig()
        self._state: AppState = AppState()
        self._load()

    # ------------------------------------------------------------------
    # 只读属性
    # ------------------------------------------------------------------

    @property
    def config(self) -> AppConfig:
        """当前用户配置（不可变）。"""
        return self._config

    @property
    def state(self) -> AppState:
        """当前运行时状态（不可变）。"""
        return self._state

    @property
    def api_key_plain(self) -> str:
        """解码后的 API Key 明文。"""
        return decode_key(self._config.api_key)

    @property
    def config_path(self) -> Path:
        """配置文件路径（调试用）。"""
        return self._config_path

    # ------------------------------------------------------------------
    # 写入操作（不可变更新）
    # ------------------------------------------------------------------

    def update_config(self, **kwargs: Any) -> AppConfig:
        """更新配置字段并保存。返回新的 AppConfig 实例。"""
        current = asdict(self._config)
        current.update(kwargs)
        self._config = AppConfig(**current)
        self._save()
        return self._config

    def update_state(self, **kwargs: Any) -> AppState:
        """更新状态字段并保存。返回新的 AppState 实例。"""
        current = asdict(self._state)
        # balance_history 需要转为 tuple 以保持不可变约束
        if "balance_history" in kwargs:
            kwargs["balance_history"] = tuple(kwargs["balance_history"])
        current.update(kwargs)
        self._state = AppState(**current)
        self._save()
        return self._state

    def set_api_key(self, api_key: str) -> None:
        """设置 API Key（自动 Base64 编码后存储）。"""
        encoded = encode_key(api_key)
        self.update_config(api_key=encoded)

    def add_balance_record(self, balance: float, time: datetime | None = None) -> None:
        """添加余额快照到历史记录。

        滚动覆盖，最多保留 MAX_BALANCE_HISTORY 条。
        """
        if time is None:
            time = datetime.now()
        record = {"time": time.isoformat(timespec="seconds"), "balance": balance}
        history = list(self._state.balance_history)
        history.append(record)
        if len(history) > MAX_BALANCE_HISTORY:
            history = history[-MAX_BALANCE_HISTORY:]
        self.update_state(balance_history=history)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """从磁盘加载配置和状态。文件不存在时使用默认值。"""
        if not self._config_path.exists():
            logger.info("配置文件不存在，使用默认值: %s", self._config_path)
            return

        try:
            raw = self._config_path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("读取配置文件失败: %s", exc)
            return

        try:
            config_data = {
                "api_key": data.get("api_key", ""),
                "refresh_interval_minutes": data.get(
                    "refresh_interval_minutes", DEFAULT_REFRESH_INTERVAL
                ),
                "window_opacity": data.get("window_opacity", DEFAULT_WINDOW_OPACITY),
                "always_on_top": data.get("always_on_top", DEFAULT_ALWAYS_ON_TOP),
                "show_tray_icon": data.get("show_tray_icon", DEFAULT_SHOW_TRAY_ICON),
                "auto_start": data.get("auto_start", False),
                "theme": data.get("theme", "light"),
                "language": data.get("language", "zh_CN"),
                "window_x": data.get("window_x"),
                "window_y": data.get("window_y"),
                "window_width": data.get("window_width"),
                "window_height": data.get("window_height"),
            }
            state_data = {
                "today_first_balance": data.get("today_first_balance", 0.0),
                "today_first_time": data.get("today_first_time"),
                "last_balance": data.get("last_balance", 0.0),
                "last_updated": data.get("last_updated"),
                "balance_history": tuple(data.get("balance_history", [])),
            }
            self._config = AppConfig(**config_data)
            self._state = AppState(**state_data)
            logger.info("配置加载成功")
        except (TypeError, ValueError) as exc:
            logger.error("配置数据格式错误，使用默认值: %s", exc)

    def _save(self) -> None:
        """将配置和状态保存到磁盘。"""
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error("创建配置目录失败: %s", exc)
            return

        combined = {**asdict(self._config), **asdict(self._state)}
        # balance_history 转为 list 以便 JSON 序列化
        combined["balance_history"] = list(combined["balance_history"])

        try:
            raw = json.dumps(combined, ensure_ascii=False, indent=2)
            self._config_path.write_text(raw, encoding="utf-8")
            logger.debug("配置保存成功: %s", self._config_path)
        except OSError as exc:
            logger.error("保存配置文件失败: %s", exc)
