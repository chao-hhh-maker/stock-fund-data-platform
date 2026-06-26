"""接口测试：认证、权限、查询、采集、导出、监控全链路。"""

from __future__ import annotations

from tests.conftest import auth_header


def test_health_public(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_login_success_and_failure(client):
    ok = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert ok.status_code == 200
    assert ok.json()["role"] == "admin"

    bad = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert bad.status_code == 401


def test_me_requires_token(client, viewer_token):
    assert client.get("/api/auth/me").status_code == 401
    resp = client.get("/api/auth/me", headers=auth_header(viewer_token))
    assert resp.status_code == 200
    assert resp.json()["username"] == "viewer"


def test_instruments_seeded(client, viewer_token):
    resp = client.get("/api/instruments", headers=auth_header(viewer_token))
    assert resp.status_code == 200
    assert resp.json()["total"] >= 8


def test_stock_daily_query_paginated(client, viewer_token):
    resp = client.get(
        "/api/stocks/600519.SH/daily?page=1&page_size=10", headers=auth_header(viewer_token)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] > 0
    assert len(body["items"]) <= 10
    assert body["items"][0]["code"] == "600519.SH"


def test_fund_nav_query(client, viewer_token):
    resp = client.get("/api/funds/510300.OF/nav", headers=auth_header(viewer_token))
    assert resp.status_code == 200
    assert resp.json()["total"] > 0


def test_viewer_cannot_trigger_crawl(client, viewer_token):
    resp = client.post(
        "/api/tasks/crawl",
        json={"job_type": "stock_daily", "target_codes": "600519.SH"},
        headers=auth_header(viewer_token),
    )
    assert resp.status_code == 403


def test_admin_quick_crawl_and_runs(client, admin_token):
    resp = client.post(
        "/api/tasks/crawl",
        json={"job_type": "stock_daily", "target_codes": "000001.SZ,600519.SH"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    run = resp.json()
    assert run["status"] in ("success", "partial")
    assert run["rows_affected"] > 0

    runs = client.get("/api/tasks/runs", headers=auth_header(admin_token))
    assert runs.status_code == 200
    assert runs.json()["total"] >= 1


def test_job_lifecycle_and_logs(client, admin_token):
    created = client.post(
        "/api/tasks",
        json={"name": "测试任务", "job_type": "fund_nav", "target_codes": "510300.OF", "cron": ""},
        headers=auth_header(admin_token),
    )
    assert created.status_code == 200
    job_id = created.json()["id"]

    run = client.post(f"/api/tasks/{job_id}/run", headers=auth_header(admin_token))
    assert run.status_code == 200

    logs = client.get(f"/api/tasks/{job_id}/logs", headers=auth_header(admin_token))
    assert logs.status_code == 200
    assert len(logs.json()) >= 1


def test_export_csv_and_download(client, admin_token):
    resp = client.post(
        "/api/exports",
        json={"dataset": "stock_daily", "file_format": "csv", "code": "600519.SH"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    rec = resp.json()
    assert rec["row_count"] > 0

    dl = client.get(f"/api/exports/{rec['id']}/download", headers=auth_header(admin_token))
    assert dl.status_code == 200
    assert len(dl.content) > 0


def test_dashboard_stats(client, admin_token):
    resp = client.get("/api/dashboard", headers=auth_header(admin_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["stock_count"] >= 5
    assert body["fund_count"] >= 3
    assert body["stock_daily_rows"] > 0
