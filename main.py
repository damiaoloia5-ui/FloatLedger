"""DeepSeek API 消费监控桌面弹窗 — 程序入口。

启动流程（优化：窗口尽快出现，非关键初始化延迟执行）:
1. 单实例检测（已运行则激活现有窗口并退出）
2. 加载本地配置 (snapshot.json)
3. 创建主窗口 + 单实例监听 + 系统托盘
4. ★ 立即显示窗口
5. 延迟执行：API Key 检查、API 客户端、调度器、首次刷新
6. 进入 Qt 事件循环
"""

import logging
import sys

from PyQt6.QtCore import QIODeviceBase, QTimer
from PyQt6.QtNetwork import QLocalSocket, QLocalServer
from PyQt6.QtWidgets import QApplication, QInputDialog

from core.config import ConfigManager
from i18n import set_language, t
from ui.overlay_window import OverlayWindow
from ui.tray_icon import TrayIcon

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"

# 单实例通信的服务器名称
_SINGLE_INSTANCE_SERVER = "DeepSeekMonitor_SingleInstance"

# 模块级引用，防止 QLocalServer 被垃圾回收
_single_instance_server: QLocalServer | None = None


def _setup_logging(debug: bool = False) -> None:
    """配置日志。"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)


# ---------------------------------------------------------------------------
# 单实例检测
# ---------------------------------------------------------------------------


def _is_already_running() -> bool:
    """检测是否已有实例在运行。

    尝试连接到已有的 QLocalServer：
    - 连接成功 → 说明已有实例 → 发送"显示窗口"指令后返回 True
    - 连接失败 → 说明无已有实例 → 返回 False
    """
    socket = QLocalSocket()
    socket.connectToServer(_SINGLE_INSTANCE_SERVER, QIODeviceBase.OpenModeFlag.WriteOnly)

    if socket.waitForConnected(50):
        # 已有实例在运行，发送激活指令
        socket.write(b"SHOW")
        socket.flush()
        socket.waitForBytesWritten(500)
        socket.disconnectFromServer()
        return True

    return False


def _start_single_instance_server(window: OverlayWindow) -> None:
    """启动单实例监听服务器。

    当未来启动的新实例连接时，恢复并激活当前窗口。
    服务器对象存储在模块级变量中，防止被垃圾回收。
    """
    global _single_instance_server

    # 清理可能残留的服务器（上次崩溃未清理）
    QLocalServer.removeServer(_SINGLE_INSTANCE_SERVER)

    _single_instance_server = QLocalServer()
    _single_instance_server.newConnection.connect(
        lambda: _on_new_instance(_single_instance_server, window)
    )
    _single_instance_server.listen(_SINGLE_INSTANCE_SERVER)


def _on_new_instance(server: QLocalServer, window: OverlayWindow) -> None:
    """处理新实例的连接请求 — 恢复并激活窗口。"""
    socket = server.nextPendingConnection()
    if socket is None:
        return

    socket.waitForReadyRead(1000)
    data = socket.readAll().data()
    socket.disconnectFromServer()

    if data == b"SHOW":
        window.show()
        window.raise_()
        window.activateWindow()


# ---------------------------------------------------------------------------
# API Key 首次配置
# ---------------------------------------------------------------------------


def _prompt_api_key(parent) -> str | None:
    """弹出输入框让用户输入 API Key。"""
    key, ok = QInputDialog.getText(
        parent,
        t("api_key_dialog_title"),
        t("api_key_dialog_prompt"),
        echo=QInputDialog.TextInputEchoMode.Password,
    )
    if ok and key.strip():
        return key.strip()
    return None


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------


def main() -> int:
    """程序入口。"""
    _setup_logging(debug="--debug" in sys.argv)
    logger = logging.getLogger("main")
    logger.info("DeepSeek 余额监控启动中…")

    # 创建 Qt 应用
    app = QApplication(sys.argv)
    app.setApplicationName("DeepSeek Monitor")
    app.setQuitOnLastWindowClosed(False)  # 有托盘图标，关闭窗口不退出

    # 单实例检测：已有实例在运行 → 激活它并退出
    if _is_already_running():
        logger.info("已有实例在运行，激活现有窗口并退出")
        return 0

    # 加载配置
    config = ConfigManager()
    logger.info("配置目录: %s", config.config_path)

    # 初始化语言（必须在创建 UI 之前）
    set_language(getattr(config.config, "language", "zh_CN"))

    # 创建主窗口
    window = OverlayWindow(config)

    # 启动单实例监听（必须在窗口创建之后）
    _start_single_instance_server(window)

    # 创建系统托盘（关闭按钮依赖此对象，必须在 show 之前）
    tray = TrayIcon()
    tray.set_window(window)
    window.set_tray_icon(tray)

    if config.config.show_tray_icon:
        tray.show()

    # ★ 尽早显示窗口，用户立刻看到界面
    window.show()
    logger.info("窗口已显示")

    # 延迟执行非关键初始化（API 客户端、调度器、首次刷新）
    # QTimer.singleShot(0) 将任务推迟到下一个事件循环迭代，
    # 让窗口先完成首次绘制再执行。
    def _deferred_setup() -> None:
        from api.deepseek_client import DeepSeekClient
        from ui.settings_dialog import SettingsDialog

        # API Key 检查
        api_key = config.api_key_plain
        if not api_key:
            key = _prompt_api_key(window)
            if key:
                config.set_api_key(key)
                api_key = key
                logger.info("API Key 已配置")
            else:
                logger.warning("未配置 API Key，将显示提示")

        # 创建 API 客户端
        client: DeepSeekClient | None = None
        if api_key:
            try:
                client = DeepSeekClient(api_key)
                window.set_api_client(client)
            except ValueError as exc:
                logger.error("API Client 初始化失败: %s", exc)

        # 启动定时刷新
        scheduler = window.get_scheduler()
        if client:
            scheduler.start()

        # 余额更新 → 同步托盘 tooltip
        window.balance_updated.connect(tray.update_tooltip)

        # 设置信号 — 打开设置对话框
        def _on_settings() -> None:
            nonlocal client
            dialog = SettingsDialog(config, parent=window)

            # 保存后应用变更
            def _on_saved() -> None:
                nonlocal client
                new_key = config.api_key_plain
                if new_key:
                    try:
                        client = DeepSeekClient(new_key)
                        window.set_api_client(client)
                        scheduler.start()
                    except ValueError as exc:
                        logger.error("重建 API Client 失败: %s", exc)

                # 应用窗口和主题变更
                window.apply_config_changes()

                # 托盘可见性
                if config.config.show_tray_icon:
                    tray.show()
                else:
                    tray.hide()

                # 自动刷新
                if client:
                    window.refresh_balance()

            dialog.settings_saved.connect(_on_saved)
            dialog.exec()

        window.settings_requested.connect(_on_settings)

        # 首次自动刷新
        if client:
            window.refresh_balance()

        logger.info("延迟初始化完成")

    QTimer.singleShot(0, _deferred_setup)

    logger.info("启动完成")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
