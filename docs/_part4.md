
---

# 第 4 章　系统实现

> 对应课程模块 3（核心学时）。本章说明前后端关键实现，标注 `[AI生成]` 的代码段均经人工审查、调试与测试。完整代码节选见附录 A。

## 4.1 后端工程结构

后端基于 FastAPI 分层组织：`api/`（路由）、`core/`（基础设施）、`services/`（业务）、`models.py`（ORM）、`schemas.py`（契约）、`tasks/`（调度）。应用入口 `main.py` 用 `lifespan` 管理启动/关闭生命周期：

启动顺序：① `init_db()` 建表 + 自动迁移；② `run_all(db, with_market_data=True)` 写入种子数据（用户/标的/样例行情）；③ 启动 APScheduler 调度器；④ 可选后台线程 `_kickoff_auto_crawl()` 拉真实数据（首屏样例秒开，后台刷新成真实）。关闭时安全停止调度器。同时注册 CORS 与 `APIMetricsMiddleware`（API 性能监控），并以统一前缀 `/api` 挂载 8 个路由模块。

## 4.2 认证与三层数据权限

### 4.2.1 JWT 认证

密码哈希使用 passlib 的 `pbkdf2_sha256`（纯 Python，避免 Windows 上 bcrypt 原生库安装问题）。登录校验通过后由 `create_access_token` 签发 JWT，payload 含 `sub`（用户名）、`role`（角色）、`exp`（过期）。请求侧 `get_current_user` 依赖解析并校验 JWT，无效或用户停用即返回 401。该段为注释驱动生成并经人工改造 `[AI生成]`（见 `core/security.py`、`api/deps.py`，附录 A.1）。

### 4.2.2 RBAC 与四类权限

权限分四层，逐层在依赖与查询逻辑中落地：

1. **功能权限**：敏感操作（采集、任务管理、SQL 查询、系统管理）用 `require_admin` 依赖拦截，非管理员返回 403；导出由角色 `can_export` 控制。
2. **行级权限**：角色 `data_scope`（all/stock/fund）经 `check_asset_access` 限制可访问的资产类型；`apply_instrument_visibility` 进一步按租户/部门过滤标的可见性。
3. **时间权限**：`clamp_start_date` 按角色 `max_history_days` 钳制查询起始日期。如 analyst 仅可见近 365 天，请求更早日期会被收紧到下界。
4. **字段级权限**：`can_view_sensitive` 决定敏感字段（成交额 amount）是否可见。无权限时在**查询和导出两处统一脱敏为 0**（修复了早期「查询接口绕过脱敏」的真实缺陷，见 5.5）。

这四层在 `api/deps.py` 中集中实现（附录 A.1），查询接口 `data.py` 调用它们完成「行级过滤 → 时间钳制 → 字段脱敏」的串联。

### 4.2.3 多租户与审计

`Tenant` 模型 + `User.tenant_id/department` 实现机构级与部门级隔离；`apply_instrument_visibility` 保证普通用户只能看到公共标的和本租户/本部门标的。关键操作（登录、登录失败、采集、导出、SQL 查询、用户管理）经 `audit_service.log()` 落 `audit_logs` 表，管理员可在审计页查询。

## 4.3 数据采集与多源兜底

采集是本项目工程含量最高的部分，对应题目模块 1。核心设计（`services/crawler.py`，附录 A.2）：

- **四级数据源兜底**：股票日线按 `akshare(东方财富) → 腾讯财经 → 新浪财经 → 内置样例` 顺序尝试，任一真实源成功即返回，全部失败才回退样例并记录失败原因。三个真实源使用**不同域名**（`push2his.eastmoney`、`web.ifzq.gtimg.cn`、`quotes.sina.cn`），可绕开校园网/办公网对单一源的封锁——这是保证答辩现场能拉到真实数据的关键设计。`[AI生成]` 骨架 + 人工补腾讯/新浪兜底源。
- **智能重试**：`_retry()` 对网络类失败做指数退避重试，重试次数累计写入运行记录。
- **错误隔离**：单个代码失败不中断整体，记入 `errors`，整体状态按失败比例置为 success/partial/failed。
- **增量/全量**：`incremental=True` 时只采集库中最新日期之后的数据。
- **幂等 upsert**：`_upsert_stock_rows/_upsert_fund_rows` 按唯一键判断存在则更新、否则插入，返回 (新增, 更新) 行数，重复采集不产生脏数据。
- **数据血缘**：每行落库带 `source` 标记，运行记录 `message` 区分「新增 N 行 / 更新 M 行」及回退原因。
- **采集后缓存失效**：`cache.invalidate_prefix()` 清理受影响标的的查询缓存，避免脏读。
- **跨源校验**：真实源采集成功后，用副源 `_collect_secondary_stock` 抓取并 `cross_source_validate` 比对收盘价，偏差超 5% 登记 `DataQualityIssue`。

公开数据源（公告/新闻/舆情）由 `crawl_announcements()` 采集，优先 akshare 东财新闻接口，失败回退确定性样例公告，幂等去重（同标题不重复插入）。

## 4.4 数据清洗与标准化

`services/cleaning.py`（附录 A.3）实现题目模块 2 的清洗与标准化：

- **证券代码标准化** `normalize_code()`：将 `sh600519 / 600519 / 600519.SH / 基金代码` 等写法统一为 `数字.市场后缀`。规则：含后缀者统一大写；6 位纯数字股票 6/9 开头→.SH、0/3 开头→.SZ；基金补 .OF。`[AI生成]` + 人工补基金分支与边界用例。
- **日期归一** `_to_date()`：不同源日期格式不一（akshare 返回 date，腾讯返回字符串），入库前统一转 date，规避 SQLite「只接受 date 对象」报错。
- **异常值/缺失值处理**：剔除价格缺失、NaN、非正的异常行。
- **OHLC 一致性校验**：修正越界 high/low，保证 high≥max(open,close)、low≤min(open,close)，避免 K 线显示异常。
- **衍生字段**：基于前一交易日计算股票 `pct_change`（涨跌幅）与基金 `daily_return`（日增长率）。
- **基金净值复权** `adj_nav`：以累计净值增量识别分红，按「单位净值日收益 + 分红再投」累乘推进，近似分红再投资收益曲线。
- **行业分类统一** `guess_industry(code, standard)`：内置申万一级映射，并提供到中信、GICS 的对照，实现一码多标准归类。

## 4.5 存储、缓存与限流

- **存储**：SQLAlchemy 2.0 ORM，默认 SQLite（`is_sqlite` 自动加 `check_same_thread=False`），可经 `DATABASE_URL` 一行切到 MySQL。
- **TTL 缓存**（`core/cache.py`）：进程内字典实现，含命中/未命中统计与命中率，支持 TTL 过期与 `invalidate_prefix` 按前缀失效。行情/净值查询读缓存，采集后按标的前缀失效。这是 Redis 缓存的轻量等价实现。
- **令牌桶限流**（`core/rate_limit.py`）：每用户每分钟最多 `RATE_LIMIT_PER_MINUTE`（默认 120）次，超限返回 429。不同用户独立计桶。

## 4.6 查询、SQL 接口与 WebSocket

- **行情/净值查询**（`api/data.py`）：分页 + 日期筛选，串联三层数据权限与 TTL 缓存。
- **受控 SQL 查询**（`api/query.py`）：仅管理员，仅允许单条 SELECT/WITH；表名白名单（stock_daily、fund_nav、instruments、crawl_jobs/runs、export_records、announcements、data_quality_issues、alert_records）；禁 insert/update/delete/drop/alter/create/truncate 等关键字与多语句；强制注入 LIMIT（上限 `SQL_QUERY_MAX_ROWS`）；每条查询审计。这是 ClickHouse「通用查询/列式聚合」的等价实现。
- **WebSocket**（`api/ws.py`）：`/ws/quotes?token=JWT`，query 参数鉴权后按 `WS_PUSH_INTERVAL`（默认 3s）周期推送行情快照。交易时段推送 `realtime_service` 的新浪秒级实时价，休市推送库中最新收盘。前端断线自动降级为 HTTP 轮询。
- **Python SDK**（`sdk/stockfund_client.py`）：对 REST API 的封装，提供 login/查询/采集/导出/SQL 等方法，对应题目「Python 封装」。

## 4.7 数据导出与加密压缩

`services/export_service.py` + `api/exports.py` 实现题目模块 4 的导出：

- 支持 **CSV / Excel / Parquet** 三格式（Parquet 无引擎时自动回退 CSV，见缺陷 BUG-03）。
- 导出复用查询侧数据权限：行级、时间、字段级脱敏一并生效。
- **加密压缩**：可选 zip 压缩 + AES 加密（`pyzipper`，密码取自 `EXPORT_ZIP_PASSWORD`；缺库回退标准 zip）。
- **配额**：管理员无限制，普通用户每日 `VIEWER_EXPORT_DAILY_QUOTA`（默认 20）次。
- **历史追踪**：每次导出落 `export_records`，可在导出页查看并重新下载。

## 4.8 监控运维与告警

`services/monitor_service.py` + `api/monitor.py` 实现题目模块 5：

- **完整性检查** `check_integrity()`：按 `calendar_service` 的 A 股交易日历（剔除周末与法定节假日），检测每个标的近 N 个交易日的数据缺口，输出完整率（对基金取 min(actual/expected,1.0) 上限，容忍披露滞后）。
- **异常监测** `detect_anomalies()`：单日涨跌幅超 `ANOMALY_PCT_CHANGE_THRESHOLD`（11%）、成交量超近期均值 `ANOMALY_VOLUME_RATIO`（5×）、净值断崖等，登记数据质量问题。
- **延迟告警**：最新数据距今 >7 天触发告警。
- **告警分发** `dispatch_alerts()`：落 `AlertRecord`（含 fingerprint 去重），并可 best-effort POST 到 `ALERT_WEBHOOK_URL`，记录 dispatch_status。
- **系统指标**：采集成功率、缓存命中率、运行总数、DB 文件大小。
- **API 性能监控**：`APIMetricsMiddleware` 统计各接口请求数/平均耗时/最大耗时/错误率，`/monitor/api-stats` 输出。

## 4.9 数据质量与人工校对

`services/data_quality_service.py` + `/data-quality` 接口实现题目模块 2「人工数据检查校对」与跨源验证闭环：跨源偏差（cross_source）、字段异常（anomaly）、缺失（missing）三类问题落 `DataQualityIssue`，管理员在前端「数据质量」页可标记「修正/忽略」并填写处理说明，状态流转 open→resolved/ignored，记录处理人与时间。

## 4.10 任务调度

`tasks/scheduler.py` 基于 APScheduler `BackgroundScheduler`：应用启动时 `load_jobs()` 加载所有 enabled 且 cron 非空的任务并注册；到点回调 `execute_job_by_id` 用独立 DB 会话执行采集（trigger=scheduled）。任务的 `frequency` 预设（realtime/minute/daily/weekly/quarterly/manual）映射为 cron 表达式，也可手动填写 cron。cron 非法时记录日志并跳过注册，不影响应用启动。

## 4.11 前端实现要点

前端为 Vue 3 + Vite SPA，14 个页面，关键实现：

- **路由与守卫**（`router/index.js`）：未登录跳登录页（带 redirect）；已登录访问登录页转仪表盘；带 `meta.admin` 的页面（SQL 查询台、系统管理、审计日志）对非管理员拦截并提示。
- **状态管理**（`stores/auth.js`）：Pinia 持久化 token、username、role 及四类权限标志（dataScope、maxHistoryDays、canExport、canViewSensitive）到 localStorage；`isAdmin`、`roleLabel` 等 getter。
- **请求层**（`api/http.js`）：Axios 实例 baseURL=`/api`，请求拦截器注入 `Authorization: Bearer`，响应拦截器统一处理 401（登出跳登录）、403（无权限提示）、429（频率限制提示）。
- **接口集中定义**（`api/index.js`）：所有后端接口集中封装，并提供 WebSocket 连接函数。
- **数据驾驶舱**（`Dashboard.vue`）：实时行情 ticker 优先走 WebSocket，断线降级为 5s HTTP 轮询；四张统计卡（StatCard 数字动画）、成功率仪表盘、行业饼图、走势速览、最近运行表；状态指示「实时/盘中/收盘」。
- **行情页**（`Stocks.vue`/`Funds.vue`）：K 线（蜡烛+成交量）/收盘线切换、关键指标条、全量/增量采集（管理员）、导出。
- **侧边栏**（`MainLayout.vue`）：六组二级菜单，按 `auth.isAdmin` 过滤管理员项，空组自动隐藏；顶栏展示角色标签、数据范围、导出权限、健康状态与实时时钟。
- **主题**（`styles/theme.css`）：CSS 变量定义深色金融科技风（深蓝底、霓虹青强调、毛玻璃卡片）。
- **Vite 代理**（`vite.config.js`）：`/api` 代理到 `127.0.0.1:8000` 且 `ws:true`，开发期免跨域、支持 WebSocket 升级。

> （图 4-1～4-6，待补）登录页、数据驾驶舱、股票 K 线、采集任务、监控运维、系统管理页面实测截图

<div style="page-break-after: always;"></div>
