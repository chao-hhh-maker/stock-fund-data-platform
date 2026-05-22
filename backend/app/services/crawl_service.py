"""
数据采集服务
负责协调采集器、数据清洗和数据库写入
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
import logging

from app.models.crawl import CrawlJob, CrawlRun
from app.models.stock_daily import StockDaily
from app.models.fund_nav import FundNav
from app.tasks.crawlers.stock_crawler import StockDailyCrawler
from app.tasks.crawlers.fund_crawler import FundNavCrawler

logger = logging.getLogger(__name__)


class CrawlService:
    """数据采集服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.stock_crawler = StockDailyCrawler()
        self.fund_crawler = FundNavCrawler()
    
    def create_crawl_run(self, job_id: int) -> CrawlRun:
        """
        创建采集任务执行记录
        
        Args:
            job_id: 任务ID
        
        Returns:
            创建的 CrawlRun 对象
        """
        crawl_run = CrawlRun(
            job_id=job_id,
            start_time=datetime.now(),
            status='running',
            records_count=0
        )
        self.db.add(crawl_run)
        self.db.commit()
        self.db.refresh(crawl_run)
        
        logger.info(f"创建采集任务执行记录: run_id={crawl_run.id}, job_id={job_id}")
        return crawl_run
    
    def update_crawl_run_success(self, run_id: int, records_count: int):
        """
        更新采集任务执行记录为成功
        
        Args:
            run_id: 执行记录ID
            records_count: 采集记录数
        """
        crawl_run = self.db.query(CrawlRun).filter(CrawlRun.id == run_id).first()
        if crawl_run:
            crawl_run.end_time = datetime.now()
            crawl_run.status = 'success'
            crawl_run.records_count = records_count
            self.db.commit()
            logger.info(f"采集任务执行成功: run_id={run_id}, records={records_count}")
    
    def update_crawl_run_failed(self, run_id: int, error_message: str):
        """
        更新采集任务执行记录为失败
        
        Args:
            run_id: 执行记录ID
            error_message: 错误信息
        """
        crawl_run = self.db.query(CrawlRun).filter(CrawlRun.id == run_id).first()
        if crawl_run:
            crawl_run.end_time = datetime.now()
            crawl_run.status = 'failed'
            crawl_run.error_message = str(error_message)[:1000]  # 限制长度
            self.db.commit()
            logger.error(f"采集任务执行失败: run_id={run_id}, error={error_message}")
    
    def crawl_stock_daily(
        self, 
        job_id: int,
        stock_codes: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> int:
        """
        执行股票日线数据采集
        
        Args:
            job_id: 任务ID
            stock_codes: 股票代码列表，None表示采集所有
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            采集的记录数
        """
        # 创建执行记录
        crawl_run = self.create_crawl_run(job_id)
        
        try:
            # 如果没有指定股票代码，从数据库获取所有活跃股票
            if not stock_codes:
                from app.models.instrument import Instrument
                instruments = self.db.query(Instrument).filter(
                    Instrument.type == 'stock',
                    Instrument.status == 'active'
                ).all()
                stock_codes = [inst.code for inst in instruments]
                
                if not stock_codes:
                    # 如果数据库没有股票，使用测试代码
                    stock_codes = ['000001', '600000', '000002']
                    logger.info("数据库中没有股票，使用测试代码")
            
            total_records = 0
            
            # 逐个采集股票
            for stock_code in stock_codes:
                try:
                    # 获取原始数据
                    df = self.stock_crawler.fetch_stock_daily(stock_code, start_date, end_date)
                    
                    if df.empty:
                        continue
                    
                    # 清洗和标准化
                    df_cleaned = self.stock_crawler.clean_and_standardize(df)
                    
                    if df_cleaned.empty:
                        continue
                    
                    # 准备数据库记录
                    records = self.stock_crawler.prepare_for_database(df_cleaned, stock_code)
                    
                    # 批量插入数据库
                    for record in records:
                        # 检查是否已存在
                        existing = self.db.query(StockDaily).filter(
                            StockDaily.code == record['code'],
                            StockDaily.trade_date == record['trade_date']
                        ).first()
                        
                        if existing:
                            # 更新现有记录
                            for key, value in record.items():
                                setattr(existing, key, value)
                        else:
                            # 插入新记录
                            stock_daily = StockDaily(**record)
                            self.db.add(stock_daily)
                    
                    total_records += len(records)
                    logger.info(f"股票 {stock_code} 采集完成，{len(records)} 条记录")
                    
                except Exception as e:
                    logger.error(f"采集股票 {stock_code} 时出错: {e}")
                    # 继续采集下一个股票，不中断整个流程
                    continue
            
            # 提交所有更改
            self.db.commit()
            
            # 更新执行记录为成功
            self.update_crawl_run_success(crawl_run.id, total_records)
            
            logger.info(f"股票日线采集完成，共 {total_records} 条记录")
            return total_records
            
        except Exception as e:
            # 回滚事务
            self.db.rollback()
            # 更新执行记录为失败
            self.update_crawl_run_failed(crawl_run.id, str(e))
            raise
    
    def crawl_fund_nav(
        self,
        job_id: int,
        fund_codes: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> int:
        """
        执行基金净值数据采集
        
        Args:
            job_id: 任务ID
            fund_codes: 基金代码列表，None表示采集所有
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            采集的记录数
        """
        # 创建执行记录
        crawl_run = self.create_crawl_run(job_id)
        
        try:
            # 如果没有指定基金代码，从数据库获取所有活跃基金
            if not fund_codes:
                from app.models.instrument import Instrument
                instruments = self.db.query(Instrument).filter(
                    Instrument.type == 'fund',
                    Instrument.status == 'active'
                ).all()
                fund_codes = [inst.code for inst in instruments]
                
                if not fund_codes:
                    # 如果数据库没有基金，使用测试代码
                    fund_codes = ['000001', '110022', '000002']
                    logger.info("数据库中没有基金，使用测试代码")
            
            total_records = 0
            
            # 逐个采集基金
            for fund_code in fund_codes:
                try:
                    # 获取原始数据
                    df = self.fund_crawler.fetch_fund_nav(fund_code, start_date, end_date)
                    
                    if df.empty:
                        continue
                    
                    # 清洗和标准化
                    df_cleaned = self.fund_crawler.clean_and_standardize(df)
                    
                    if df_cleaned.empty:
                        continue
                    
                    # 准备数据库记录
                    records = self.fund_crawler.prepare_for_database(df_cleaned, fund_code)
                    
                    # 批量插入数据库
                    for record in records:
                        # 检查是否已存在
                        existing = self.db.query(FundNav).filter(
                            FundNav.code == record['code'],
                            FundNav.nav_date == record['nav_date']
                        ).first()
                        
                        if existing:
                            # 更新现有记录
                            for key, value in record.items():
                                setattr(existing, key, value)
                        else:
                            # 插入新记录
                            fund_nav = FundNav(**record)
                            self.db.add(fund_nav)
                    
                    total_records += len(records)
                    logger.info(f"基金 {fund_code} 采集完成，{len(records)} 条记录")
                    
                except Exception as e:
                    logger.error(f"采集基金 {fund_code} 时出错: {e}")
                    # 继续采集下一个基金，不中断整个流程
                    continue
            
            # 提交所有更改
            self.db.commit()
            
            # 更新执行记录为成功
            self.update_crawl_run_success(crawl_run.id, total_records)
            
            logger.info(f"基金净值采集完成，共 {total_records} 条记录")
            return total_records
            
        except Exception as e:
            # 回滚事务
            self.db.rollback()
            # 更新执行记录为失败
            self.update_crawl_run_failed(crawl_run.id, str(e))
            raise
