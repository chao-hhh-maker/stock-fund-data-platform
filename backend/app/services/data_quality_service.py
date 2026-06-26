"""数据质量服务（模块2 人工校对 + 模块5 异常监测）。

负责把跨源偏差、关键字段异常、缺失等问题落库为 DataQualityIssue，
支持管理员人工校对（标记已修正/已忽略）。
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import DataQualityIssue


def record_issue(
    db: Session,
    issue_type: str,
    message: str,
    code: str = "",
    dataset: str = "",
    severity: str = "warning",
    *,
    commit: bool = True,
    dedup: bool = True,
) -> Optional[DataQualityIssue]:
    """登记一条数据质量问题。dedup=True 时同 code+type 的未处理问题不重复插入。"""
    if dedup:
        existing = (
            db.query(DataQualityIssue)
            .filter(
                DataQualityIssue.issue_type == issue_type,
                DataQualityIssue.code == code,
                DataQualityIssue.dataset == dataset,
                DataQualityIssue.status == "open",
            )
            .first()
        )
        if existing:
            existing.message = message
            existing.severity = severity
            if commit:
                db.commit()
            return existing
    issue = DataQualityIssue(
        issue_type=issue_type,
        code=code,
        dataset=dataset,
        severity=severity,
        message=message,
    )
    db.add(issue)
    if commit:
        db.commit()
        db.refresh(issue)
    return issue


def list_issues(
    db: Session, status: Optional[str] = None, page: int = 1, page_size: int = 20
) -> tuple[List[DataQualityIssue], int]:
    q = db.query(DataQualityIssue)
    if status:
        q = q.filter(DataQualityIssue.status == status)
    total = q.count()
    items = (
        q.order_by(DataQualityIssue.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def resolve_issue(
    db: Session, issue_id: int, status: str, note: str, resolved_by: str
) -> Optional[DataQualityIssue]:
    issue = db.query(DataQualityIssue).filter(DataQualityIssue.id == issue_id).first()
    if not issue:
        return None
    issue.status = status
    issue.resolved_note = note
    issue.resolved_by = resolved_by
    issue.resolved_at = datetime.now()
    db.commit()
    db.refresh(issue)
    return issue
