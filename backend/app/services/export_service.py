"""
数据导出服务
"""
import pandas as pd
import os
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import logging
import json

from app.models.export import ExportRecord
from app.models.stock_daily import StockDaily
from app.models.fund_nav import FundNav
from app.models.instrument import Instrument

logger = logging.getLogger(__name__)


class ExportService:
    """数据导出服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.export_dir = "exports"
        
        # 创建导出目录
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
    
    def create_export_record(
        self,
        user_id: int,
        export_type: str,
        query_params: Dict[str, Any],
        file_format: str = 'csv'
    ) -> ExportRecord:
        """
        创建导出记录
        
        Args:
            user_id: 用户ID
            export_type: 导出类型
            query_params: 查询参数
            file_format: 文件格式
        
        Returns:
            创建的导出记录
        """
        export_record = ExportRecord(
            user_id=user_id,
            export_type=export_type,
            query_params=json.dumps(query_params),
            file_format=file_format,
            status='pending'
        )
        self.db.add(export_record)
        self.db.commit()
        self.db.refresh(export_record)
        
        logger.info(f"创建导出记录: export_id={export_record.id}, type={export_type}")
        return export_record
    
    def update_export_status(
        self,
        export_id: int,
        status: str,
        record_count: int = 0,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """
        更新导出状态
        
        Args:
            export_id: 导出记录ID
            status: 状态
            record_count: 记录数
            file_path: 文件路径
            file_size: 文件大小
            error_message: 错误信息
        """
        export_record = self.db.query(ExportRecord).filter(
            ExportRecord.id == export_id
        ).first()
        
        if export_record:
            export_record.status = status
            export_record.record_count = record_count
            
            if file_path:
                export_record.file_path = file_path
            
            if file_size:
                export_record.file_size = file_size
            
            if error_message:
                export_record.error_message = str(error_message)[:1000]
            
            if status in ['completed', 'failed']:
                export_record.completed_at = datetime.now()
            
            self.db.commit()
            logger.info(f"更新导出状态: export_id={export_id}, status={status}")
    
    def export_stock_daily(
        self,
        export_id: int,
        code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        file_format: str = 'csv'
    ) -> str:
        """
        导出股票日线数据
        
        Args:
            export_id: 导出记录ID
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            file_format: 文件格式
        
        Returns:
            文件路径
        """
        try:
            # 更新状态为处理中
            self.update_export_status(export_id, 'processing')
            
            # 构建查询
            query = self.db.query(StockDaily)
            
            if code:
                query = query.filter(StockDaily.code == code)
            
            if start_date:
                query = query.filter(StockDaily.trade_date >= start_date)
            
            if end_date:
                query = query.filter(StockDaily.trade_date <= end_date)
            
            # 执行查询
            items = query.all()
            
            if not items:
                self.update_export_status(export_id, 'completed', record_count=0)
                logger.warning(f"导出数据为空: export_id={export_id}")
                return ""
            
            # 转换为 DataFrame
            data = []
            for item in items:
                data.append({
                    'code': item.code,
                    'trade_date': item.trade_date.isoformat() if item.trade_date else '',
                    'open': float(item.open) if item.open else 0,
                    'high': float(item.high) if item.high else 0,
                    'low': float(item.low) if item.low else 0,
                    'close': float(item.close) if item.close else 0,
                    'volume': item.volume or 0,
                    'amount': float(item.amount) if item.amount else 0,
                    'change_pct': float(item.change_pct) if item.change_pct else 0,
                    'turnover_rate': float(item.turnover_rate) if item.turnover_rate else 0
                })
            
            df = pd.DataFrame(data)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stock_daily_{timestamp}.{file_format}"
            file_path = os.path.join(self.export_dir, filename)
            
            # 导出文件
            if file_format == 'csv':
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            elif file_format == 'excel':
                df.to_excel(file_path, index=False, engine='openpyxl')
            elif file_format == 'parquet':
                df.to_parquet(file_path, index=False)
            else:
                raise ValueError(f"不支持的文件格式: {file_format}")
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 更新状态为完成
            self.update_export_status(
                export_id,
                'completed',
                record_count=len(items),
                file_path=file_path,
                file_size=file_size
            )
            
            logger.info(f"股票数据导出成功: export_id={export_id}, records={len(items)}")
            return file_path
            
        except Exception as e:
            # 更新状态为失败
            self.update_export_status(export_id, 'failed', error_message=str(e))
            logger.error(f"股票数据导出失败: export_id={export_id}, error={e}")
            raise
    
    def export_fund_nav(
        self,
        export_id: int,
        code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        file_format: str = 'csv'
    ) -> str:
        """
        导出基金净值数据
        
        Args:
            export_id: 导出记录ID
            code: 基金代码
            start_date: 开始日期
            end_date: 结束日期
            file_format: 文件格式
        
        Returns:
            文件路径
        """
        try:
            # 更新状态为处理中
            self.update_export_status(export_id, 'processing')
            
            # 构建查询
            query = self.db.query(FundNav)
            
            if code:
                query = query.filter(FundNav.code == code)
            
            if start_date:
                query = query.filter(FundNav.nav_date >= start_date)
            
            if end_date:
                query = query.filter(FundNav.nav_date <= end_date)
            
            # 执行查询
            items = query.all()
            
            if not items:
                self.update_export_status(export_id, 'completed', record_count=0)
                logger.warning(f"导出数据为空: export_id={export_id}")
                return ""
            
            # 转换为 DataFrame
            data = []
            for item in items:
                data.append({
                    'code': item.code,
                    'nav_date': item.nav_date.isoformat() if item.nav_date else '',
                    'unit_nav': float(item.unit_nav) if item.unit_nav else 0,
                    'accumulated_nav': float(item.accumulated_nav) if item.accumulated_nav else 0,
                    'daily_growth': float(item.daily_growth) if item.daily_growth else 0
                })
            
            df = pd.DataFrame(data)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fund_nav_{timestamp}.{file_format}"
            file_path = os.path.join(self.export_dir, filename)
            
            # 导出文件
            if file_format == 'csv':
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            elif file_format == 'excel':
                df.to_excel(file_path, index=False, engine='openpyxl')
            elif file_format == 'parquet':
                df.to_parquet(file_path, index=False)
            else:
                raise ValueError(f"不支持的文件格式: {file_format}")
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 更新状态为完成
            self.update_export_status(
                export_id,
                'completed',
                record_count=len(items),
                file_path=file_path,
                file_size=file_size
            )
            
            logger.info(f"基金数据导出成功: export_id={export_id}, records={len(items)}")
            return file_path
            
        except Exception as e:
            # 更新状态为失败
            self.update_export_status(export_id, 'failed', error_message=str(e))
            logger.error(f"基金数据导出失败: export_id={export_id}, error={e}")
            raise
