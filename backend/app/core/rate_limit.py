"""查询限流：令牌桶算法。

进程内实现，作为分布式限流（如 Redis + Lua）的等价实现。
对应题目二「模块 4：查询权限控制和限流」。
"""

from __future__ import annotations

import threading
import time
from typing import Dict


class TokenBucket:
    """单个令牌桶。"""

    __slots__ = ("capacity", "tokens", "refill_rate", "last")

    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate  # 每秒补充令牌数
        self.last = time.monotonic()

    def consume(self, amount: int = 1) -> bool:
        now = time.monotonic()
        # 按经过时间补充令牌
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.refill_rate)
        self.last = now
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


class RateLimiter:
    """按标识（用户名）限流。"""

    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def allow(self, identity: str) -> bool:
        with self._lock:
            bucket = self._buckets.get(identity)
            if bucket is None:
                bucket = TokenBucket(self.per_minute, self.per_minute / 60.0)
                self._buckets[identity] = bucket
            return bucket.consume(1)

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()
