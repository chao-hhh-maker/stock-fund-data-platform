# 测试报告（test.md）

> 模块 4 交付物 · 单元测试、接口测试、功能测试与缺陷记录

## 1. 测试范围与策略

| 类型 | 工具 | 覆盖对象 |
| --- | --- | --- |
| 单元测试 | Pytest | 清洗、行业分类、价格校验、交叉验证、交易日历、TTL 缓存、令牌桶限流 |
| 接口测试 | Pytest + FastAPI TestClient | 认证、权限、查询、采集（全量/增量）、导出、监控、元数据、审计全链路 |
| 功能测试 | 手工 + curl 脚本 | 登录→采集→查询→导出→监控→审计 主链路 |

测试环境隔离：使用独立 SQLite 测试库，关闭调度器，强制样例数据（不依赖网络），关闭限流。

当前测试规模：**38 个用例，全部通过**（test_api 11 + test_cleaning 6 + test_enhancements 11 + test_monitor_api 10）。

## 2. 测试用例清单

### 2.1 单元测试（test_cleaning.py）

| 用例 | 验证点 | 结果 |
| --- | --- | --- |
| test_normalize_code_stock_suffix_inference | 6 位代码按首位推断 .SH/.SZ | PASSED |
| test_normalize_code_prefix_form | sh/sz 前缀写法归一化 | PASSED |
| test_normalize_code_fund | 基金补 .OF 后缀 | PASSED |
| test_normalize_code_keeps_existing_suffix | 已有后缀转大写保留 | PASSED |
| test_clean_stock_daily_drops_invalid_and_computes_pct | 异常行剔除 + 涨跌幅计算 | PASSED |
| test_clean_fund_nav_computes_daily_return | 日增长率计算 | PASSED |

### 2.2 接口测试（test_api.py）

| 用例 | 验证点 | 结果 |
| --- | --- | --- |
| test_health_public | 健康检查公开可访问，DB 正常 | PASSED |
| test_login_success_and_failure | 登录成功返回角色；错误凭证 401 | PASSED |
| test_me_requires_token | 无 token 401，有 token 返回用户 | PASSED |
| test_instruments_seeded | 种子标的 ≥ 8 个 | PASSED |
| test_stock_daily_query_paginated | 行情分页查询正确 | PASSED |
| test_fund_nav_query | 基金净值查询有数据 | PASSED |
| test_viewer_cannot_trigger_crawl | 普通用户采集被拒 403（RBAC） | PASSED |
| test_admin_quick_crawl_and_runs | 管理员采集成功且有运行记录 | PASSED |
| test_job_lifecycle_and_logs | 任务创建→执行→日志 闭环 | PASSED |
| test_export_csv_and_download | 导出 CSV 且可下载 | PASSED |
| test_dashboard_stats | 仪表盘统计准确 | PASSED |

## 3. 执行结果

```
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-8.3.4
collected 38 items

tests/test_api.py ...........                                            [ 28%]
tests/test_cleaning.py ......                                            [ 44%]
tests/test_enhancements.py ...........                                   [ 73%]
tests/test_monitor_api.py ..........                                     [100%]

============================= 38 passed in 1.00s ==============================
```

**结论：38 个测试用例全部通过。**

### 新增功能测试要点

| 用例 | 验证点 |
| --- | --- |
| test_guess_industry_* | 行业分类映射正确 |
| test_clean_stock_fixes_inconsistent_high_low | OHLC 价格一致性校验 |
| test_cross_source_validate_detects_deviation | 跨源偏差检测 |
| test_calendar_skips_weekend/holiday | 交易日历节假日剔除 |
| test_cache_hit_and_miss / invalidate_prefix | TTL 缓存命中与失效 |
| test_rate_limiter_blocks_over_limit | 令牌桶限流 |
| test_metrics/integrity/alerts_endpoint | 监控运维接口 |
| test_data_dictionary / lineage_endpoint | 元数据与血缘 |
| test_audit_log_records_login / requires_admin | 审计日志与权限 |
| test_incremental_crawl | 增量采集 |
| test_viewer_can_export_with_quota | 普通用户导出配额 + 字段级权限 |

## 4. 功能测试（手工 / curl 实测记录）

实际启动后端后通过 curl 验证：

| 步骤 | 命令 / 操作 | 实测结果 |
| --- | --- | --- |
| 健康检查 | GET /api/health | status=ok, database=ok, scheduler=running |
| 管理员登录 | POST /api/auth/login | 返回 144 字符 JWT，role=admin |
| 仪表盘 | GET /api/dashboard | stocks=5, funds=3, daily_rows=300, nav_rows=180 |
| 行情查询 | GET /api/stocks/600519.SH/daily | total=60，含 OHLC 与涨跌幅 |
| 临时采集 | POST /api/tasks/crawl | status=success, rows=60, source=sample |
| 导出 | POST /api/exports (fund_nav csv) | row_count=60，生成文件 |
| 普通用户采集 | viewer 调用 /api/tasks/crawl | 403（权限拦截生效） |
| 下载 | GET /api/exports/1/download | http 200, 2926 bytes |
| 无 token | GET /api/dashboard | 401 |

## 5. 缺陷记录与修复

| 编号 | 现象 | 根因 | 修复 | 状态 |
| --- | --- | --- | --- | --- |
| BUG-01 | 配置 .env 后启动报 `error parsing value for field "CORS_ORIGINS"` | pydantic-settings 对 `List` 类型字段强制按 JSON 解析 env 值，逗号分隔字符串解析失败 | 将 `CORS_ORIGINS` 改为字符串存储，新增 `cors_origins_list` 属性解析为列表 | 已修复 |
| BUG-02 | MySQL 建表脚本 crawl_runs 报语法错误 | `trigger` 是 MySQL 保留字 | 字段名加反引号 `` `trigger` `` | 已修复 |
| BUG-03 | Parquet 导出在无 pyarrow 环境失败 | 缺少 parquet 引擎 | 捕获异常自动回退 CSV | 已修复 |
| BUG-04 | 新版 akshare 基金接口报 `unexpected keyword argument 'fund'` | akshare 升级后 `fund_open_fund_info_em` 参数由 `fund` 改为 `symbol`，ETF 改用 `fund_etf_fund_info_em` | 适配新版签名，按代码区分 ETF/开放式基金 | 已修复 |
| BUG-05 | 仪表盘接口 500 `name 'func' is not defined` | monitor.py 用到 `func.count` 但未导入 | 补充 `from sqlalchemy import func` | 已修复 |

## 6. 结论

核心业务链路（认证 → 权限 → 采集 → 清洗 → 存储 → 查询 → 导出 → 监控）经单元、接口、功能三层测试验证，全部通过；已知缺陷均已修复。系统满足课程设计题目二的功能要求，具备稳定演示能力。
