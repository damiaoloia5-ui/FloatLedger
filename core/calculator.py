"""消费差值计算 + 跨天逻辑。

今日消费 = 今日首次余额 - 当前余额

特殊情况：
- 首次启动（无历史）→ 消费 = 0，以当前余额为基准线
- 跨天 → 重置基准线为当前余额，消费 = 0
- 余额增加（充值）→ 重置基准线，消费 = 0
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime

from api.deepseek_client import BalanceInfo
from core.config import AppState

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SpendingResult:
    """消费计算结果（不可变）。"""

    today_spending: float  # 今日消费金额（≥ 0）
    new_first_balance: float  # 新的今日首次余额基准线
    new_first_time: str  # 基准线时间 (ISO 格式)
    baseline_reset: bool  # 基准线是否被重置


def calculate_today_spending(
    state: AppState,
    current_balance: float,
    balance_info: BalanceInfo,  # noqa: ARG001 — 保留参数以备未来扩展
) -> SpendingResult:
    """计算今日消费金额。

    Args:
        state: 当前持久化状态（包含基准线信息）。
        current_balance: API 返回的当前余额。
        balance_info: 完整余额信息（预留扩展用）。

    Returns:
        SpendingResult 包含消费金额和新的基准线信息。
    """
    now = datetime.now()
    today = now.date()
    now_iso = now.isoformat(timespec="seconds")

    # 情况 1：无历史记录（首次启动）
    if state.today_first_time is None or state.today_first_balance <= 0.0:
        logger.info("首次记录或无历史，设定基准线: ¥%.2f", current_balance)
        return SpendingResult(
            today_spending=0.0,
            new_first_balance=current_balance,
            new_first_time=now_iso,
            baseline_reset=True,
        )

    # 解析基准线日期
    try:
        first_time = datetime.fromisoformat(state.today_first_time)
        first_date = first_time.date()
    except (ValueError, TypeError):
        logger.warning("基准线时间格式异常，重置基准线")
        return SpendingResult(
            today_spending=0.0,
            new_first_balance=current_balance,
            new_first_time=now_iso,
            baseline_reset=True,
        )

    # 情况 2：跨天
    if first_date != today:
        logger.info(
            "跨天重置: %s → %s，新基准 ¥%.2f", first_date, today, current_balance
        )
        return SpendingResult(
            today_spending=0.0,
            new_first_balance=current_balance,
            new_first_time=now_iso,
            baseline_reset=True,
        )

    # 情况 3：同日但余额增加（充值）
    spending = state.today_first_balance - current_balance
    if spending < 0:
        logger.info(
            "检测到充值（余额增加），重置基准线: ¥%.2f → ¥%.2f",
            state.today_first_balance,
            current_balance,
        )
        return SpendingResult(
            today_spending=0.0,
            new_first_balance=current_balance,
            new_first_time=now_iso,
            baseline_reset=True,
        )

    # 情况 4：正常消费
    logger.debug(
        "今日消费: ¥%.2f (基准 ¥%.2f - 当前 ¥%.2f)",
        spending,
        state.today_first_balance,
        current_balance,
    )
    return SpendingResult(
        today_spending=spending,
        new_first_balance=state.today_first_balance,
        new_first_time=state.today_first_time,
        baseline_reset=False,
    )
