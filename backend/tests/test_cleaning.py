"""单元测试：数据清洗与标准化（不依赖数据库 / 网络）。"""

from __future__ import annotations

from datetime import date

from app.services import cleaning


def test_normalize_code_stock_suffix_inference():
    assert cleaning.normalize_code("600519") == "600519.SH"
    assert cleaning.normalize_code("000001") == "000001.SZ"
    assert cleaning.normalize_code("300750") == "300750.SZ"


def test_normalize_code_prefix_form():
    assert cleaning.normalize_code("sh600519") == "600519.SH"
    assert cleaning.normalize_code("sz000001") == "000001.SZ"


def test_normalize_code_fund():
    assert cleaning.normalize_code("510300", "fund") == "510300.OF"


def test_normalize_code_keeps_existing_suffix():
    assert cleaning.normalize_code("600519.sh") == "600519.SH"


def test_clean_stock_daily_drops_invalid_and_computes_pct():
    rows = [
        {"code": "X", "trade_date": date(2024, 1, 2), "open": 10, "high": 11, "low": 9, "close": 10, "volume": 100, "amount": 1000},
        {"code": "X", "trade_date": date(2024, 1, 3), "open": 10, "high": 12, "low": 10, "close": 11, "volume": 100, "amount": 1100},
        # 异常行：close 为 0，应被丢弃
        {"code": "X", "trade_date": date(2024, 1, 4), "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0, "amount": 0},
    ]
    cleaned = cleaning.clean_stock_daily(rows)
    assert len(cleaned) == 2
    # 第二天涨幅 (11-10)/10 = 10%
    assert cleaned[1]["pct_change"] == 10.0


def test_clean_fund_nav_computes_daily_return():
    rows = [
        {"code": "F", "nav_date": date(2024, 1, 2), "unit_nav": 1.0, "accum_nav": 1.0},
        {"code": "F", "nav_date": date(2024, 1, 3), "unit_nav": 1.02, "accum_nav": 1.02},
    ]
    cleaned = cleaning.clean_fund_nav(rows)
    assert len(cleaned) == 2
    assert cleaned[1]["daily_return"] == 2.0
