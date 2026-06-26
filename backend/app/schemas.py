"""Pydantic schemas：请求 / 响应数据契约。"""

from __future__ import annotations

from datetime import datetime, date
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


# ---------- 通用 ----------
class Pagination(BaseModel, Generic[T]):
    """统一分页响应。"""

    items: List[T]
    total: int
    page: int
    page_size: int


class Message(BaseModel):
    message: str


# ---------- 认证 ----------
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    data_scope: str = "all"
    max_history_days: int = 0
    can_export: bool = True
    can_view_sensitive: bool = False


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    data_scope: str = "all"
    max_history_days: int = 0
    can_export: bool = True
    can_view_sensitive: bool = False
    tenant_id: Optional[int] = None
    department: str = ""

    model_config = {"from_attributes": True}


# ---------- 标的 ----------
class InstrumentOut(BaseModel):
    id: int
    code: str
    name: str
    asset_type: str
    market: str
    category: str
    is_active: bool

    model_config = {"from_attributes": True}


class InstrumentCreate(BaseModel):
    code: str = Field(..., max_length=16)
    name: str = Field(..., max_length=64)
    asset_type: str = Field(..., pattern="^(stock|fund)$")
    market: str = ""
    category: str = ""


# ---------- 行情 / 净值 ----------
class StockDailyOut(BaseModel):
    code: str
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    pct_change: float
    source: str

    model_config = {"from_attributes": True}


class FundNavOut(BaseModel):
    code: str
    nav_date: date
    unit_nav: float
    accum_nav: float
    adj_nav: float = 0
    daily_return: float
    source: str

    model_config = {"from_attributes": True}


# ---------- 采集任务 ----------
class CrawlJobCreate(BaseModel):
    name: str = Field(..., max_length=64)
    job_type: str = Field(..., pattern="^(stock_daily|fund_nav|announcement)$")
    target_codes: str = ""
    mode: str = Field("full", pattern="^(full|incremental)$")
    frequency: str = Field("daily", pattern="^(realtime|minute|daily|weekly|quarterly|manual)$")
    cron: str = ""
    enabled: bool = True


class CrawlJobUpdate(BaseModel):
    name: Optional[str] = None
    target_codes: Optional[str] = None
    mode: Optional[str] = Field(None, pattern="^(full|incremental)$")
    frequency: Optional[str] = Field(None, pattern="^(realtime|minute|daily|weekly|quarterly|manual)$")
    cron: Optional[str] = None
    enabled: Optional[bool] = None


class CrawlJobOut(BaseModel):
    id: int
    name: str
    job_type: str
    target_codes: str
    mode: str
    frequency: str = "daily"
    cron: str
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CrawlRunOut(BaseModel):
    id: int
    job_id: int
    trigger: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    rows_affected: int
    retries: int
    source: str
    message: str

    model_config = {"from_attributes": True}


class TriggerCrawlRequest(BaseModel):
    """临时手动采集（无需预建任务）。"""

    job_type: str = Field(..., pattern="^(stock_daily|fund_nav|announcement)$")
    target_codes: str = Field("", description="逗号分隔的证券代码；公告采集可留空")
    mode: str = Field("full", pattern="^(full|incremental)$")


# ---------- 导出 ----------
class ExportRequest(BaseModel):
    dataset: str = Field(..., pattern="^(stock_daily|fund_nav|instruments)$")
    file_format: str = Field("csv", pattern="^(csv|excel|parquet)$")
    code: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    # 加密压缩（模块4：导出数据加密和压缩）
    compress: bool = False
    encrypt: bool = False


class ExportRecordOut(BaseModel):
    id: int
    dataset: str
    file_format: str
    params: str
    file_name: str
    row_count: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- 监控 / 仪表盘 ----------
class HealthOut(BaseModel):
    status: str
    app: str
    env: str
    database: str
    scheduler: str
    time: datetime


class DashboardStats(BaseModel):
    instrument_count: int
    stock_count: int
    fund_count: int
    stock_daily_rows: int
    fund_nav_rows: int
    job_count: int
    crawl_success_rate: float = 100.0
    industry_distribution: List[dict] = []
    recent_runs: List[CrawlRunOut]
    recent_exports: List[ExportRecordOut]


class AuditLogOut(BaseModel):
    id: int
    username: str
    role: str
    action: str
    target: str
    detail: str
    ip: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- 公告 / 新闻 / 舆情（模块1 公开数据源）----------
class AnnouncementOut(BaseModel):
    id: int
    code: str
    title: str
    category: str
    source: str
    url: str
    summary: str
    sentiment: str
    publish_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- 数据质量（模块2/5）----------
class DataQualityIssueOut(BaseModel):
    id: int
    issue_type: str
    code: str
    dataset: str
    severity: str
    message: str
    status: str
    resolved_by: str
    resolved_note: str
    created_at: datetime
    resolved_at: Optional[datetime]

    @field_validator("resolved_by", "resolved_note", mode="before")
    @classmethod
    def _blank_for_null(cls, value):
        return "" if value is None else value

    model_config = {"from_attributes": True}


class ResolveIssueRequest(BaseModel):
    status: str = Field("resolved", pattern="^(resolved|ignored|open)$")
    note: str = ""


# ---------- 告警记录（模块5）----------
class AlertRecordOut(BaseModel):
    id: int
    level: str
    alert_type: str
    target: str
    message: str
    fingerprint: str
    status: str
    dispatch_status: str
    resolved_by: str
    resolved_note: str
    created_at: datetime
    resolved_at: Optional[datetime]

    @field_validator(
        "fingerprint", "status", "dispatch_status", "resolved_by", "resolved_note", mode="before"
    )
    @classmethod
    def _blank_for_null(cls, value):
        return "" if value is None else value

    model_config = {"from_attributes": True}


class ResolveAlertRequest(BaseModel):
    status: str = Field("resolved", pattern="^(resolved|ignored|open)$")
    note: str = ""


# ---------- 受控 SQL 查询（模块4）----------
class SqlQueryRequest(BaseModel):
    sql: str = Field(..., min_length=1, max_length=2000)
    limit: int = Field(200, ge=1, le=5000)


class SqlQueryResult(BaseModel):
    columns: List[str]
    rows: List[dict]
    row_count: int
    truncated: bool
    elapsed_ms: float


# ---------- 用户 / 角色 / 租户管理（模块6）----------
class RoleOut(BaseModel):
    id: int
    name: str
    description: str
    data_scope: str
    max_history_days: int
    can_export: bool
    can_view_sensitive: bool

    model_config = {"from_attributes": True}


class RoleUpdate(BaseModel):
    description: Optional[str] = None
    data_scope: Optional[str] = Field(None, pattern="^(all|stock|fund)$")
    max_history_days: Optional[int] = Field(None, ge=0)
    can_export: Optional[bool] = None
    can_view_sensitive: Optional[bool] = None


class TenantOut(BaseModel):
    id: int
    name: str
    code: str
    description: str
    is_active: bool

    model_config = {"from_attributes": True}


class TenantCreate(BaseModel):
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=64)
    description: str = ""


class AdminUserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    department: str
    tenant_id: Optional[int]
    tenant_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=4, max_length=128)
    role_name: str = Field(..., max_length=32)
    full_name: str = ""
    department: str = ""
    tenant_id: Optional[int] = None


class AdminUserUpdate(BaseModel):
    password: Optional[str] = Field(None, min_length=4, max_length=128)
    role_name: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    tenant_id: Optional[int] = None
    is_active: Optional[bool] = None


# ---------- 数据源注册表（模块1）----------
class DataSourceOut(BaseModel):
    key: str
    name: str
    category: str
    description: str
    status: str  # online / offline / fallback / unknown
    last_used: Optional[str] = None
    hit_count: int = 0


