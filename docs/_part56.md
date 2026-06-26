
---

# 第 5 章　测试与调试

> 对应课程模块 4。在 AI 辅助下生成单元测试与功能测试用例，对后端接口做 Swagger/TestClient 测试，并用 AI 辅助定位缺陷。

## 5.1 测试策略

**表 5-1　测试范围与工具**

| 类型 | 工具 | 覆盖对象 |
| --- | --- | --- |
| 单元测试 | Pytest | 清洗、行业分类、价格校验、跨源验证、交易日历、TTL 缓存、令牌桶限流 |
| 接口测试 | Pytest + FastAPI TestClient | 认证、权限、查询、采集（全量/增量）、导出、监控、元数据、审计全链路 |
| 升级回归 | Pytest | 三层权限、受控 SQL、WebSocket、多租户、数据质量、API 性能等增强能力 |
| 功能测试 | 手工 + curl 脚本 | 登录→采集→查询→导出→监控→审计 主链路 |

**测试环境隔离**：使用独立 SQLite 测试库，关闭调度器（`SCHEDULER_ENABLED=false`），强制样例数据（`CRAWL_FORCE_SAMPLE`，不依赖网络），关闭限流，保证测试可重复、与网络无关。

**当前测试规模**：**65 个用例，全部通过**。分布：test_api 11 + test_cleaning 6 + test_enhancements 11 + test_monitor_api 10 + test_upgrade 27。

执行结果：

```
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-8.3.4
collected 65 items

tests/test_api.py ...........                                            [ 16%]
tests/test_cleaning.py ......                                            [ 26%]
tests/test_enhancements.py ...........                                   [ 43%]
tests/test_monitor_api.py ..........                                     [ 58%]
tests/test_upgrade.py ...........................                        [100%]

============================= 65 passed in 4.22s ==============================
```

> （图 5-1，待补）`python -m pytest` 全绿终端截图

## 5.2 单元测试

**表 5-2　单元测试用例（test_cleaning.py + test_enhancements.py 节选）**

| 用例 | 验证点 | 结果 |
| --- | --- | --- |
| test_normalize_code_stock_suffix_inference | 6 位代码按首位推断 .SH/.SZ | PASSED |
| test_normalize_code_prefix_form | sh/sz 前缀写法归一化 | PASSED |
| test_normalize_code_fund | 基金补 .OF 后缀 | PASSED |
| test_normalize_code_keeps_existing_suffix | 已有后缀转大写保留 | PASSED |
| test_clean_stock_daily_drops_invalid_and_computes_pct | 异常行剔除 + 涨跌幅计算 | PASSED |
| test_clean_fund_nav_computes_daily_return | 日增长率计算 | PASSED |
| test_guess_industry_* | 申万/中信/GICS 行业映射正确 | PASSED |
| test_clean_stock_fixes_inconsistent_high_low | OHLC 价格一致性校验 | PASSED |
| test_cross_source_validate_detects_deviation | 跨源偏差检测 | PASSED |
| test_calendar_skips_weekend/holiday | 交易日历节假日剔除 | PASSED |
| test_cache_hit_and_miss / invalidate_prefix | TTL 缓存命中与按前缀失效 | PASSED |
| test_rate_limiter_blocks_over_limit | 令牌桶超限拦截 | PASSED |

控制结构覆盖示例：`clean_stock_daily` 用例同时覆盖「正常数据、价格为 0 的异常值剔除、首行无前收的涨跌幅为 0」三条分支，符合指导书对控制结构单元测试的要求。

## 5.3 接口测试

**表 5-3　接口测试用例（test_api.py）**

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

**表 5-4　增强能力回归测试（test_upgrade.py + test_monitor_api.py 节选，共 37 例）**

| 用例 | 验证点 |
| --- | --- |
| test_analyst_data_scope_stock_only | 行级权限：研究员仅可访问股票 |
| test_analyst_history_clamped | 时间权限：研究员历史被钳制到近 365 天 |
| test_sensitive_field_masked_for_viewer | 字段级权限：普通用户 amount 脱敏为 0 |
| test_viewer_cannot_export / quota | 功能权限 + 导出配额 |
| test_sql_query_select_only / blocks_dml | 受控 SQL：仅 SELECT、拦截 DML/多语句 |
| test_sql_query_forces_limit | 受控 SQL：强制注入 LIMIT |
| test_ws_quotes_requires_token | WebSocket token 鉴权 |
| test_tenant_visibility_isolation | 多租户/部门标的隔离 |
| test_data_quality_resolve_flow | 数据质量人工校对状态流转 |
| test_api_metrics_recorded | API 性能监控统计 |
| test_metrics/integrity/alerts_endpoint | 监控运维接口 |
| test_data_dictionary / lineage_endpoint | 元数据与血缘 |
| test_audit_log_records_login / requires_admin | 审计日志与权限 |
| test_incremental_crawl | 增量采集只取新数据 |

> （图 5-2，待补）Swagger 接口调试截图（登录获取 token → 调用受保护接口）

## 5.4 功能测试

启动后端后通过 curl 实测主链路：

**表 5-5　功能测试实测记录**

| 步骤 | 命令 / 操作 | 实测结果 |
| --- | --- | --- |
| 健康检查 | GET /api/health | status=ok, database=ok, scheduler=running |
| 管理员登录 | POST /api/auth/login | 返回 JWT，role=admin |
| 仪表盘 | GET /api/dashboard | 标的/行情/净值统计准确 |
| 行情查询 | GET /api/stocks/600519.SH/daily | 含 OHLC 与涨跌幅 |
| 临时采集 | POST /api/tasks/crawl | status=success，返回行数与来源 |
| 导出 | POST /api/exports (fund_nav csv) | 生成文件，落导出记录 |
| 普通用户采集 | viewer 调用 /api/tasks/crawl | 403（权限拦截生效） |
| 研究员越权 | analyst 查询基金 | 403（行级权限生效） |
| 下载 | GET /api/exports/1/download | HTTP 200，返回文件流 |
| 无 token | GET /api/dashboard | 401 |

前端功能测试按演示脚本走查：登录 → 驾驶舱 → 采集 → 图表刷新 → 导出 → 下载 → 监控告警 → 切换 viewer/analyst 验证权限按钮/菜单消失，均符合预期。

## 5.5 缺陷定位与修复记录

在 AI 辅助下（提供错误栈让 AI 分析根因）定位并修复的代表性缺陷：

**表 5-6　缺陷记录与修复**

| 编号 | 现象 | 根因 | 修复 | 状态 |
| --- | --- | --- | --- | --- |
| BUG-01 | 配置 .env 后启动报 `error parsing value for field "CORS_ORIGINS"` | pydantic-settings 对 List 字段强制按 JSON 解析 env，逗号分隔字符串解析失败 | 改为字符串存储 + `cors_origins_list` 属性解析为列表 | 已修复 |
| BUG-02 | MySQL 建表脚本 crawl_runs 报语法错误 | `trigger` 是 MySQL 保留字 | 字段名加反引号；补 (code,trade_date) 唯一约束保幂等 | 已修复 |
| BUG-03 | Parquet 导出在无 pyarrow 环境失败 | 缺 parquet 引擎 | 捕获异常自动回退 CSV | 已修复 |
| BUG-04 | 新版 akshare 基金接口报 `unexpected keyword argument 'fund'` | akshare 升级后 `fund_open_fund_info_em` 参数由 `fund` 改为 `symbol`，ETF 改用 `fund_etf_fund_info_em` | 适配新版签名，按代码区分 ETF/开放式 | 已修复 |
| BUG-05 | 仪表盘接口 500 `name 'func' is not defined` | monitor.py 用 `func.count` 但未导入 | 补 `from sqlalchemy import func` | 已修复 |
| BUG-06 | 字段级权限绕过：查询接口直接暴露成交额 amount，仅导出脱敏 | 脱敏逻辑只加在导出侧，查询侧遗漏 | 在 data.py 查询侧按 `can_view_sensitive` 统一脱敏，与导出一致 | 已修复 |
| BUG-07 | 基金完整率虚低 | 完整性检查把基金也按股票交易日要求，未容忍披露滞后 | 完整率取 min(actual/expected, 1.0) 上限 | 已修复 |

**结论**：核心业务链路（认证 → 权限 → 采集 → 清洗 → 存储 → 查询 → 导出 → 监控）经单元、接口、功能三层测试验证，65 个用例全部通过，已知缺陷均已修复，系统具备稳定演示能力。

> （图 5-3，待补）缺陷修复前后对比 / Git diff 截图

<div style="page-break-after: always;"></div>

---

# 第 6 章　部署与使用

> 对应课程模块 5。系统已在本地部署验证（Windows 11 + Python 3.13 + Node 22）。

## 6.1 环境要求

**表 6-1　环境要求**

| 组件 | 版本 | 必需 |
| --- | --- | --- |
| Python | 3.10+（已在 3.13 验证） | 是 |
| Node.js | 18+（已在 22 验证） | 是 |
| MySQL | 8.0+ | 否（默认用 SQLite） |

## 6.2 后端部署

```bash
cd backend

# 1) 创建虚拟环境
python -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # macOS / Linux

# 2) 安装依赖
pip install -r requirements.txt

# 3) 配置（可选，默认 SQLite 无需改）
cp .env.example .env

# 4) 启动
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

启动后：API 根 `http://127.0.0.1:8000/`、Swagger 文档 `http://127.0.0.1:8000/docs`、健康检查 `http://127.0.0.1:8000/api/health`。**首次启动自动建表、创建默认账号、登记预置标的（30 股票 + 16 基金）并生成样例行情，无需手工初始化。**

**默认账号**：管理员 `admin/admin123`、普通用户 `viewer/viewer123`、研究员 `analyst/analyst123`。

## 6.3 前端部署

```bash
cd frontend
npm install                      # 如遇缓存权限问题：npm install --cache ./.npm-cache
npm run dev                      # 开发模式，http://localhost:5173
# 或
npm run build                    # 生产构建，产物在 dist/
```

开发模式下 `/api` 已配置代理到后端 8000 端口（含 WebSocket 升级），无需额外配置跨域。

## 6.4 切换 MySQL 与启用真实数据源

**切换 MySQL（可选）**：

```sql
CREATE DATABASE stock_fund_platform DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE stock_fund_platform;
SOURCE sql/init.sql;
```

修改 `backend/.env`：`DATABASE_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/stock_fund_platform?charset=utf8mb4`，确保已装 `pymysql`，重启后端即可。

**启用真实数据源（可选）**：默认无网络时用内置样例数据。`pip install akshare` 后系统优先用 akshare 拉真实数据（失败仍自动回退样例）；如需启动即拉真实数据，置 `AUTO_CRAWL_ON_STARTUP=true`。

## 6.5 配置项说明

`backend/.env.example` 提供完整模板，关键项：

**表 6-2　核心配置项**

| 配置 | 默认 | 说明 |
| --- | --- | --- |
| DATABASE_URL | sqlite:///./stock_fund_platform.db | 数据库连接，可切 MySQL |
| SECRET_KEY / ACCESS_TOKEN_EXPIRE_MINUTES | （示例）/ 720 | JWT 密钥与有效期（12h） |
| CORS_ORIGINS | localhost:5173,127.0.0.1:5173 | 允许的前端来源 |
| USE_SAMPLE_DATA_FALLBACK / CRAWL_FORCE_SAMPLE | true / false | 样例兜底开关 / 强制只用样例 |
| CRAWL_MAX_RETRIES / CRAWL_LOOKBACK_DAYS | 2 / 400 | 重试次数 / 采集回看天数 |
| AUTO_CRAWL_ON_STARTUP / REALTIME_ENABLED | false / true | 启动后台采集 / 实时行情 |
| RATE_LIMIT_PER_MINUTE / CACHE_TTL_SECONDS | 120 / 30 | 限流阈值 / 缓存有效期 |
| VIEWER_EXPORT_DAILY_QUOTA | 20 | 普通用户每日导出配额 |
| EXPORT_ZIP_PASSWORD / SQL_QUERY_MAX_ROWS | stockfund-2026 / 1000 | 导出加密密码 / SQL 行数上限 |
| WS_PUSH_INTERVAL / SCHEDULER_ENABLED | 3 / true | WS 推送间隔 / 调度开关 |
| ALERT_WEBHOOK_URL / ANOMALY_* | 空 / 11.0,5.0 | 告警 webhook / 异常阈值 |

## 6.6 软件使用说明

**登录**：打开 `http://localhost:5173`，输入账号密码进入数据驾驶舱。管理员可采集/导出/任务管理/SQL/系统管理；普通用户查询查看；研究员仅股票、近一年、禁导出。

**数据驾驶舱**：统计卡片 + 实时行情滚动条（实时/盘中/收盘状态）+ 采集成功率仪表盘 + 行业分布饼图 + 走势速览 + 最近采集运行。

**股票/基金行情**：选择标的与日期 → 查询 → 看 K 线（或收盘线）/净值双曲线与明细表（涨红跌绿）→ 管理员可「采集该标的」实时补数或「导出」。

**采集任务**：查看任务列表；管理员可新建任务（名称/类型/目标代码/模式/频率/cron）、执行、查看日志、删除；支持「一键采集全部/仅股票/仅基金」。

**数据治理**：数据质量页处理跨源偏差/异常问题（修正/忽略）；元数据页查看数据字典（含敏感级别）与数据血缘。

**查询服务**：SQL 查询台（管理员，只读 SELECT + 预设查询）；数据导出（选数据集/格式/加密压缩 → 下载历史记录）。

**监控运维**：系统指标卡、完整性进度、告警中心、API 性能统计、告警处理历史；系统管理（用户/角色/租户 CRUD）；审计日志。

> （图 6-1，待补）各角色登录后的页面差异截图（admin 全功能 vs viewer/analyst 受限）

## 6.7 演示脚本（5–8 分钟）

1. 登录（admin），展示数据驾驶舱数据概览与实时行情滚动条。
2. 数据源接入页：展示 akshare/腾讯/新浪/样例多源在线状态与命中统计。
3. 股票行情 → 看 K 线 → 点「采集该股票」展示实时入库 → 数据刷新；切到基金看净值双曲线。
4. 采集任务页：新建一个定时任务 → 执行一次 → 看运行日志；或「一键采集全部」。
5. 数据治理：数据质量页展示跨源偏差问题并「修正」；元数据页展示字典与血缘。
6. 导出基金净值（勾选加密压缩）→ 下载；SQL 查询台执行预设查询。
7. 监控运维：完整性、告警中心、API 性能。
8. 退出，用 viewer 登录展示成交额脱敏；用 analyst 登录展示仅股票 + 禁导出（行级/功能权限）。

**兜底方案**：保留样例数据，断网时全链路仍可演示；答辩前不清空数据库，预启动后端、前端、Swagger、README 与本报告标签页。

<div style="page-break-after: always;"></div>
