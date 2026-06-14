"""API Key 简单编解码工具。

使用 Base64 编码，非加密级别防护，仅防止明文存储 API Key。
安全性依赖文件系统权限（%APPDATA% 用户隔离目录）。
"""

import base64
import logging

logger = logging.getLogger(__name__)


def encode_key(api_key: str) -> str:
    """将 API Key 进行 Base64 编码。

    Args:
        api_key: 明文 API Key。

    Returns:
        Base64 编码后的字符串。空输入返回空字符串。
    """
    if not api_key:
        return ""
    return base64.b64encode(api_key.encode("utf-8")).decode("ascii")


def decode_key(encoded: str) -> str:
    """将 Base64 编码的 API Key 解码为明文。

    Args:
        encoded: Base64 编码的字符串。

    Returns:
        解码后的明文 API Key。解码失败返回空字符串。
    """
    if not encoded:
        return ""
    try:
        return base64.b64decode(encoded.encode("ascii")).decode("utf-8")
    except Exception:
        logger.warning("API Key 解码失败，数据可能已损坏")
        return ""
