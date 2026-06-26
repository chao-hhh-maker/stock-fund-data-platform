"""交易日历与节假日。

对应题目二「模块 5：节假日和特殊日期处理」。
内置 A 股法定节假日（简化，覆盖近年主要假期），用于：
- 采集时跳过非交易日
- 数据完整性检查时正确识别"应有但缺失"的交易日
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Set

# A 股主要法定节假日（简化集合，可按年补充）。格式 (月, 日) 的固定假期 + 显式日期。
# 这里用显式日期集合覆盖常见休市日；非交易日 = 周末 ∪ 节假日。
_HOLIDAYS: Set[str] = {
    # 2025
    "2025-01-01",
    "2025-01-28", "2025-01-29", "2025-01-30", "2025-01-31", "2025-02-03", "2025-02-04",
    "2025-04-04", "2025-05-01", "2025-05-02", "2025-05-05",
    "2025-06-02", "2025-10-01", "2025-10-02", "2025-10-03", "2025-10-06", "2025-10-07", "2025-10-08",
    # 2026（预估主要假期）
    "2026-01-01",
    "2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19", "2026-02-20",
    "2026-04-06", "2026-05-01", "2026-06-19",
    "2026-10-01", "2026-10-02", "2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08",
}


def is_trading_day(d: date) -> bool:
    """判断是否为交易日：非周末且非节假日。"""
    if d.weekday() >= 5:  # 周六日
        return False
    return d.isoformat() not in _HOLIDAYS


def trading_days_between(start: date, end: date) -> List[date]:
    """返回 [start, end] 区间内的所有交易日（升序）。"""
    result: List[date] = []
    cursor = start
    while cursor <= end:
        if is_trading_day(cursor):
            result.append(cursor)
        cursor += timedelta(days=1)
    return result


def expected_trading_days(start: date, end: date) -> int:
    """区间内应有的交易日数量。"""
    return len(trading_days_between(start, end))
