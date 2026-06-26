"""采集任务路由：任务 CRUD、手动触发、运行记录。"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models import CrawlJob, CrawlRun, User
from app.schemas import (
    CrawlJobCreate,
    CrawlJobOut,
    CrawlJobUpdate,
    CrawlRunOut,
    Pagination,
    TriggerCrawlRequest,
)
from app.services import task_service
from app.services import audit_service
from app.tasks import scheduler

router = APIRouter(prefix="/tasks", tags=["采集任务"])


@router.get("", response_model=List[CrawlJobOut], summary="任务列表")
def list_jobs(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> List[CrawlJobOut]:
    jobs = db.query(CrawlJob).order_by(CrawlJob.id.desc()).all()
    return [CrawlJobOut.model_validate(j) for j in jobs]


@router.post("", response_model=CrawlJobOut, summary="创建采集任务（管理员）")
def create_job(
    payload: CrawlJobCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> CrawlJobOut:
    job = CrawlJob(**payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    scheduler.add_or_update_job(job)
    return CrawlJobOut.model_validate(job)


@router.patch("/{job_id}", response_model=CrawlJobOut, summary="更新任务（管理员）")
def update_job(
    job_id: int,
    payload: CrawlJobUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> CrawlJobOut:
    job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(job, k, v)
    db.commit()
    db.refresh(job)
    scheduler.add_or_update_job(job)
    return CrawlJobOut.model_validate(job)


@router.delete("/{job_id}", summary="删除任务（管理员）")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    scheduler.remove_job(job_id)
    db.delete(job)
    db.commit()
    return {"message": "已删除"}


@router.post("/{job_id}/run", response_model=CrawlRunOut, summary="手动触发任务（管理员）")
def run_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> CrawlRunOut:
    job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    run = task_service.execute_job(db, job, trigger="manual")
    return CrawlRunOut.model_validate(run)


@router.post("/crawl", response_model=CrawlRunOut, summary="临时采集（管理员，无需建任务）")
def quick_crawl(
    payload: TriggerCrawlRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> CrawlRunOut:
    """创建一次性任务并立即执行，便于快速演示。"""
    job = CrawlJob(
        name=f"临时-{payload.job_type}",
        job_type=payload.job_type,
        target_codes=payload.target_codes,
        mode=payload.mode,
        cron="",
        enabled=True,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    run = task_service.execute_job(db, job, trigger="manual")
    audit_service.log_action(
        db, username=_.username, role=_.role.name, action="crawl",
        target=payload.job_type, detail=f"codes={payload.target_codes};mode={payload.mode};rows={run.rows_affected}",
    )
    return CrawlRunOut.model_validate(run)


@router.post("/crawl-all", summary="一键采集全部标的（管理员，后台执行）")
def crawl_all(
    background: BackgroundTasks,
    asset_type: str = Query("all", pattern="^(all|stock|fund)$"),
    mode: str = Query("full", pattern="^(full|incremental)$"),
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
) -> dict:
    """对库中所有已登记标的批量采集（真实数据源可用时拉真实数据）。

    采集在后台执行，接口立即返回；进度可在「运行记录」查看，避免前端超时。
    """
    from app.models import Instrument

    types = ["stock", "fund"] if asset_type == "all" else [asset_type]
    job_types = {"stock": "stock_daily", "fund": "fund_nav"}
    created_jobs = []
    for t in types:
        codes = [
            r[0] for r in db.query(Instrument.code).filter(Instrument.asset_type == t).all()
        ]
        if not codes:
            continue
        # 复用同名任务，避免每次点击都新建，保持任务列表整洁
        name = f"一键采集-{t}"
        job = db.query(CrawlJob).filter(CrawlJob.name == name).first()
        if job:
            job.target_codes = ",".join(codes)
            job.mode = mode
        else:
            job = CrawlJob(
                name=name, job_type=job_types[t], target_codes=",".join(codes),
                mode=mode, cron="", enabled=True,
            )
            db.add(job)
        db.commit()
        db.refresh(job)
        created_jobs.append(job.id)
        # 后台执行，避免阻塞请求导致前端超时
        background.add_task(task_service.execute_job_by_id, job.id, "manual")

    audit_service.log_action(
        db, username=current.username, role=current.role.name, action="crawl",
        target=f"crawl-all:{asset_type}", detail=f"已提交后台任务 {created_jobs}",
    )
    return {
        "message": "采集任务已提交后台执行，请在「运行记录」查看进度",
        "job_ids": created_jobs,
        "background": True,
    }



@router.get("/runs", response_model=Pagination[CrawlRunOut], summary="运行记录列表")
def list_runs(
    job_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Pagination[CrawlRunOut]:
    q = db.query(CrawlRun)
    if job_id:
        q = q.filter(CrawlRun.job_id == job_id)
    if status_filter:
        q = q.filter(CrawlRun.status == status_filter)
    total = q.count()
    items = (
        q.order_by(CrawlRun.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return Pagination(
        items=[CrawlRunOut.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=CrawlJobOut, summary="任务详情")
def get_job(
    job_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> CrawlJobOut:
    job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    return CrawlJobOut.model_validate(job)


@router.get(
    "/{job_id}/logs",
    response_model=List[CrawlRunOut],
    summary="任务运行日志",
)
def job_logs(
    job_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> List[CrawlRunOut]:
    runs = (
        db.query(CrawlRun)
        .filter(CrawlRun.job_id == job_id)
        .order_by(CrawlRun.started_at.desc())
        .limit(limit)
        .all()
    )
    return [CrawlRunOut.model_validate(r) for r in runs]
