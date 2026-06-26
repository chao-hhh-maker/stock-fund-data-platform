"""内置样例数据生成器。

当外部数据源（akshare 等）不可用或处于离线 / 答辩环境时，
回退到确定性的样例数据生成器，保证「克隆即可演示完整链路」。

样例数据基于固定随机种子生成，具备可复现性；价格走势用随机游走模拟，
贴近真实行情形态，便于前端图表演示。
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Dict, List

# 预置标的：覆盖沪深主要行业龙头股票与各类基金，便于演示
SAMPLE_INSTRUMENTS: List[Dict] = [
    # —— 白酒 / 食品饮料 ——
    {"code": "600519.SH", "name": "贵州茅台", "asset_type": "stock", "market": "SH", "category": "食品饮料"},
    {"code": "000858.SZ", "name": "五粮液", "asset_type": "stock", "market": "SZ", "category": "食品饮料"},
    {"code": "600887.SH", "name": "伊利股份", "asset_type": "stock", "market": "SH", "category": "食品饮料"},
    # —— 金融 ——
    {"code": "601318.SH", "name": "中国平安", "asset_type": "stock", "market": "SH", "category": "非银金融"},
    {"code": "600036.SH", "name": "招商银行", "asset_type": "stock", "market": "SH", "category": "银行"},
    {"code": "000001.SZ", "name": "平安银行", "asset_type": "stock", "market": "SZ", "category": "银行"},
    {"code": "601398.SH", "name": "工商银行", "asset_type": "stock", "market": "SH", "category": "银行"},
    {"code": "600030.SH", "name": "中信证券", "asset_type": "stock", "market": "SH", "category": "非银金融"},
    # —— 新能源 / 电力设备 ——
    {"code": "300750.SZ", "name": "宁德时代", "asset_type": "stock", "market": "SZ", "category": "电力设备"},
    {"code": "002594.SZ", "name": "比亚迪", "asset_type": "stock", "market": "SZ", "category": "汽车"},
    {"code": "601012.SH", "name": "隆基绿能", "asset_type": "stock", "market": "SH", "category": "电力设备"},
    # —— 医药 ——
    {"code": "600276.SH", "name": "恒瑞医药", "asset_type": "stock", "market": "SH", "category": "医药生物"},
    {"code": "300760.SZ", "name": "迈瑞医疗", "asset_type": "stock", "market": "SZ", "category": "医药生物"},
    {"code": "603259.SH", "name": "药明康德", "asset_type": "stock", "market": "SH", "category": "医药生物"},
    # —— 科技 / 电子 ——
    {"code": "002415.SZ", "name": "海康威视", "asset_type": "stock", "market": "SZ", "category": "电子"},
    {"code": "002230.SZ", "name": "科大讯飞", "asset_type": "stock", "market": "SZ", "category": "计算机"},
    {"code": "600703.SH", "name": "三安光电", "asset_type": "stock", "market": "SH", "category": "电子"},
    {"code": "688981.SH", "name": "中芯国际", "asset_type": "stock", "market": "SH", "category": "电子"},
    # —— 家电 ——
    {"code": "000333.SZ", "name": "美的集团", "asset_type": "stock", "market": "SZ", "category": "家用电器"},
    {"code": "000651.SZ", "name": "格力电器", "asset_type": "stock", "market": "SZ", "category": "家用电器"},
    # —— 消费 / 互联网 ——
    {"code": "600900.SH", "name": "长江电力", "asset_type": "stock", "market": "SH", "category": "公用事业"},
    {"code": "601888.SH", "name": "中国中免", "asset_type": "stock", "market": "SH", "category": "商贸零售"},
    {"code": "603288.SH", "name": "海天味业", "asset_type": "stock", "market": "SH", "category": "食品饮料"},
    {"code": "002714.SZ", "name": "牧原股份", "asset_type": "stock", "market": "SZ", "category": "农林牧渔"},
    # —— 能源 / 材料 ——
    {"code": "601857.SH", "name": "中国石油", "asset_type": "stock", "market": "SH", "category": "石油石化"},
    {"code": "600028.SH", "name": "中国石化", "asset_type": "stock", "market": "SH", "category": "石油石化"},
    {"code": "601088.SH", "name": "中国神华", "asset_type": "stock", "market": "SH", "category": "煤炭"},
    {"code": "600585.SH", "name": "海螺水泥", "asset_type": "stock", "market": "SH", "category": "建筑材料"},
    {"code": "601899.SH", "name": "紫金矿业", "asset_type": "stock", "market": "SH", "category": "有色金属"},
    {"code": "600009.SH", "name": "上海机场", "asset_type": "stock", "market": "SH", "category": "交通运输"},

    # —— 宽基指数基金 ——
    {"code": "510300.OF", "name": "沪深300ETF", "asset_type": "fund", "market": "OF", "category": "宽基指数"},
    {"code": "510050.OF", "name": "上证50ETF", "asset_type": "fund", "market": "OF", "category": "宽基指数"},
    {"code": "159919.OF", "name": "嘉实沪深300ETF", "asset_type": "fund", "market": "OF", "category": "宽基指数"},
    {"code": "510500.OF", "name": "中证500ETF", "asset_type": "fund", "market": "OF", "category": "宽基指数"},
    {"code": "588000.OF", "name": "科创50ETF", "asset_type": "fund", "market": "OF", "category": "宽基指数"},
    # —— 行业指数基金 ——
    {"code": "161725.OF", "name": "招商中证白酒", "asset_type": "fund", "market": "OF", "category": "行业指数"},
    {"code": "512880.OF", "name": "证券ETF", "asset_type": "fund", "market": "OF", "category": "行业指数"},
    {"code": "512170.OF", "name": "医疗ETF", "asset_type": "fund", "market": "OF", "category": "行业指数"},
    {"code": "515030.OF", "name": "新能源车ETF", "asset_type": "fund", "market": "OF", "category": "行业指数"},
    {"code": "512480.OF", "name": "半导体ETF", "asset_type": "fund", "market": "OF", "category": "行业指数"},
    # —— 主动 / 混合 / 债券 ——
    {"code": "110011.OF", "name": "易方达中小盘", "asset_type": "fund", "market": "OF", "category": "混合型"},
    {"code": "161005.OF", "name": "富国天惠成长", "asset_type": "fund", "market": "OF", "category": "混合型"},
    {"code": "001714.OF", "name": "工银瑞信文体产业", "asset_type": "fund", "market": "OF", "category": "混合型"},
    {"code": "000961.OF", "name": "天弘沪深300", "asset_type": "fund", "market": "OF", "category": "宽基指数"},
    {"code": "100038.OF", "name": "富国天利增长债券", "asset_type": "fund", "market": "OF", "category": "债券型"},
    {"code": "050026.OF", "name": "博时信用债券", "asset_type": "fund", "market": "OF", "category": "债券型"},
]

# 每个标的的基准价格，使随机游走有合理起点（未列出的按默认值）
_BASE_PRICE: Dict[str, float] = {
    "600519.SH": 1680.0, "000858.SZ": 150.0, "600887.SH": 28.0,
    "601318.SH": 48.0, "600036.SH": 36.0, "000001.SZ": 11.5,
    "601398.SH": 5.6, "600030.SH": 22.0,
    "300750.SZ": 190.0, "002594.SZ": 240.0, "601012.SH": 22.0,
    "600276.SH": 48.0, "300760.SZ": 280.0, "603259.SH": 65.0,
    "002415.SZ": 32.0, "002230.SZ": 45.0, "600703.SH": 14.0, "688981.SH": 55.0,
    "000333.SZ": 68.0, "000651.SZ": 38.0,
    "600900.SH": 28.0, "601888.SH": 95.0, "603288.SH": 42.0, "002714.SZ": 45.0,
    "601857.SH": 8.5, "600028.SH": 6.2, "601088.SH": 38.0,
    "600585.SH": 25.0, "601899.SH": 16.0, "600009.SH": 40.0,
    # 基金
    "510300.OF": 3.85, "510050.OF": 2.75, "159919.OF": 3.90, "510500.OF": 6.20, "588000.OF": 1.05,
    "161725.OF": 1.05, "512880.OF": 0.95, "512170.OF": 0.48, "515030.OF": 1.35, "512480.OF": 0.85,
    "110011.OF": 6.20, "161005.OF": 3.20, "001714.OF": 2.80, "000961.OF": 1.85,
    "100038.OF": 1.45, "050026.OF": 1.12,
}


def _trading_days(days: int, end: date | None = None) -> List[date]:
    """生成最近 N 个工作日（跳过周末，简化处理，不含节假日）。"""
    end = end or date.today()
    result: List[date] = []
    cursor = end
    while len(result) < days:
        if cursor.weekday() < 5:  # 0-4 为周一至周五
            result.append(cursor)
        cursor -= timedelta(days=1)
    return list(reversed(result))


def _seeded_rng(code: str) -> random.Random:
    """按代码生成确定性随机源，保证样例数据可复现。"""
    return random.Random(hash(code) & 0xFFFFFFFF)


def generate_stock_daily(code: str, days: int = 60) -> List[Dict]:
    """生成股票日线样例数据。"""
    rng = _seeded_rng(code)
    base = _BASE_PRICE.get(code, 50.0)
    rows: List[Dict] = []
    prev_close = base
    for d in _trading_days(days):
        # 日波动 ±3% 随机游走
        change_ratio = rng.uniform(-0.03, 0.03)
        close = round(prev_close * (1 + change_ratio), 2)
        open_ = round(prev_close * (1 + rng.uniform(-0.015, 0.015)), 2)
        high = round(max(open_, close) * (1 + rng.uniform(0, 0.02)), 2)
        low = round(min(open_, close) * (1 - rng.uniform(0, 0.02)), 2)
        volume = round(rng.uniform(1e6, 5e7), 0)
        amount = round(volume * close, 2)
        rows.append(
            {
                "code": code,
                "trade_date": d,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "amount": amount,
                # pct_change 留待清洗阶段统一计算
            }
        )
        prev_close = close
    return rows


def generate_fund_nav(code: str, days: int = 60) -> List[Dict]:
    """生成基金净值样例数据。"""
    rng = _seeded_rng(code)
    base = _BASE_PRICE.get(code, 1.50)
    rows: List[Dict] = []
    unit = base
    accum = base
    for d in _trading_days(days):
        change_ratio = rng.uniform(-0.02, 0.025)
        new_unit = round(unit * (1 + change_ratio), 4)
        accum = round(accum + (new_unit - unit), 4)
        rows.append(
            {
                "code": code,
                "nav_date": d,
                "unit_nav": new_unit,
                "accum_nav": accum,
                # daily_return 留待清洗阶段统一计算
            }
        )
        unit = new_unit
    return rows


# 公告/新闻/舆情样例模板（模块1 公开数据源抓取，离线兜底）
_ANNOUNCEMENT_TEMPLATES: List[Dict] = [
    {"category": "announcement", "title": "{name}关于2025年年度报告披露的提示性公告",
     "source": "上市公司公告", "sentiment": "neutral",
     "summary": "公司董事会审议通过年度报告，将于近期在指定媒体披露。"},
    {"category": "announcement", "title": "{name}关于回购公司股份的进展公告",
     "source": "上市公司公告", "sentiment": "positive",
     "summary": "公司累计回购股份金额达计划上限，彰显管理层信心。"},
    {"category": "report", "title": "{name}2025年第四季度业绩预告",
     "source": "证监会指定平台", "sentiment": "positive",
     "summary": "预计归母净利润同比增长 15%-20%，主营业务稳健增长。"},
    {"category": "news", "title": "机构调研密集关注{name}，看好行业景气度",
     "source": "财经新闻", "sentiment": "positive",
     "summary": "多家券商发布研报维持买入评级，目标价上调。"},
    {"category": "sentiment", "title": "{name}股吧讨论热度上升，投资者情绪偏谨慎",
     "source": "舆情监测", "sentiment": "negative",
     "summary": "近期市场波动加大，部分投资者对短期股价表现存在分歧。"},
    {"category": "announcement", "title": "中国证监会关于加强证券基金行业信息披露监管的通知",
     "source": "证监会公告", "sentiment": "neutral",
     "summary": "进一步规范信息披露行为，保护投资者合法权益。"},
]


def generate_announcements(code: str, name: str, count: int = 4) -> List[Dict]:
    """为某标的生成样例公告/新闻/舆情。"""
    rng = _seeded_rng(code + "_ann")
    templates = list(_ANNOUNCEMENT_TEMPLATES)
    rng.shuffle(templates)
    rows: List[Dict] = []
    base_day = date.today()
    for i, tpl in enumerate(templates[:count]):
        pub = base_day - timedelta(days=rng.randint(0, 30))
        rows.append(
            {
                "code": code if "{name}" in tpl["title"] else "",
                "title": tpl["title"].format(name=name),
                "category": tpl["category"],
                "source": tpl["source"],
                "url": f"https://example.com/ann/{code}/{i}",
                "summary": tpl["summary"],
                "sentiment": tpl["sentiment"],
                "publish_date": pub,
            }
        )
    return rows
