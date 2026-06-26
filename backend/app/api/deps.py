"""FastAPI 依赖：数据库会话、当前用户、RBAC 权限校验、数据权限。"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import RateLimiter
from app.core.security import decode_access_token
from app.models import Instrument, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/token")

# 全局限流器单例
rate_limiter = RateLimiter(settings.RATE_LIMIT_PER_MINUTE)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """解析 JWT 并返回当前用户。"""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的登录凭证或登录已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exc
    username = payload.get("sub")
    if not username:
        raise credentials_exc
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise credentials_exc
    return user


def require_admin(current: User = Depends(get_current_user)) -> User:
    """要求管理员角色，用于采集触发、导出、任务管理等敏感操作。"""
    if current.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限才能执行该操作",
        )
    return current


def rate_limit(current: User = Depends(get_current_user)) -> User:
    """查询限流依赖：按用户名令牌桶限流，超限返回 429。"""
    if settings.RATE_LIMIT_ENABLED and not rate_limiter.allow(current.username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"请求过于频繁，每分钟最多 {settings.RATE_LIMIT_PER_MINUTE} 次，请稍后再试",
        )
    return current


# ---------- 数据权限（模块6：行级 / 时间 / 字段级）----------
def allowed_asset_types(user: User) -> Optional[list[str]]:
    """根据角色 data_scope 返回可访问的资产类型；None 表示全部（行级权限）。"""
    scope = (user.role.data_scope or "all").lower()
    if scope in ("stock", "fund"):
        return [scope]
    return None


def check_asset_access(user: User, asset_type: str) -> None:
    """校验用户是否有权访问该资产类型，无权抛 403。"""
    allowed = allowed_asset_types(user)
    if allowed is not None and asset_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"当前角色的数据范围（{user.role.data_scope}）不包含 {asset_type} 数据",
        )


def clamp_start_date(user: User, start_date: Optional[date]) -> Optional[date]:
    """按角色 max_history_days 钳制查询起始日期（时间权限）。

    max_history_days>0 时，用户最多只能查到 today - max_history_days，
    若请求的 start_date 更早或未指定，则收紧到该下界。
    """
    limit_days = user.role.max_history_days or 0
    if limit_days <= 0:
        return start_date
    earliest = date.today() - timedelta(days=limit_days)
    if start_date is None or start_date < earliest:
        return earliest
    return start_date


def can_view_sensitive(user: User) -> bool:
    """是否可见敏感字段（如成交额 amount）。"""
    return bool(user.role.can_view_sensitive)

# ---------- 租户 / 部门数据隔离 ----------
def apply_instrument_visibility(query, user: User):
    """给 Instrument 查询追加租户/部门可见性过滤。

    规则：管理员可见全部；普通用户可见公共标的（tenant_id 为空）和同租户标的；
    若标的设置了 department，则还要求与用户 department 一致。
    """
    if user.role.name == "admin":
        return query
    tenant_conditions = [Instrument.tenant_id.is_(None)]
    if user.tenant_id is not None:
        tenant_conditions.append(Instrument.tenant_id == user.tenant_id)
    query = query.filter(or_(*tenant_conditions))
    query = query.filter(
        or_(Instrument.department.is_(None), Instrument.department == "", Instrument.department == user.department)
    )
    return query


def ensure_instrument_visible(db: Session, user: User, code: str, asset_type: str) -> None:
    """校验指定标的是否在当前用户租户/部门范围内。"""
    base = db.query(Instrument).filter(Instrument.code == code, Instrument.asset_type == asset_type)
    if not base.first():
        return
    visible = apply_instrument_visibility(base, user).first()
    if not visible:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前用户无权访问该机构或部门范围内的数据",
        )
