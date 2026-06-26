"""采集任务执行服务：包装 crawler，记录 CrawlRun 运行日志。"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import CrawlJob, CrawlRun
from app.services import crawler

logger = logging.getLogger("task_service")


def _parse_codes(target_codes: str) -> List[str]:
    return [c.strip() for c in (target_codes or "").split(",") if c.strip()]


def execute_job(db: Session, job: CrawlJob, trigger: str = "manual") -> CrawlRun:
    """执行一个采集任务并写入运行记录。"""
    run = CrawlRun(job_id=job.id, trigger=trigger, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    codes = _parse_codes(job.target_codes)
    incremental = job.mode == "incremental"
    try:
        if job.job_type == "stock_daily":
            result = crawler.crawl_stock_daily(db, codes, incremental=incremental)
        elif job.job_type == "fund_nav":
            result = crawler.crawl_fund_nav(db, codes, incremental=incremental)
        elif job.job_type == "announcement":
            result = crawler.crawl_announcements(db, codes or None)
        else:
            raise ValueError(f"未知任务类型：{job.job_type}")

        run.status = result.status
        run.rows_affected = result.rows_affected
        run.retries = result.retries
        run.source = result.source
        run.message = result.message
    except Exception as exc:  # noqa: BLE001 - 保证调度线程不崩溃
        logger.exception("任务执行失败 job_id=%s", job.id)
        run.status = "failed"
        run.message = f"执行异常：{exc}"
    finally:
        run.finished_at = datetime.now()
        db.commit()
        db.refresh(run)
    return run


def execute_job_by_id(job_id: int, trigger: str = "scheduled") -> None:
    """供调度器回调：使用独立会话执行任务。"""
    db = SessionLocal()
    try:
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if job and job.enabled:
            execute_job(db, job, trigger=trigger)
    finally:
        db.close()
