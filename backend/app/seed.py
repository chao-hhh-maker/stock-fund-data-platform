"""种子数据：登记预置标的，可选预采集一批样例行情，保证演示零等待。"""

from __future__ import annotations

import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import FundNav, Instrument, StockDaily
from app.services import crawler, sample_data, user_service

logger = logging.getLogger("seed")


def seed_instruments(db: Session) -> None:
    """登记预置标的主数据。"""
    for item in sample_data.SAMPLE_INSTRUMENTS:
        if not db.query(Instrument).filter(Instrument.code == item["code"]).first():
            db.add(Instrument(**item))
    db.commit()


def seed_market_data(db: Session) -> None:
    """为尚无数据的预置标的预采集样例行情（快速、确定性，保证零等待启动）。

    初始化只用样例数据（即使装了 akshare 也不在启动时拉真实数据，避免启动卡顿）；
    真实数据由用户在页面上按需点击「采集」获取。已有数据的标的跳过，重启更快。
    """
    have_stock = {
        r[0] for r in db.query(StockDaily.code).distinct().all()
    }
    have_fund = {
        r[0] for r in db.query(FundNav.code).distinct().all()
    }
    stocks = [
        i["code"] for i in sample_data.SAMPLE_INSTRUMENTS
        if i["asset_type"] == "stock" and i["code"] not in have_stock
    ]
    funds = [
        i["code"] for i in sample_data.SAMPLE_INSTRUMENTS
        if i["asset_type"] == "fund" and i["code"] not in have_fund
    ]
    if not stocks and not funds:
        return
    # 强制样例数据初始化，保证启动快速且离线可用
    original = settings.CRAWL_FORCE_SAMPLE
    settings.CRAWL_FORCE_SAMPLE = True
    try:
        if stocks:
            crawler.crawl_stock_daily(db, stocks)
        if funds:
            crawler.crawl_fund_nav(db, funds)
    finally:
        settings.CRAWL_FORCE_SAMPLE = original


def run_all(db: Session, with_market_data: bool = True) -> None:
    user_service.ensure_seed_users(db, settings)
    seed_instruments(db)
    _cleanup_orphan_runs(db)
    if with_market_data:
        seed_market_data(db)
    logger.info("种子数据初始化完成")


def _cleanup_orphan_runs(db: Session) -> None:
    """启动时把残留的 running 运行记录标记为 failed（上次异常退出导致）。"""
    from datetime import datetime

    from app.models import CrawlRun

    orphans = db.query(CrawlRun).filter(CrawlRun.status == "running").all()
    for run in orphans:
        run.status = "failed"
        run.finished_at = datetime.now()
        run.message = (run.message or "") + " [启动时清理：上次未正常结束]"
    if orphans:
        db.commit()
        logger.info("清理了 %d 条残留运行记录", len(orphans))
