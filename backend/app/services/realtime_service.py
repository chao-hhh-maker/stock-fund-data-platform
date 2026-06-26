"""实时行情服务（模块1：实时数据更新频率 / 模块4：WebSocket 实时推送）。

交易时段从新浪秒级快照接口 `hq.sinajs.cn` 批量拉取实时价，休市时回退到库中最新收盘价。
新浪批量接口：GET https://hq.sinajs.cn/list=sh600519,sz000001 （需 Referer），
返回 var hq_str_sh600519="贵州茅台,开,昨收,现价,最高,最低,...,日期,时间";
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, time
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import FundNav, Instrument, StockDaily

logger = logging.getLogger("realtime")

_SINA_LINE = re.compile(r'hq_str_(\w+)="([^"]*)"')


def is_trading_now() -> bool:
    """是否处于 A 股连续竞价时段（粗略：工作日 9:30-11:30 / 13:00-15:00）。"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    t = now.time()
    return (time(9, 30) <= t <= time(11, 30)) or (time(13, 0) <= t <= time(15, 0))


def _sina_symbol(code: str) -> str:
    """600519.SH -> sh600519；000001.SZ -> sz000001。"""
    num, _, suffix = code.partition(".")
    prefix = "sh" if suffix.upper() == "SH" else "sz"
    return f"{prefix}{num}"


def _fetch_sina_realtime(codes: List[str]) -> Dict[str, Dict]:
    """批量拉新浪实时快照，返回 {标准代码: {price, prev_close, open, high, low, ...}}。"""
    if not codes:
        return {}
    import requests

    sina_map = {_sina_symbol(c): c for c in codes}
    url = "https://hq.sinajs.cn/list=" + ",".join(sina_map.keys())
    resp = requests.get(
        url, timeout=settings.CRAWL_REQUEST_TIMEOUT,
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"},
    )
    resp.raise_for_status()
    text = resp.content.decode("gbk", errors="ignore")
    out: Dict[str, Dict] = {}
    for sym, payload in _SINA_LINE.findall(text):
        parts = payload.split(",")
        std = sina_map.get(sym)
        if not std or len(parts) < 32:
            continue
        try:
            prev_close = float(parts[2])
            price = float(parts[3])
            if price <= 0:  # 停牌/未开盘，用昨收兜底
                price = prev_close
            pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else 0.0
            out[std] = {
                "name": parts[0], "open": float(parts[1]), "prev_close": prev_close,
                "price": price, "high": float(parts[4]), "low": float(parts[5]),
                "pct_change": pct, "date": parts[30], "time": parts[31],
            }
        except (ValueError, IndexError):
            continue
    return out


def snapshot(db: Session, stock_limit: int = 10, fund_limit: int = 4) -> Dict:
    """返回行情快照：交易时段拉新浪实时；否则用库中最新收盘。供 WebSocket 推送。"""
    stocks = (
        db.query(Instrument).filter(Instrument.asset_type == "stock")
        .order_by(Instrument.code).limit(stock_limit).all()
    )
    fund_insts = (
        db.query(Instrument).filter(Instrument.asset_type == "fund")
        .order_by(Instrument.code).limit(fund_limit).all()
    )

    quotes: List[Dict] = []
    realtime = False
    live: Dict[str, Dict] = {}
    if settings.REALTIME_ENABLED and is_trading_now():
        try:
            live = _fetch_sina_realtime([s.code for s in stocks])
            realtime = bool(live)
        except Exception as exc:  # noqa: BLE001 - 实时失败回退收盘
            logger.debug("实时行情拉取失败，回退收盘：%s", exc)

    for inst in stocks:
        if inst.code in live:
            q = live[inst.code]
            quotes.append({
                "code": inst.code, "name": inst.name, "type": "stock",
                "price": round(q["price"], 2), "pct_change": q["pct_change"],
                "date": q["date"], "realtime": True,
            })
        else:
            row = (
                db.query(StockDaily).filter(StockDaily.code == inst.code)
                .order_by(StockDaily.trade_date.desc()).first()
            )
            if row:
                quotes.append({
                    "code": inst.code, "name": inst.name, "type": "stock",
                    "price": row.close, "pct_change": row.pct_change,
                    "date": str(row.trade_date), "realtime": False,
                })

    for inst in fund_insts:
        row = (
            db.query(FundNav).filter(FundNav.code == inst.code)
            .order_by(FundNav.nav_date.desc()).first()
        )
        if row:
            quotes.append({
                "code": inst.code, "name": inst.name, "type": "fund",
                "price": row.unit_nav, "pct_change": row.daily_return,
                "date": str(row.nav_date), "realtime": False,
            })

    return {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "market_open": is_trading_now(),
        "realtime": realtime,
        "quotes": quotes,
    }
