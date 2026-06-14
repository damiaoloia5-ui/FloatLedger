"""QTimer 定时刷新调度。"""

import logging

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

logger = logging.getLogger(__name__)


class RefreshScheduler(QObject):
    """定时刷新调度器。

    用法:
        scheduler = RefreshScheduler(interval_minutes=5)
        scheduler.refresh_requested.connect(some_refresh_handler)
        scheduler.start()
    """

    refresh_requested = pyqtSignal()  # 请求刷新数据

    def __init__(
        self, interval_minutes: int = 5, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._interval_ms = interval_minutes * 60 * 1000
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timeout)

    def start(self) -> None:
        """启动定时刷新。"""
        if self._timer.isActive():
            self._timer.stop()
        self._timer.start(self._interval_ms)
        logger.info("定时刷新已启动，间隔 %d 分钟", self._interval_ms // 60000)

    def stop(self) -> None:
        """停止定时刷新。"""
        self._timer.stop()
        logger.info("定时刷新已停止")

    def set_interval(self, minutes: int) -> None:
        """更新刷新间隔（若正在运行则立即生效）。"""
        self._interval_ms = minutes * 60 * 1000
        if self._timer.isActive():
            self._timer.setInterval(self._interval_ms)
        logger.info("刷新间隔已更新为 %d 分钟", minutes)

    def is_running(self) -> bool:
        """定时器是否在运行。"""
        return self._timer.isActive()

    def _on_timeout(self) -> None:
        """定时器超时回调。"""
        logger.debug("定时刷新触发")
        self.refresh_requested.emit()
