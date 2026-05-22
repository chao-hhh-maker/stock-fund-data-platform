"""
采集任务相关API接口
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import Response, ErrorCode
from app.services.crawl_service import CrawlService
from app.models.crawl import CrawlJob, CrawlRun

router = APIRouter(prefix="/api/tasks", tags=["采集任务"])


@router.post("/crawl/stock", response_model=Response, summary="执行股票日线采集")
def crawl_stock_daily(
    stock_codes: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    手动触发股票日线数据采集
    
    - **stock_codes**: 股票代码列表，不传则采集所有
    - **start_date**: 开始日期 (YYYYMMDD)
    - **end_date**: 结束日期 (YYYYMMDD)
    """
    try:
        # 创建一个默认任务记录
        job = CrawlJob(
            job_name="手动股票采集",
            job_type="stock_daily",
            is_enabled=1
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # 执行采集
        service = CrawlService(db)
        records_count = service.crawl_stock_daily(
            job_id=job.id,
            stock_codes=stock_codes,
            start_date=start_date,
            end_date=end_date
        )
        
        return Response(
            code=ErrorCode.SUCCESS,
            message=f"股票采集完成，共 {records_count} 条记录",
            data={"job_id": job.id, "records_count": records_count}
        )
        
    except Exception as e:
        return Response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"股票采集失败: {str(e)}",
            data=None
        )


@router.post("/crawl/fund", response_model=Response, summary="执行基金净值采集")
def crawl_fund_nav(
    fund_codes: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    手动触发基金净值数据采集
    
    - **fund_codes**: 基金代码列表，不传则采集所有
    - **start_date**: 开始日期 (YYYY-MM-DD)
    - **end_date**: 结束日期 (YYYY-MM-DD)
    """
    try:
        # 创建一个默认任务记录
        job = CrawlJob(
            job_name="手动基金采集",
            job_type="fund_nav",
            is_enabled=1
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # 执行采集
        service = CrawlService(db)
        records_count = service.crawl_fund_nav(
            job_id=job.id,
            fund_codes=fund_codes,
            start_date=start_date,
            end_date=end_date
        )
        
        return Response(
            code=ErrorCode.SUCCESS,
            message=f"基金采集完成，共 {records_count} 条记录",
            data={"job_id": job.id, "records_count": records_count}
        )
        
    except Exception as e:
        return Response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"基金采集失败: {str(e)}",
            data=None
        )


@router.get("/", response_model=Response, summary="获取任务列表")
def get_tasks(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取采集任务列表
    
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        # 查询任务总数
        total = db.query(CrawlJob).count()
        
        # 分页查询
        offset = (page - 1) * page_size
        jobs = db.query(CrawlJob).offset(offset).limit(page_size).all()
        
        tasks_list = []
        for job in jobs:
            tasks_list.append({
                "id": job.id,
                "job_name": job.job_name,
                "job_type": job.job_type,
                "is_enabled": bool(job.is_enabled),
                "created_at": job.created_at
            })
        
        return Response(
            code=ErrorCode.SUCCESS,
            message="获取任务列表成功",
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": tasks_list
            }
        )
        
    except Exception as e:
        return Response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取任务列表失败: {str(e)}",
            data=None
        )


@router.get("/{task_id}", response_model=Response, summary="获取任务详情")
def get_task_detail(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个任务的详细信息
    
    - **task_id**: 任务ID
    """
    try:
        job = db.query(CrawlJob).filter(CrawlJob.id == task_id).first()
        
        if not job:
            return Response(
                code=ErrorCode.NOT_FOUND,
                message="任务不存在",
                data=None
            )
        
        # 获取最近的执行记录
        runs = db.query(CrawlRun).filter(
            CrawlRun.job_id == task_id
        ).order_by(CrawlRun.start_time.desc()).limit(10).all()
        
        runs_list = []
        for run in runs:
            runs_list.append({
                "id": run.id,
                "start_time": run.start_time,
                "end_time": run.end_time,
                "status": run.status,
                "records_count": run.records_count,
                "error_message": run.error_message
            })
        
        return Response(
            code=ErrorCode.SUCCESS,
            message="获取任务详情成功",
            data={
                "job": {
                    "id": job.id,
                    "job_name": job.job_name,
                    "job_type": job.job_type,
                    "is_enabled": bool(job.is_enabled),
                    "created_at": job.created_at
                },
                "recent_runs": runs_list
            }
        )
        
    except Exception as e:
        return Response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取任务详情失败: {str(e)}",
            data=None
        )


@router.get("/{task_id}/logs", response_model=Response, summary="获取任务执行日志")
def get_task_logs(
    task_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取任务的执行历史记录
    
    - **task_id**: 任务ID
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        # 检查任务是否存在
        job = db.query(CrawlJob).filter(CrawlJob.id == task_id).first()
        if not job:
            return Response(
                code=ErrorCode.NOT_FOUND,
                message="任务不存在",
                data=None
            )
        
        # 查询执行记录总数
        total = db.query(CrawlRun).filter(CrawlRun.job_id == task_id).count()
        
        # 分页查询
        offset = (page - 1) * page_size
        runs = db.query(CrawlRun).filter(
            CrawlRun.job_id == task_id
        ).order_by(CrawlRun.start_time.desc()).offset(offset).limit(page_size).all()
        
        runs_list = []
        for run in runs:
            runs_list.append({
                "id": run.id,
                "start_time": run.start_time,
                "end_time": run.end_time,
                "status": run.status,
                "records_count": run.records_count,
                "error_message": run.error_message
            })
        
        return Response(
            code=ErrorCode.SUCCESS,
            message="获取执行日志成功",
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": runs_list
            }
        )
        
    except Exception as e:
        return Response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取执行日志失败: {str(e)}",
            data=None
        )
