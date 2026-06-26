"""APScheduler 调度器封装：加载启用的定时采集任务。"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import SessionLocal
from app.models import CrawlJob
from app.services.task_service import execute_job_by_id

logger = logging.getLogger("scheduler")

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def _job_id(job_id: int) -> str:
    return f"crawl_job_{job_id}"


# 频率预设 → cron 表达式映射（模块1 灵活更新频率配置）
# realtime/minute 在课设中按"每分钟/每5分钟"近似；daily 收盘后；weekly 周一；quarterly 季度首日。
_FREQUENCY_CRON = {
    "realtime": "*/1 * * * *",
    "minute": "*/5 * * * *",
    "daily": "0 18 * * 1-5",
    "weekly": "0 18 * * 1",
    "quarterly": "0 18 1 1,4,7,10 *",
}


def _resolve_cron(job: CrawlJob) -> str:
    """确定任务的 cron：显式 cron 优先，否则按 frequency 预设映射；manual 不调度。"""
    if job.cron and job.cron.strip():
        return job.cron.strip()
    freq = getattr(job, "frequency", "daily") or "daily"
    return _FREQUENCY_CRON.get(freq, "")


def add_or_update_job(job: CrawlJob) -> None:
    """根据 CrawlJob 的 cron / frequency 注册 / 更新调度。无有效 cron 则移除。"""
    sid = _job_id(job.id)
    if scheduler.get_job(sid):
        scheduler.remove_job(sid)
    cron = _resolve_cron(job)
    if job.enabled and cron:
        try:
            trigger = CronTrigger.from_crontab(cron, timezone="Asia/Shanghai")
            scheduler.add_job(
                execute_job_by_id,
                trigger=trigger,
                id=sid,
                args=[job.id, "scheduled"],
                replace_existing=True,
            )
            logger.info("已注册定时任务 %s cron=%s (freq=%s)", sid, cron, getattr(job, "frequency", ""))
        except ValueError as exc:
            logger.error("任务 %s cron 表达式非法：%s", sid, exc)


def remove_job(job_id: int) -> None:
    sid = _job_id(job_id)
    if scheduler.get_job(sid):
        scheduler.remove_job(sid)


def load_jobs() -> None:
    """启动时加载所有启用且含 cron 的任务。"""
    db = SessionLocal()
    try:
        jobs = db.query(CrawlJob).filter(CrawlJob.enabled.is_(True)).all()
        for job in jobs:
            if _resolve_cron(job):
                add_or_update_job(job)
    finally:
        db.close()


def start() -> None:
    if not scheduler.running:
        scheduler.start()
        load_jobs()
        logger.info("调度器已启动")


def shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("调度器已停止")
