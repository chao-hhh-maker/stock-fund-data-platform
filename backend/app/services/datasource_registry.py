"""数据源注册表（模块1：多渠道数据源接入的统一登记与可视化）。

集中登记平台对接的各类数据源（开源 SDK / 公开网站 / 商业 API 占位 / 样例兜底），
并在采集过程中记录各源的命中次数与最近使用时间，供 /datasources 接口与前端展示。

这是「多渠道数据源接入」的可见性等价实现：真实可用的源（akshare/腾讯/新浪/样例/公告）
标 online，商业授权源（Wind/同花顺）标 offline 占位并预留 source 字段扩展。
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Dict, List, Optional

# 数据源静态登记表
_REGISTRY: List[Dict] = [
    {"key": "akshare", "name": "AKShare（东方财富）", "category": "开源数据", "status": "online",
     "description": "第三方开源数据：A股日线、基金净值（前复权）"},
    {"key": "tushare", "name": "Tushare", "category": "开源数据", "status": "offline",
     "description": "第三方开源数据，需 token；架构预留，未默认启用"},
    {"key": "tencent", "name": "腾讯财经", "category": "公开网站", "status": "online",
     "description": "公开行情接口（web.ifzq.gtimg.cn），akshare 失败时兜底"},
    {"key": "sina", "name": "新浪财经", "category": "公开网站", "status": "online",
     "description": "公开行情接口（hq.sinajs.cn），多源兜底第三级"},
    {"key": "announcement", "name": "公告/新闻/舆情", "category": "公开数据", "status": "online",
     "description": "证监会公告、上市公司公告、新闻舆情（样例兜底）"},
    {"key": "sample", "name": "内置样例数据", "category": "离线兜底", "status": "online",
     "description": "确定性样例生成器，保证离线/答辩可演示"},
    {"key": "wind", "name": "Wind 万得", "category": "商业API", "status": "offline",
     "description": "商业授权数据源，课设不接入；预留 source 字段可扩展"},
    {"key": "ths", "name": "同花顺 iFinD", "category": "商业API", "status": "offline",
     "description": "商业授权数据源，课设不接入；预留扩展"},
    {"key": "macro", "name": "宏观/行业/另类数据", "category": "第三方服务", "status": "offline",
     "description": "宏观经济、行业数据、另类数据对接占位"},
]

_lock = threading.Lock()
_usage: Dict[str, Dict] = {}


def record_hit(key: str) -> None:
    """记录某数据源被成功使用一次。"""
    with _lock:
        u = _usage.setdefault(key, {"hit_count": 0, "last_used": None})
        u["hit_count"] += 1
        u["last_used"] = datetime.now().isoformat(timespec="seconds")


def list_sources() -> List[Dict]:
    """返回所有数据源及其运行时使用统计。"""
    out: List[Dict] = []
    with _lock:
        for src in _REGISTRY:
            u = _usage.get(src["key"], {})
            item = dict(src)
            item["hit_count"] = u.get("hit_count", 0)
            item["last_used"] = u.get("last_used")
            # 若某源近期有命中，状态标记为 fallback/online 实际命中
            out.append(item)
    return out


def get_source(key: str) -> Optional[Dict]:
    return next((dict(s) for s in _REGISTRY if s["key"] == key), None)
