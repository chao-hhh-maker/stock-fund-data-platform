"""轻量缓存层。

进程内 TTL 缓存，作为 Redis 的等价实现（架构上等价：键值 + 过期 + 命中统计）。
代码预留 `CacheBackend` 接口，未来可无缝替换为真实 Redis。

对应题目二「模块 3：高频查询结果缓存」「模块 4：查询优化」。
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional, Tuple


class CacheBackend:
    """缓存后端接口（便于未来替换为 Redis）。"""

    def get(self, key: str) -> Optional[Any]:  # pragma: no cover - 接口定义
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl: int) -> None:  # pragma: no cover
        raise NotImplementedError

    def clear(self) -> None:  # pragma: no cover
        raise NotImplementedError


class InMemoryTTLCache(CacheBackend):
    """线程安全的进程内 TTL 缓存，带命中率统计。"""

    def __init__(self) -> None:
        self._store: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            item = self._store.get(key)
            if not item:
                self.misses += 1
                return None
            expire_at, value = item
            if time.time() > expire_at:
                # 已过期，惰性删除
                self._store.pop(key, None)
                self.misses += 1
                return None
            self.hits += 1
            return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        with self._lock:
            self._store[key] = (time.time() + ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def invalidate_prefix(self, prefix: str) -> int:
        """按前缀失效（如某标的数据更新后清其查询缓存）。返回清除条数。"""
        with self._lock:
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys:
                self._store.pop(k, None)
            return len(keys)

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return round(self.hits / total * 100, 1) if total else 0.0

    def stats(self) -> Dict[str, Any]:
        return {
            "backend": "in-memory-ttl",
            "entries": len(self._store),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate,
        }


# 全局缓存单例
cache = InMemoryTTLCache()
