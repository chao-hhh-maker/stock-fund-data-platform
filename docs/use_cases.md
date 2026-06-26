# 交互场景文档（use_cases.md）

> **项目名称**：股票基金数据获取和管理平台  
> **课程模块**：模块 1：项目启动与 AI 辅助需求分析  
> **文档定位**：关键用户故事的交互场景 / 用例  
> **最终报告映射**：最终报告第 2 章 2.3 节  
> **代码依据**：frontend/src/views、backend/app/api、backend/app/services  
> **整理日期**：2026 年 6 月

## 0. 文档说明

本文档为课程设计过程文档的整理版，用于提交到 GitHub/Gitee 仓库。它与最终课程设计报告保持一致：仓库中保留本文件作为平时过程材料，最终报告中已将其核心内容合并到对应章节。

| 项目 | 内容 |
| --- | --- |
| 文档状态 | 最终整理版 |
| 是否合并进最终报告 | 是 |
| 后续需补充 | 团队真实姓名、学号、仓库地址、必要截图 |

---

约定：主路径为正常流程，扩展为异常 / 替代流程。接口前缀统一 `/api`。

---

## UC-01 用户登录（对应 US-01）

- 参与者：平台用户
- 前置条件：用户已存在且处于启用状态
- 主路径：
  1. 用户在登录页输入用户名、密码并提交。
  2. 前端 POST `/api/auth/login`。
  3. 后端校验密码（pbkdf2_sha256），通过则签发 JWT（含 sub、role、exp）。
  4. 前端保存 token 与角色到本地存储，跳转仪表盘。
- 扩展：
  - 3a 密码错误：返回 401，前端提示「用户名或密码错误」。
  - 4a 后续请求 token 过期：拦截器捕获 401，清理登录态并跳回登录页。

---

## UC-02 手动采集（对应 US-03/US-04/US-06/US-07）

- 参与者：管理员
- 前置条件：已登录且角色为 admin
- 主路径：
  1. 管理员在股票/基金页点击「采集」，或在任务页点击「执行」。
  2. 前端 POST `/api/tasks/crawl`（或 `/api/tasks/{id}/run`）。
  3. 后端创建 CrawlRun（status=running）。
  4. 采集器对每个代码：抓取 → 清洗标准化 → upsert 入库。
  5. 汇总影响行数与来源，更新运行状态为 success/partial/failed。
  6. 返回运行记录，前端刷新数据与图表。
- 扩展：
  - 1a 非管理员触发：后端返回 403。
  - 4a 外部数据源异常：捕获后回退样例数据，source=sample，流程继续。
  - 4b 个别代码失败：记入 errors，整体状态置为 partial，不中断其它代码。

---

## UC-03 定时采集（对应 US-05）

- 参与者：系统（调度器）
- 前置条件：存在 enabled=true 且 cron 非空的任务
- 主路径：
  1. 应用启动时，调度器加载所有启用且含 cron 的任务。
  2. APScheduler 按 cron 到点回调 `execute_job_by_id`。
  3. 使用独立数据库会话执行任务（同 UC-02 步骤 3-5），trigger=scheduled。
- 扩展：
  - 1a cron 表达式非法：记录错误日志，跳过该任务的调度注册。
  - 2a 应用关闭：调度器安全停止，不影响进行中的请求。

---

## UC-04 行情查询（对应 US-10/US-11/US-12）

- 参与者：普通用户 / 管理员
- 主路径：
  1. 用户在股票/基金页选择标的与日期范围。
  2. 前端 GET `/api/stocks/{code}/daily`（或 `/api/funds/{code}/nav`），带分页与日期参数。
  3. 后端按条件查询并分页返回。
  4. 前端渲染表格与 ECharts 走势图。
- 扩展：
  - 3a 无数据：返回空列表，前端显示「暂无数据」。

---

## UC-05 数据导出与下载（对应 US-13/US-14）

- 参与者：管理员
- 主路径：
  1. 管理员选择数据集、格式、可选代码，提交导出。
  2. 前端 POST `/api/exports`。
  3. 后端查询数据 → 用 pandas 写入文件（CSV/Excel/Parquet）→ 落 export_records。
  4. 返回导出记录。
  5. 管理员在导出页点击「下载」，GET `/api/exports/{id}/download` 获取文件流。
- 扩展：
  - 3a Parquet 引擎缺失：自动回退 CSV。
  - 5a 文件已被清理：返回 404 并提示重新导出。

---

## UC-06 查看仪表盘与健康（对应 US-15/US-16）

- 参与者：所有登录用户
- 主路径：
  1. 进入仪表盘，前端 GET `/api/dashboard`。
  2. 后端聚合标的数、数据行数、最近 5 条运行与导出记录。
  3. 前端以统计卡片 + 表格展示。
  4. 健康检查 GET `/api/health`（公开）返回 DB 与调度器状态。

## 用例到测试的追踪关系

| 用例 | 自动化测试 / 手工验证 | 说明 |
| --- | --- | --- |
| UC-01 用户登录 | `test_login_success_and_failure`、`test_me_requires_token` | 覆盖成功、失败、无 token 三类分支 |
| UC-02 手动采集 | `test_admin_quick_crawl_and_runs`、`test_viewer_cannot_trigger_crawl` | 覆盖管理员成功与普通用户 403 |
| UC-03 定时采集 | `test_job_lifecycle_and_logs`、任务页手工验证 | 覆盖任务创建、执行与日志 |
| UC-04 行情查询 | `test_stock_daily_query_paginated`、`test_fund_nav_query` | 覆盖分页和净值查询 |
| UC-05 导出下载 | `test_export_csv_and_download`、`test_encrypted_export` | 覆盖 CSV、压缩/加密、下载 |
| UC-06 监控健康 | `test_health_public`、`test_metrics_endpoint`、`test_integrity_endpoint` | 覆盖健康、完整性、指标 |

## 提交前核对

- [ ] 每个主路径都能对应到前端菜单或 Swagger 接口。
- [ ] 每个异常路径至少有一种测试或手工验证方式。
- [ ] 权限失败、数据源失败、无数据三类情况均已写入扩展流程。
