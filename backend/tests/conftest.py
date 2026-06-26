"""Pytest 共享夹具：使用独立 SQLite 内存库与 TestClient。"""

from __future__ import annotations

import os

# 测试环境：关闭调度器、使用独立测试库、强制样例数据（不依赖网络）
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///./test_stock_fund.db"
os.environ["CRAWL_FORCE_SAMPLE"] = "true"
os.environ["RATE_LIMIT_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.database import Base, engine, SessionLocal
from app.main import app
from app.seed import run_all


@pytest.fixture(scope="session", autouse=True)
def _prepare_db():
    """整个测试会话开始前重建表并灌入种子数据。"""
    get_settings.cache_clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        run_all(db, with_market_data=True)
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    # 直接用 TestClient，不触发 lifespan（避免重复建表 / 启动调度器）
    return TestClient(app)


@pytest.fixture()
def admin_token(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture()
def viewer_token(client):
    resp = client.post("/api/auth/login", json={"username": "viewer", "password": "viewer123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
