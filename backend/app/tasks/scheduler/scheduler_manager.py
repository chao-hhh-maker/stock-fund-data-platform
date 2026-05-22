"""
APScheduler 调度器管理器
负责任务的定时调度和执行
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime
from typing import Dict, Optional
import logging
import json

from app.core.database import SessionLocal
from app.models.crawl import CrawlJob, CrawlRun
from app.services.crawl_service import CrawlService

logger = logging.getLogger(__name__)


class TaskScheduler:
    """任务调度器管理器"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.job_mapping: Dict[str, int] = {}  # APScheduler job_id -> CrawlJob.id
        
        # 注册事件监听器
        self.scheduler.add_listener(self._job_executed_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        
        logger.info("任务调度器初始化完成")
    
    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("任务调度器已启动")
    
    def shutdown(self, wait=True):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            logger.info("任务调度器已关闭")
    
    def _job_executed_listener(self, event):
        """
        任务执行完成后的事件监听器
        
        Args:
            event: APScheduler 事件对象
        """
        job_id = event.job_id
        
        # 从映射中获取 CrawlJob.id
        crawl_job_id = self.job_mapping.get(job_id)
        if not crawl_job_id:
            logger.warning(f"未找到任务映射: job_id={job_id}")
            return
        
        db = SessionLocal()
        try:
            # 获取最近的执行记录
            crawl_run = db.query(CrawlRun).filter(
                CrawlRun.job_id == crawl_job_id
            ).order_by(CrawlRun.start_time.desc()).first()
            
            if crawl_run:
                if event.exception:
                    # 任务执行失败
                    crawl_run.status = 'failed'
                    crawl_run.error_message = str(event.exception)[:1000]
                    logger.error(f"定时任务执行失败: job_id={crawl_job_id}, error={event.exception}")
                else:
                    # 任务执行成功
                    crawl_run.status = 'success'
                    logger.info(f"定时任务执行成功: job_id={crawl_job_id}")
                
                crawl_run.end_time = datetime.now()
                db.commit()
                
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            db.rollback()
        finally:
            db.close()
    
    def add_crawl_job(self, crawl_job: CrawlJob):
        """
        添加采集任务到调度器
        
        Args:
            crawl_job: 采集任务配置对象
        """
        if not crawl_job.is_enabled:
            logger.info(f"任务未启用，跳过: job_id={crawl_job.id}")
            return
        
        if not crawl_job.schedule_cron:
            logger.warning(f"任务没有 CRON 表达式，跳过: job_id={crawl_job.id}")
            return
        
        try:
            # 解析 CRON 表达式
            cron_parts = crawl_job.schedule_cron.split()
            if len(cron_parts) != 5:
                logger.error(f"CRON 表达式格式错误: {crawl_job.schedule_cron}")
                return
            
            minute, hour, day, month, day_of_week = cron_parts
            
            # 创建触发器
            trigger = CronTrigger(
                minute=minute if minute != '*' else None,
                hour=hour if hour != '*' else None,
                day=day if day != '*' else None,
                month=month if month != '*' else None,
                day_of_week=day_of_week if day_of_week != '*' else None
            )
            
            # 根据任务类型确定执行函数
            if crawl_job.job_type == 'stock_daily':
                func = self._execute_stock_crawl
            elif crawl_job.job_type == 'fund_nav':
                func = self._execute_fund_crawl
            else:
                logger.warning(f"不支持的任务类型: {crawl_job.job_type}")
                return
            
            # 解析额外配置
            extra_config = {}
            if crawl_job.extra_config:
                try:
                    extra_config = json.loads(crawl_job.extra_config)
                except Exception as e:
                    logger.warning(f"解析额外配置失败: {e}")
            
            # 添加任务到调度器
            job = self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=f"crawl_{crawl_job.id}",
                name=crawl_job.job_name,
                args=[crawl_job.id],
                kwargs=extra_config,
                replace_existing=True
            )
            
            # 保存映射关系
            self.job_mapping[job.id] = crawl_job.id
            
            logger.info(f"添加定时任务成功: job_id={crawl_job.id}, name={crawl_job.job_name}, cron={crawl_job.schedule_cron}")
            
        except Exception as e:
            logger.error(f"添加定时任务失败: job_id={crawl_job.id}, error={e}")
    
    def remove_crawl_job(self, crawl_job_id: int):
        """
        从调度器移除采集任务
        
        Args:
            crawl_job_id: 采集任务ID
        """
        job_id = f"crawl_{crawl_job_id}"
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            
            # 从映射中移除
            if job_id in self.job_mapping:
                del self.job_mapping[job_id]
            
            logger.info(f"移除定时任务: job_id={crawl_job_id}")
        else:
            logger.warning(f"任务不存在于调度器中: job_id={crawl_job_id}")
    
    def pause_job(self, crawl_job_id: int):
        """暂停任务"""
        job_id = f"crawl_{crawl_job_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.pause_job(job_id)
            logger.info(f"暂停任务: job_id={crawl_job_id}")
    
    def resume_job(self, crawl_job_id: int):
        """恢复任务"""
        job_id = f"crawl_{crawl_job_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.resume_job(job_id)
            logger.info(f"恢复任务: job_id={crawl_job_id}")
    
    def load_jobs_from_database(self):
        """
        从数据库加载所有启用的任务到调度器
        系统启动时调用
        """
        db = SessionLocal()
        try:
            # 查询所有启用的任务
            enabled_jobs = db.query(CrawlJob).filter(
                CrawlJob.is_enabled == 1,
                CrawlJob.schedule_cron.isnot(None)
            ).all()
            
            logger.info(f"从数据库加载 {len(enabled_jobs)} 个定时任务")
            
            for job in enabled_jobs:
                self.add_crawl_job(job)
            
            logger.info("定时任务加载完成")
            
        except Exception as e:
            logger.error(f"加载定时任务失败: {e}")
        finally:
            db.close()
    
    def _execute_stock_crawl(self, job_id: int, **kwargs):
        """
        执行股票采集任务
        
        Args:
            job_id: 任务ID
            **kwargs: 额外参数
        """
        logger.info(f"开始执行定时股票采集任务: job_id={job_id}")
        
        db = SessionLocal()
        try:
            service = CrawlService(db)
            
            # 从 kwargs 获取参数
            stock_codes = kwargs.get('stock_codes')
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            
            # 执行采集
            records_count = service.crawl_stock_daily(
                job_id=job_id,
                stock_codes=stock_codes,
                start_date=start_date,
                end_date=end_date
            )
            
            logger.info(f"定时股票采集完成: job_id={job_id}, records={records_count}")
            
        except Exception as e:
            logger.error(f"定时股票采集失败: job_id={job_id}, error={e}")
            raise
        finally:
            db.close()
    
    def _execute_fund_crawl(self, job_id: int, **kwargs):
        """
        执行基金采集任务
        
        Args:
            job_id: 任务ID
            **kwargs: 额外参数
        """
        logger.info(f"开始执行定时基金采集任务: job_id={job_id}")
        
        db = SessionLocal()
        try:
            service = CrawlService(db)
            
            # 从 kwargs 获取参数
            fund_codes = kwargs.get('fund_codes')
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            
            # 执行采集
            records_count = service.crawl_fund_nav(
                job_id=job_id,
                fund_codes=fund_codes,
                start_date=start_date,
                end_date=end_date
            )
            
            logger.info(f"定时基金采集完成: job_id={job_id}, records={records_count}")
            
        except Exception as e:
            logger.error(f"定时基金采集失败: job_id={job_id}, error={e}")
            raise
        finally:
            db.close()


# 全局调度器实例
scheduler_manager = TaskScheduler()
