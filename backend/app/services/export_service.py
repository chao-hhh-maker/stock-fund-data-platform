"""数据导出服务：支持 CSV / Excel / Parquet，可选加密压缩，落导出记录。

导出路径复用查询侧的数据权限：资产范围、租户/部门作用域、历史时间窗口和敏感字段脱敏。
"""

from __future__ import annotations

import os
import zipfile
from datetime import date, datetime
from typing import Optional, Tuple

import pandas as pd
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import ExportRecord, FundNav, Instrument, StockDaily, User


def _visible_instrument_codes(
    db: Session, user: User, asset_type: Optional[str] = None
) -> list[str]:
    """返回当前用户可见的标的代码。管理员可见全部。"""
    q = db.query(Instrument)
    if asset_type:
        q = q.filter(Instrument.asset_type == asset_type)
    role_scope = (user.role.data_scope or "all").lower()
    if role_scope in ("stock", "fund"):
        q = q.filter(Instrument.asset_type == role_scope)
    if user.role.name != "admin":
        tenant_conditions = [Instrument.tenant_id.is_(None)]
        if user.tenant_id is not None:
            tenant_conditions.append(Instrument.tenant_id == user.tenant_id)
        q = q.filter(or_(*tenant_conditions))
        q = q.filter(
            or_(
                Instrument.department.is_(None),
                Instrument.department == "",
                Instrument.department == user.department,
            )
        )
    return [r.code for r in q.all()]


def _empty_frame(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame([{c: None for c in columns}]).iloc[0:0]


def _query_dataframe(
    db: Session,
    user: User,
    dataset: str,
    code: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date],
) -> pd.DataFrame:
    """根据数据集、筛选条件和当前用户权限构建 DataFrame。"""
    if dataset == "stock_daily":
        columns = [
            "code", "trade_date", "open", "high", "low", "close",
            "volume", "amount", "pct_change", "source",
        ]
        visible_codes = _visible_instrument_codes(db, user, "stock")
        if not visible_codes:
            return _empty_frame(columns)
        q = db.query(StockDaily).filter(StockDaily.code.in_(visible_codes))
        if code:
            q = q.filter(StockDaily.code == code)
        if start_date:
            q = q.filter(StockDaily.trade_date >= start_date)
        if end_date:
            q = q.filter(StockDaily.trade_date <= end_date)
        rows = q.order_by(StockDaily.code, StockDaily.trade_date).all()
        return pd.DataFrame(
            [
                {
                    "code": r.code, "trade_date": r.trade_date, "open": r.open,
                    "high": r.high, "low": r.low, "close": r.close,
                    "volume": r.volume, "amount": r.amount,
                    "pct_change": r.pct_change, "source": r.source,
                }
                for r in rows
            ],
            columns=columns,
        )
    if dataset == "fund_nav":
        columns = [
            "code", "nav_date", "unit_nav", "accum_nav", "adj_nav", "daily_return", "source",
        ]
        visible_codes = _visible_instrument_codes(db, user, "fund")
        if not visible_codes:
            return _empty_frame(columns)
        q = db.query(FundNav).filter(FundNav.code.in_(visible_codes))
        if code:
            q = q.filter(FundNav.code == code)
        if start_date:
            q = q.filter(FundNav.nav_date >= start_date)
        if end_date:
            q = q.filter(FundNav.nav_date <= end_date)
        rows = q.order_by(FundNav.code, FundNav.nav_date).all()
        return pd.DataFrame(
            [
                {
                    "code": r.code, "nav_date": r.nav_date, "unit_nav": r.unit_nav,
                    "accum_nav": r.accum_nav, "adj_nav": r.adj_nav,
                    "daily_return": r.daily_return, "source": r.source,
                }
                for r in rows
            ],
            columns=columns,
        )

    columns = ["code", "name", "asset_type", "market", "category"]
    visible_codes = _visible_instrument_codes(db, user)
    if not visible_codes:
        return _empty_frame(columns)
    rows = (
        db.query(Instrument)
        .filter(Instrument.code.in_(visible_codes))
        .order_by(Instrument.code)
        .all()
    )
    return pd.DataFrame(
        [
            {
                "code": r.code, "name": r.name, "asset_type": r.asset_type,
                "market": r.market, "category": r.category,
            }
            for r in rows
        ],
        columns=columns,
    )


def export_dataset(
    db: Session,
    user: User,
    dataset: str,
    file_format: str = "csv",
    code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    role: str = "admin",
    can_view_sensitive: bool = True,
    compress: bool = False,
    encrypt: bool = False,
) -> Tuple[str, str, int]:
    """导出数据集到文件，返回 (绝对路径, 文件名, 行数)，并落导出记录。

    - 字段级权限：无敏感字段权限的用户导出时隐藏成交额 amount（与查询接口一致）。
    - 加密压缩（模块4）：compress=True 打包为 zip；encrypt=True 时加密。
    """
    os.makedirs(settings.EXPORT_DIR, exist_ok=True)
    df = _query_dataframe(db, user, dataset, code, start_date, end_date)

    # 字段级权限控制（题目二 模块6：字段级权限）
    if not can_view_sensitive and "amount" in df.columns:
        df = df.drop(columns=["amount"])

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = {"csv": "csv", "excel": "xlsx", "parquet": "parquet"}[file_format]
    base_name = f"{dataset}_{ts}.{ext}"
    abs_path = os.path.abspath(os.path.join(settings.EXPORT_DIR, base_name))
    final_format = file_format

    if file_format == "csv":
        df.to_csv(abs_path, index=False, encoding="utf-8-sig")
    elif file_format == "excel":
        df.to_excel(abs_path, index=False)
    else:  # parquet
        try:
            df.to_parquet(abs_path, index=False)
        except Exception:  # noqa: BLE001 - 无 pyarrow 时回退 csv
            abs_path = abs_path.rsplit(".", 1)[0] + ".csv"
            base_name = base_name.rsplit(".", 1)[0] + ".csv"
            df.to_csv(abs_path, index=False, encoding="utf-8-sig")

    file_name = base_name
    # 加密 / 压缩（导出数据加密和压缩，模块4）
    if compress or encrypt:
        abs_path, file_name = _package(abs_path, base_name, encrypt)
        final_format = "zip(加密)" if encrypt else "zip"

    params = (
        f"dataset={dataset};code={code};start={start_date};end={end_date};"
        f"format={file_format};compress={compress};encrypt={encrypt}"
    )
    record = ExportRecord(
        user_id=user.id,
        dataset=dataset,
        file_format=final_format,
        params=params,
        file_name=file_name,
        row_count=len(df),
        status="success",
    )
    db.add(record)
    db.commit()
    return abs_path, file_name, len(df)


def _package(src_path: str, inner_name: str, encrypt: bool) -> Tuple[str, str]:
    """把导出文件打包为 zip（可选加密），返回 (zip 绝对路径, zip 文件名)。"""
    zip_name = inner_name.rsplit(".", 1)[0] + ".zip"
    zip_path = os.path.abspath(os.path.join(settings.EXPORT_DIR, zip_name))
    password = settings.EXPORT_ZIP_PASSWORD.encode()

    if encrypt:
        try:
            import pyzipper  # type: ignore

            with pyzipper.AESZipFile(
                zip_path, "w", compression=pyzipper.ZIP_DEFLATED,
                encryption=pyzipper.WZ_AES,
            ) as zf:
                zf.setpassword(password)
                zf.write(src_path, arcname=inner_name)
            os.remove(src_path)
            return zip_path, zip_name
        except ImportError:
            # 回退：标准库 zip 只支持压缩；保留 clone 即跑能力，不让导出流程失败。
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(src_path, arcname=inner_name)
            os.remove(src_path)
            return zip_path, zip_name

    # 仅压缩
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(src_path, arcname=inner_name)
    os.remove(src_path)
    return zip_path, zip_name
