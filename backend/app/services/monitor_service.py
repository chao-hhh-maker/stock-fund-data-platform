"""数据监控与运维服务。

对应题目二「模块 5：数据监控与运维」：
- 数据完整性检查（交易日缺口检测，节假日感知）
- 关键字段异常监测
- 系统健康指标（存储、采集成功率、缓存命中率）
- 告警中心（数据延迟 / 采集失败 / 数据缺口）
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import date, datetime, timedelta
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.cache import cache
from app.core.config import settings
from app.models import (
    AlertRecord,
    CrawlRun,
    DataQualityIssue,
    ExportRecord,
    FundNav,
    Instrument,
    StockDaily,
)
from app.services import calendar_service

logger = logging.getLogger("monitor_service")


def check_integrity(db: Session, lookback_days: int = 30) -> List[Dict]:
    """检查每个标的近 N 天的数据完整性（交易日缺口）。"""
    end = date.today()
    start = end - timedelta(days=lookback_days)
    expected = calendar_service.expected_trading_days(start, end)
    report: List[Dict] = []

    instruments = db.query(Instrument).all()
    for inst in instruments:
        if inst.asset_type == "stock":
            actual = (
                db.query(func.count(func.distinct(StockDaily.trade_date)))
                .filter(
                    StockDaily.code == inst.code,
                    StockDaily.trade_date >= start,
                    StockDaily.trade_date <= end,
                )
                .scalar()
            ) or 0
            latest = (
                db.query(func.max(StockDaily.trade_date))
                .filter(StockDaily.code == inst.code)
                .scalar()
            )
        else:
            actual = (
                db.query(func.count(func.distinct(FundNav.nav_date)))
                .filter(
                    FundNav.code == inst.code,
                    FundNav.nav_date >= start,
                    FundNav.nav_date <= end,
                )
                .scalar()
            ) or 0
            latest = (
                db.query(func.max(FundNav.nav_date)).filter(FundNav.code == inst.code).scalar()
            )

        # 基金净值披露可能滞后，完整率以较宽口径计算
        completeness = round(min(actual / expected, 1.0) * 100, 1) if expected else 100.0
        delay_days = (end - latest).days if latest else None
        report.append(
            {
                "code": inst.code,
                "name": inst.name,
                "asset_type": inst.asset_type,
                "expected": expected,
                "actual": actual,
                "completeness": completeness,
                "latest": str(latest) if latest else None,
                "delay_days": delay_days,
            }
        )
    return sorted(report, key=lambda x: x["completeness"])


def build_alerts(db: Session, integrity: List[Dict]) -> List[Dict]:
    """根据完整性与采集记录生成告警列表。"""
    alerts: List[Dict] = []

    # 数据缺口告警
    for item in integrity:
        if item["completeness"] < 80:
            alerts.append(
                {
                    "level": "warning",
                    "type": "数据缺口",
                    "target": f"{item['name']}({item['code']})",
                    "message": f"近期数据完整率仅 {item['completeness']}%（{item['actual']}/{item['expected']}）",
                }
            )
        if item["delay_days"] is not None and item["delay_days"] > 7:
            alerts.append(
                {
                    "level": "warning",
                    "type": "数据延迟",
                    "target": f"{item['name']}({item['code']})",
                    "message": f"最新数据距今 {item['delay_days']} 天，可能未及时更新",
                }
            )

    # 采集失败告警
    failed_runs = (
        db.query(CrawlRun)
        .filter(CrawlRun.status.in_(["failed", "partial"]))
        .order_by(CrawlRun.started_at.desc())
        .limit(10)
        .all()
    )
    for run in failed_runs:
        alerts.append(
            {
                "level": "error" if run.status == "failed" else "warning",
                "type": "采集异常",
                "target": f"任务#{run.job_id} 运行#{run.id}",
                "message": run.message or run.status,
            }
        )
    return alerts


def detect_anomalies(db: Session, lookback_days: int = 30) -> List[Dict]:
    """关键字段异常监测（模块5）：单日涨跌幅异常、成交量突变、净值断崖。

    返回异常列表，并登记为 DataQualityIssue（issue_type=anomaly）。
    """
    from app.services import data_quality_service

    end = date.today()
    start = end - timedelta(days=lookback_days)
    anomalies: List[Dict] = []
    pct_threshold = settings.ANOMALY_PCT_CHANGE_THRESHOLD
    vol_ratio = settings.ANOMALY_VOLUME_RATIO

    stock_codes = [r[0] for r in db.query(StockDaily.code).distinct().all()]
    for code in stock_codes:
        rows = (
            db.query(StockDaily)
            .filter(StockDaily.code == code, StockDaily.trade_date >= start)
            .order_by(StockDaily.trade_date)
            .all()
        )
        if not rows:
            continue
        vols = [r.volume for r in rows if r.volume]
        avg_vol = sum(vols) / len(vols) if vols else 0
        for r in rows:
            # 涨跌幅异常（排除涨跌停附近的正常 ±10%）
            if abs(r.pct_change) >= pct_threshold:
                anomalies.append({
                    "level": "warning", "type": "涨跌幅异常",
                    "target": f"{code} {r.trade_date}",
                    "message": f"单日涨跌幅 {r.pct_change}% 超过阈值 {pct_threshold}%",
                })
            # 成交量突变
            if avg_vol and r.volume > avg_vol * vol_ratio:
                anomalies.append({
                    "level": "info", "type": "成交量突变",
                    "target": f"{code} {r.trade_date}",
                    "message": f"成交量 {r.volume:.0f} 超过近期均值 {vol_ratio} 倍（均值 {avg_vol:.0f}）",
                })

    fund_codes = [r[0] for r in db.query(FundNav.code).distinct().all()]
    for code in fund_codes:
        rows = (
            db.query(FundNav)
            .filter(FundNav.code == code, FundNav.nav_date >= start)
            .order_by(FundNav.nav_date)
            .all()
        )
        for r in rows:
            if abs(r.daily_return) >= pct_threshold:
                anomalies.append({
                    "level": "warning", "type": "净值断崖",
                    "target": f"{code} {r.nav_date}",
                    "message": f"单日净值变动 {r.daily_return}% 异常",
                })

    # 登记到数据质量问题表（去重）
    for a in anomalies[:50]:
        code = a["target"].split(" ")[0]
        data_quality_service.record_issue(
            db, issue_type="anomaly", code=code,
            dataset="stock_daily" if "涨跌" in a["type"] or "成交" in a["type"] else "fund_nav",
            severity=a["level"], message=f"{a['type']}：{a['message']}",
            commit=False, dedup=True,
        )
    db.commit()
    return anomalies


def _alert_fingerprint(alert: Dict) -> str:
    raw = "|".join(
        str(alert.get(k, "")) for k in ("level", "type", "target", "message")
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def dispatch_alerts(db: Session, alerts: List[Dict]) -> int:
    """告警分发（模块5）：去重落库 AlertRecord，并 best-effort 推送到 webhook。

    同一指纹且 status=open 的告警不会重复插入；会更新时间和消息，避免监控页每刷新一次
    历史记录就膨胀一批。返回新落库的告警条数。
    """
    saved = 0
    webhook = settings.ALERT_WEBHOOK_URL.strip()
    new_records: List[AlertRecord] = []
    for a in alerts:
        fp = _alert_fingerprint(a)
        existing = (
            db.query(AlertRecord)
            .filter(AlertRecord.fingerprint == fp, AlertRecord.status == "open")
            .first()
        )
        if existing:
            existing.level = a.get("level", existing.level)
            existing.alert_type = a.get("type", existing.alert_type)
            existing.target = a.get("target", existing.target)
            existing.message = a.get("message", existing.message)
            continue
        rec = AlertRecord(
            level=a.get("level", "warning"),
            alert_type=a.get("type", ""),
            target=a.get("target", ""),
            message=a.get("message", ""),
            fingerprint=fp,
            status="open",
            dispatch_status="pending" if webhook else "skipped",
        )
        db.add(rec)
        new_records.append(rec)
        saved += 1
    db.commit()

    if webhook and new_records:
        alerts_to_send = [
            {
                "level": r.level,
                "type": r.alert_type,
                "target": r.target,
                "message": r.message,
            }
            for r in new_records[:20]
        ]
        try:
            import requests

            resp = requests.post(
                webhook,
                json={"source": "stock-fund-platform", "count": len(new_records), "alerts": alerts_to_send},
                timeout=5,
            )
            new_status = "sent" if resp.ok else "failed"
        except Exception as exc:  # noqa: BLE001 - 分发失败不影响主流程
            logger.warning("告警 webhook 推送失败：%s", exc)
            new_status = "failed"
        for r in new_records:
            r.dispatch_status = new_status
        db.commit()
    return saved


def list_alert_records(
    db: Session, page: int = 1, page_size: int = 20, status: str | None = None
) -> tuple[List[AlertRecord], int]:
    q = db.query(AlertRecord)
    if status:
        q = q.filter(AlertRecord.status == status)
    q = q.order_by(AlertRecord.id.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def resolve_alert(
    db: Session, alert_id: int, status: str, note: str, resolved_by: str
) -> AlertRecord | None:
    alert = db.query(AlertRecord).filter(AlertRecord.id == alert_id).first()
    if not alert:
        return None
    alert.status = status
    if status in ("resolved", "ignored"):
        alert.resolved_by = resolved_by
        alert.resolved_note = note
        alert.resolved_at = datetime.now()
    elif status == "open":
        alert.resolved_by = ""
        alert.resolved_note = ""
        alert.resolved_at = None
    db.commit()
    db.refresh(alert)
    return alert


def system_metrics(db: Session) -> Dict:
    """系统运行指标：存储、采集成功率、缓存命中率。"""
    total_runs = db.query(func.count(CrawlRun.id)).scalar() or 0
    success_runs = (
        db.query(func.count(CrawlRun.id)).filter(CrawlRun.status == "success").scalar()
    ) or 0
    success_rate = round(success_runs / total_runs * 100, 1) if total_runs else 100.0

    # 估算数据库文件大小（SQLite）
    db_size_mb = None
    try:
        from app.core.config import settings

        if settings.is_sqlite:
            path = settings.DATABASE_URL.replace("sqlite:///", "").lstrip("./")
            if os.path.exists(path):
                db_size_mb = round(os.path.getsize(path) / 1024 / 1024, 2)
    except Exception:  # noqa: BLE001
        db_size_mb = None

    return {
        "total_runs": total_runs,
        "success_runs": success_runs,
        "crawl_success_rate": success_rate,
        "stock_daily_rows": db.query(func.count(StockDaily.id)).scalar() or 0,
        "fund_nav_rows": db.query(func.count(FundNav.id)).scalar() or 0,
        "export_count": db.query(func.count(ExportRecord.id)).scalar() or 0,
        "db_size_mb": db_size_mb,
        "cache": cache.stats(),
        "checked_at": datetime.now(),
    }




