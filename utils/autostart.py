"""Windows 开机自启工具。

通过注册表 HKEY_CURRENT_USER\\...\\Run 实现开机自动启动。
打包后使用 .exe 路径，开发模式使用 Python 命令行。
"""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_REGISTRY_NAME = "FloatLedger"


def _get_executable_command() -> str:
    """获取用于注册表的可执行命令。"""
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后
        return f'"{sys.executable}"'
    else:
        # 开发模式
        main_py = Path(__file__).resolve().parent.parent / "main.py"
        return f'"{sys.executable}" "{main_py}"'


def is_auto_start_enabled() -> bool:
    """检查开机自启是否已启用。"""
    if sys.platform != "win32":
        return False
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REGISTRY_KEY, 0, winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, _REGISTRY_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except OSError as exc:
        logger.debug("检查开机自启状态失败: %s", exc)
        return False


def enable_auto_start() -> bool:
    """启用开机自启。返回是否成功。"""
    if sys.platform != "win32":
        logger.warning("开机自启仅支持 Windows")
        return False
    try:
        import winreg

        command = _get_executable_command()
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REGISTRY_KEY, 0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, _REGISTRY_NAME, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        logger.info("开机自启已启用: %s", command)
        return True
    except OSError as exc:
        logger.error("启用开机自启失败: %s", exc)
        return False


def disable_auto_start() -> bool:
    """禁用开机自启。返回是否成功。"""
    if sys.platform != "win32":
        return False
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REGISTRY_KEY, 0, winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, _REGISTRY_NAME)
        except FileNotFoundError:
            pass  # 已经是禁用状态
        winreg.CloseKey(key)
        logger.info("开机自启已禁用")
        return True
    except OSError as exc:
        logger.error("禁用开机自启失败: %s", exc)
        return False


def set_auto_start(enabled: bool) -> bool:
    """设置开机自启状态。"""
    return enable_auto_start() if enabled else disable_auto_start()
