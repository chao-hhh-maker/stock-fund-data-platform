"""审计日志服务。"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_action(
    db: Session,
    *,
    username: str = "",
    role: str = "",
    action: str,
    target: str = "",
    detail: str = "",
    ip: str = "",
) -> None:
    """写入一条审计日志（失败不影响主流程）。"""
    try:
        db.add(
            AuditLog(
                username=username,
                role=role,
                action=action,
                target=target,
                detail=detail,
                ip=ip,
            )
        )
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
