"""数据导出路由：触发导出、下载文件、导出记录。"""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import check_asset_access, clamp_start_date, ensure_instrument_visible, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models import ExportRecord, User
from app.schemas import ExportRecordOut, ExportRequest, Pagination
from app.services import audit_service, cleaning, export_service

router = APIRouter(prefix="/exports", tags=["数据导出"])


def _check_quota(db: Session, user: User) -> None:
    """导出权限与每日配额检查。"""
    # 功能权限：角色是否允许导出
    if not user.role.can_export:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前角色无导出权限",
        )
    if user.role.name == "admin":
        return
    today_start = datetime.combine(date.today(), datetime.min.time())
    used = (
        db.query(func.count(ExportRecord.id))
        .filter(ExportRecord.user_id == user.id, ExportRecord.created_at >= today_start)
        .scalar()
    ) or 0
    if used >= settings.VIEWER_EXPORT_DAILY_QUOTA:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"已达今日导出配额（{settings.VIEWER_EXPORT_DAILY_QUOTA} 次），请明日再试或联系管理员",
        )


@router.post("", response_model=ExportRecordOut, summary="导出数据集")
def create_export(
    payload: ExportRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ExportRecordOut:
    # 普通用户受每日配额限制；导出必须复用查询侧的数据权限。
    _check_quota(db, current)
    export_code = payload.code
    start_date = payload.start_date
    if payload.dataset == "stock_daily":
        check_asset_access(current, "stock")
        export_code = cleaning.normalize_code(payload.code, "stock") if payload.code else None
        if export_code:
            ensure_instrument_visible(db, current, export_code, "stock")
        start_date = clamp_start_date(current, payload.start_date)
    elif payload.dataset == "fund_nav":
        check_asset_access(current, "fund")
        export_code = cleaning.normalize_code(payload.code, "fund") if payload.code else None
        if export_code:
            ensure_instrument_visible(db, current, export_code, "fund")
        start_date = clamp_start_date(current, payload.start_date)

    _, file_name, row_count = export_service.export_dataset(
        db,
        current,
        dataset=payload.dataset,
        file_format=payload.file_format,
        code=export_code,
        start_date=start_date,
        end_date=payload.end_date,
        role=current.role.name,
        can_view_sensitive=current.role.can_view_sensitive,
        compress=payload.compress,
        encrypt=payload.encrypt,
    )
    audit_service.log_action(
        db, username=current.username, role=current.role.name, action="export",
        target=payload.dataset,
        detail=(
            f"format={payload.file_format};code={payload.code};rows={row_count};"
            f"compress={payload.compress};encrypt={payload.encrypt}"
        ),
    )
    record = (
        db.query(ExportRecord)
        .filter(ExportRecord.file_name == file_name)
        .order_by(ExportRecord.id.desc())
        .first()
    )
    return ExportRecordOut.model_validate(record)


@router.get("", response_model=Pagination[ExportRecordOut], summary="导出记录列表")
def list_exports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Pagination[ExportRecordOut]:
    q = db.query(ExportRecord)
    if _.role.name != "admin":
        q = q.filter(ExportRecord.user_id == _.id)
    q = q.order_by(ExportRecord.id.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return Pagination(
        items=[ExportRecordOut.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{record_id}/download", summary="下载导出文件")
def download_export(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FileResponse:
    record = db.query(ExportRecord).filter(ExportRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="导出记录不存在")
    if _.role.name != "admin" and record.user_id != _.id:
        raise HTTPException(status_code=403, detail="无权下载其他用户的导出文件")
    abs_path = os.path.abspath(os.path.join(settings.EXPORT_DIR, record.file_name))
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="导出文件已不存在，请重新导出")
    return FileResponse(
        abs_path, filename=record.file_name, media_type="application/octet-stream"
    )

