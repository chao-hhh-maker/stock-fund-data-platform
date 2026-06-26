"""数据库会话与基类。

使用 SQLAlchemy 2.0 风格。SQLite 下自动加 check_same_thread=False，
以便 FastAPI 多线程 / 调度器线程共享连接。
"""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.core.config import settings


class Base(DeclarativeBase):
    """所有 ORM 模型的声明式基类。"""


def _build_engine():
    connect_args = {}
    if settings.is_sqlite:
        connect_args["check_same_thread"] = False
    return create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        echo=False,
        future=True,
    )


engine = _build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：提供请求级数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """创建所有表（开发 / 演示用；生产建议用 alembic 或 sql/init.sql）。"""
    # 导入模型以注册到 metadata
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _auto_migrate()


def _auto_migrate() -> None:
    """轻量自动迁移：为已存在的旧表补齐新增列。

    SQLAlchemy 的 create_all 只会创建缺失的表，不会给已存在的表加列。
    为兼容早期版本建立的数据库（避免用户手动删库），这里检测并补齐新增列。
    仅支持 SQLite / MySQL 的 ADD COLUMN（幂等，缺啥补啥）。
    """
    from sqlalchemy import inspect, text

    # 期望的新增列：{表名: [(列名, 列定义)]}
    expected = {
        "crawl_jobs": [
            ("mode", "VARCHAR(16) DEFAULT 'full'"),
            ("frequency", "VARCHAR(16) DEFAULT 'daily'"),
        ],
        "crawl_runs": [("retries", "INTEGER DEFAULT 0")],
        "fund_nav": [("adj_nav", "FLOAT DEFAULT 0")],
        "roles": [
            ("data_scope", "VARCHAR(16) DEFAULT 'all'"),
            ("max_history_days", "INTEGER DEFAULT 0"),
            ("can_export", "BOOLEAN DEFAULT 1"),
            ("can_view_sensitive", "BOOLEAN DEFAULT 0"),
        ],
        "users": [
            ("tenant_id", "INTEGER"),
            ("department", "VARCHAR(64) DEFAULT ''"),
        ],
        "instruments": [
            ("tenant_id", "INTEGER"),
            ("department", "VARCHAR(64) DEFAULT ''"),
        ],
        "alert_records": [
            ("fingerprint", "VARCHAR(64) DEFAULT ''"),
            ("status", "VARCHAR(16) DEFAULT 'open'"),
            ("resolved_by", "VARCHAR(64) DEFAULT ''"),
            ("resolved_note", "TEXT"),
            ("resolved_at", "DATETIME"),
        ],
    }
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, columns in expected.items():
            if table not in existing_tables:
                continue
            existing_cols = {c["name"] for c in inspector.get_columns(table)}
            for col_name, col_def in columns:
                if col_name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"))

        if "alert_records" in existing_tables:
            alert_cols = {c["name"] for c in inspect(conn).get_columns("alert_records")}
            if "status" in alert_cols:
                conn.execute(text("UPDATE alert_records SET status = 'open' WHERE status IS NULL OR status = ''"))
            if "dispatch_status" in alert_cols:
                conn.execute(text("UPDATE alert_records SET dispatch_status = 'skipped' WHERE dispatch_status IS NULL OR dispatch_status = ''"))
            if "fingerprint" in alert_cols:
                conn.execute(text("UPDATE alert_records SET fingerprint = '' WHERE fingerprint IS NULL"))
            if "resolved_by" in alert_cols:
                conn.execute(text("UPDATE alert_records SET resolved_by = '' WHERE resolved_by IS NULL"))
            if "resolved_note" in alert_cols:
                conn.execute(text("UPDATE alert_records SET resolved_note = '' WHERE resolved_note IS NULL"))

        if "data_quality_issues" in existing_tables:
            issue_cols = {c["name"] for c in inspect(conn).get_columns("data_quality_issues")}
            if "status" in issue_cols:
                conn.execute(text("UPDATE data_quality_issues SET status = 'open' WHERE status IS NULL OR status = ''"))
            if "resolved_by" in issue_cols:
                conn.execute(text("UPDATE data_quality_issues SET resolved_by = '' WHERE resolved_by IS NULL"))
            if "resolved_note" in issue_cols:
                conn.execute(text("UPDATE data_quality_issues SET resolved_note = '' WHERE resolved_note IS NULL"))



