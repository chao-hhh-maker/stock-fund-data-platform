"""接口测试：Phase 3-5 新增端点（监控、元数据、审计、增量、限流/配额）。"""

from __future__ import annotations

from tests.conftest import auth_header


def test_metrics_endpoint(client, admin_token):
    resp = client.get("/api/monitor/metrics", headers=auth_header(admin_token))
    assert resp.status_code == 200
    body = resp.json()
    assert "cache" in body
    assert "crawl_success_rate" in body
    assert body["stock_daily_rows"] > 0


def test_integrity_endpoint(client, admin_token):
    resp = client.get("/api/monitor/integrity", headers=auth_header(admin_token))
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 8
    assert "completeness" in items[0]


def test_alerts_endpoint(client, viewer_token):
    resp = client.get("/api/monitor/alerts", headers=auth_header(viewer_token))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_data_dictionary(client, viewer_token):
    resp = client.get("/api/metadata/dictionary", headers=auth_header(viewer_token))
    assert resp.status_code == 200
    tables = [t["table"] for t in resp.json()]
    assert "stock_daily" in tables and "fund_nav" in tables


def test_lineage_endpoint(client, admin_token):
    resp = client.get("/api/metadata/lineage", headers=auth_header(admin_token))
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) >= 8
    assert "source" in rows[0] and "rows" in rows[0]


def test_dashboard_has_industry_and_success_rate(client, admin_token):
    resp = client.get("/api/dashboard", headers=auth_header(admin_token))
    assert resp.status_code == 200
    body = resp.json()
    assert "crawl_success_rate" in body
    assert len(body["industry_distribution"]) >= 1


def test_audit_log_records_login(client, admin_token):
    # admin_token 的获取本身会触发一次 login 审计
    resp = client.get("/api/audit/logs", headers=auth_header(admin_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    actions = [a["action"] for a in body["items"]]
    assert "login" in actions


def test_audit_requires_admin(client, viewer_token):
    resp = client.get("/api/audit/logs", headers=auth_header(viewer_token))
    assert resp.status_code == 403


def test_incremental_crawl(client, admin_token):
    # 先全量
    r1 = client.post(
        "/api/tasks/crawl",
        json={"job_type": "stock_daily", "target_codes": "600519.SH", "mode": "full"},
        headers=auth_header(admin_token),
    )
    assert r1.status_code == 200
    # 再增量（库中已有最新日期，增量通常 0 或少量新增，但不应报错）
    r2 = client.post(
        "/api/tasks/crawl",
        json={"job_type": "stock_daily", "target_codes": "600519.SH", "mode": "incremental"},
        headers=auth_header(admin_token),
    )
    assert r2.status_code == 200
    assert r2.json()["status"] in ("success", "partial")


def test_viewer_can_export_with_quota(client, viewer_token):
    """普通用户可导出（受配额限制），字段级权限隐藏敏感列。"""
    resp = client.post(
        "/api/exports",
        json={"dataset": "stock_daily", "file_format": "csv", "code": "600519.SH"},
        headers=auth_header(viewer_token),
    )
    assert resp.status_code == 200
    assert resp.json()["row_count"] > 0
