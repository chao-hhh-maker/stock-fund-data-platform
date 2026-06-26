"""元数据与数据血缘服务。

对应题目二「模块 3：元数据管理」：数据字典、字段说明、数据血缘、更新时效。
"""

from __future__ import annotations

from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import FundNav, Instrument, StockDaily

# 数据字典：表与字段说明（静态元数据）
# sensitivity（模块3 数据权限和敏感级别标记）：public 公开 / internal 内部 / sensitive 敏感
DATA_DICTIONARY: List[Dict] = [
    {
        "table": "instruments",
        "comment": "证券标的主数据",
        "fields": [
            {"name": "code", "type": "string", "desc": "标准化证券代码，如 600519.SH", "sensitivity": "public"},
            {"name": "name", "type": "string", "desc": "证券名称", "sensitivity": "public"},
            {"name": "asset_type", "type": "string", "desc": "类型：stock / fund", "sensitivity": "public"},
            {"name": "market", "type": "string", "desc": "市场：SH/SZ/OF", "sensitivity": "public"},
            {"name": "category", "type": "string", "desc": "行业 / 基金分类（申万/中信/GICS）", "sensitivity": "public"},
        ],
    },
    {
        "table": "stock_daily",
        "comment": "股票日线行情",
        "fields": [
            {"name": "trade_date", "type": "date", "desc": "交易日期", "sensitivity": "public"},
            {"name": "open/high/low/close", "type": "float", "desc": "开高低收价格（前复权）", "sensitivity": "public"},
            {"name": "volume", "type": "float", "desc": "成交量（手）", "sensitivity": "internal"},
            {"name": "amount", "type": "float", "desc": "成交额（元）", "sensitivity": "sensitive"},
            {"name": "pct_change", "type": "float", "desc": "涨跌幅(%)，清洗时计算", "sensitivity": "public"},
            {"name": "source", "type": "string", "desc": "数据来源：akshare / tencent / sina / sample", "sensitivity": "internal"},
        ],
    },
    {
        "table": "fund_nav",
        "comment": "基金净值",
        "fields": [
            {"name": "nav_date", "type": "date", "desc": "净值日期", "sensitivity": "public"},
            {"name": "unit_nav", "type": "float", "desc": "单位净值", "sensitivity": "public"},
            {"name": "accum_nav", "type": "float", "desc": "累计净值", "sensitivity": "public"},
            {"name": "adj_nav", "type": "float", "desc": "复权净值（分红再投，清洗时计算）", "sensitivity": "public"},
            {"name": "daily_return", "type": "float", "desc": "日增长率(%)，清洗时计算", "sensitivity": "public"},
            {"name": "source", "type": "string", "desc": "数据来源：akshare / sample", "sensitivity": "internal"},
        ],
    },
    {
        "table": "announcements",
        "comment": "公开数据源：公告/新闻/舆情",
        "fields": [
            {"name": "title", "type": "string", "desc": "公告/新闻标题", "sensitivity": "public"},
            {"name": "category", "type": "string", "desc": "类型：announcement/news/sentiment/report", "sensitivity": "public"},
            {"name": "sentiment", "type": "string", "desc": "舆情情绪：positive/neutral/negative", "sensitivity": "public"},
            {"name": "publish_date", "type": "date", "desc": "发布日期", "sensitivity": "public"},
            {"name": "source", "type": "string", "desc": "来源渠道", "sensitivity": "internal"},
        ],
    },
]


SENSITIVE_FIELDS = {"amount"}  # 字段级权限：无权限用户脱敏的字段


def get_data_dictionary() -> List[Dict]:
    return DATA_DICTIONARY


def get_lineage(db: Session) -> List[Dict]:
    """数据血缘：按标的统计来源、行数、最新更新日期。"""
    lineage: List[Dict] = []

    # 股票
    stock_stats = (
        db.query(
            StockDaily.code,
            StockDaily.source,
            func.count(StockDaily.id),
            func.max(StockDaily.trade_date),
            func.min(StockDaily.trade_date),
        )
        .group_by(StockDaily.code, StockDaily.source)
        .all()
    )
    for code, source, cnt, latest, earliest in stock_stats:
        lineage.append(
            {
                "code": code,
                "dataset": "stock_daily",
                "source": source,
                "rows": cnt,
                "earliest": str(earliest) if earliest else None,
                "latest": str(latest) if latest else None,
            }
        )

    # 基金
    fund_stats = (
        db.query(
            FundNav.code,
            FundNav.source,
            func.count(FundNav.id),
            func.max(FundNav.nav_date),
            func.min(FundNav.nav_date),
        )
        .group_by(FundNav.code, FundNav.source)
        .all()
    )
    for code, source, cnt, latest, earliest in fund_stats:
        lineage.append(
            {
                "code": code,
                "dataset": "fund_nav",
                "source": source,
                "rows": cnt,
                "earliest": str(earliest) if earliest else None,
                "latest": str(latest) if latest else None,
            }
        )

    return sorted(lineage, key=lambda x: (x["dataset"], x["code"]))
