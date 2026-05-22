"""
采集任务相关模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class CrawlJob(Base):
    """采集任务配置表"""
    __tablename__ = "crawl_jobs"

    id = Column(Integer, primary_key=True, index=True, comment="任务ID")
    job_name = Column(String(100), nullable=False, comment="任务名称")
    job_type = Column(Enum('stock_daily', 'fund_nav', 'instrument_info'), nullable=False, comment="任务类型")
    target_codes = Column(Text, comment="目标代码列表(JSON格式,NULL表示全部)")
    schedule_cron = Column(String(100), comment="定时表达式(CRON)")
    is_enabled = Column(Integer, default=1, comment="是否启用")
    retry_times = Column(Integer, default=3, comment="重试次数")
    timeout_seconds = Column(Integer, default=300, comment="超时时间(秒)")
    extra_config = Column(Text, comment="额外配置(JSON格式)")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    runs = relationship("CrawlRun", backref="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CrawlJob(id={self.id}, name='{self.job_name}', type='{self.job_type}')>"


class CrawlRun(Base):
    """采集任务执行记录表"""
    __tablename__ = "crawl_runs"

    id = Column(Integer, primary_key=True, index=True, comment="执行记录ID")
    job_id = Column(Integer, ForeignKey("crawl_jobs.id"), nullable=False, comment="任务ID")
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    status = Column(Enum('running', 'success', 'failed', 'timeout'), nullable=False, comment="执行状态")
    records_count = Column(Integer, default=0, comment="采集记录数")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<CrawlRun(id={self.id}, job_id={self.job_id}, status='{self.status}')>"
