"""单元测试：Phase 2 清洗增强、Phase 3 缓存、Phase 4 日历。"""

from __future__ import annotations

from datetime import date

from app.services import cleaning, calendar_service
from app.core.cache import InMemoryTTLCache
from app.core.rate_limit import RateLimiter


# ---------- 行业分类映射 ----------
def test_guess_industry_known():
    assert cleaning.guess_industry("600519.SH") == "食品饮料"
    assert cleaning.guess_industry("300750.SZ") == "电力设备"


def test_guess_industry_fallback():
    assert cleaning.guess_industry("510300.OF") in ("指数基金", "场内基金")
    assert cleaning.guess_industry("600000.SH") == "沪市股票"


# ---------- 价格一致性校验 ----------
def test_clean_stock_fixes_inconsistent_high_low():
    rows = [
        # high 低于 close（异常），low 高于 open（异常），应被修正
        {"code": "X", "trade_date": date(2024, 1, 2), "open": 10, "high": 9,
         "low": 11, "close": 12, "volume": 100, "amount": 1000},
    ]
    cleaned = cleaning.clean_stock_daily(rows)
    r = cleaned[0]
    assert r["high"] >= max(r["open"], r["close"])
    assert r["low"] <= min(r["open"], r["close"])


# ---------- 跨源交叉验证 ----------
def test_cross_source_validate_detects_deviation():
    primary = [{"d": "2024-01-02", "p": 100}, {"d": "2024-01-03", "p": 200}]
    secondary = [{"d": "2024-01-02", "p": 101}, {"d": "2024-01-03", "p": 150}]
    warnings = cleaning.cross_source_validate(primary, secondary, "p", "d", tolerance=0.05)
    # 第二天偏差 (200-150)/150=33% 超过 5%，应告警；第一天 1% 不告警
    assert len(warnings) == 1
    assert "2024-01-03" in warnings[0]


# ---------- 交易日历 ----------
def test_calendar_skips_weekend():
    assert not calendar_service.is_trading_day(date(2025, 1, 4))   # 周六
    assert not calendar_service.is_trading_day(date(2025, 1, 5))   # 周日


def test_calendar_skips_holiday():
    assert not calendar_service.is_trading_day(date(2025, 1, 1))   # 元旦


def test_calendar_normal_trading_day():
    assert calendar_service.is_trading_day(date(2025, 1, 2))       # 周四非节假日


def test_expected_trading_days_count():
    # 2025-01-02 ~ 2025-01-08，扣除周末，应有 5 个交易日（1/4、1/5 周末）
    n = calendar_service.expected_trading_days(date(2025, 1, 2), date(2025, 1, 8))
    assert n == 5


# ---------- TTL 缓存 ----------
def test_cache_hit_and_miss():
    c = InMemoryTTLCache()
    assert c.get("k") is None       # miss
    c.set("k", "v", ttl=60)
    assert c.get("k") == "v"        # hit
    assert c.hits == 1 and c.misses == 1
    assert c.hit_rate == 50.0


def test_cache_invalidate_prefix():
    c = InMemoryTTLCache()
    c.set("stock:600519", 1, 60)
    c.set("stock:000001", 2, 60)
    c.set("fund:110011", 3, 60)
    removed = c.invalidate_prefix("stock:")
    assert removed == 2
    assert c.get("fund:110011") == 3


# ---------- 限流令牌桶 ----------
def test_rate_limiter_blocks_over_limit():
    rl = RateLimiter(per_minute=3)
    assert rl.allow("u1")
    assert rl.allow("u1")
    assert rl.allow("u1")
    assert not rl.allow("u1")       # 第 4 次超限
    assert rl.allow("u2")           # 不同用户独立
