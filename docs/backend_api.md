# 后端接口文档（backend_api.md）

> **项目名称**：股票基金数据获取和管理平台  
> **课程模块**：模块 2：AI 辅助设计  
> **文档定位**：RESTful API 设计与 OpenAPI 3.0 片段  
> **最终报告映射**：最终报告第 3 章 3.5 节  
> **代码依据**：backend/app/api、backend/app/schemas.py、FastAPI Swagger  
> **整理日期**：2026 年 6 月

## 0. 文档说明

本文档为课程设计过程文档的整理版，用于提交到 GitHub/Gitee 仓库。它与最终课程设计报告保持一致：仓库中保留本文件作为平时过程材料，最终报告中已将其核心内容合并到对应章节。

| 项目 | 内容 |
| --- | --- |
| 文档状态 | 最终整理版 |
| 是否合并进最终报告 | 是 |
| 后续需补充 | 团队真实姓名、学号、仓库地址、必要截图 |

---

## 1. 通用约定

- 统一前缀：`/api`
- 认证：除 `/api/health`、`/api/auth/login`、`/api/auth/token` 外，均需请求头 `Authorization: Bearer <token>`。
- 分页响应结构：`{ items: [], total, page, page_size }`。
- 错误响应：`{ "detail": "错误信息" }`，HTTP 状态码区分 400/401/403/404。
- 权限：标注「管理员」的接口需 admin 角色，否则返回 403。

## 2. 接口清单

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | /api/health | 健康检查 | 公开 |
| POST | /api/auth/login | 登录 | 公开 |
| POST | /api/auth/token | OAuth2 表单登录 | 公开 |
| GET | /api/auth/me | 当前用户 | 登录 |
| GET | /api/dashboard | 仪表盘统计 | 登录 |
| GET | /api/instruments | 标的列表（按角色 data_scope 行级过滤） | 登录 |
| GET | /api/stocks/{code}/daily | 股票日线查询（敏感列脱敏 + 时间权限钳制） | 登录 |
| GET | /api/funds/{code}/nav | 基金净值查询（含复权净值 adj_nav） | 登录 |
| POST | /api/query/sql | 受控只读 SQL 查询（白名单表 + 强制 LIMIT） | 管理员 |
| WS | /api/ws/quotes | WebSocket 实时行情/净值推送（?token=JWT） | 登录 |
| GET | /api/datasources | 数据源注册表与命中统计 | 登录 |
| GET | /api/announcements | 公告/新闻/舆情查询 | 登录 |
| GET | /api/tasks | 任务列表 | 登录 |
| POST | /api/tasks | 创建任务（支持 frequency 频率预设） | 管理员 |
| PATCH | /api/tasks/{id} | 更新任务 | 管理员 |
| DELETE | /api/tasks/{id} | 删除任务 | 管理员 |
| POST | /api/tasks/{id}/run | 执行任务 | 管理员 |
| POST | /api/tasks/crawl | 临时采集（stock_daily/fund_nav/announcement） | 管理员 |
| GET | /api/tasks/runs | 运行记录 | 登录 |
| GET | /api/tasks/{id} | 任务详情 | 登录 |
| GET | /api/tasks/{id}/logs | 任务日志 | 登录 |
| POST | /api/exports | 导出数据（支持 compress/encrypt 加密压缩） | 登录（受配额/功能权限/脱敏） |
| GET | /api/exports | 导出记录 | 登录 |
| GET | /api/exports/{id}/download | 下载导出文件 | 登录 |
| GET | /api/monitor/metrics | 系统运行指标（成功率/缓存/存储） | 登录 |
| GET | /api/monitor/integrity | 数据完整性检查 | 登录 |
| GET | /api/monitor/alerts | 告警中心（含异常监测，落库+分发） | 登录 |
| GET | /api/monitor/api-stats | API 性能指标（请求数/耗时/错误率） | 登录 |
| GET | /api/monitor/alert-records | 历史告警记录 | 登录 |
| GET | /api/metadata/dictionary | 数据字典（含字段敏感级别） | 登录 |
| GET | /api/metadata/lineage | 数据血缘 | 登录 |
| GET | /api/data-quality | 数据质量问题列表（跨源偏差/异常） | 登录 |
| POST | /api/data-quality/{id}/resolve | 人工校对（标记修正/忽略） | 管理员 |
| GET | /api/admin/users | 用户列表 | 管理员 |
| POST | /api/admin/users | 创建用户 | 管理员 |
| PATCH | /api/admin/users/{id} | 更新用户 | 管理员 |
| DELETE | /api/admin/users/{id} | 删除用户 | 管理员 |
| GET | /api/admin/roles | 角色列表 | 管理员 |
| PATCH | /api/admin/roles/{id} | 更新角色权限（数据/时间/功能） | 管理员 |
| GET | /api/admin/tenants | 租户列表 | 管理员 |
| POST | /api/admin/tenants | 创建租户 | 管理员 |
| GET | /api/audit/logs | 操作审计日志 | 管理员 |

> 采集相关接口（/api/tasks/crawl、/api/tasks）支持 `mode`（full/incremental）与 `frequency`（realtime/minute/daily/weekly/quarterly/manual）参数。
> 查询接口受令牌桶限流（429）+ 行级（data_scope）/时间（max_history_days）/字段级（敏感列脱敏）数据权限控制；结果走 TTL 缓存，采集后自动失效。
> 受控 SQL 查询仅允许单条 SELECT、表名白名单、禁 DML/DDL/多语句，并强制注入 LIMIT。

## 3. OpenAPI 3.0 片段（YAML）

```yaml
openapi: 3.0.3
info:
  title: 股票基金数据获取和管理平台 API
  version: 0.1.0
servers:
  - url: http://127.0.0.1:8000/api
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    LoginRequest:
      type: object
      required: [username, password]
      properties:
        username: { type: string }
        password: { type: string }
    Token:
      type: object
      properties:
        access_token: { type: string }
        token_type: { type: string, example: bearer }
        role: { type: string, enum: [admin, viewer, analyst] }
        username: { type: string }
    StockDailyOut:
      type: object
      properties:
        code: { type: string }
        trade_date: { type: string, format: date }
        open: { type: number }
        high: { type: number }
        low: { type: number }
        close: { type: number }
        volume: { type: number }
        amount: { type: number }
        pct_change: { type: number }
        source: { type: string }
    CrawlRunOut:
      type: object
      properties:
        id: { type: integer }
        job_id: { type: integer }
        trigger: { type: string, enum: [manual, scheduled] }
        status: { type: string, enum: [running, success, partial, failed] }
        rows_affected: { type: integer }
        source: { type: string }
        message: { type: string }
security:
  - bearerAuth: []
paths:
  /health:
    get:
      summary: 健康检查
      security: []
      responses:
        '200': { description: OK }
  /auth/login:
    post:
      summary: 用户登录
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/LoginRequest' }
      responses:
        '200':
          description: 登录成功
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Token' }
        '401': { description: 用户名或密码错误 }
  /stocks/{code}/daily:
    get:
      summary: 股票日线查询
      parameters:
        - { name: code, in: path, required: true, schema: { type: string } }
        - { name: start_date, in: query, schema: { type: string, format: date } }
        - { name: end_date, in: query, schema: { type: string, format: date } }
        - { name: page, in: query, schema: { type: integer, default: 1 } }
        - { name: page_size, in: query, schema: { type: integer, default: 60 } }
      responses:
        '200':
          description: 分页行情
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items: { $ref: '#/components/schemas/StockDailyOut' }
                  total: { type: integer }
                  page: { type: integer }
                  page_size: { type: integer }
  /tasks/crawl:
    post:
      summary: 临时采集（管理员）
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [job_type, target_codes]
              properties:
                job_type: { type: string, enum: [stock_daily, fund_nav, announcement] }
                target_codes: { type: string, example: "600519.SH,000001.SZ" }
      responses:
        '200':
          description: 运行记录
          content:
            application/json:
              schema: { $ref: '#/components/schemas/CrawlRunOut' }
        '403': { description: 需要管理员权限 }
  /exports:
    post:
      summary: 导出数据集（管理员）
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [dataset]
              properties:
                dataset: { type: string, enum: [stock_daily, fund_nav, instruments] }
                file_format: { type: string, enum: [csv, excel, parquet], default: csv }
                code: { type: string }
                start_date: { type: string, format: date }
                end_date: { type: string, format: date }
      responses:
        '200': { description: 导出记录 }
```

## 4. 请求示例

```bash
# 登录
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 查询行情（带 token）
curl "http://127.0.0.1:8000/api/stocks/600519.SH/daily?page_size=10" \
  -H "Authorization: Bearer <token>"

# 触发采集
curl -X POST http://127.0.0.1:8000/api/tasks/crawl \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"job_type":"stock_daily","target_codes":"000001.SZ"}'
```

## 接口实现对应关系

| 路由文件 | 负责接口 | 主要能力 |
| --- | --- | --- |
| `api/auth.py` | `/auth/login`、`/auth/token`、`/auth/me` | 登录、JWT 签发、当前用户 |
| `api/data.py` | `/instruments`、`/stocks/{code}/daily`、`/funds/{code}/nav` | 标的、股票行情、基金净值查询 |
| `api/tasks.py` | `/tasks`、`/tasks/crawl`、`/tasks/crawl-all` | 任务 CRUD、手动采集、运行日志 |
| `api/exports.py` | `/exports` | 多格式导出、压缩加密、下载隔离 |
| `api/monitor.py` | `/health`、`/dashboard`、`/monitor/*`、`/metadata/*` | 仪表盘、完整性、告警、数据血缘、审计 |
| `api/query.py` | `/query/sql` | 受控 SQL 查询 |
| `api/admin.py` | `/admin/users`、`/admin/roles`、`/admin/tenants` | 用户、角色、租户管理 |
| `api/ws.py` | `/ws/quotes` | WebSocket 实时行情推送 |

## 提交前核对

- [ ] 后端启动后 Swagger 能正常访问：`http://127.0.0.1:8000/docs`。
- [ ] 文档中的路径、方法、权限与 Swagger 一致。
- [ ] 管理员接口、登录接口、公开接口边界清晰。
