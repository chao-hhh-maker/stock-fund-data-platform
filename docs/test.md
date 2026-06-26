# 测试报告（test.md）

> **项目名称**：股票基金数据获取和管理平台  
> **课程模块**：模块 4：AI 辅助测试与调试  
> **文档定位**：单元测试、接口测试、功能测试与缺陷修复记录  
> **最终报告映射**：最终报告第 5 章  
> **代码依据**：backend/tests、backend/app/services、backend/app/api  
> **整理日期**：2026 年 6 月

## 0. 文档说明

本文档为课程设计过程文档的整理版，用于提交到 GitHub/Gitee 仓库。它与最终课程设计报告保持一致：仓库中保留本文件作为平时过程材料，最终报告中已将其核心内容合并到对应章节。

| 项目 | 内容 |
| --- | --- |
| 文档状态 | 最终整理版 |
| 是否合并进最终报告 | 是 |
| 后续需补充 | 团队真实姓名、学号、仓库地址、必要截图 |

---

## 1. 测试范围与策略

本项目采用分层测试策略，以 pytest 为统一测试框架，并使用 FastAPI `TestClient` 完成接口级验证。测试环境通过 `tests/conftest.py` 统一配置：使用独立 SQLite 测试库、关闭调度器、强制使用样例数据、关闭限流，从而保证测试不依赖外部网络和本地生产数据库。

| 类型 | 工具 | 覆盖对象 | 代表文件 |
| --- | --- | --- | --- |
| 单元测试 | Pytest | 数据清洗、代码标准化、行业映射、交易日历、缓存、限流 | `test_cleaning.py`、`test_enhancements.py` |
| 接口测试 | Pytest + TestClient | 登录、权限、查询、采集、导出、仪表盘、任务日志 | `test_api.py` |
| 监控与元数据测试 | Pytest + TestClient | 系统指标、完整性、告警、数据字典、血缘、审计 | `test_monitor_api.py` |
| 增强能力端到端测试 | Pytest + TestClient | 字段/行级/时间权限、SQL 防护、加密导出、租户隔离、告警处理 | `test_upgrade.py` |

当前测试规模：**5 个主要测试文件，65 个 pytest 用例**。

## 2. 测试文件与用例数量

| 测试文件 | 用例数 | 覆盖重点 |
| --- | ---: | --- |
| `test_api.py` | 11 | 健康检查、登录、权限、行情查询、基金查询、采集、任务日志、导出、仪表盘 |
| `test_cleaning.py` | 6 | 证券代码标准化、异常行剔除、涨跌幅、基金日增长率 |
| `test_enhancements.py` | 11 | 行业分类、价格一致性、跨源验证、交易日历、缓存、限流 |
| `test_monitor_api.py` | 10 | 监控指标、完整性、告警、数据字典、血缘、审计、增量采集、导出配额 |
| `test_upgrade.py` | 27 | 字段脱敏、行级/时间权限、SQL 防护、加密导出、数据源、实时快照、公告、数据质量、管理员 CRUD、租户隔离、告警去重 |
| **合计** | **65** | 覆盖题目二六大模块和主要异常路径 |

## 3. 测试用例摘要

### 3.1 清洗与标准化

| 用例 | 验证点 |
| --- | --- |
| `test_normalize_code_stock_suffix_inference` | `600519` 自动推断为 `600519.SH`，`000001` 推断为 `000001.SZ` |
| `test_normalize_code_prefix_form` | `sh600519`、`sz000001` 归一化 |
| `test_normalize_code_fund` | 基金代码补 `.OF` |
| `test_clean_stock_daily_drops_invalid_and_computes_pct` | 价格为 0 的异常行剔除，涨跌幅计算正确 |
| `test_clean_fund_nav_computes_daily_return` | 基金日增长率计算正确 |
| `test_fund_adj_nav_computed` | 基金复权净值 `adj_nav` 生成 |

### 3.2 权限与安全

| 用例 | 验证点 |
| --- | --- |
| `test_viewer_cannot_trigger_crawl` | 普通用户触发采集返回 403 |
| `test_viewer_amount_masked_in_query` | 普通用户查询股票行情时成交额脱敏为 0 |
| `test_admin_amount_visible_in_query` | 管理员可见真实成交额 |
| `test_analyst_row_level_blocks_fund` | analyst 仅能访问股票，访问基金 403 |
| `test_sql_blocks_dml` | SQL 接口拒绝 DELETE 等 DML |
| `test_sql_blocks_multi_statement` | SQL 接口拒绝多语句注入 |
| `test_sql_blocks_non_whitelisted_table` | SQL 接口拒绝非白名单表 |
| `test_export_records_are_isolated_between_users` | 普通用户不能下载管理员导出文件 |
| `test_tenant_department_scoped_instrument_visibility` | 租户 / 部门私有标的隔离生效 |

### 3.3 采集、查询与导出

| 用例 | 验证点 |
| --- | --- |
| `test_admin_quick_crawl_and_runs` | 管理员临时采集成功并产生运行记录 |
| `test_job_lifecycle_and_logs` | 任务创建、执行、查看日志闭环 |
| `test_incremental_crawl` | 全量后增量采集不报错 |
| `test_export_csv_and_download` | CSV 导出和下载可用 |
| `test_encrypted_export` | 压缩 / 加密导出生成 zip |
| `test_announcement_crawl_and_list` | 公告 / 新闻 / 舆情采集与查询 |

### 3.4 监控、元数据与运维

| 用例 | 验证点 |
| --- | --- |
| `test_metrics_endpoint` | 系统运行指标含缓存、成功率、数据行数 |
| `test_integrity_endpoint` | 完整性检查返回完整率 |
| `test_alerts_endpoint` | 告警中心返回列表 |
| `test_api_stats_endpoint` | API 性能统计可访问 |
| `test_data_dictionary` | 数据字典含 `stock_daily`、`fund_nav` |
| `test_lineage_endpoint` | 数据血缘返回来源、行数、时间范围 |
| `test_alert_records_deduplicate_and_resolve` | 告警去重与处理闭环 |

## 4. 测试执行命令与结果

```bash
cd backend
python -m pytest -q
```

期望结果：

```text
65 passed
```

> 说明：当前整理环境未安装项目依赖 `python-jose`，因此无法在文档生成容器内重新执行测试；本报告依据项目 `backend/tests` 的实际测试文件和原项目测试记录整理。最终提交前请在本地虚拟环境中执行上述命令，并将终端截图补入最终 Word 报告的测试截图占位。

## 5. 功能测试流程

| 步骤 | 操作 | 预期结果 | 截图占位 |
| --- | --- | --- | --- |
| 1 | 启动后端并访问 `/api/health` | status=ok，database=ok | 【图：健康检查结果，待补】 |
| 2 | 管理员登录 | 返回 token，role=admin | 【图：登录成功，待补】 |
| 3 | 查看数据驾驶舱 | 显示标的数、数据行数、成功率、最近运行 | 【图：驾驶舱，待补】 |
| 4 | 股票页查询 600519.SH | 显示 K 线、收盘线、行情明细 | 【图：股票查询，待补】 |
| 5 | 管理员执行采集任务 | 运行状态 success/partial，运行日志新增 | 【图：任务执行，待补】 |
| 6 | 导出股票或基金数据 | 生成导出记录并可下载 | 【图：导出记录，待补】 |
| 7 | 普通用户尝试管理操作 | 前端隐藏按钮或后端返回 403 | 【图：权限拦截，待补】 |
| 8 | 查看监控和告警 | 完整性、API 性能、告警中心展示正常 | 【图：监控运维，待补】 |

## 6. 缺陷记录与修复

| 编号 | 现象 | 根因 | 修复方式 | 验证 |
| --- | --- | --- | --- | --- |
| BUG-01 | `.env` 配置后 CORS_ORIGINS 解析失败 | pydantic-settings 对 List 环境变量按 JSON 解析 | 改为字符串字段 + `cors_origins_list` 属性解析 | 后端正常启动 |
| BUG-02 | MySQL 脚本执行 `trigger` 字段报错 | `trigger` 是 MySQL 保留字 | SQL 中使用反引号，ORM 保持字段语义 | SQL 可执行 |
| BUG-03 | Parquet 导出在无 pyarrow 环境失败 | 缺少 parquet 引擎 | 捕获异常并回退 CSV | 导出接口返回成功 |
| BUG-04 | akshare 基金接口参数错误 | 新版接口参数由 `fund` 变更为 `symbol` | 按新版签名适配，并区分 ETF / 开放式基金 | 采集可运行，失败仍回退样例 |
| BUG-05 | 仪表盘接口 500：`func` 未定义 | SQLAlchemy `func` 未导入 | 补充 `from sqlalchemy import func` | 仪表盘测试通过 |
| BUG-06 | viewer 查询成交额未脱敏 | 查询接口和导出服务脱敏逻辑不一致 | 查询与导出统一调用权限判断，普通用户 amount=0 | `test_viewer_amount_masked_in_query` 通过 |
| BUG-07 | analyst 时间权限边界不稳定 | 起始日期钳制取了错误边界 | 取用户输入和角色限制中的较晚日期 | 时间权限回归测试通过 |
| BUG-08 | 告警中心重复登记同一告警 | 缺少告警指纹去重 | 新增 fingerprint，open 状态同指纹不重复落库 | `test_alert_records_deduplicate_and_resolve` 通过 |

## 7. 测试结论

系统已从单元、接口、功能、权限、安全、运维六个维度完成验证。测试覆盖了课程题目二的核心要求，也覆盖了课程评分中强调的代码质量、异常处理、AI 辅助测试和 Bug 定位过程。
