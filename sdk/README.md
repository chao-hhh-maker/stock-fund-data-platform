# 股票基金数据平台 · Python SDK

对平台 RESTful API 的轻量 Python 封装（模块4「Python 封装」交付物）。

## 安装依赖

```bash
pip install requests pandas   # pandas 可选，用于 DataFrame 输出
```

## 快速开始

确保后端已启动（默认 `http://127.0.0.1:8000`），然后：

```python
from stockfund_client import StockFundClient

cli = StockFundClient("http://127.0.0.1:8000")
cli.login("admin", "admin123")

# 标的与行情
instruments = cli.instruments(asset_type="stock")
df = cli.stock_daily("600519.SH", start_date="2025-01-01")   # DataFrame
nav = cli.fund_nav("510300.OF")

# 采集（管理员）
cli.crawl(job_type="stock_daily", target_codes="600519.SH,000001.SZ", mode="incremental")

# 导出（支持加密压缩）
rec = cli.export("stock_daily", file_format="csv", code="600519.SH", compress=True, encrypt=True)

# 受控 SQL 查询（管理员）
rows = cli.sql("SELECT code, COUNT(*) c FROM stock_daily GROUP BY code ORDER BY c DESC")
```

## 直接运行自测

```bash
cd sdk
python stockfund_client.py
```

## 方法一览

| 方法 | 说明 |
| --- | --- |
| `login(username, password)` | 登录并缓存 JWT |
| `instruments(asset_type=None)` | 标的列表 |
| `stock_daily(code, start_date, end_date)` | 股票日线（DataFrame） |
| `fund_nav(code, start_date, end_date)` | 基金净值（DataFrame） |
| `crawl(job_type, target_codes, mode)` | 触发采集 |
| `export(dataset, file_format, code, compress, encrypt)` | 导出数据 |
| `sql(sql, limit)` | 受控只读 SQL 查询 |
| `dashboard()` | 仪表盘统计 |
