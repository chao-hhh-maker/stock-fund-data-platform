# 架构与类设计文档（architect.md）

> **项目名称**：股票基金数据获取和管理平台  
> **课程模块**：模块 2：AI 辅助设计  
> **文档定位**：架构设计、技术选型、核心类 / 模块职责  
> **最终报告映射**：最终报告第 3 章 3.1-3.3 节  
> **代码依据**：backend/app、frontend/src、sdk、sql/init.sql  
> **整理日期**：2026 年 6 月

## 0. 文档说明

本文档为课程设计过程文档的整理版，用于提交到 GitHub/Gitee 仓库。它与最终课程设计报告保持一致：仓库中保留本文件作为平时过程材料，最终报告中已将其核心内容合并到对应章节。

| 项目 | 内容 |
| --- | --- |
| 文档状态 | 最终整理版 |
| 是否合并进最终报告 | 是 |
| 后续需补充 | 团队真实姓名、学号、仓库地址、必要截图 |

---

## 1. 技术选型

| 层次 | 选型 | 理由 |
| --- | --- | --- |
| 前端 | Vue 3 + Vite + Element Plus + ECharts + Pinia + Vue Router | 组件成熟、开发快、图表能力强，适合课程演示 |
| 后端 | FastAPI + SQLAlchemy 2.0 + Pydantic v2 + Uvicorn | 自动生成 Swagger 文档，类型安全，开发效率高 |
| 调度 | APScheduler（BackgroundScheduler） | 轻量内嵌，支持 cron，无需独立中间件 |
| 数据处理 | Pandas | 清洗、导出便捷 |
| 数据源 | akshare（可选）+ 内置样例兜底 | 真实数据可用，断网亦可演示 |
| 存储 | SQLite（默认零配置）/ MySQL 8（可切换） | 兼顾即跑与课程要求 |
| 安全 | JWT（python-jose）+ passlib(pbkdf2_sha256) | 无原生编译依赖，跨平台稳定 |
| 测试 | Pytest + FastAPI TestClient | 覆盖单元与接口测试 |

## 2. 总体架构

采用前后端分离 + 后端分层架构：

```
┌─────────────────────────────────────────────┐
│  前端 SPA (Vue3)                              │
│  登录 / 仪表盘 / 股票 / 基金 / 任务 / 导出     │
└───────────────┬─────────────────────────────┘
                │ HTTP(JSON) + JWT
┌───────────────▼─────────────────────────────┐
│  API 层 (FastAPI Routers)                     │
│  auth / data / tasks / exports / monitor      │
├───────────────────────────────────────────────┤
│  依赖与中间件：CORS、JWT 鉴权、RBAC            │
├───────────────────────────────────────────────┤
│  服务层 (services)                            │
│  user / crawler / cleaning / task / export    │
├───────────────────────────────────────────────┤
│  调度层 (tasks/scheduler) APScheduler          │
├───────────────────────────────────────────────┤
│  数据层 (models + SQLAlchemy ORM)             │
└───────────────┬─────────────────────────────┘
                │
        ┌───────▼────────┐      ┌──────────────┐
        │ SQLite / MySQL │      │ 外部数据源    │
        └────────────────┘      │ akshare/样例  │
                                └──────────────┘
```

## 3. 分层职责

- **API 层**：参数校验、鉴权、调用服务、组装响应；不含业务逻辑。
- **服务层**：核心业务（采集、清洗、任务执行、导出、用户）。
- **数据层**：ORM 模型与会话管理。
- **调度层**：定时任务注册与触发，复用服务层逻辑。
- **核心层（core）**：配置、数据库、安全工具。

设计原则：单向依赖（API → service → model），服务层不反向依赖 API；采集与清洗解耦，便于替换数据源。

## 4. 核心类设计

### 4.1 领域模型类（models.py）

| 类 | 关键属性 | 关系 |
| --- | --- | --- |
| Tenant | id, name, code, is_active | 1—N User（机构级隔离） |
| Role | id, name, data_scope, max_history_days, can_export, can_view_sensitive | 1—N User（行级/时间/字段/功能权限） |
| User | id, username, hashed_password, role_id, tenant_id, department, is_active | N—1 Role / Tenant |
| Instrument | id, code, name, asset_type, market, category | 主数据 |
| StockDaily | code, trade_date, OHLC, volume, amount, pct_change, source | 唯一(code,date) |
| FundNav | code, nav_date, unit_nav, accum_nav, adj_nav, daily_return, source | 唯一(code,date) |
| Announcement | id, code, title, category, sentiment, publish_date, source | 公开数据源 |
| CrawlJob | id, name, job_type, target_codes, mode, frequency, cron, enabled | 1—N CrawlRun |
| CrawlRun | id, job_id, trigger, status, started/finished, rows_affected, source, message | N—1 CrawlJob |
| ExportRecord | id, user_id, dataset, file_format, params, file_name, row_count | N—1 User |
| DataQualityIssue | id, issue_type, code, severity, message, status, resolved_by | 跨源/异常问题 |
| AlertRecord | id, level, alert_type, target, message, dispatch_status | 告警历史 |
| AuditLog | id, username, role, action, target, detail, ip | 操作审计 |

### 4.2 服务类 / 模块

- `crawler`：`crawl_stock_daily()`, `crawl_fund_nav()`，内部 `_collect_one_*`（含 akshare→样例 回退）、`_upsert_*`（幂等写入）。
- `cleaning`：`normalize_code()`, `clean_stock_daily()`, `clean_fund_nav()`。
- `task_service`：`execute_job()`, `execute_job_by_id()`（调度回调）。
- `export_service`：`export_dataset()` → DataFrame → 文件 + 记录。
- `user_service`：`authenticate()`, `create_user()`, `ensure_seed_users()`。
- `scheduler`：`add_or_update_job()`, `remove_job()`, `load_jobs()`, `start()/shutdown()`。

### 4.3 关键时序：手动采集

```
Client → API(/tasks/crawl) → task_service.execute_job
   → 新建 CrawlRun(running)
   → crawler.crawl_*()
       → _collect_one_*  (akshare 失败 → sample_data)
       → cleaning.clean_*()
       → _upsert_*()  (幂等)
   → 更新 CrawlRun(status, rows, source) → 返回
```

## 5. 关键设计决策

1. **样例数据兜底**：保证离线可演示，降低答辩风险。
2. **SQLite 默认**：克隆即跑；MySQL 通过 `DATABASE_URL` 一行切换。
3. **幂等 upsert**：重复采集不产生脏数据。
4. **粗粒度 RBAC**：role 写入 JWT，敏感操作用 `require_admin` 依赖拦截。
5. **错误隔离**：单代码失败不影响整体，状态分级 success/partial/failed。

## 6. 增强能力与轻量等价实现

为覆盖题目二企业级需求清单，同时保持「克隆即跑」，采用如下等价实现策略：

| 题目能力 | 等价实现 | 预留扩展 |
| --- | --- | --- |
| Redis 实时缓存 | 进程内 TTL 缓存 `core/cache.py`（命中率统计 + 采集后主动失效） | `CacheBackend` 接口，可换 Redis |
| 查询限流 | 令牌桶 `core/rate_limit.py`（每用户每分钟） | 可换 Redis+Lua 分布式限流 |
| ClickHouse 历史存储 | 关系库承担，受控 SQL 聚合查询模拟列式视角 | 表结构兼容迁移 |
| MongoDB/ES 文档存储 | `announcements` 表承担公告/舆情文档存储 | 可换文档库 |
| 商业数据源（Wind/同花顺） | 数据源注册表占位登记 | `_fetch_*_via_xxx` 扩展点 |
| WebSocket 实时推送 | `api/ws.py` 周期推送最新快照 | 可接真实行情流 |
| 导出 AES 加密 | `pyzipper` 加密 zip，缺库回退标准 zip | 配置化密码 |

新增服务模块：
- `services/calendar_service`：A 股交易日历与节假日。
- `services/monitor_service`：完整性、系统指标、异常监测、告警生成与分发。
- `services/metadata_service`：数据字典（含敏感级别）与数据血缘。
- `services/datasource_registry`：多渠道数据源登记与命中统计。
- `services/data_quality_service`：跨源偏差/异常问题落库与人工校对。
- `services/audit_service`：操作审计日志。
- `core/cache` / `core/rate_limit` / `core/metrics_middleware`：缓存、限流、API 性能监控基础设施。

新增 API 路由：
- `api/query`：受控只读 SQL 查询（白名单 + 强制 LIMIT）。
- `api/ws`：WebSocket 实时行情推送。
- `api/admin`：用户 / 角色 / 租户管理。

Python SDK：`sdk/stockfund_client.py` —— 对 REST API 的 Python 封装（模块4「Python 封装」）。

## 7. 前端页面结构（深色金融科技风）

| 页面 | 职责 |
| --- | --- |
| 登录 | 网格背景 + 光晕，快捷填充演示账号 |
| 数据驾驶舱 | 统计卡片 + WebSocket 实时滚动条 + 成功率仪表盘 + 行业饼图 + 走势速览 |
| 股票行情 | K 线（蜡烛图+成交量）/ 收盘线切换 + 关键指标条 + 全量/增量采集 |
| 基金净值 | 单位/累计净值双曲线 + 累计涨幅 |
| 公告舆情 | 公告/年报/新闻/舆情信息流 + 情绪标记 + 采集 |
| 采集任务 | 任务 CRUD + 全量/增量 + 频率预设 + cron + 运行日志抽屉 |
| 数据源接入 | 多渠道数据源在线状态与命中统计卡片 |
| 数据质量 | 跨源偏差/异常问题列表 + 人工校对（修正/忽略） |
| 监控运维 | 系统指标卡 + 完整性进度 + 告警中心 + API 性能监控 |
| 元数据血缘 | 数据字典（含敏感级别）+ 血缘追踪表 |
| SQL 查询台 | 受控只读 SQL 输入 + 结果表（管理员） |
| 数据导出 | 导出记录 + 多格式 + 加密压缩 + 下载 |
| 系统管理 | 用户/角色/租户 CRUD（管理员） |
| 审计日志 | 登录/采集/导出/SQL/管理操作审计（管理员） |

复用组件：`StatCard`（数字滚动卡片）、`LineChart`（暗色面积折线）、`KLineChart`（蜡烛+成交量）、`MiniChart`（饼图/仪表盘）。

## 架构质量核对

| 质量属性 | 设计措施 | 代码落点 |
| --- | --- | --- |
| 可运行性 | SQLite 默认、首次启动自动建表和种子数据 | `core/database.py`、`seed.py` |
| 可演示性 | 真实数据源失败自动回退样例数据 | `services/crawler.py`、`services/sample_data.py` |
| 可维护性 | API、service、model 单向分层 | `api/`、`services/`、`models.py` |
| 可扩展性 | 数据源注册表、缓存接口、SQL 白名单、WebSocket 独立路由 | `datasource_registry.py`、`cache.py`、`query.py`、`ws.py` |
| 安全性 | JWT、RBAC、行级/时间级/字段级权限、审计日志 | `security.py`、`deps.py`、`audit_service.py` |
| 可测试性 | 业务逻辑沉入 service 层，测试夹具隔离数据库 | `backend/tests/` |

## 提交前核对

- [ ] 架构图与实际目录一致。
- [ ] 核心类表格与 `models.py` 一致。
- [ ] 文档说明了轻量等价实现，而不是虚构 Redis/ClickHouse/MongoDB 已完整部署。
