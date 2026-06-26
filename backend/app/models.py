"""ORM 数据模型。

核心表：
- tenants                      租户（机构级隔离，模块6 多租户）
- users / roles                用户与角色（RBAC + 数据/时间权限）
- instruments                  证券主数据（股票/基金统一标的）
- stock_daily                  股票日线行情
- fund_nav                     基金净值
- announcements                公开数据源：公告/新闻/舆情（模块1）
- crawl_jobs / crawl_runs      采集任务定义与执行记录
- export_records               导出历史
- audit_logs                   操作审计
- data_quality_issues          数据质量问题（跨源偏差/异常，模块2/5）
- alert_records                告警历史（模块5 告警分发）
"""

from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    Date,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Tenant(Base):
    """租户：机构级数据隔离（模块6 多租户）。"""

    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(128), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    users: Mapped[list["User"]] = relationship(back_populates="tenant")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(128), default="")
    # 数据权限：可访问的资产范围 all / stock / fund（行级权限）
    data_scope: Mapped[str] = mapped_column(String(16), default="all")
    # 时间权限：可访问的历史天数，0 表示不限（模块6 时间权限）
    max_history_days: Mapped[int] = mapped_column(Integer, default=0)
    # 功能权限：是否允许导出
    can_export: Mapped[bool] = mapped_column(Boolean, default=True)
    # 是否可见敏感字段（如成交额 amount）
    can_view_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    full_name: Mapped[str] = mapped_column(String(64), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    # 多租户与部门（模块6 机构级/部门级隔离）
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"), nullable=True, index=True)
    department: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    role: Mapped["Role"] = relationship(back_populates="users")
    tenant: Mapped["Tenant | None"] = relationship(back_populates="users")


class Instrument(Base):
    """证券标的主数据：股票与基金统一管理。"""

    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 标准化代码，例如 600519.SH / 000001.SZ / 510300.OF
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    # asset_type: stock / fund
    asset_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    # 市场: SH / SZ / OF(场外基金) 等
    market: Mapped[str] = mapped_column(String(8), default="")
    # 行业 / 基金类型
    category: Mapped[str] = mapped_column(String(32), default="")
    # 可选租户 / 部门作用域：为空表示全局公共标的；非空时仅对应机构/部门可见。
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"), nullable=True, index=True)
    department: Mapped[str] = mapped_column(String(64), default="", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class StockDaily(Base):
    """股票日线行情。"""

    __tablename__ = "stock_daily"
    __table_args__ = (
        UniqueConstraint("code", "trade_date", name="uq_stock_daily_code_date"),
        Index("ix_stock_daily_code_date", "code", "trade_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float, default=0)
    amount: Mapped[float] = mapped_column(Float, default=0)
    # 涨跌幅(%)，清洗时计算
    pct_change: Mapped[float] = mapped_column(Float, default=0)
    source: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class FundNav(Base):
    """基金净值。"""

    __tablename__ = "fund_nav"
    __table_args__ = (
        UniqueConstraint("code", "nav_date", name="uq_fund_nav_code_date"),
        Index("ix_fund_nav_code_date", "code", "nav_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    nav_date: Mapped[date] = mapped_column(Date, nullable=False)
    # 单位净值
    unit_nav: Mapped[float] = mapped_column(Float)
    # 累计净值
    accum_nav: Mapped[float] = mapped_column(Float)
    # 复权净值（分红再投资假设，清洗时计算；模块2 基金净值复权）
    adj_nav: Mapped[float] = mapped_column(Float, default=0)
    # 日增长率(%)
    daily_return: Mapped[float] = mapped_column(Float, default=0)
    source: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CrawlJob(Base):
    """采集任务定义。"""

    __tablename__ = "crawl_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    # job_type: stock_daily / fund_nav
    job_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # 目标代码，逗号分隔；为空表示采集全部已登记标的
    target_codes: Mapped[str] = mapped_column(Text, default="")
    # 采集模式：full 全量 / incremental 增量
    mode: Mapped[str] = mapped_column(String(16), default="full")
    # 更新频率预设：realtime / minute / daily / weekly / quarterly / manual（模块1 频率配置）
    frequency: Mapped[str] = mapped_column(String(16), default="daily")
    # cron 表达式（定时任务），为空表示仅手动触发
    cron: Mapped[str] = mapped_column(String(64), default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    runs: Mapped[list["CrawlRun"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class CrawlRun(Base):
    """采集任务执行记录。"""

    __tablename__ = "crawl_runs"
    __table_args__ = (Index("ix_crawl_runs_job_started", "job_id", "started_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("crawl_jobs.id"), nullable=False)
    # trigger: manual / scheduled
    trigger: Mapped[str] = mapped_column(String(16), default="manual")
    # status: running / success / partial / failed
    status: Mapped[str] = mapped_column(String(16), default="running", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rows_affected: Mapped[int] = mapped_column(Integer, default=0)
    retries: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(String(32), default="")
    message: Mapped[str] = mapped_column(Text, default="")

    job: Mapped["CrawlJob"] = relationship(back_populates="runs")


class ExportRecord(Base):
    """数据导出记录。"""

    __tablename__ = "export_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # dataset: stock_daily / fund_nav / instruments
    dataset: Mapped[str] = mapped_column(String(32), nullable=False)
    file_format: Mapped[str] = mapped_column(String(16), default="csv")
    params: Mapped[str] = mapped_column(Text, default="")
    file_name: Mapped[str] = mapped_column(String(256), default="")
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AuditLog(Base):
    """操作审计日志：记录登录、采集、导出等关键操作。

    对应题目二「模块 6：数据权限和审计日志」。
    """

    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_user_time", "username", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), default="", index=True)
    role: Mapped[str] = mapped_column(String(32), default="")
    action: Mapped[str] = mapped_column(String(32), nullable=False)  # login/crawl/export/...
    target: Mapped[str] = mapped_column(String(128), default="")
    detail: Mapped[str] = mapped_column(Text, default="")
    ip: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Announcement(Base):
    """公开数据源：证监会公告 / 上市公司公告 / 新闻舆情（模块1 公开数据源抓取）。"""

    __tablename__ = "announcements"
    __table_args__ = (
        Index("ix_announcement_code_time", "code", "publish_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), default="", index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    # 类型：announcement(公告) / news(新闻) / sentiment(舆情) / report(年报)
    category: Mapped[str] = mapped_column(String(32), default="announcement")
    source: Mapped[str] = mapped_column(String(32), default="")
    url: Mapped[str] = mapped_column(String(512), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    # 舆情情绪：positive / neutral / negative
    sentiment: Mapped[str] = mapped_column(String(16), default="neutral")
    publish_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DataQualityIssue(Base):
    """数据质量问题：跨源偏差 / 关键字段异常，支持人工校对（模块2 人工校对 + 模块5 异常监测）。"""

    __tablename__ = "data_quality_issues"
    __table_args__ = (Index("ix_dq_status_time", "status", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 类型：cross_source(跨源偏差) / anomaly(字段异常) / missing(缺失)
    issue_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(16), default="", index=True)
    dataset: Mapped[str] = mapped_column(String(32), default="")
    severity: Mapped[str] = mapped_column(String(16), default="warning")  # info/warning/error
    message: Mapped[str] = mapped_column(Text, default="")
    # 状态：open(待处理) / resolved(已修正) / ignored(已忽略)
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)
    resolved_by: Mapped[str] = mapped_column(String(64), default="")
    resolved_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AlertRecord(Base):
    """告警历史记录：落库 + 可选 webhook 分发（模块5 告警分发）。"""

    __tablename__ = "alert_records"
    __table_args__ = (
        Index("ix_alert_time", "created_at"),
        Index("ix_alert_fingerprint_status", "fingerprint", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(16), default="warning")  # info/warning/error
    alert_type: Mapped[str] = mapped_column(String(32), default="")
    target: Mapped[str] = mapped_column(String(128), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    fingerprint: Mapped[str] = mapped_column(String(64), default="", index=True)
    # 处理状态：open / resolved / ignored
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)
    # 分发状态：pending / sent / failed / skipped
    dispatch_status: Mapped[str] = mapped_column(String(16), default="pending")
    resolved_by: Mapped[str] = mapped_column(String(64), default="")
    resolved_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


