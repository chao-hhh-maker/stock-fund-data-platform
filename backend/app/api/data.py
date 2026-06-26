"""数据查询路由：标的、股票日线、基金净值（分页 + 筛选 + 数据权限）。

数据权限（模块6）：
- 行级权限：按角色 data_scope 限制可见资产类型（all/stock/fund）。
- 时间权限：按角色 max_history_days 钳制起始日期。
- 字段级权限：无敏感字段权限的用户，成交额 amount 脱敏为 0。
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import (
    allowed_asset_types,
    apply_instrument_visibility,
    can_view_sensitive,
    check_asset_access,
    clamp_start_date,
    ensure_instrument_visible,
    get_current_user,
    rate_limit,
)
from app.core.cache import cache
from app.core.config import settings
from app.core.database import get_db
from app.models import FundNav, Instrument, StockDaily, User
from app.services import cleaning
from app.schemas import (
    FundNavOut,
    InstrumentOut,
    Pagination,
    StockDailyOut,
)

router = APIRouter(tags=["数据查询"])


@router.get("/instruments", response_model=Pagination[InstrumentOut], summary="标的列表")
def list_instruments(
    asset_type: Optional[str] = Query(None, pattern="^(stock|fund)$"),
    keyword: Optional[str] = Query(None, description="按代码或名称模糊匹配"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> Pagination[InstrumentOut]:
    q = apply_instrument_visibility(db.query(Instrument), current)
    # 行级权限：限制到角色允许的资产类型
    allowed = allowed_asset_types(current)
    if allowed is not None:
        q = q.filter(Instrument.asset_type.in_(allowed))
    if asset_type:
        q = q.filter(Instrument.asset_type == asset_type)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter((Instrument.code.like(like)) | (Instrument.name.like(like)))
    total = q.count()
    items = (
        q.order_by(Instrument.code)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return Pagination(
        items=[InstrumentOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/stocks/{code}/daily",
    response_model=Pagination[StockDailyOut],
    summary="股票日线查询",
)
def stock_daily(
    code: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(60, ge=1, le=500),
    db: Session = Depends(get_db),
    current: User = Depends(rate_limit),
) -> Pagination[StockDailyOut]:
    code = cleaning.normalize_code(code, "stock")
    # 行级权限：无股票数据范围则拒绝
    check_asset_access(current, "stock")
    ensure_instrument_visible(db, current, code, "stock")
    # 时间权限：钳制起始日期
    start_date = clamp_start_date(current, start_date)
    show_sensitive = can_view_sensitive(current)

    cache_key = f"stock:{code}:{start_date}:{end_date}:{page}:{page_size}:{int(show_sensitive)}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    q = db.query(StockDaily).filter(StockDaily.code == code)
    if start_date:
        q = q.filter(StockDaily.trade_date >= start_date)
    if end_date:
        q = q.filter(StockDaily.trade_date <= end_date)
    total = q.count()
    rows = (
        q.order_by(StockDaily.trade_date)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = []
    for r in rows:
        out = StockDailyOut.model_validate(r)
        # 字段级权限：成交额 amount 对无权限用户脱敏（修复查询接口绕过导出脱敏的漏洞）
        if not show_sensitive:
            out.amount = 0.0
        items.append(out)
    result = Pagination(items=items, total=total, page=page, page_size=page_size)
    cache.set(cache_key, result, settings.CACHE_TTL_SECONDS)
    return result


@router.get(
    "/funds/{code}/nav",
    response_model=Pagination[FundNavOut],
    summary="基金净值查询",
)
def fund_nav(
    code: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(60, ge=1, le=500),
    db: Session = Depends(get_db),
    current: User = Depends(rate_limit),
) -> Pagination[FundNavOut]:
    code = cleaning.normalize_code(code, "fund")
    # 行级权限：无基金数据范围则拒绝
    check_asset_access(current, "fund")
    ensure_instrument_visible(db, current, code, "fund")
    # 时间权限：钳制起始日期
    start_date = clamp_start_date(current, start_date)

    cache_key = f"fund:{code}:{start_date}:{end_date}:{page}:{page_size}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    q = db.query(FundNav).filter(FundNav.code == code)
    if start_date:
        q = q.filter(FundNav.nav_date >= start_date)
    if end_date:
        q = q.filter(FundNav.nav_date <= end_date)
    total = q.count()
    items = (
        q.order_by(FundNav.nav_date)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    result = Pagination(
        items=[FundNavOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )
    cache.set(cache_key, result, settings.CACHE_TTL_SECONDS)
    return result



