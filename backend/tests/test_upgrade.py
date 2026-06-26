"""单元 / 接口测试：本次全面升级新增能力。

覆盖：字段级权限脱敏、行级/时间权限、受控 SQL 查询、加密压缩导出、
数据源注册表、公告采集、数据质量、异常监测、用户/角色/租户管理、复权净值、多标准行业分类。
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.services import cleaning


def _hdr(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def analyst_token(client: TestClient) -> str:
    resp = client.post("/api/auth/login", json={"username": "analyst", "password": "analyst123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


# ---------- 字段级权限（修复查询接口绕过脱敏的 Bug）----------
def test_viewer_amount_masked_in_query(client, viewer_token):
    resp = client.get("/api/stocks/600519.SH/daily", headers=_hdr(viewer_token), params={"page_size": 5})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items, "应有行情数据"
    assert all(i["amount"] == 0 for i in items), "普通用户成交额必须脱敏为 0"


def test_admin_amount_visible_in_query(client, admin_token):
    resp = client.get("/api/stocks/600519.SH/daily", headers=_hdr(admin_token), params={"page_size": 5})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(i["amount"] > 0 for i in items), "管理员应能看到真实成交额"


# ---------- 行级 / 时间权限 ----------
def test_analyst_row_level_blocks_fund(client, analyst_token):
    # analyst 角色 data_scope=stock，访问基金应 403
    resp = client.get("/api/funds/510300.OF/nav", headers=_hdr(analyst_token))
    assert resp.status_code == 403


def test_analyst_can_access_stock(client, analyst_token):
    resp = client.get("/api/stocks/600519.SH/daily", headers=_hdr(analyst_token), params={"page_size": 3})
    assert resp.status_code == 200


def test_analyst_instruments_filtered_to_stock(client, analyst_token):
    resp = client.get("/api/instruments", headers=_hdr(analyst_token), params={"page_size": 200})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items and all(i["asset_type"] == "stock" for i in items), "analyst 只应看到股票标的"


# ---------- 受控 SQL 查询 ----------
def test_sql_select_ok(client, admin_token):
    resp = client.post("/api/query/sql", headers=_hdr(admin_token),
                       json={"sql": "SELECT code, COUNT(*) AS n FROM stock_daily GROUP BY code"})
    assert resp.status_code == 200
    body = resp.json()
    assert "code" in body["columns"] and body["row_count"] > 0


def test_sql_blocks_dml(client, admin_token):
    resp = client.post("/api/query/sql", headers=_hdr(admin_token),
                       json={"sql": "DELETE FROM stock_daily"})
    assert resp.status_code == 400


def test_sql_blocks_multi_statement(client, admin_token):
    resp = client.post("/api/query/sql", headers=_hdr(admin_token),
                       json={"sql": "SELECT 1 FROM stock_daily; DROP TABLE users"})
    assert resp.status_code == 400


def test_sql_blocks_non_whitelisted_table(client, admin_token):
    resp = client.post("/api/query/sql", headers=_hdr(admin_token),
                       json={"sql": "SELECT * FROM users"})
    assert resp.status_code == 400


def test_sql_forbidden_for_viewer(client, viewer_token):
    resp = client.post("/api/query/sql", headers=_hdr(viewer_token),
                       json={"sql": "SELECT 1 FROM stock_daily"})
    assert resp.status_code == 403


# ---------- 加密压缩导出 ----------
def test_encrypted_export(client, admin_token):
    resp = client.post("/api/exports", headers=_hdr(admin_token),
                       json={"dataset": "stock_daily", "file_format": "csv",
                             "code": "600519.SH", "compress": True, "encrypt": True})
    assert resp.status_code == 200
    rec = resp.json()
    assert rec["file_name"].endswith(".zip")
    from app.core.config import settings
    assert os.path.exists(os.path.join(settings.EXPORT_DIR, rec["file_name"]))


# ---------- 数据源注册表 ----------
def test_datasources_listing(client, admin_token):
    resp = client.get("/api/datasources", headers=_hdr(admin_token))
    assert resp.status_code == 200
    keys = {s["key"] for s in resp.json()}
    assert {"akshare", "tencent", "sina", "sample", "announcement"} <= keys


# ---------- 实时行情快照 ----------
def test_realtime_snapshot(client, admin_token):
    resp = client.get("/api/realtime/quotes", headers=_hdr(admin_token))
    assert resp.status_code == 200
    body = resp.json()
    assert "quotes" in body and "market_open" in body
    # 休市/测试环境应回退到库中收盘数据
    assert isinstance(body["quotes"], list)


def test_realtime_sina_symbol():
    from app.services.realtime_service import _sina_symbol
    assert _sina_symbol("600519.SH") == "sh600519"
    assert _sina_symbol("000001.SZ") == "sz000001"


# ---------- 公告采集 ----------
def test_announcement_crawl_and_list(client, admin_token):
    crawl = client.post("/api/tasks/crawl", headers=_hdr(admin_token),
                        json={"job_type": "announcement", "target_codes": "", "mode": "full"})
    assert crawl.status_code == 200
    listing = client.get("/api/announcements", headers=_hdr(admin_token))
    assert listing.status_code == 200
    assert listing.json()["total"] > 0


# ---------- 数据质量 + 异常监测 ----------
def test_data_quality_endpoint(client, admin_token):
    # 触发告警（内部会跑异常监测并登记问题）
    client.get("/api/monitor/alerts", headers=_hdr(admin_token))
    resp = client.get("/api/data-quality", headers=_hdr(admin_token))
    assert resp.status_code == 200
    assert "items" in resp.json()


def test_api_stats_endpoint(client, admin_token):
    resp = client.get("/api/monitor/api-stats", headers=_hdr(admin_token))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ---------- 用户 / 角色 / 租户管理 ----------
def test_admin_user_crud(client, admin_token):
    # 创建
    create = client.post("/api/admin/users", headers=_hdr(admin_token),
                        json={"username": "tester1", "password": "test1234",
                              "role_name": "viewer", "full_name": "测试员"})
    assert create.status_code == 200, create.text
    uid = create.json()["id"]
    # 列表含新用户
    users = client.get("/api/admin/users", headers=_hdr(admin_token)).json()
    assert any(u["username"] == "tester1" for u in users)
    # 更新
    upd = client.patch(f"/api/admin/users/{uid}", headers=_hdr(admin_token),
                      json={"department": "风控部"})
    assert upd.status_code == 200 and upd.json()["department"] == "风控部"
    # 新用户可登录
    login = client.post("/api/auth/login", json={"username": "tester1", "password": "test1234"})
    assert login.status_code == 200
    # 删除
    dele = client.delete(f"/api/admin/users/{uid}", headers=_hdr(admin_token))
    assert dele.status_code == 200


def test_admin_endpoints_forbidden_for_viewer(client, viewer_token):
    assert client.get("/api/admin/users", headers=_hdr(viewer_token)).status_code == 403


def test_roles_and_tenants_listing(client, admin_token):
    roles = client.get("/api/admin/roles", headers=_hdr(admin_token)).json()
    assert {"admin", "viewer", "analyst"} <= {r["name"] for r in roles}
    tenants = client.get("/api/admin/tenants", headers=_hdr(admin_token)).json()
    assert {"HQ", "RESEARCH"} <= {t["code"] for t in tenants}


# ---------- 基金复权净值 ----------
def test_fund_adj_nav_computed():
    from datetime import date
    rows = [
        {"code": "F", "nav_date": date(2024, 1, 2), "unit_nav": 1.0, "accum_nav": 1.0},
        {"code": "F", "nav_date": date(2024, 1, 3), "unit_nav": 1.1, "accum_nav": 1.2},  # 含分红
    ]
    cleaned = cleaning.clean_fund_nav(rows)
    assert all("adj_nav" in r for r in cleaned)
    # 含分红日的复权净值应高于单纯单位净值涨幅
    assert cleaned[1]["adj_nav"] >= cleaned[1]["unit_nav"]


# ---------- 多标准行业分类 ----------
def test_industry_multi_standard():
    assert cleaning.guess_industry("600519.SH", "sw") == "食品饮料"
    assert cleaning.guess_industry("600519.SH", "citic") == "食品饮料"
    assert cleaning.guess_industry("600519.SH", "gics") == "Consumer Staples"
    allstd = cleaning.industry_all_standards("300750.SZ")
    assert set(allstd.keys()) == {"sw", "citic", "gics"}

# ---------- 导出记录隔离 / 下载隔离 ----------
def test_export_records_are_isolated_between_users(client, admin_token, viewer_token):
    admin_rec = client.post(
        "/api/exports",
        headers=_hdr(admin_token),
        json={"dataset": "stock_daily", "file_format": "csv", "code": "600519.SH"},
    )
    assert admin_rec.status_code == 200, admin_rec.text
    admin_id = admin_rec.json()["id"]

    viewer_rec = client.post(
        "/api/exports",
        headers=_hdr(viewer_token),
        json={"dataset": "stock_daily", "file_format": "csv", "code": "600519.SH"},
    )
    assert viewer_rec.status_code == 200, viewer_rec.text
    viewer_id = viewer_rec.json()["id"]

    listing = client.get("/api/exports", headers=_hdr(viewer_token))
    assert listing.status_code == 200
    ids = {item["id"] for item in listing.json()["items"]}
    assert viewer_id in ids
    assert admin_id not in ids

    forbidden = client.get(f"/api/exports/{admin_id}/download", headers=_hdr(viewer_token))
    assert forbidden.status_code == 403
    own = client.get(f"/api/exports/{viewer_id}/download", headers=_hdr(viewer_token))
    assert own.status_code == 200


# ---------- SQL LIMIT 统一由接口参数控制 ----------
def test_sql_user_limit_is_overridden_by_api_limit(client, admin_token):
    resp = client.post(
        "/api/query/sql",
        headers=_hdr(admin_token),
        json={"sql": "SELECT * FROM stock_daily LIMIT 100000", "limit": 3},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["row_count"] == 3
    assert body["truncated"] is True


# ---------- 租户 / 部门数据隔离 ----------
def test_tenant_department_scoped_instrument_visibility(client, viewer_token, analyst_token):
    from datetime import date

    from app.models import Instrument, StockDaily, Tenant

    private_code = "999999.SH"
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.code == "RESEARCH").first()
        assert tenant is not None
        inst = db.query(Instrument).filter(Instrument.code == private_code).first()
        if not inst:
            db.add(
                Instrument(
                    code=private_code,
                    name="研究部专属股票",
                    asset_type="stock",
                    market="SH",
                    category="内部研究",
                    tenant_id=tenant.id,
                    department="研究部",
                )
            )
        row = db.query(StockDaily).filter(StockDaily.code == private_code).first()
        if not row:
            db.add(
                StockDaily(
                    code=private_code,
                    trade_date=date.today(),
                    open=10,
                    high=11,
                    low=9,
                    close=10.5,
                    volume=1000,
                    amount=10500,
                    pct_change=0,
                    source="tenant-test",
                )
            )
        db.commit()
    finally:
        db.close()

    hidden = client.get(
        "/api/instruments",
        headers=_hdr(viewer_token),
        params={"keyword": private_code, "page_size": 20},
    )
    assert hidden.status_code == 200
    assert hidden.json()["total"] == 0

    forbidden = client.get(f"/api/stocks/{private_code}/daily", headers=_hdr(viewer_token))
    assert forbidden.status_code == 403

    visible = client.get(
        "/api/instruments",
        headers=_hdr(analyst_token),
        params={"keyword": private_code, "page_size": 20},
    )
    assert visible.status_code == 200
    assert visible.json()["total"] == 1

    allowed = client.get(f"/api/stocks/{private_code}/daily", headers=_hdr(analyst_token))
    assert allowed.status_code == 200
    assert allowed.json()["total"] == 1

# ---------- 告警去重与处理 ----------
def test_alert_records_deduplicate_and_resolve(client, admin_token):
    from app.models import AlertRecord
    from app.services import monitor_service

    alert = {"level": "warning", "type": "测试告警", "target": "unit-test", "message": "同一告警不应重复落库"}
    db = SessionLocal()
    try:
        before = db.query(AlertRecord).filter(AlertRecord.target == "unit-test", AlertRecord.status == "open").count()
        monitor_service.dispatch_alerts(db, [alert])
        monitor_service.dispatch_alerts(db, [alert])
        after = db.query(AlertRecord).filter(AlertRecord.target == "unit-test", AlertRecord.status == "open").count()
        assert after == before + 1
        rec = db.query(AlertRecord).filter(AlertRecord.target == "unit-test", AlertRecord.status == "open").order_by(AlertRecord.id.desc()).first()
        assert rec.fingerprint
    finally:
        db.close()

    listing = client.get("/api/monitor/alert-records", headers=_hdr(admin_token), params={"status": "open"})
    assert listing.status_code == 200
    rec = next(i for i in listing.json()["items"] if i["target"] == "unit-test")
    resolved = client.post(
        f"/api/monitor/alert-records/{rec['id']}/resolve",
        headers=_hdr(admin_token),
        json={"status": "resolved", "note": "测试处理"},
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolved_by"] == "admin"


# ---------- 登录响应暴露前端权限所需字段 ----------
def test_login_returns_role_permissions(client):
    resp = client.post("/api/auth/login", json={"username": "analyst", "password": "analyst123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data_scope"] == "stock"
    assert body["can_export"] is False
    assert body["max_history_days"] == 365
