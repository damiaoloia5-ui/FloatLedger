"""
DeepSeek API 客户端 — 封装余额查询接口。

接口文档: https://api-docs.deepseek.com/zh-cn/api/get-user-balance
"""

import logging
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

BASE_URL = "https://api.deepseek.com"
BALANCE_ENDPOINT = "/user/balance"
REQUEST_TIMEOUT = 15  # 秒
LOW_BALANCE_THRESHOLD = 5.0  # 低于此金额视为低余额（CNY）


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BalanceInfo:
    """DeepSeek 账户余额快照（不可变）。"""

    currency: str          # 货币类型，如 "CNY"
    total_balance: float   # 总余额 = 充值 + 赠送
    topped_up_balance: float   # 充值余额（永不过期）
    granted_balance: float     # 赠送余额（可能有有效期）
    is_available: bool     # 余额是否足够继续调用 API

    @property
    def is_low_balance(self) -> bool:
        """余额是否处于低位（建议充值）。"""
        return self.total_balance < LOW_BALANCE_THRESHOLD


# ---------------------------------------------------------------------------
# 自定义异常
# ---------------------------------------------------------------------------


class DeepSeekAPIError(Exception):
    """DeepSeek API 相关的所有异常的基类。"""


class AuthenticationError(DeepSeekAPIError):
    """API Key 无效或未提供。"""


class RateLimitError(DeepSeekAPIError):
    """请求频率超限。"""


class NetworkError(DeepSeekAPIError):
    """网络连接失败、DNS 解析失败等。"""


class UnexpectedResponseError(DeepSeekAPIError):
    """响应格式不符合预期。"""


# ---------------------------------------------------------------------------
# API 客户端
# ---------------------------------------------------------------------------


class DeepSeekClient:
    """DeepSeek API 客户端。

    用法:
        client = DeepSeekClient(api_key="sk-xxx")
        balance = client.get_balance()
        print(f"余额: ¥{balance.total_balance}")
    """

    def __init__(self, api_key: str, base_url: str = BASE_URL) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("api_key 不能为空")
        self._api_key = api_key.strip()
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            }
        )

    # ------------------------------------------------------------------
    # 公开方法
    # ------------------------------------------------------------------

    def get_balance(self) -> BalanceInfo:
        """查询当前账户余额。

        Returns:
            BalanceInfo: 包含总余额、充值余额、赠送余额等信息。

        Raises:
            AuthenticationError: API Key 无效 (HTTP 401)。
            RateLimitError: 请求过于频繁 (HTTP 429)。
            NetworkError: DNS / 连接 / 超时 错误。
            UnexpectedResponseError: 响应 JSON 结构不匹配或 HTTP 非预期状态码。
        """
        url = f"{self._base_url}{BALANCE_ENDPOINT}"

        try:
            response = self._session.get(url, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.Timeout:
            raise NetworkError(f"请求超时（>{REQUEST_TIMEOUT}s）: {url}")
        except requests.exceptions.ConnectionError as exc:
            raise NetworkError(f"无法连接到 DeepSeek API: {exc}")
        except requests.exceptions.RequestException as exc:
            raise NetworkError(f"网络请求异常: {exc}")

        self._raise_for_status(response)

        try:
            body = response.json()
        except (requests.exceptions.JSONDecodeError, ValueError) as exc:
            raise UnexpectedResponseError(
                f"API 返回非 JSON 响应: {exc}\n原始内容: {response.text[:300]}"
            )
        return self._parse_balance_response(body)

    def test_connection(self) -> bool:
        """快速测试 API Key 是否有效。

        Returns:
            True 表示连接成功且 Key 有效。
        """
        try:
            self.get_balance()
            return True
        except DeepSeekAPIError:
            return False

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        """根据 HTTP 状态码抛出对应异常。"""
        if response.status_code == 200:
            return
        if response.status_code == 401:
            raise AuthenticationError("API Key 无效或已过期，请检查配置")
        if response.status_code == 429:
            raise RateLimitError("请求频率超限，请稍后再试")
        if response.status_code >= 500:
            raise DeepSeekAPIError(
                f"DeepSeek 服务端错误 (HTTP {response.status_code})，请稍后重试"
            )
        raise UnexpectedResponseError(
            f"非预期的 HTTP 状态码 {response.status_code}: {response.text[:200]}"
        )

    @staticmethod
    def _parse_balance_response(data: dict) -> BalanceInfo:
        """将 API JSON 响应解析为 BalanceInfo 对象。"""
        try:
            is_available = data["is_available"]
            infos = data["balance_infos"]

            if not infos:
                raise UnexpectedResponseError("balance_infos 数组为空")

            # 只取第一个币种（对绝大多数用户来说就是 CNY）
            first = infos[0]
            balance = BalanceInfo(
                currency=first.get("currency", "CNY"),
                total_balance=float(first["total_balance"]),
                topped_up_balance=float(first["topped_up_balance"]),
                granted_balance=float(first["granted_balance"]),
                is_available=bool(is_available),
            )
            logger.debug("余额查询成功: ¥%.2f", balance.total_balance)
            return balance

        except (KeyError, ValueError, TypeError) as exc:
            raise UnexpectedResponseError(
                f"API 响应结构异常: {exc}\n原始数据: {data}"
            )

    def __repr__(self) -> str:
        key_preview = self._api_key[:8] + "***" if len(self._api_key) > 8 else "***"
        return f"DeepSeekClient(key={key_preview})"
