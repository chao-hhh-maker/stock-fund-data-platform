"""
数据导出相关API接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.core.database import get_db
from app.core.response import Response, ErrorCode
from app.services.export_service import ExportService
from app.models.export import ExportRecord

router = APIRouter(prefix="/api/exports", tags=["数据导出"])


@router.post("/", response_model=Response, summary="创建导出任务")
def create_export(
    export_type: str = Query(..., description="导出类型: stock_daily, fund_nav, instrument"),
    code: Optional[str] = Query(None, description="代码筛选"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    file_format: str = Query("csv", description="文件格式: csv, excel, parquet"),
    user_id: int = Query(1, description="用户ID（临时固定为1）"),
    db: Session = Depends(get_db)
):
    """
    创建数据导出任务
    
    - **export_type**: 导出类型（stock_daily/fund_nav/instrument）
    - **code**: 代码筛选（可选）
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    - **file_format**: 文件格式（csv/excel/parquet）
    - **user_id**: 用户ID
    """
    try:
        # 验证导出类型
        if export_type not in ['stock_daily', 'fund_nav', 'instrument']:
            return Response(
                code=ErrorCode.BAD_REQUEST,
                message="无效的导出类型",
                data=None
            )
        
        # 验证文件格式
        if file_format not in ['csv', 'excel', 'parquet']:
            return Response(
                code=ErrorCode.BAD_REQUEST,
                message="无效的文件格式",
                data=None
            )
        
        # 创建导出服务
        service = ExportService(db)
        
        # 准备查询参数
        query_params = {
            "export_type": export_type,
            "code": code,
            "start_date": start_date,
            "end_date": end_date,
            "file_format": file_format
        }
        
        # 创建导出记录
        export_record = service.create_export_record(
            user_id=user_id,
            export_type=export_type,
            query_params=query_params,
            file_format=file_format
        )
        
        # 执行导出
        if export_type == 'stock_daily':
            file_path = service.export_stock_daily(
                export_id=export_record.id,
                code=code,
                start_date=start_date,
                end_date=end_date,
                file_format=file_format
            )
        elif export_type == 'fund_nav':
            file_path = service.export_fund_nav(
                export_id=export_record.id,
                code=code,
                start_date=start_date,
                end_date=end_date,
                file_format=file_format
            )
        else:
            # 暂时不支持 instrument 导出
            service.update_export_status(export_record.id, 'failed', error_message="暂不支持该类型导出")
            return Response(
                code=ErrorCode.BAD_REQUEST,
                message="暂不支持该类型导出",
                data=None
            )
        
        return Response(
            code=ErrorCode.SUCCESS,
            message="导出成功",
            data={
                "export_id": export_record.id,
                "file_path": file_path,
                "record_count": export_record.record_count,
                "file_format": file_format
            }
        )
        
    except Exception as e:
        return Response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"导出失败: {str(e)}",
            data=None
        )


@router.get("/", response_model=Response, summary="获取导出记录列表")
def get_export_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: Session = Depends(get_db)
):
    """
    获取导出记录列表
    
    - **page**: 页码
    - **page_size**: 每页数量
    - **user_id**: 用户ID筛选（可选）
    - **status**: 状态筛选（pending/processing/completed/failed）
    """
    try:
        # 构建查询
        query = db.query(ExportRecord)
        
        # 用户ID筛选
        if user_id:
            query = query.filter(ExportRecord.user_id == user_id)
        
        # 状态筛选
        if status:
            query = query.filter(ExportRecord.status == status)
        
        # 按创建时间降序排列
        query = query.order_by(ExportRecord.created_at.desc())
        
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
                "user_id": item.user_id,
                "export_type": item.export_type,
                "file_format": item.file_format,
                "record_count": item.record_count,
                "file_size": item.file_size,
                "status": item.status,
                "file_path": item.file_path,
                "error_message": item.error_message,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "completed_at": item.completed_at.isoformat() if item.completed_at else None
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


@router.get("/{export_id}/download", summary="下载导出文件")
def download_export_file(
    export_id: int,
    db: Session = Depends(get_db)
):
    """
    下载导出文件
    
    - **export_id**: 导出记录ID
    """
    try:
        # 查询导出记录
        export_record = db.query(ExportRecord).filter(
            ExportRecord.id == export_id
        ).first()
        
        if not export_record:
            raise HTTPException(status_code=404, detail="导出记录不存在")
        
        if export_record.status != 'completed':
            raise HTTPException(status_code=400, detail="文件尚未生成或导出失败")
        
        if not export_record.file_path or not os.path.exists(export_record.file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 返回文件
        filename = os.path.basename(export_record.file_path)
        media_type = 'text/csv'
        
        if export_record.file_format == 'excel':
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif export_record.file_format == 'parquet':
            media_type = 'application/octet-stream'
        
        return FileResponse(
            path=export_record.file_path,
            filename=filename,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")
