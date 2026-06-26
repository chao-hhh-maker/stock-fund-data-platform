"""数据采集服务。

负责：抓取（akshare 优先，失败回退样例数据）→ 清洗标准化 → 入库（幂等 upsert）。
对应题目二「模块 1：数据获取与采集」。

设计要点：
- 任何单个代码失败都不会中断整体采集，错误写入运行记录。
- 采集来源（source）随数据落库，便于数据血缘追踪。
- upsert 保证重复采集不产生脏数据（幂等）。
- 支持增量采集（只拉库中已有最新日期之后的数据）与全量采集。
- 智能重试：网络类失败按指数退避重试，最终失败才回退样例数据。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.cache import cache
from app.core.config import settings
from app.models import FundNav, Instrument, StockDaily
from app.services import cleaning, data_quality_service, datasource_registry, sample_data

logger = logging.getLogger("crawler")

# 检测 akshare 是否可用：仅在模块加载时检查并提示一次，避免采集时刷屏。
try:
    import akshare as _ak  # noqa: F401

    AKSHARE_AVAILABLE = True
except Exception:  # noqa: BLE001
    AKSHARE_AVAILABLE = False
    logger.info(
        "未检测到 akshare，采集将使用内置样例数据（离线可演示）。"
        "如需真实行情请执行：pip install akshare"
    )


@dataclass
class CrawlResult:
    """单次采集的聚合结果。"""

    rows_affected: int = 0
    rows_inserted: int = 0  # 新增行数（增量真正拉到的新数据）
    rows_updated: int = 0   # 更新行数（已有行被刷新）
    source: str = ""
    status: str = "success"  # success / partial / failed
    errors: List[str] = field(default_factory=list)
    retries: int = 0  # 累计重试次数，用于运行日志展示
    fallback_reasons: List[str] = field(default_factory=list)  # 回退样例的真实原因

    @property
    def message(self) -> str:
        parts = []
        if self.retries:
            parts.append(f"重试 {self.retries} 次")
        if self.errors:
            parts.append(f"{len(self.errors)} 个代码失败：" + "; ".join(self.errors[:5]))
        else:
            # 明确区分新增/更新，避免增量"看起来没反应"的困惑
            detail = f"新增 {self.rows_inserted} 行 / 更新 {self.rows_updated} 行"
            if self.rows_inserted == 0 and self.rows_updated > 0:
                detail += "（数据已是最新，无新增）"
            parts.append(detail)
            if self.fallback_reasons:
                uniq = list(dict.fromkeys(self.fallback_reasons))
                parts.append("akshare 不可用已回退样例：" + "; ".join(uniq[:2]))
        return "，".join(parts)


def _retry(fn: Callable, *, attempts: int, base_delay: float, label: str) -> Tuple[object, int]:
    """指数退避重试。返回 (结果, 重试次数)。全部失败则抛出最后异常。"""
    last_exc: Optional[Exception] = None
    for i in range(attempts):
        try:
            return fn(), i
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if i < attempts - 1:
                delay = base_delay * (2 ** i)
                logger.warning("%s 第 %d 次失败：%s，%.1fs 后重试", label, i + 1, exc, delay)
                time.sleep(delay)
    raise last_exc  # type: ignore[misc]


# ---------- akshare 抓取（已适配新版 API 签名）----------
def _fetch_stock_via_akshare(code: str, start_date: Optional[date]) -> List[Dict]:
    """用 akshare 获取股票日线（前复权）。

    默认只取最近 CRAWL_LOOKBACK_DAYS 天，避免拉取全部历史（动辄数千行）导致超时。
    增量场景下 start_date 由调用方指定为库中最新日期。
    """
    import akshare as ak

    symbol = code.split(".")[0]
    effective_start = start_date or (date.today() - timedelta(days=settings.CRAWL_LOOKBACK_DAYS))
    kwargs = {
        "symbol": symbol, "period": "daily", "adjust": "qfq",
        "start_date": effective_start.strftime("%Y%m%d"),
        "end_date": date.today().strftime("%Y%m%d"),
        "timeout": settings.CRAWL_REQUEST_TIMEOUT,
    }
    df = ak.stock_zh_a_hist(**kwargs)
    if df is None or df.empty:
        raise ValueError("akshare 返回空数据")
    rows: List[Dict] = []
    for _, r in df.iterrows():
        rows.append(
            {
                "code": code,
                "trade_date": r["日期"],
                "open": r["开盘"],
                "high": r["最高"],
                "low": r["最低"],
                "close": r["收盘"],
                "volume": r["成交量"],
                "amount": r["成交额"],
            }
        )
    return rows


def _fetch_stock_via_tencent(code: str, start_date: Optional[date]) -> List[Dict]:
    """备用数据源：腾讯财经日线（域名 web.ifzq.gtimg.cn，与东财不同，可绕开部分网络限制）。

    返回前复权日线。校园网/办公网封锁东方财富时，腾讯接口通常仍可用。
    """
    import requests

    symbol = code.split(".")[0]
    market = code.split(".")[-1].lower()  # sh / sz
    prefix = "sh" if market == "sh" else "sz"
    secid = f"{prefix}{symbol}"
    days = settings.CRAWL_LOOKBACK_DAYS
    # qfqday=前复权日K
    url = (
        "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        f"?param={secid},day,,,{max(days, 320)},qfq"
    )
    resp = requests.get(url, timeout=settings.CRAWL_REQUEST_TIMEOUT,
                        headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    payload = resp.json()
    node = payload.get("data", {}).get(secid, {})
    kline = node.get("qfqday") or node.get("day") or []
    if not kline:
        raise ValueError("腾讯接口返回空数据")
    cutoff = start_date or (date.today() - timedelta(days=days))
    rows: List[Dict] = []
    for item in kline:
        # item: [日期, 开, 收, 高, 低, 成交量(手), ...]
        d = _as_date(item[0])
        if d < cutoff:
            continue
        rows.append(
            {
                "code": code,
                "trade_date": item[0],
                "open": float(item[1]),
                "close": float(item[2]),
                "high": float(item[3]),
                "low": float(item[4]),
                "volume": float(item[5]) if len(item) > 5 else 0.0,
                "amount": 0.0,
            }
        )
    if not rows:
        raise ValueError("腾讯接口无近期数据")
    return rows


def _fetch_stock_via_sina(code: str, start_date: Optional[date]) -> List[Dict]:
    """备用数据源 3：新浪财经日线（域名 hq.sinajs.cn / finance.sina.com.cn）。

    新浪的日 K 数据接口返回最近若干日 OHLC，作为 akshare/腾讯之外的第三重兜底，
    进一步提升「多渠道数据源接入」的真实可用性（不同域名，绕开单一源封锁）。
    """
    import requests

    symbol = code.split(".")[0]
    market = code.split(".")[-1].lower()
    prefix = "sh" if market == "sh" else "sz"
    secid = f"{prefix}{symbol}"
    days = max(settings.CRAWL_LOOKBACK_DAYS, 320)
    url = (
        "https://quotes.sina.cn/cn/api/json_v2.php/"
        f"CN_MarketDataService.getKLineData?symbol={secid}&scale=240&ma=no&datalen={days}"
    )
    resp = requests.get(
        url, timeout=settings.CRAWL_REQUEST_TIMEOUT,
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"},
    )
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise ValueError("新浪接口返回空数据")
    cutoff = start_date or (date.today() - timedelta(days=days))
    rows: List[Dict] = []
    for item in data:
        # item: {day, open, high, low, close, volume}
        d = _as_date(item["day"])
        if d < cutoff:
            continue
        rows.append(
            {
                "code": code,
                "trade_date": item["day"],
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
                "volume": float(item.get("volume", 0)),
                "amount": 0.0,
            }
        )
    if not rows:
        raise ValueError("新浪接口无近期数据")
    return rows


def _fetch_fund_via_akshare(code: str) -> List[Dict]:
    """用 akshare 获取基金净值，并只保留最近 CRAWL_LOOKBACK_DAYS 天。

    ETF（场内，如 510300）与开放式基金（如 110011）接口不同，按代码规则区分。
    新版签名：开放式 fund_open_fund_info_em(symbol, indicator)，ETF fund_etf_fund_info_em(fund,...)。
    akshare 基金接口返回全历史，这里在内存中裁剪到近窗口，避免存入过多老旧数据。
    """
    import akshare as ak

    cutoff = date.today() - timedelta(days=settings.CRAWL_LOOKBACK_DAYS)

    def _recent(rows: List[Dict]) -> List[Dict]:
        out = []
        for r in rows:
            try:
                d = _as_date(r["nav_date"])
            except Exception:  # noqa: BLE001
                continue
            if d >= cutoff:
                out.append(r)
        return out

    symbol = code.split(".")[0]
    # 5 开头多为场内 ETF/LOF，优先走 ETF 接口
    if symbol.startswith("5"):
        df = ak.fund_etf_fund_info_em(fund=symbol)
        if df is None or df.empty:
            raise ValueError("akshare 返回空数据")
        rows = []
        for _, r in df.iterrows():
            unit = r.get("单位净值") or r.get("基金份额净值")
            accum = r.get("累计净值", unit)
            rows.append(
                {"code": code, "nav_date": r["净值日期"], "unit_nav": unit, "accum_nav": accum}
            )
        return _recent(rows)

    df = ak.fund_open_fund_info_em(symbol=symbol, indicator="单位净值走势")
    if df is None or df.empty:
        raise ValueError("akshare 返回空数据")
    rows = []
    for _, r in df.iterrows():
        rows.append(
            {
                "code": code,
                "nav_date": r["净值日期"],
                "unit_nav": r["单位净值"],
                "accum_nav": r.get("累计净值", r["单位净值"]),
            }
        )
    return _recent(rows)


# ---------- 增量起点 ----------
def _latest_stock_date(db: Session, code: str) -> Optional[date]:
    return db.query(func.max(StockDaily.trade_date)).filter(StockDaily.code == code).scalar()


def _latest_fund_date(db: Session, code: str) -> Optional[date]:
    return db.query(func.max(FundNav.nav_date)).filter(FundNav.code == code).scalar()


# ---------- 单标的采集（含重试 + 多源兜底）----------
def _collect_one_stock(
    code: str, days: int, start_date: Optional[date]
) -> Tuple[List[Dict], str, int, str]:
    """返回 (rows, source, retries, fallback_reason)。

    数据源优先级：akshare(东财) → 腾讯财经 → 新浪财经 → 样例兜底。
    任一真实源成功即返回；全部失败才回退样例，并记录最后的失败原因。
    """
    code = cleaning.normalize_code(code, "stock")
    if not AKSHARE_AVAILABLE or settings.CRAWL_FORCE_SAMPLE:
        return sample_data.generate_stock_daily(code, days), "sample", 0, ""

    last_err = ""
    # 1) akshare（东方财富）—— 仅尝试 1 次，失败快速切换备用源，避免长时间重试
    try:
        rows, retries = _retry(
            lambda: _fetch_stock_via_akshare(code, start_date),
            attempts=1,
            base_delay=settings.CRAWL_RETRY_BASE_DELAY,
            label=f"股票 {code}/akshare",
        )
        return rows, "akshare", retries, ""
    except Exception as exc:  # noqa: BLE001
        last_err = f"akshare:{type(exc).__name__}"
        logger.warning("akshare 获取股票 %s 失败：%s，尝试腾讯源", code, exc)

    # 2) 腾讯财经（不同域名，绕开东财封锁/限流）
    try:
        rows = _fetch_stock_via_tencent(code, start_date)
        return rows, "tencent", 1, ""
    except Exception as exc:  # noqa: BLE001
        last_err = f"akshare+tencent 均失败({type(exc).__name__})"
        logger.warning("腾讯获取股票 %s 也失败：%s，尝试新浪源", code, exc)

    # 3) 新浪财经（第三重兜底，再换一个域名）
    try:
        rows = _fetch_stock_via_sina(code, start_date)
        return rows, "sina", 2, ""
    except Exception as exc:  # noqa: BLE001
        last_err = f"akshare+tencent+sina 均失败({type(exc).__name__})"
        logger.warning("新浪获取股票 %s 也失败：%s，回退样例数据", code, exc)

    # 4) 样例兜底
    if not settings.USE_SAMPLE_DATA_FALLBACK:
        raise RuntimeError(last_err)
    return sample_data.generate_stock_daily(code, days), "sample", settings.CRAWL_MAX_RETRIES - 1, last_err


def _collect_secondary_stock(code: str, start_date: Optional[date]) -> Tuple[List[Dict], str]:
    """采集副源股票数据用于跨源交叉验证（不入库，仅比对）。

    与主源不同的源：主源若为 akshare，副源用腾讯；否则用新浪。失败返回空。
    """
    code = cleaning.normalize_code(code, "stock")
    for fetch, name in ((_fetch_stock_via_tencent, "tencent"), (_fetch_stock_via_sina, "sina")):
        try:
            return fetch(code, start_date), name
        except Exception:  # noqa: BLE001
            continue
    return [], ""


def _collect_one_fund(code: str, days: int) -> Tuple[List[Dict], str, int, str]:
    code = cleaning.normalize_code(code, "fund")
    if not AKSHARE_AVAILABLE or settings.CRAWL_FORCE_SAMPLE:
        return sample_data.generate_fund_nav(code, days), "sample", 0, ""
    try:
        rows, retries = _retry(
            lambda: _fetch_fund_via_akshare(code),
            attempts=settings.CRAWL_MAX_RETRIES,
            base_delay=settings.CRAWL_RETRY_BASE_DELAY,
            label=f"基金 {code}",
        )
        return rows, "akshare", retries, ""
    except Exception as exc:  # noqa: BLE001
        logger.warning("akshare 获取基金 %s 最终失败：%s，回退样例数据", code, exc)
        if not settings.USE_SAMPLE_DATA_FALLBACK:
            raise
        reason = f"akshare:{type(exc).__name__}"
        return sample_data.generate_fund_nav(code, days), "sample", settings.CRAWL_MAX_RETRIES - 1, reason


def _upsert_instrument(db: Session, code: str, asset_type: str) -> None:
    """确保标的存在于主数据表，并补全行业分类。"""
    inst = db.query(Instrument).filter(Instrument.code == code).first()
    meta = next((i for i in sample_data.SAMPLE_INSTRUMENTS if i["code"] == code), None)
    category = meta["category"] if meta else cleaning.guess_industry(code)
    if inst:
        if not inst.category and category:
            inst.category = category
        return
    db.add(
        Instrument(
            code=code,
            name=meta["name"] if meta else code,
            asset_type=asset_type,
            market=meta["market"] if meta else code.split(".")[-1],
            category=category,
        )
    )


def _upsert_stock_rows(db: Session, rows: List[Dict], source: str) -> Tuple[int, int]:
    """返回 (新增行数, 更新行数)。"""
    inserted = updated = 0
    for row in rows:
        existing = (
            db.query(StockDaily)
            .filter(StockDaily.code == row["code"], StockDaily.trade_date == row["trade_date"])
            .first()
        )
        if existing:
            existing.open, existing.high, existing.low, existing.close = (
                row["open"], row["high"], row["low"], row["close"],
            )
            existing.volume, existing.amount, existing.pct_change = (
                row["volume"], row["amount"], row["pct_change"],
            )
            existing.source = source
            updated += 1
        else:
            db.add(StockDaily(**row, source=source))
            inserted += 1
    return inserted, updated


def _upsert_fund_rows(db: Session, rows: List[Dict], source: str) -> Tuple[int, int]:
    """返回 (新增行数, 更新行数)。"""
    inserted = updated = 0
    for row in rows:
        existing = (
            db.query(FundNav)
            .filter(FundNav.code == row["code"], FundNav.nav_date == row["nav_date"])
            .first()
        )
        if existing:
            existing.unit_nav, existing.accum_nav, existing.daily_return = (
                row["unit_nav"], row["accum_nav"], row["daily_return"],
            )
            existing.adj_nav = row.get("adj_nav", row["unit_nav"])
            existing.source = source
            updated += 1
        else:
            db.add(FundNav(**row, source=source))
            inserted += 1
    return inserted, updated


def crawl_stock_daily(
    db: Session, codes: List[str], days: int = 60, incremental: bool = False
) -> CrawlResult:
    """采集一批股票日线：抓取→清洗→入库→跨源校验。

    incremental=True 时只采集库中最新日期之后的数据（增量），否则全量。
    采集成功后会尝试用副源做跨源交叉验证，偏差超阈值则登记数据质量问题。
    """
    result = CrawlResult()
    sources = set()
    for code in codes:
        norm = cleaning.normalize_code(code, "stock")
        try:
            start = None
            if incremental:
                latest = _latest_stock_date(db, norm)
                if latest:
                    start = latest
            raw, source, retries, reason = _collect_one_stock(norm, days, start)
            result.retries += retries
            if reason:
                result.fallback_reasons.append(reason)
            cleaned = cleaning.clean_stock_daily(raw)
            _upsert_instrument(db, norm, "stock")
            ins, upd = _upsert_stock_rows(db, cleaned, source)
            result.rows_inserted += ins
            result.rows_updated += upd
            result.rows_affected += ins + upd
            sources.add(source)
            datasource_registry.record_hit(source)
            # 跨源交叉验证（仅对真实源，样例不验证）
            if source in ("akshare", "tencent", "sina") and cleaned:
                _cross_validate_stock(db, norm, cleaned, source, start)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"{norm}:{exc}")
    db.commit()
    # 缓存失效：采集后清理受影响标的的查询缓存，避免脏读
    for code in codes:
        cache.invalidate_prefix(f"stock:{cleaning.normalize_code(code, 'stock')}:")
    result.source = ",".join(sorted(sources)) or "none"
    result.status = _status_of(result, len(codes))
    return result


def _cross_validate_stock(
    db: Session, code: str, primary_cleaned: List[Dict], primary_source: str,
    start_date: Optional[date],
) -> None:
    """用副源做跨源交叉验证，偏差超阈值登记数据质量问题（激活原死桩函数）。"""
    try:
        secondary, sec_name = _collect_secondary_stock(code, start_date)
        if not secondary or sec_name == primary_source:
            return
        sec_cleaned = cleaning.clean_stock_daily(secondary)
        warnings = cleaning.cross_source_validate(
            primary_cleaned, sec_cleaned, price_key="close", date_key="trade_date",
        )
        if warnings:
            data_quality_service.record_issue(
                db,
                issue_type="cross_source",
                code=code,
                dataset="stock_daily",
                severity="warning",
                message=(
                    f"{primary_source} vs {sec_name} 收盘价偏差：" + "; ".join(warnings[:5])
                ),
                commit=False,
            )
    except Exception as exc:  # noqa: BLE001 - 校验失败不影响主采集
        logger.debug("跨源验证 %s 跳过：%s", code, exc)


def crawl_fund_nav(
    db: Session, codes: List[str], days: int = 60, incremental: bool = False
) -> CrawlResult:
    """采集一批基金净值：抓取→清洗→入库。"""
    result = CrawlResult()
    sources = set()
    for code in codes:
        norm = cleaning.normalize_code(code, "fund")
        try:
            raw, source, retries, reason = _collect_one_fund(norm, days)
            result.retries += retries
            if reason:
                result.fallback_reasons.append(reason)
            if incremental:
                latest = _latest_fund_date(db, norm)
                if latest:
                    raw = [r for r in raw if _as_date(r["nav_date"]) > latest]
            cleaned = cleaning.clean_fund_nav(raw)
            _upsert_instrument(db, norm, "fund")
            ins, upd = _upsert_fund_rows(db, cleaned, source)
            result.rows_inserted += ins
            result.rows_updated += upd
            result.rows_affected += ins + upd
            sources.add(source)
            datasource_registry.record_hit(source)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"{norm}:{exc}")
    db.commit()
    for code in codes:
        cache.invalidate_prefix(f"fund:{cleaning.normalize_code(code, 'fund')}:")
    result.source = ",".join(sorted(sources)) or "none"
    result.status = _status_of(result, len(codes))
    return result


def _as_date(value) -> date:
    """把字符串 / datetime / date 统一成 date，用于增量比较。"""
    if isinstance(value, date):
        return value
    import pandas as pd

    return pd.to_datetime(value).date()


def _status_of(result: CrawlResult, total: int) -> str:
    if not result.errors:
        return "success"
    if len(result.errors) >= total:
        return "failed"
    return "partial"



def _fetch_news_via_akshare(inst: Instrument) -> List[Dict]:
    """尝试通过 akshare 东方财富新闻接口获取个股新闻。

    网络、接口签名或数据为空时返回空列表，由调用方回退样例公告，保证演示不受外部源影响。
    """
    if not AKSHARE_AVAILABLE or settings.CRAWL_FORCE_SAMPLE:
        return []
    try:
        import akshare as ak

        fetch = getattr(ak, "stock_news_em", None)
        if fetch is None:
            return []
        symbol = inst.code.split(".")[0]
        df = fetch(symbol=symbol)
        if df is None or df.empty:
            return []
        rows: List[Dict] = []
        for _, r in df.head(8).iterrows():
            title = r.get("新闻标题") or r.get("标题") or r.get("title") or ""
            if not title:
                continue
            publish = r.get("发布时间") or r.get("时间") or r.get("date") or date.today()
            rows.append(
                {
                    "code": inst.code,
                    "title": str(title)[:256],
                    "category": "news",
                    "source": str(r.get("文章来源") or r.get("来源") or "东方财富新闻"),
                    "url": str(r.get("新闻链接") or r.get("链接") or ""),
                    "summary": str(r.get("新闻内容") or r.get("摘要") or title)[:500],
                    "sentiment": "neutral",
                    "publish_date": _as_date(publish),
                }
            )
        return rows
    except Exception as exc:  # noqa: BLE001 - 真实公告源失败不影响采集主链路
        logger.debug("akshare 新闻源 %s 跳过：%s", inst.code, exc)
        return []
def crawl_announcements(db: Session, codes: Optional[List[str]] = None) -> CrawlResult:
    """采集公开数据源：公告/新闻/舆情（模块1 公开数据源抓取）。

    课设环境用确定性样例兜底；架构上可替换为证监会/交易所公告抓取。
    幂等：同标的同标题不重复插入。
    """
    from app.models import Announcement

    result = CrawlResult()
    insts = db.query(Instrument).all()
    if codes:
        norm_set = {cleaning.normalize_code(c, "stock") for c in codes} | {
            cleaning.normalize_code(c, "fund") for c in codes
        }
        insts = [i for i in insts if i.code in norm_set]
    sources = set()
    for inst in insts:
        try:
            rows = _fetch_news_via_akshare(inst)
            if rows:
                sources.add("akshare-news")
            else:
                rows = sample_data.generate_announcements(inst.code, inst.name)
                sources.add("announcement-sample")
            for row in rows:
                exists = (
                    db.query(Announcement)
                    .filter(Announcement.title == row["title"])
                    .first()
                )
                if exists:
                    continue
                db.add(Announcement(**row))
                result.rows_affected += 1
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"{inst.code}:{exc}")
    db.commit()
    datasource_registry.record_hit("announcement")
    result.source = ",".join(sorted(sources)) or "announcement-sample"
    result.status = _status_of(result, len(insts) or 1)
    return result


