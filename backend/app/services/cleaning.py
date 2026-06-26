"""数据清洗与标准化服务。

对应题目二「模块 2：数据清洗与标准化」：
- 缺失值处理
- 异常值校验
- 证券代码标准化（新旧 / 带后缀 / 不带后缀统一）
- 衍生字段计算（涨跌幅、日增长率）
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List


def _to_date(value):
    """把字符串 / datetime / pandas.Timestamp 统一转换为 date 对象。

    不同数据源日期格式不一（akshare 返回 date，腾讯返回字符串），
    入库前统一，避免 SQLite「只接受 date 对象」的报错。
    """
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    # 字符串或其它：交给 pandas 解析（兼容 2025-05-19 / 20250519 等）
    try:
        import pandas as pd

        ts = pd.to_datetime(value)
        return ts.date()
    except Exception:  # noqa: BLE001
        return None


def normalize_code(raw: str, asset_type: str = "stock") -> str:
    """统一证券代码格式为 `数字.市场后缀`。

    规则（简化但实用）：
    - 已含 .SH/.SZ/.OF 等后缀的，统一为大写后缀。
    - 6 位纯数字股票：6/9 开头 → .SH，0/3 开头 → .SZ。
    - 基金（asset_type=fund）默认补 .OF 后缀。

    示例：
        sh600519 -> 600519.SH
        600519   -> 600519.SH
        000001   -> 000001.SZ
        510300   -> 510300.OF (fund)
    """
    code = raw.strip().upper().replace(" ", "")
    if not code:
        return code

    # 处理 sh600519 / sz000001 前缀写法
    if code.startswith("SH") and code[2:].isdigit():
        return f"{code[2:]}.SH"
    if code.startswith("SZ") and code[2:].isdigit():
        return f"{code[2:]}.SZ"

    if "." in code:
        num, _, suffix = code.partition(".")
        return f"{num}.{suffix}"

    if code.isdigit():
        if asset_type == "fund":
            return f"{code}.OF"
        if code[0] in ("6", "9"):
            return f"{code}.SH"
        if code[0] in ("0", "3"):
            return f"{code}.SZ"
    return code


def clean_stock_daily(rows: List[Dict]) -> List[Dict]:
    """清洗股票日线数据。

    - 丢弃缺少关键价格字段或非正价格的异常行
    - 价格四舍五入到 2 位
    - 计算 pct_change（基于前一交易日收盘价）
    """
    cleaned: List[Dict] = []
    rows = [r for r in rows if r.get("trade_date") is not None]
    # 统一日期为 date 对象（兼容不同数据源的字符串/Timestamp）
    for r in rows:
        r["trade_date"] = _to_date(r["trade_date"])
    rows = [r for r in rows if r["trade_date"] is not None]
    rows.sort(key=lambda r: r["trade_date"])

    prev_close = None
    for row in rows:
        close = row.get("close")
        # 异常值校验：价格缺失或非正数则跳过
        if close is None or _is_invalid(close):
            continue
        for field in ("open", "high", "low", "close"):
            val = row.get(field)
            row[field] = round(float(val), 2) if val is not None and not _is_invalid(val) else round(float(close), 2)

        row["volume"] = max(float(row.get("volume") or 0), 0)
        row["amount"] = max(float(row.get("amount") or 0), 0)

        # 价格一致性校验（金融逻辑）：high 应≥max(open,close)，low 应≤min(open,close)。
        # 修正越界的 high/low，保证 OHLC 自洽，避免 K 线显示异常。
        row["high"] = max(row["high"], row["open"], row["close"])
        row["low"] = min(row["low"], row["open"], row["close"])

        if prev_close and prev_close > 0:
            row["pct_change"] = round((row["close"] - prev_close) / prev_close * 100, 2)
        else:
            row["pct_change"] = 0.0
        prev_close = row["close"]
        cleaned.append(row)
    return cleaned


def clean_fund_nav(rows: List[Dict]) -> List[Dict]:
    """清洗基金净值数据。

    - 丢弃净值缺失 / 非正的异常行
    - 计算 daily_return（基于前一日单位净值）
    - 计算复权净值 adj_nav（分红再投资假设，模块2 基金净值复权）

    复权逻辑：以累计净值的增量反映分红，复权净值在首日对齐单位净值后，
    按"单位净值日收益 + 分红再投"累乘推进，近似分红再投资的真实收益曲线。
    """
    cleaned: List[Dict] = []
    rows = [r for r in rows if r.get("nav_date") is not None]
    for r in rows:
        r["nav_date"] = _to_date(r["nav_date"])
    rows = [r for r in rows if r["nav_date"] is not None]
    rows.sort(key=lambda r: r["nav_date"])

    prev_unit = None
    prev_accum = None
    adj = None  # 复权净值
    for row in rows:
        unit = row.get("unit_nav")
        if unit is None or _is_invalid(unit):
            continue
        row["unit_nav"] = round(float(unit), 4)
        accum = row.get("accum_nav")
        row["accum_nav"] = round(float(accum), 4) if accum is not None and not _is_invalid(accum) else row["unit_nav"]

        if prev_unit and prev_unit > 0:
            row["daily_return"] = round((row["unit_nav"] - prev_unit) / prev_unit * 100, 2)
            # 复权净值：单位净值涨跌 + 累计净值增量中超出单位净值变化的部分（即分红）
            unit_growth = (row["unit_nav"] - prev_unit) / prev_unit
            div = 0.0
            if prev_accum is not None:
                accum_change = row["accum_nav"] - prev_accum
                unit_change = row["unit_nav"] - prev_unit
                # 分红 = 累计净值变化 - 单位净值变化（仅取正向部分，避免噪声）
                div = max(accum_change - unit_change, 0.0)
            div_ratio = div / prev_unit if prev_unit > 0 else 0.0
            adj = round(adj * (1 + unit_growth + div_ratio), 4)
        else:
            row["daily_return"] = 0.0
            adj = row["unit_nav"]
        row["adj_nav"] = adj
        prev_unit = row["unit_nav"]
        prev_accum = row["accum_nav"]
        cleaned.append(row)
    return cleaned


def _is_invalid(value) -> bool:
    """判断数值是否为无效（NaN / inf / 非正）。"""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return True
    if f != f:  # NaN
        return True
    if f in (float("inf"), float("-inf")):
        return True
    return f <= 0


# ---------- 行业分类映射（支持申万 / 中信 / GICS 三套标准）----------
# 模块2「行业分类统一（申万、中信、GICS 等分类映射）」。
# 主映射按申万一级，并提供到中信、GICS 的对照，实现一码多标准归类。
_INDUSTRY_MAP: Dict[str, str] = {
    "600519": "食品饮料", "000858": "食品饮料", "600887": "食品饮料",
    "603288": "食品饮料", "161725": "食品饮料",
    "601318": "非银金融", "600030": "非银金融",
    "000001": "银行", "600036": "银行", "601398": "银行",
    "300750": "电力设备", "601012": "电力设备",
    "002594": "汽车",
    "600276": "医药生物", "300760": "医药生物", "603259": "医药生物",
    "000333": "家用电器", "000651": "家用电器",
    "002415": "电子", "600703": "电子", "688981": "电子",
    "002230": "计算机",
    "600900": "公用事业", "601888": "商贸零售", "002714": "农林牧渔",
    "601857": "石油石化", "600028": "石油石化", "601088": "煤炭",
    "600585": "建筑材料", "601899": "有色金属", "600009": "交通运输",
}

# 申万一级 → 中信一级（简化对照）
_SW_TO_CITIC: Dict[str, str] = {
    "食品饮料": "食品饮料", "非银金融": "非银行金融", "银行": "银行",
    "电力设备": "电力设备及新能源", "汽车": "汽车", "医药生物": "医药",
    "家用电器": "家电", "电子": "电子", "计算机": "计算机",
    "公用事业": "电力及公用事业", "商贸零售": "商贸零售", "农林牧渔": "农林牧渔",
    "石油石化": "石油石化", "煤炭": "煤炭", "建筑材料": "建材",
    "有色金属": "有色金属", "交通运输": "交通运输",
}

# 申万一级 → GICS 板块（简化对照）
_SW_TO_GICS: Dict[str, str] = {
    "食品饮料": "Consumer Staples", "非银金融": "Financials", "银行": "Financials",
    "电力设备": "Industrials", "汽车": "Consumer Discretionary", "医药生物": "Health Care",
    "家用电器": "Consumer Discretionary", "电子": "Information Technology",
    "计算机": "Information Technology", "公用事业": "Utilities",
    "商贸零售": "Consumer Discretionary", "农林牧渔": "Consumer Staples",
    "石油石化": "Energy", "煤炭": "Energy", "建筑材料": "Materials",
    "有色金属": "Materials", "交通运输": "Industrials",
}


def guess_industry(code: str, standard: str = "sw") -> str:
    """根据证券代码推断行业分类。

    standard: sw(申万一级，默认) / citic(中信) / gics(GICS 板块)。
    先按申万一级归类，再按所选标准做映射，实现「行业分类统一」。
    """
    num = code.split(".")[0]
    sw = _INDUSTRY_MAP.get(num)
    if sw is None:
        if num.startswith("5") or num.startswith("159") or num.startswith("588"):
            sw = "场内基金"
        elif num.startswith(("0", "3")):
            sw = "深市股票"
        elif num.startswith(("6", "9")):
            sw = "沪市股票"
        else:
            sw = "其他"
    if standard == "citic":
        return _SW_TO_CITIC.get(sw, sw)
    if standard == "gics":
        return _SW_TO_GICS.get(sw, sw)
    return sw


def industry_all_standards(code: str) -> Dict[str, str]:
    """返回某标的在三套标准下的分类，用于元数据/前端展示。"""
    return {
        "sw": guess_industry(code, "sw"),
        "citic": guess_industry(code, "citic"),
        "gics": guess_industry(code, "gics"),
    }


def cross_source_validate(
    primary: List[Dict], secondary: List[Dict], price_key: str, date_key: str,
    tolerance: float = 0.05,
) -> List[str]:
    """跨数据源交叉验证：比较两个数据源同一日期的价格偏差。

    返回偏差超过容忍度（默认 5%）的日期告警列表，用于数据质量监控。
    主源为准，副源用于校验。
    """
    sec_map = {str(r[date_key]): r[price_key] for r in secondary if r.get(price_key)}
    warnings: List[str] = []
    for r in primary:
        d = str(r.get(date_key))
        pv = r.get(price_key)
        sv = sec_map.get(d)
        if pv and sv and sv > 0:
            deviation = abs(pv - sv) / sv
            if deviation > tolerance:
                warnings.append(f"{d}: 偏差 {deviation:.1%}")
    return warnings

