"""
数据查询相关API接口
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date

from app.core.database import get_db
from app.core.response import Response, ErrorCode
from app.models.stock_daily import StockDaily
from app.models.fund_nav import FundNav
from app.models.instrument import Instrument

router = APIRouter(prefix="/api", tags=["数据查询"])


@router.get("/stocks/{code}/daily", response_model=Response, summary="查询股票日线数据")
def get_stock_daily(
    code: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """
    查询指定股票的日线数据
    
    - **code**: 股票代码（6位）
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，最大1000
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    """
    try:
        # 构建查询
        query = db.query(StockDaily).filter(StockDaily.code == code)
        
        # 日期筛选
        if start_date:
            query = query.filter(StockDaily.trade_date >= start_date)
        if end_date:
            query = query.filter(StockDaily.trade_date <= end_date)
        
        # 按日期降序排列
        query = query.order_by(StockDaily.trade_date.desc())
        
        # 查询总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        # 转换为字典列表
        data_list = []
        for item in items:
            data_list.append({
                "id": item.id,
                "code": item.code,
                "trade_date": item.trade_date.isoformat() if item.trade_date else None,
                "open": float(item.open) if item.open else None,
                "high": float(item.high) if item.high else None,
                "low": float(item.low) if item.low else None,
                "close": float(item.close) if item.close else None,
                "volume": item.volume,
                "amount": float(item.amount) if item.amount else None,
                "change_pct": float(item.change_pct) if item.change_pct else None,
                "turnover_rate": float(item.turnover_rate) if item.turnover_rate else None,
                "data_source": item.data_source
            })
        
        return Response(
            code=ErrorCode.SUCCESS,
            message="查询成功",
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": data_list
            }
        )
        
    except Exception as e:
        return Response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"查询失败: {str(e)}",
            data=None
        )


@router.get("/funds/{code}/nav", response_model=Response, summary="查询基金净值数据")
def get_fund_nav(
    code: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """
    查询指定基金的净值数据
    
    - **code**: 基金代码（6位）
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，最大1000
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    """
    try:
        # 构建查询
        query = db.query(FundNav).filter(FundNav.code == code)
        
        # 日期筛选
        if start_date:
            query = query.filter(FundNav.nav_date >= start_date)
        if end_date:
            query = query.filter(FundNav.nav_date <= end_date)
        
        # 按日期降序排列
        query = query.order_by(FundNav.nav_date.desc())
        
        # 查询总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        # 转换为字典列表
        data_list = []
        for item in items:
            data_list.append({
                "id": item.id,
                "code": item.code,
                "nav_date": item.nav_date.isoformat() if item.nav_date else None,
                "unit_nav": float(item.unit_nav) if item.unit_nav else None,
                "accumulated_nav": float(item.accumulated_nav) if item.accumulated_nav else None,
                "daily_growth": float(item.daily_growth) if item.daily_growth else None,
                "data_source": item.data_source
            })
        
        return Response(
            code=ErrorCode.SUCCESS,
            message="查询成功",
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": data_list
            }
        )
        
    except Exception as e:
        return Response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"查询失败: {str(e)}",
            data=None
        )


@router.get("/instruments", response_model=Response, summary="查询金融工具列表")
def get_instruments(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    type: Optional[str] = Query(None, description="类型: stock 或 fund"),
    market: Optional[str] = Query(None, description="市场: SH, SZ, BJ"),
    status: Optional[str] = Query("active", description="状态: active 或 delisted"),
    db: Session = Depends(get_db)
):
    """
    查询金融工具（股票/基金）列表
    
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，最大1000
    - **type**: 类型筛选（stock/fund）
    - **market**: 市场筛选（SH/SZ/BJ）
    - **status**: 状态筛选（active/delisted）
    """
    try:
        # 构建查询
        query = db.query(Instrument)
        
        # 类型筛选
        if type:
            query = query.filter(Instrument.type == type)
        
        # 市场筛选
        if market:
            query = query.filter(Instrument.market == market)
        
        # 状态筛选
        if status:
            query = query.filter(Instrument.status == status)
        
        # 按ID降序排列
        query = query.order_by(Instrument.id.desc())
        
        # 查询总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        # 转换为字典列表
        data_list = []
        for item in items:
            data_list.append({
                "id": item.id,
                "code": item.code,
                "name": item.name,
                "type": item.type,
                "market": item.market,
                "industry": item.industry,
                "list_date": item.list_date.isoformat() if item.list_date else None,
                "status": item.status
            })
        
        return Response(
            code=ErrorCode.SUCCESS,
            message="查询成功",
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": data_list
            }
        )
        
    except Exception as e:
        return Response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"查询失败: {str(e)}",
            data=None
        )
