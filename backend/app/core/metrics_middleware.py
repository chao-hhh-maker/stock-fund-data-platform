"""API 性能监控中间件（模块5：API 服务性能和可用性监控）。

进程内统计每个路由的请求数、累计耗时、错误数，暴露给 /monitor/api-stats。
轻量等价实现：无需 Prometheus，零依赖，clone 即跑。
"""

from __future__ import annotations

import threading
import time
from typing import Dict, List

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_lock = threading.Lock()
# path -> {count, total_ms, errors, max_ms}
_stats: Dict[str, Dict[str, float]] = {}


def _record(path: str, elapsed_ms: float, is_error: bool) -> None:
    with _lock:
        s = _stats.setdefault(path, {"count": 0, "total_ms": 0.0, "errors": 0, "max_ms": 0.0})
        s["count"] += 1
        s["total_ms"] += elapsed_ms
        s["max_ms"] = max(s["max_ms"], elapsed_ms)
        if is_error:
            s["errors"] += 1


def get_api_stats() -> List[Dict]:
    """返回各路径性能指标，按平均耗时降序。"""
    out: List[Dict] = []
    with _lock:
        for path, s in _stats.items():
            count = s["count"] or 1
            out.append({
                "path": path,
                "count": int(s["count"]),
                "avg_ms": round(s["total_ms"] / count, 2),
                "max_ms": round(s["max_ms"], 2),
                "errors": int(s["errors"]),
                "error_rate": round(s["errors"] / count * 100, 2),
            })
    return sorted(out, key=lambda x: x["avg_ms"], reverse=True)


def reset_stats() -> None:
    with _lock:
        _stats.clear()


class APIMetricsMiddleware(BaseHTTPMiddleware):
    """记录每个请求的耗时与状态码。"""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        is_error = False
        try:
            response = await call_next(request)
            is_error = response.status_code >= 500
            return response
        except Exception:
            is_error = True
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            # 用路由模板（而非含参数的真实路径）聚合，避免维度爆炸
            route = request.scope.get("route")
            path = getattr(route, "path", None) or request.url.path
            _record(path, elapsed_ms, is_error)
