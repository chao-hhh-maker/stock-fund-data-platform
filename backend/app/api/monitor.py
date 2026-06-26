"""监控与仪表盘路由：健康检查、统计概览。"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.config import settings
from app.core.database import get_db
from app.core.metrics_middleware import get_api_stats
from app.models import (
    AlertRecord,
    Announcement,
    AuditLog,
    CrawlJob,
    CrawlRun,
    DataQualityIssue,
    ExportRecord,
    FundNav,
    Instrument,
    StockDaily,
    User,
)
from app.schemas import (
    AlertRecordOut,
    AnnouncementOut,
    AuditLogOut,
    CrawlRunOut,
    DashboardStats,
    DataQualityIssueOut,
    DataSourceOut,
    ExportRecordOut,
    HealthOut,
    Pagination,
    ResolveAlertRequest,
    ResolveIssueRequest,
)
from app.services import (
    data_quality_service,
    datasource_registry,
    metadata_service,
    monitor_service,
    realtime_service,
)
from app.tasks import scheduler

router = APIRouter(tags=["监控"])


@router.get("/health", response_model=HealthOut, summary="健康检查（公开）")
def health(db: Session = Depends(get_db)) -> HealthOut:
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:  # noqa: BLE001
        db_status = "error"
    return HealthOut(
        status="ok",
        app=settings.APP_NAME,
        env=settings.APP_ENV,
        database=db_status,
        scheduler="running" if scheduler.scheduler.running else "stopped",
        time=datetime.now(),
    )


@router.get("/dashboard", response_model=DashboardStats, summary="仪表盘统计")
def dashboard(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> DashboardStats:
    stock_count = db.query(Instrument).filter(Instrument.asset_type == "stock").count()
    fund_count = db.query(Instrument).filter(Instrument.asset_type == "fund").count()
    recent_runs = (
        db.query(CrawlRun).order_by(CrawlRun.started_at.desc()).limit(6).all()
    )
    recent_exports = (
        db.query(ExportRecord).order_by(ExportRecord.id.desc()).limit(5).all()
    )
    # 行业分布
    industry_rows = (
        db.query(Instrument.category, func.count(Instrument.id))
        .group_by(Instrument.category)
        .all()
    )
    industry_dist = [
        {"name": cat or "未分类", "value": cnt} for cat, cnt in industry_rows
    ]
    # 采集成功率
    total_runs = db.query(func.count(CrawlRun.id)).scalar() or 0
    success_runs = (
        db.query(func.count(CrawlRun.id)).filter(CrawlRun.status == "success").scalar()
    ) or 0
    success_rate = round(success_runs / total_runs * 100, 1) if total_runs else 100.0

    return DashboardStats(
        instrument_count=stock_count + fund_count,
        stock_count=stock_count,
        fund_count=fund_count,
        stock_daily_rows=db.query(StockDaily).count(),
        fund_nav_rows=db.query(FundNav).count(),
        job_count=db.query(CrawlJob).count(),
        crawl_success_rate=success_rate,
        industry_distribution=industry_dist,
        recent_runs=[CrawlRunOut.model_validate(r) for r in recent_runs],
        recent_exports=[ExportRecordOut.model_validate(r) for r in recent_exports],
    )


@router.get("/monitor/metrics", summary="系统运行指标")
def metrics(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    return monitor_service.system_metrics(db)


@router.get("/monitor/integrity", summary="数据完整性检查")
def integrity(
    lookback_days: int = 30,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list:
    return monitor_service.check_integrity(db, lookback_days)


@router.get("/monitor/alerts", summary="告警中心")
def alerts(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list:
    integrity_report = monitor_service.check_integrity(db)
    base = monitor_service.build_alerts(db, integrity_report)
    anomalies = monitor_service.detect_anomalies(db)
    all_alerts = base + anomalies
    # 落库 + 分发（best-effort，不阻塞响应主路径）
    monitor_service.dispatch_alerts(db, all_alerts)
    return all_alerts


@router.get("/monitor/api-stats", summary="API 性能指标")
def api_stats(_: User = Depends(get_current_user)) -> list:
    """各接口请求数 / 平均耗时 / 错误率（模块5 API 性能监控）。"""
    return get_api_stats()


@router.get(
    "/monitor/alert-records",
    response_model=Pagination[AlertRecordOut],
    summary="历史告警记录",
)
def alert_records(
    status_filter: str | None = Query(None, alias="status"),
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Pagination[AlertRecordOut]:
    items, total = monitor_service.list_alert_records(db, page, page_size, status_filter)
    return Pagination(
        items=[AlertRecordOut.model_validate(a) for a in items],
        total=total, page=page, page_size=page_size,
    )


@router.post(
    "/monitor/alert-records/{alert_id}/resolve",
    response_model=AlertRecordOut,
    summary="处理历史告警（管理员）",
)
def resolve_alert_record(
    alert_id: int,
    payload: ResolveAlertRequest = Body(...),
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
) -> AlertRecordOut:
    alert = monitor_service.resolve_alert(db, alert_id, payload.status, payload.note, current.username)
    if not alert:
        raise HTTPException(status_code=404, detail="告警记录不存在")
    return AlertRecordOut.model_validate(alert)


# ---------- 数据源注册表（模块1）----------
@router.get("/datasources", response_model=list[DataSourceOut], summary="数据源注册表")
def datasources(_: User = Depends(get_current_user)) -> list:
    return datasource_registry.list_sources()


# ---------- 实时行情快照（模块1/4）----------
@router.get("/realtime/quotes", summary="实时行情快照")
def realtime_quotes(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    """交易时段返回新浪秒级实时价，休市返回库中最新收盘（供前端轮询兜底 WebSocket）。"""
    return realtime_service.snapshot(db)


# ---------- 公告 / 新闻 / 舆情（模块1）----------
@router.get("/announcements", response_model=Pagination[AnnouncementOut], summary="公告/新闻/舆情")
def announcements(
    code: str | None = None,
    category: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Pagination[AnnouncementOut]:
    q = db.query(Announcement)
    if code:
        q = q.filter(Announcement.code == code)
    if category:
        q = q.filter(Announcement.category == category)
    total = q.count()
    items = (
        q.order_by(Announcement.publish_date.desc(), Announcement.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return Pagination(
        items=[AnnouncementOut.model_validate(a) for a in items],
        total=total, page=page, page_size=page_size,
    )


# ---------- 数据质量（模块2/5）----------
@router.get(
    "/data-quality", response_model=Pagination[DataQualityIssueOut], summary="数据质量问题列表"
)
def data_quality(
    status_filter: str | None = Query(None, alias="status"),
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Pagination[DataQualityIssueOut]:
    items, total = data_quality_service.list_issues(db, status_filter, page, page_size)
    return Pagination(
        items=[DataQualityIssueOut.model_validate(i) for i in items],
        total=total, page=page, page_size=page_size,
    )


@router.post(
    "/data-quality/{issue_id}/resolve",
    response_model=DataQualityIssueOut,
    summary="人工校对数据质量问题（管理员）",
)
def resolve_data_quality(
    issue_id: int,
    payload: ResolveIssueRequest,
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
) -> DataQualityIssueOut:
    issue = data_quality_service.resolve_issue(
        db, issue_id, payload.status, payload.note, current.username
    )
    if not issue:
        raise HTTPException(status_code=404, detail="问题记录不存在")
    return DataQualityIssueOut.model_validate(issue)


@router.get("/metadata/dictionary", summary="数据字典")
def data_dictionary(_: User = Depends(get_current_user)) -> list:
    return metadata_service.get_data_dictionary()


@router.get("/metadata/lineage", summary="数据血缘")
def lineage(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list:
    return metadata_service.get_lineage(db)


@router.get(
    "/audit/logs",
    response_model=Pagination[AuditLogOut],
    summary="审计日志（管理员）",
)
def audit_logs(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Pagination[AuditLogOut]:
    q = db.query(AuditLog).order_by(AuditLog.id.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return Pagination(
        items=[AuditLogOut.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )






