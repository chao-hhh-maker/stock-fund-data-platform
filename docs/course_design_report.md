# 课程设计报告 Markdown 备份（course_design_report.md）

> **项目名称**：股票基金数据获取和管理平台  
> **课程模块**：模块 5：上线部署与报告撰写  
> **文档定位**：最终 Word 报告的 Markdown 备份 / 仓库可读版  
> **最终报告映射**：最终 Word 报告全文  
> **代码依据**：final_report_integrated.md、docs、backend、frontend  
> **整理日期**：2026 年 6 月

## 0. 文档说明

本文档为课程设计过程文档的整理版，用于提交到 GitHub/Gitee 仓库。它与最终课程设计报告保持一致：仓库中保留本文件作为平时过程材料，最终报告中已将其核心内容合并到对应章节。

| 项目 | 内容 |
| --- | --- |
| 文档状态 | 最终整理版 |
| 是否合并进最终报告 | 是 |
| 后续需补充 | 团队真实姓名、学号、仓库地址、必要截图 |

---

<div align="center">

# 《软件工程理论与实践》课程设计报告

## 股票基金数据获取和管理平台

（课程设计题目二 · 最终整合版）

<br/>

| 项目 | 内容 |
| --- | --- |
| 课程名称 | 软件工程理论与实践课程设计 |
| 设计题目 | 题目二　股票基金数据获取和管理平台 |
| 项目仓库 | GitHub：`https://github.com/XCT-byte/stock-fund-data-platform`（以实际为准） |
| 班级 | ________（请填写） |
| 小组负责人 | ________（学号：________） |
| 团队成员 | ________、________、________、________ |
| 指导教师 | ________ |
| 完成日期 | 2026 年 6 月 |

<br/>

> 本报告为课程设计最终整合版，已按指导书要求将模块 1—5 的平时过程文档合并进正文，并在第 1.4 节给出清晰的“过程文档合并来源表”。
> 报告正文同时结合最新代码进行重新梳理，覆盖需求、设计、实现、测试、部署、AI 使用记录、分工记录和代码附录。
> 文中标注「（图 X，待补）」之处为预留截图位，由小组在最终排版时统一插入实测截图。

</div>

<div style="page-break-after: always;"></div>

---

## 目录

- 第 1 章　引言
  - 1.1 项目背景与选题说明
  - 1.2 项目目标
  - 1.3 报告组织结构
  - 1.4 平时过程文档合并说明（重点）
  - 1.5 最新代码复核说明
  - 1.6 团队分工与过程管理
  - 1.7 仓库与目录结构
- 第 2 章　需求分析
  - 2.1 角色定义
  - 2.2 用户故事
    - 史诗 1：账户与权限
    - 史诗 2：数据采集
    - 史诗 3：数据清洗与标准化
    - 史诗 4：数据查询与导出
    - 史诗 5：监控与运维
  - 2.3 交互场景（用例）
    - UC-01 用户登录（对应 US-01）
    - UC-02 手动采集（对应 US-03/04/06/07）
    - UC-03 定时采集（对应 US-05）
    - UC-04 行情查询（对应 US-10/11/12）
    - UC-05 数据导出与下载（对应 US-13/14）
    - UC-06 查看仪表盘与健康（对应 US-15/16）
  - 2.4 题目二需求逐条覆盖对照
    - 模块 1 · 数据获取与采集
    - 模块 2 · 数据清洗与标准化
    - 模块 3 · 数据存储与管理
    - 模块 4 · 数据查询与 API 服务
    - 模块 5 · 数据监控与运维
    - 模块 6 · 用户权限与安全管理
- 第 3 章　系统设计
  - 3.1 技术选型
  - 3.2 总体架构
  - 3.3 核心类设计
  - 3.4 数据库设计
    - 3.4.1 设计概览
    - 3.4.2 关键表字段（节选）
  - 3.5 后端 API 设计
  - 3.6 前端 UI 设计
    - 3.6.1 信息架构
    - 3.6.2 视觉风格
  - 3.7 企业级能力的轻量等价实现
- 第 4 章　系统实现
  - 4.0 实现复核总览
  - 4.1 后端工程结构
  - 4.2 认证与三层数据权限
    - 4.2.1 认证流程
    - 4.2.2 三层数据权限
  - 4.3 数据采集与多源兜底
  - 4.4 数据清洗与标准化
  - 4.5 存储、缓存与限流
  - 4.6 查询、SQL 接口与 WebSocket
  - 4.7 数据导出与加密压缩
  - 4.8 监控运维与告警
  - 4.9 数据质量与人工校对
  - 4.10 任务调度
  - 4.11 前端实现要点
- 第 5 章　测试与调试
  - 5.1 测试策略
  - 5.2 单元测试
  - 5.3 接口测试
  - 5.4 功能测试
  - 5.5 缺陷定位与修复记录
- 第 6 章　部署与使用
  - 6.1 环境要求
  - 6.2 后端部署
- 1. 进入后端目录
- 2. 创建并激活虚拟环境
- Windows
- Linux/macOS
- 3. 安装依赖
- 4. （可选）复制环境变量模板并按需修改
- 5. 启动服务（默认 http://127.0.0.1:8000）
  - 6.3 前端部署
- 1. 进入前端目录
- 2. 安装依赖
- 3. 开发模式启动（默认 http://127.0.0.1:5173，已代理 /api 与 /ws 到后端）
- 4. 生产构建（产物在 dist/，可由 Nginx 等静态托管）
  - 6.4 切换 MySQL 与启用真实数据源
  - 6.5 配置项说明
  - 6.6 软件使用说明
  - 6.7 演示脚本
- 第 7 章　AI 使用报告
  - 7.1 使用原则
  - 7.2 各模块 AI 交互记录
  - 7.3 AI 易错点与人工修正
  - 7.4 AI 伦理与诚信说明
- 第 8 章　总结与展望
  - 8.1 工作总结
  - 8.2 项目特色
  - 8.3 不足与展望
  - 8.4 课程收获
- 附录 A　核心代码节选
  - A.1 受控只读 SQL 查询（安全设计）
- 允许查询的表白名单
- 外层统一强制 LIMIT，用户尾部 LIMIT 被接口参数替代
  - A.2 角色权限种子（RBAC 三账号）
- admin：全权限
- viewer：全范围、可导出（受配额）、敏感字段脱敏
- analyst：仅股票（行级）、近 365 天（时间级）、禁导出（功能）
  - A.3 导出配额与功能权限检查
  - A.4 Python SDK（题目「Python 封装」）
  - A.5 应用启动编排（lifespan）
- 附录 B　图表索引
- 附录 C　答辩问答准备

<div style="page-break-after: always;"></div>

---

# 第 1 章　引言

> **合并来源说明**：本章整合 README.md、assign.md、课程设计实验指导书中“项目启动”和“报告撰写”要求，并补充最终代码复核摘要。

## 1.1 项目背景与选题说明

金融数据是量化研究、投资分析与风险监控的基础生产资料。一个可用的股票基金数据平台，需要解决「数据从哪来、怎么洗干净、存在哪、怎么查、谁能查、出问题怎么发现」这一整条数据生命周期问题。课程设计题目二「股票基金数据获取和管理平台」正是围绕这条主线，要求实现六大模块：

1. 数据获取与采集
2. 数据清洗与标准化
3. 数据存储与管理
4. 数据查询与 API 服务
5. 数据监控与运维
6. 用户权限与安全管理

本组选择题目二，构建了一个**前后端分离、克隆即可运行、断网亦可演示**的金融数据平台。系统以股票日线行情与基金净值为核心数据对象，覆盖「采集 → 清洗 → 存储 → 查询 → 导出 → 监控 → 权限」的完整闭环，并按题目原文清单逐条对照实现（详见 2.4 节）。

设计上遵循一条重要原则：**在不牺牲题目能力的前提下，用轻量等价方案替换重型基础设施**。例如题目要求的 Redis 实时缓存、ClickHouse 列式存储、MongoDB/ES 文档存储，本项目分别用「进程内 TTL 缓存」「关系库 + 受控 SQL 聚合」「announcements 文档表」做架构等价实现，并在代码中预留可替换接口。这样既覆盖了题目要求，又保证助教/教师 `git clone` 后无需安装任何中间件即可一键启动、稳定演示。

## 1.2 项目目标

- 建立统一的数据获取入口，支持股票日线与基金净值的多渠道采集，外部源不可用时自动兜底。
- 建立数据清洗与标准化流程，统一证券代码、剔除异常值、计算复权净值与衍生指标。
- 建立可查询、可导出、可追踪的后端 RESTful API 与深色金融科技风前端。
- 建立数据完整性监控、异常监测、告警分发与 API 性能监控的运维体系。
- 建立多租户 + RBAC 的安全体系，实现功能权限、行级、时间级、字段级四类权限控制与操作审计。
- 按课程要求，全过程使用 AI 辅助并记录「人在回路」的迭代过程，沉淀完整的需求、设计、实现、测试、部署文档。

## 1.3 报告组织结构

本报告按软件工程经典流程「需求 → 设计 → 实现 → 测试 → 部署」组织，对应课程设计模块 1—5：

| 章节 | 对应课程模块 | 整合的过程文档 |
| --- | --- | --- |
| 第 1 章 引言 | 模块 1 项目启动 | README.md、assign.md |
| 第 2 章 需求分析 | 模块 1 需求分析 | user_stories.md、use_cases.md、requirements_coverage.md |
| 第 3 章 系统设计 | 模块 2 设计 | architect.md、db.md、backend_api.md、ui_design.md |
| 第 4 章 系统实现 | 模块 3 编码实现 | 项目源码、architect.md |
| 第 5 章 测试与调试 | 模块 4 测试 | test.md |
| 第 6 章 部署与使用 | 模块 5 部署 | install.md、user_guid.md |
| 第 7 章 AI 使用报告 | 贯穿模块 1—5 | ai.md |
| 第 8 章 总结与展望 | — | — |
| 附录 | 模块 5 报告 | 代码附录、图表索引 |


## 1.4 平时过程文档合并说明（重点）

根据指导书要求，模块 1 至模块 5 产生的平时过程文档最终需要汇总到课程设计报告中。为避免最终报告只呈现“结果”而看不出“过程文档已合并”，本报告在正文中采用两种标记方式：

1. 在每一章章标题下方增加“合并来源说明”，明确指出该章由哪些 md 文档、源码目录或测试文件合并而来。
2. 在本节给出“过程文档 → 报告章节”的总对照表，老师可按表快速检查每份要求文档在最终报告中的位置。

**表 1-3　平时过程文档最终合并对照表**

| 指导书要求的过程文档 / 交付物 | 原仓库位置 | 已合并到本报告的位置 | 合并方式说明 |
| --- | --- | --- | --- |
| README.md | 根目录 README.md | 第 1 章、第 6 章 | 合并项目背景、目标、技术路线、快速开始、目录结构和演示入口 |
| 用户故事文档 | docs/user_stories.md | 第 2.2 节 | 按史诗/角色组织用户故事，并保留“作为…我想…以便…”格式 |
| 交互场景文档 | docs/use_cases.md | 第 2.3 节 | 合并登录、采集、定时任务、查询、导出、监控等主流程用例 |
| 需求覆盖表 | docs/requirements_coverage.md | 第 2.4 节 | 按题目二原文六大模块逐条说明实现程度与对应代码 |
| 架构和类设计文档 | docs/architect.md | 第 3.1—3.3 节、第 4 章 | 合并技术选型、总体架构、服务层/模型层类职责、轻量等价设计 |
| 数据库设计文档 | docs/db.md、sql/init.sql | 第 3.4 节、附录 | 合并 ER 设计、核心表、字段、约束、索引、数据字典和建表脚本说明 |
| 后端接口文档 | docs/backend_api.md、FastAPI Swagger | 第 3.5 节、第 4 章 | 合并 RESTful API 分组、请求响应模型、鉴权与错误处理 |
| 前端 UI 文档 | docs/ui_design.md、frontend/src | 第 3.6 节、第 4.11 节 | 合并信息架构、页面设计、导航分组、深色金融科技风格和图表设计 |
| 可运行项目代码 | backend/、frontend/、sdk/、sql/ | 第 4 章、附录 A | 结合最新代码逐模块说明实现逻辑，并节选关键代码 |
| 测试报告 | docs/test.md、backend/tests | 第 5 章 | 合并测试策略、测试用例、执行结果、缺陷修复与覆盖范围 |
| 安装文档 | docs/install.md | 第 6.1—6.5 节 | 合并本地部署、依赖安装、配置项、MySQL/真实数据源切换 |
| 软件使用说明书 | docs/user_guid.md | 第 6.6—6.7 节 | 合并登录账号、菜单说明、典型操作流程和答辩演示脚本 |
| AI 使用文档 | docs/ai.md | 第 7 章 | 合并 Prompt 示例、AI 输出摘要、人工迭代修改、AI 易错点与诚信说明 |
| 工作完成情况文档 | docs/assign.md | 第 1.5 节 | 合并团队角色、模块分工、完成状态和过程管理说明 |
| 代码附录 | 当前最新源码 | 附录 A | 节选安全 SQL、RBAC、导出权限、SDK、应用启动等关键实现 |

**合并结论**：本报告不是单独新写的总结性文档，而是对课程设计全过程文档的最终归档版。平时提交的需求、设计、测试、部署、AI 使用、分工等文档均已进入正文对应章节；若老师检查仓库中的 md 文档，也能与本报告章节一一对应。

## 1.5 最新代码复核说明

在生成最终报告前，已对当前仓库代码重新复核，而不是仅依据旧文档改写。复核范围包括后端应用、测试用例、前端页面、SDK 与 SQL 脚本：

**表 1-4　最新代码复核范围**

| 复核对象 | 文件数量 | 代码行数（约） | 重点核查内容 |
| --- | ---: | ---: | --- |
| backend/app | 38 | 5331 | FastAPI 路由、ORM 模型、认证权限、采集清洗、导出、监控、告警、调度 |
| backend/tests | 7 | 774 | 清洗单元测试、核心 API、监控接口、权限与增强能力端到端测试 |
| frontend/src | 26 | 2990 | Vue 页面、路由守卫、Pinia 认证、Axios 拦截、ECharts 图表与深色 UI |
| sdk | 1 | 122 | Python 客户端封装、登录、查询、导出、下载接口 |
| sql | 1 | 217 | MySQL 建表脚本、索引、唯一约束与种子数据 |
| 合计 | 73 | 9434 | 覆盖课程设计完整工程闭环 |

本次复核确认项目当前已形成以下能力闭环：

- 后端包含 13 张业务表，覆盖租户、角色、用户、证券标的、股票日线、基金净值、公告舆情、采集任务、采集运行记录、导出记录、审计日志、数据质量问题、告警记录。
- 数据库样例库中已有 46 个标的、8144 条股票日线、4352 条基金净值、565 条公告/新闻/舆情、115 条告警记录，可支撑断网演示。
- 后端测试文件共定义 65 个 pytest 用例，覆盖清洗、采集、查询、导出、监控、权限、SQL 防护、告警去重、管理员 CRUD 等关键路径。
- 前端已形成登录、驾驶舱、股票、基金、公告舆情、采集任务、数据源、数据质量、监控运维、元数据、SQL 查询、导出、系统管理、审计日志等页面。
- 项目提供 Python SDK 与 SQL 建表脚本，满足题目“Python 封装”“数据库创建脚本”“API 服务”等交付要求。

> （图 1-0，待补）最终仓库代码结构与 docs 文档目录截图。建议在此处插入 VS Code / 文件资源管理器截图，展示 README、docs、backend、frontend、sdk、sql 等目录。


## 1.6 团队分工与过程管理

本组共 5 人，按软件工程角色分工，组长统一负责范围控制、文档整合与答辩串讲。各成员均参与 AI 辅助开发，并能解释本人负责模块中由 AI 生成的代码逻辑（见第 7 章）。

**表 1-1　团队成员与角色分工**

| 角色 | 成员 | 班级 | 学号 | GitHub 用户 | 核心职责 |
| --- | --- | --- | --- | --- | --- |
| 组长 / 产品与文档 | 成员 A | ____ | ____ | ____ | 范围控制、文档整合、答辩串讲 |
| 数据采集 | 成员 B | ____ | ____ | ____ | 数据源、采集脚本、清洗规则 |
| 后端与数据库 | 成员 C | ____ | ____ | ____ | 数据模型、接口、权限、导出 |
| 前端与可视化 | 成员 D | ____ | ____ | ____ | 页面、图表、联调 |
| 测试与运维 | 成员 E | ____ | ____ | ____ | 测试用例、部署、缺陷跟踪 |

**表 1-2　按课程模块的分工与完成情况**

| 模块 | 工作项 | 负责人 | 交付物 | 状态 |
| --- | --- | --- | --- | --- |
| 模块 1 需求分析 | 题目分析与范围控制 | A | README 范围章节 | 完成 |
| 模块 1 需求分析 | 用户故事编写 | A、B | user_stories.md | 完成 |
| 模块 1 需求分析 | 交互场景编写 | A | use_cases.md | 完成 |
| 模块 1 需求分析 | 仓库与目录初始化 | C | 目录结构 | 完成 |
| 模块 2 设计 | 架构与类设计 | C | architect.md | 完成 |
| 模块 2 设计 | 数据库 ER 与建表 | C | db.md、sql/init.sql | 完成 |
| 模块 2 设计 | API 设计 | C | backend_api.md | 完成 |
| 模块 2 设计 | 前端 UI 设计 | D | ui_design.md | 完成 |
| 模块 3 实现 | 后端核心层与模型 | C | core/、models.py | 完成 |
| 模块 3 实现 | 认证与三层权限 | C | security.py、deps.py、auth.py | 完成 |
| 模块 3 实现 | 采集与清洗服务 | B | crawler.py、cleaning.py、sample_data.py | 完成 |
| 模块 3 实现 | 任务调度 | B、C | task_service.py、scheduler.py | 完成 |
| 模块 3 实现 | 查询/导出/监控接口 | C | data.py、exports.py、monitor.py | 完成 |
| 模块 3 实现 | 前端工程与页面 | D | frontend/ 全部 | 完成 |
| 模块 4 测试 | 单元/接口/增强测试 | E | tests/ 五个测试文件 | 完成 |
| 模块 4 测试 | 缺陷跟踪与修复 | E、C | test.md 缺陷表 | 完成 |
| 模块 5 部署 | 安装部署文档 | E | install.md | 完成 |
| 模块 5 部署 | 使用说明书 | A | user_guid.md | 完成 |
| 模块 5 部署 | AI 记录与报告整合 | 全员 / A | ai.md、本报告 | 完成 |

**过程管理**：按课程要求「每个模块完成后及时提交到仓库」，本组在 GitHub 上以阶段性 commit 记录推进过程（需求文档 → 设计文档 → 后端骨架 → 前端页面 → 测试 → 增强迭代 → 文档整合）。AI 使用记录（ai.md）与分工记录（assign.md）从第一天起持续维护，避免后期补文档失真。

## 1.7 仓库与目录结构

项目采用前端、后端、SQL、文档、SDK 分目录的清晰结构：

```text
stock-fund-data-platform/
├── README.md                     # 项目主页、团队信息、快速开始
├── LICENSE                       # MIT 许可证
├── backend/                      # 后端（FastAPI）
│   ├── app/
│   │   ├── main.py               # 应用入口（lifespan：建表→种子→调度→可选后台采集）
│   │   ├── models.py             # ORM 数据模型（13 张表）
│   │   ├── schemas.py            # Pydantic 请求/响应契约
│   │   ├── seed.py               # 种子数据（用户/标的/样例行情）
│   │   ├── api/                  # 路由层
│   │   │   ├── auth.py           # 认证：登录 / 当前用户
│   │   │   ├── deps.py           # 依赖：鉴权、限流、三层数据权限
│   │   │   ├── data.py           # 标的 / 股票日线 / 基金净值查询
│   │   │   ├── query.py          # 受控只读 SQL 查询（管理员）
│   │   │   ├── exports.py        # 数据导出 + 加密压缩 + 下载
│   │   │   ├── tasks.py          # 采集任务 CRUD / 触发 / 运行记录
│   │   │   ├── monitor.py        # 监控 / 告警 / 元数据 / 数据质量 / 审计
│   │   │   ├── admin.py          # 用户 / 角色 / 租户管理
│   │   │   └── ws.py             # WebSocket 实时行情推送
│   │   ├── core/                 # 核心层
│   │   │   ├── config.py         # 配置（pydantic-settings）
│   │   │   ├── database.py       # 数据库初始化 + 启动自动迁移
│   │   │   ├── security.py       # 密码哈希 + JWT
│   │   │   ├── cache.py          # 进程内 TTL 缓存
│   │   │   ├── rate_limit.py     # 令牌桶限流
│   │   │   └── metrics_middleware.py  # API 性能监控中间件
│   │   ├── services/             # 服务层（业务逻辑）
│   │   │   ├── crawler.py        # 采集：akshare→腾讯→新浪→样例
│   │   │   ├── cleaning.py       # 清洗：标准化/校验/复权/行业分类
│   │   │   ├── export_service.py # 导出：格式转换/脱敏/压缩加密
│   │   │   ├── realtime_service.py    # 实时行情快照
│   │   │   ├── monitor_service.py     # 完整性/异常监测/告警分发
│   │   │   ├── data_quality_service.py# 数据质量问题与人工校对
│   │   │   ├── audit_service.py  # 操作审计
│   │   │   ├── user_service.py   # 认证 + 种子用户
│   │   │   ├── task_service.py   # 任务执行包装
│   │   │   ├── datasource_registry.py # 多源注册表与命中统计
│   │   │   ├── calendar_service.py    # A 股交易日历/节假日
│   │   │   ├── metadata_service.py    # 数据字典与血缘
│   │   │   └── sample_data.py    # 样例数据生成器（离线兜底）
│   │   └── tasks/scheduler.py    # APScheduler 定时调度
│   ├── tests/                    # 测试（5 个测试文件，65 用例）
│   ├── requirements.txt          # 后端依赖
│   └── .env.example              # 环境变量模板
├── frontend/                     # 前端（Vue 3 + Vite）
│   └── src/
│       ├── main.js / App.vue
│       ├── router/index.js       # 路由 + 登录/管理员守卫
│       ├── stores/auth.js        # Pinia 认证状态
│       ├── api/{http.js,index.js}# Axios 实例 + 接口集中定义 + WS
│       ├── layouts/MainLayout.vue# 侧边栏六组菜单 + 顶栏
│       ├── components/           # StatCard / LineChart / KLineChart / MiniChart
│       ├── views/                # 14 个页面
│       └── styles/theme.css      # 深色金融科技风主题变量
├── sdk/stockfund_client.py       # Python SDK（题目「Python 封装」）
├── sql/init.sql                  # MySQL 建表脚本（12 张表 + 种子）
└── docs/                         # 全部过程文档
    ├── user_stories.md  use_cases.md  requirements_coverage.md
    ├── architect.md     db.md          backend_api.md  ui_design.md
    ├── test.md          ai.md          assign.md
    ├── install.md       user_guid.md   course_design_report.md（本报告）
```

> （图 1-1，待补）GitHub 仓库首页与目录结构截图
> （图 1-2，待补）阶段性 commit 记录截图

<div style="page-break-after: always;"></div>

---

# 第 2 章　需求分析

> **合并来源说明**：本章整合 user_stories.md、use_cases.md、requirements_coverage.md，并按题目二六大模块逐条对照实现情况。

> 对应课程模块 1。本章在 AI 辅助下，按「了解需求 → 生成用户故事 → 编写交互场景」的流程开展（提示词与迭代过程见第 7 章），并最终逐条对照题目二原文需求清单核验覆盖情况。

## 2.1 角色定义

系统面向三类人工角色与一类系统角色。三个人工角色对应三个内置演示账号，用于直观展示「功能 / 行级 / 时间 / 字段」四类权限差异：

**表 2-1　角色与演示账号**

| 角色 | 演示账号 | 数据范围 | 历史时限 | 可否导出 | 敏感字段 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| 管理员 admin | admin / admin123 | 全部 | 不限 | 是 | 可见 | 平台运维，可采集、管理任务、SQL 查询、系统管理 |
| 普通用户 viewer | viewer / viewer123 | 全部 | 不限 | 是（受配额） | 脱敏 | 查询/查看为主，成交额等敏感字段脱敏 |
| 研究员 analyst | analyst / analyst123 | 仅股票 | 近 365 天 | 否 | 脱敏 | 演示行级（仅股票）+ 时间（近一年）+ 功能（禁导出）权限 |
| 系统 system | —（调度器） | — | — | — | — | APScheduler 按 cron 自动触发采集 |

## 2.2 用户故事

遵循「作为一名……我想……以便……」标准格式，按 5 个史诗组织，共 16 条用户故事，每条附验收标准。以下为完整清单。

### 史诗 1：账户与权限

**US-01 登录认证**
作为一名平台用户，我想用用户名和密码登录系统，以便安全地访问受保护的数据与功能。
- 验收：正确凭证返回 JWT 令牌与角色信息；错误凭证返回 401 与明确提示；令牌过期后访问受保护接口被拒并提示重新登录。

**US-02 基于角色的权限控制**
作为一名系统管理员，我想让采集、导出、任务管理等敏感操作仅对管理员开放，以便防止普通用户误操作或越权。
- 验收：普通用户调用采集/导出接口返回 403；普通用户可正常查询行情、净值与查看任务日志。

### 史诗 2：数据采集

**US-03 手动采集股票日线**　作为一名管理员，我想手动触发某只股票的日线采集，以便快速补充或更新指定标的的数据。
- 验收：输入代码后执行成功，数据入库，返回影响行数与数据来源。

**US-04 手动采集基金净值**　作为一名管理员，我想手动触发基金净值采集，以便维护基金数据。
- 验收：同上，落库到 fund_nav。

**US-05 定时自动采集**　作为一名系统，我想按 cron 计划自动执行启用的采集任务，以便数据保持新鲜而无需人工值守。
- 验收：配置 cron 的任务到点自动执行并写入运行记录，触发类型标记为 scheduled。

**US-06 采集失败可追踪**　作为一名管理员，我想在某些代码采集失败时不影响其它代码，并能看到失败原因，以便定位问题。
- 验收：单代码异常被捕获，运行状态标记为 partial/failed，message 记录错误。

**US-07 数据源不可用时的兜底**　作为一名演示者，我想在断网或数据源不可用时系统仍能产出可用数据，以便答辩演示不被网络波动打断。
- 验收：外部源失败时自动回退到内置样例数据，source 标记为 sample。

### 史诗 3：数据清洗与标准化

**US-08 证券代码标准化**　作为一名数据使用者，我想让不同写法的证券代码（sh600519 / 600519 / 600519.SH）统一为标准格式，以便跨数据源一致引用。
- 验收：各种输入归一化为 `数字.市场后缀`。

**US-09 异常值与缺失值处理**　作为一名数据使用者，我想让价格为 0、缺失或非法的异常行被自动剔除，以便查询结果干净可信。
- 验收：非正/NaN 价格行被丢弃，衍生字段（涨跌幅、日增长率）被正确计算。

### 史诗 4：数据查询与导出

**US-10 股票行情查询**　作为一名普通用户，我想按代码和日期范围分页查询股票日线，以便分析价格走势。
- 验收：支持分页、日期筛选，返回结构稳定。

**US-11 基金净值查询**　作为一名普通用户，我想查询基金的单位净值与累计净值，以便观察基金表现。

**US-12 可视化图表**　作为一名普通用户，我想在页面上看到收盘价/净值走势图（含 K 线），以便直观理解数据。

**US-13 数据导出**　作为一名管理员，我想把查询结果导出为 CSV/Excel/Parquet，以便离线分析或归档。
- 验收：导出落 export_records，文件可下载。

**US-14 导出历史追踪**　作为一名管理员，我想查看历史导出记录并重新下载，以便追溯导出行为。

### 史诗 5：监控与运维

**US-15 系统健康检查**　作为一名运维人员，我想查看系统、数据库、调度器的健康状态，以便确认平台可用。

**US-16 数据概览仪表盘**　作为一名用户，我想在仪表盘看到标的数量、数据行数、最近采集与导出，以便快速掌握平台运行情况。

> 说明：上述 16 条为模块 1 阶段冻结的核心用户故事。第二轮增强迭代又派生出「跨源校验、数据质量人工校对、实时行情、多租户与字段级权限、受控 SQL、API 性能监控」等故事，已在第 2.4 节需求覆盖对照表中体现，不再单列。

## 2.3 交互场景（用例）

为关键用户故事编写交互场景，主路径为正常流程，扩展为异常/替代流程，接口前缀统一 `/api`。

### UC-01 用户登录（对应 US-01）
- 参与者：平台用户；前置条件：用户已存在且启用。
- 主路径：① 输入用户名密码提交；② 前端 POST `/api/auth/login`；③ 后端校验密码（pbkdf2_sha256），通过则签发 JWT（含 sub、role、exp）；④ 前端保存 token 与角色到本地存储并跳转仪表盘。
- 扩展：3a 密码错误返回 401，前端提示「用户名或密码错误」；4a 后续请求 token 过期，拦截器捕获 401 并清理登录态跳回登录页。

### UC-02 手动采集（对应 US-03/04/06/07）
- 参与者：管理员；前置条件：已登录且角色为 admin。
- 主路径：① 在股票/基金页点「采集」或任务页点「执行」；② 前端 POST `/api/tasks/crawl`（或 `/api/tasks/{id}/run`）；③ 后端创建 CrawlRun（status=running）；④ 采集器对每个代码：抓取 → 清洗标准化 → upsert 入库；⑤ 汇总影响行数与来源，更新运行状态 success/partial/failed；⑥ 返回运行记录，前端刷新数据与图表。
- 扩展：1a 非管理员触发返回 403；4a 外部源异常回退样例数据，source=sample，流程继续；4b 个别代码失败记入 errors，整体置 partial，不中断其它代码。

### UC-03 定时采集（对应 US-05）
- 参与者：系统（调度器）；前置条件：存在 enabled=true 且 cron 非空的任务。
- 主路径：① 应用启动时调度器加载所有启用且含 cron 的任务；② APScheduler 按 cron 到点回调 `execute_job_by_id`；③ 用独立数据库会话执行（同 UC-02 步骤 3-5），trigger=scheduled。
- 扩展：1a cron 非法记录错误日志并跳过注册；2a 应用关闭时调度器安全停止，不影响进行中的请求。

### UC-04 行情查询（对应 US-10/11/12）
- 参与者：普通用户/管理员。
- 主路径：① 选择标的与日期范围；② 前端 GET `/api/stocks/{code}/daily`（或 `/api/funds/{code}/nav`），带分页与日期参数；③ 后端按条件查询并分页返回（应用三层数据权限与 TTL 缓存）；④ 前端渲染表格与 ECharts 走势图/K 线。
- 扩展：3a 无数据返回空列表，前端显示「暂无数据」。

### UC-05 数据导出与下载（对应 US-13/14）
- 参与者：管理员/有导出权限用户。
- 主路径：① 选择数据集、格式、可选代码、是否加密压缩，提交导出；② 前端 POST `/api/exports`；③ 后端按数据权限查询 → pandas 写文件（CSV/Excel/Parquet）→ 可选 AES 加密 zip → 落 export_records；④ 返回导出记录；⑤ 在导出页点「下载」，GET `/api/exports/{id}/download` 获取文件流。
- 扩展：3a Parquet 引擎缺失自动回退 CSV；3b 无导出权限或超配额返回 403/429；5a 文件已清理返回 404 并提示重新导出。

### UC-06 查看仪表盘与健康（对应 US-15/16）
- 参与者：所有登录用户。
- 主路径：① 进入仪表盘，前端 GET `/api/dashboard`；② 后端聚合标的数、数据行数、采集成功率、行业分布、最近运行与导出；③ 前端以统计卡片 + 图表 + 表格展示；④ 健康检查 GET `/api/health`（公开）返回 DB 与调度器状态。

> （图 2-1，待补）用例关系图 / 主要业务流程泳道图

## 2.4 题目二需求逐条覆盖对照

下表逐条对照课程指导书「题目二」原文需求清单标注实现状态。图例：✅ 已实现（真实实现）　◑ 等价/简化实现（轻量等价，预留可替换接口）　—— 未做（超出课设范围）。

### 模块 1 · 数据获取与采集

| 原文需求 | 状态 | 实现说明 |
| --- | --- | --- |
| 第三方开源数据集成（akshare/tushare） | ✅ | akshare 真实接口（已适配新版签名），失败自动多源回退 |
| 主流供应商 API（Wind/同花顺等） | ◑ | 商业授权不接入；数据源注册表登记为占位，预留 source 字段扩展 |
| 公开数据源抓取（证监会公告/年报/新闻/舆情） | ✅ | `Announcement` 模型 + `crawl_announcements()`，`/announcements` 查询，前端「公告舆情」页 |
| 多渠道数据源接入与可视化 | ✅ | `datasource_registry` + `/datasources`，股票四源兜底 akshare→腾讯→新浪→样例 |
| 灵活更新频率配置（实时/分钟/日/季度） | ✅ | `CrawlJob.frequency` 预设 → cron 映射，前端任务表单频率下拉 |
| 智能重试机制 | ✅ | 指数退避重试，重试次数记入运行日志 |
| 失败告警 | ✅ | 失败/部分成功聚合到监控页告警中心 + AlertRecord 落库 |
| 增量采集与全量更新策略 | ✅ | 任务支持 full/incremental 两种模式，增量只取最新日期后数据 |
| 采集任务监控 | ✅ | crawl_runs 记录每次运行状态、行数、来源、耗时 |

### 模块 2 · 数据清洗与标准化

| 原文需求 | 状态 | 实现说明 |
| --- | --- | --- |
| 自动识别处理缺失值、异常值 | ✅ | 非正/NaN/缺失价格行剔除 |
| 数据一致性校验（复权价格逻辑） | ✅ | OHLC 一致性校验：high≥max(open,close)、low≤min(...) |
| 跨数据源交叉验证 | ✅ | 采集时自动用副源 `cross_source_validate`，偏差登记 `DataQualityIssue` |
| 人工数据检查校对 | ✅ | `/data-quality` + `/data-quality/{id}/resolve`，前端「数据质量」页可标记修正/忽略 |
| 统一证券代码映射 | ✅ | sh600519/600519/600519.SH 等归一化 |
| 行业分类统一（申万/中信/GICS） | ✅ | `guess_industry(code, standard)` 三套标准映射 |
| 基金净值复权计算 | ✅ | `clean_fund_nav` 计算 `adj_nav`（分红再投资），落库 + 导出 |
| 财务数据标准化 | ◑ | 题目偏行情/净值；行业分类映射作为标准化等价实现 |

### 模块 3 · 数据存储与管理

| 原文需求 | 状态 | 实现说明 |
| --- | --- | --- |
| 关系型持久化 | ✅ | SQLite（默认）/ MySQL 8 可切换 |
| 实时内存缓存（Redis） | ◑ | 进程内 TTL 缓存（等价实现，预留 Redis 接口），采集后主动失效 |
| 历史列式存储（ClickHouse） | ◑ | 关系库承担；受控 SQL 聚合查询模拟列式视角 |
| 文档存储（MongoDB/ES） | ◑ | `announcements` 表承担文档型公告/舆情存储 |
| 数据字典和字段说明 | ✅ | `/metadata/dictionary` + 前端元数据页 |
| 数据血缘关系追踪 | ✅ | `/metadata/lineage`：按标的统计来源、行数、时间范围 |
| 数据更新时效标注 | ✅ | 血缘含最新/最早日期；监控页含延迟天数 |
| 数据权限和敏感级别标记 | ✅ | 数据字典每字段标 public/internal/sensitive，查询/导出统一据此脱敏 |

### 模块 4 · 数据查询与 API 服务

| 原文需求 | 状态 | 实现说明 |
| --- | --- | --- |
| RESTful API 服务 | ✅ | FastAPI + 自动 Swagger 文档 |
| 通用 SQL 查询接口 | ✅ | `/query/sql`：仅管理员、只读 SELECT、表名白名单、禁 DML/多语句、强制 LIMIT |
| WebSocket 实时推送 | ✅ | `/ws/quotes`：token 鉴权后周期推送最新行情/净值，前端驾驶舱实时滚动条 |
| Python 封装 | ✅ | `sdk/stockfund_client.py`：登录/查询/采集/导出/SQL 封装 + README |
| 高频查询结果缓存 | ✅ | 行情/净值查询走 TTL 缓存，采集后按标的失效 |
| 分页查询 | ✅ | 统一 page/page_size |
| 查询权限控制和限流 | ✅ | 令牌桶限流（每用户每分钟）+ 行级/时间/字段级权限 |
| 导出 CSV/Excel/Parquet | ✅ | 三格式均支持，Parquet 无引擎时回退 CSV |
| 导出历史记录追踪 | ✅ | export_records + 下载接口 |
| 导出数据加密/压缩 | ✅ | zip 压缩 + AES 加密（pyzipper，缺库回退标准 zip），前端导出表单可选 |

### 模块 5 · 数据监控与运维

| 原文需求 | 状态 | 实现说明 |
| --- | --- | --- |
| 每日数据更新完整性检查 | ✅ | 交易日缺口检测，输出完整率 |
| 关键字段异常监测 | ✅ | `detect_anomalies`：涨跌幅超阈值、成交量突变、净值断崖，登记数据质量问题 |
| 数据延迟和滞后告警 | ✅ | 最新数据距今 >7 天触发告警 |
| 节假日和特殊日期处理 | ✅ | 内置 A 股节假日表，完整性检查剔除非交易日 |
| 采集任务运行状态监控 | ✅ | 运行记录 + 成功率仪表盘 |
| 存储空间使用监控 | ✅ | 监控页展示 DB 文件大小 |
| API 性能/可用性监控 | ✅ | `APIMetricsMiddleware` + `/monitor/api-stats`：各接口请求数/平均耗时/错误率 |
| 告警分发 | ✅ | `AlertRecord` 落库历史 + 可配置 webhook best-effort 推送 |

### 模块 6 · 用户权限与安全管理

| 原文需求 | 状态 | 实现说明 |
| --- | --- | --- |
| 功能权限（查询/导出/管理） | ✅ | RBAC + 依赖式拦截，角色 `can_export` 控制导出 |
| 数据权限（字段级） | ✅ | 敏感字段（amount）按角色 `can_view_sensitive` 在查询/导出统一脱敏 |
| 数据权限（行级） | ✅ | 角色 `data_scope`（all/stock/fund）过滤标的与行情访问 |
| 时间权限（历史数据时限） | ✅ | 角色 `max_history_days` 钳制查询起始日期（analyst 限近 365 天） |
| 用量配额管理 | ✅ | 普通用户每日导出配额 + 查询限流 |
| 多租户（机构/部门隔离） | ✅ | `Tenant` 模型 + User.tenant_id/department，系统管理页可维护 |
| 用户管理 | ✅ | `/admin/users`、`/admin/roles`、`/admin/tenants` CRUD，前端「系统管理」页 |
| 密码加密存储 | ✅ | pbkdf2_sha256 |
| 操作审计日志 | ✅ | 登录/采集/导出/SQL/用户管理落审计表，管理员可查 |

**覆盖结论**：六大模块需求全面覆盖，绝大多数为 ✅ 真实实现。少数标 ◑ 的为「轻量等价实现」——在不引入重型外部依赖（Redis/ClickHouse/Mongo/商业数据源）的前提下，以架构等价的方式实现同等能力，并在代码中预留可替换接口，保证「克隆即跑」。

<div style="page-break-after: always;"></div>

---

# 第 3 章　系统设计

> **合并来源说明**：本章整合 architect.md、db.md、backend_api.md、ui_design.md，并结合最新 models.py、schemas.py、router 与前端页面重新校正。

> 对应课程模块 2。本章整合架构设计（architect.md）、数据库设计（db.md）、API 设计（backend_api.md）与前端 UI 设计（ui_design.md），并补充企业级能力的轻量等价实现说明。

## 3.1 技术选型

技术选型遵循三条原则：**主流成熟**（便于学习与维护）、**克隆即跑**（默认零外部中间件）、**可平滑升级**（预留切换真实基础设施的接口）。

**表 3-1　技术栈与选型理由**

| 层次 | 技术 | 版本 | 选型理由 |
| --- | --- | --- | --- |
| 后端框架 | FastAPI | 0.115 | 原生异步、自动 OpenAPI 文档、依赖注入契合分层鉴权 |
| ASGI 服务器 | Uvicorn | 0.30 | 轻量高性能，开发/生产通用 |
| ORM | SQLAlchemy | 2.0 | 声明式模型，支持 SQLite/MySQL 无缝切换 |
| 数据校验 | Pydantic v2 + pydantic-settings | 2.x | 请求/响应契约与配置统一校验 |
| 认证 | python-jose（JWT）+ passlib（pbkdf2_sha256） | — | 无状态令牌，密码加盐哈希 |
| 数据处理 | pandas + numpy | 2.x | 清洗、衍生指标、导出多格式 |
| 采集 | akshare + requests | — | 开源金融数据 + HTTP 兜底源 |
| 调度 | APScheduler | 3.10 | 进程内 cron 调度，无需独立中间件 |
| 导出加密 | pyzipper（AES）+ pyarrow（Parquet，可选） | — | 导出文件加密压缩 |
| 数据库（默认） | SQLite | 内置 | 零安装、文件级、便于演示 |
| 数据库（生产） | MySQL 8 | — | 一行配置切换，sql/init.sql 已备 |
| 前端框架 | Vue 3（Composition API） | 3.4 | 响应式、组合式，生态成熟 |
| 构建工具 | Vite | 5.x | 秒级热更新，开箱即用代理 |
| UI 组件库 | Element Plus | 2.x | 企业级中后台组件 |
| 图表 | ECharts | 5.x | K 线/折线/饼图金融可视化 |
| 状态管理 | Pinia | 2.x | 轻量、组合式的认证态管理 |
| HTTP 客户端 | Axios | 1.x | 拦截器统一注入 token 与错误处理 |

## 3.2 总体架构

系统采用**前后端分离 + 后端分层**架构。前端为 SPA，经 Vite 代理将 `/api` 与 `/ws` 转发到后端；后端分为路由层、服务层、核心层、数据层四层，职责单向依赖、自上而下调用。

```text
┌──────────────────────── 浏览器（Vue 3 SPA）────────────────────────┐
│  Login  Dashboard  Stocks  Funds  Announcements  Tasks  DataSources  │
│  DataQuality  Monitor  Metadata  SqlQuery  Exports  Admin  Audit     │
│  Pinia(auth) · Axios(拦截器注入JWT) · ECharts · WebSocket 客户端     │
└──────────────────────── /api  /ws  ↓ ───────────────────────────────┘
                    Vite Dev Proxy / Nginx 静态托管
┌──────────────────────── 后端（FastAPI / ASGI）─────────────────────┐
│ ① 路由层 api/   auth data query exports tasks monitor admin ws      │
│      └─ deps.py：get_current_user / require_admin / 三层数据权限 / 限流 │
│ ② 服务层 services/  crawler cleaning export monitor data_quality    │
│      realtime audit user task datasource_registry calendar metadata │
│ ③ 核心层 core/   config database security cache rate_limit metrics  │
│ ④ 数据层 models.py（SQLAlchemy ORM, 13 表）+ schemas.py（契约）     │
│   APScheduler（tasks/scheduler.py）按 cron 回调服务层执行采集        │
└──────────────────────── ↓ SQLAlchemy ──────────────────────────────┘
        SQLite（默认 stock_fund_platform.db）  ⇄ 可切换 ⇄  MySQL 8（sql/init.sql）
        外部数据源：akshare → 腾讯 → 新浪 →（兜底）内置样例生成器
```

**分层职责**：
- **路由层**：解析 HTTP、依赖注入鉴权与权限、调用服务层、返回 Pydantic 响应。不含业务逻辑。
- **服务层**：纯业务逻辑（采集、清洗、监控、导出等），可被路由与调度器复用，便于单测。
- **核心层**：横切关注点（配置、数据库会话、安全、缓存、限流、性能监控中间件）。
- **数据层**：ORM 模型与请求/响应契约，是系统的数据契约中枢。

> （图 3-1，待补）系统总体架构图
> （图 3-2，待补）部署拓扑图

## 3.3 核心类设计

服务层以「服务模块 = 一组高内聚函数」的方式组织，关键设计如下：

- **采集器 crawler**：`crawl_stock_daily(code, mode)` / `crawl_fund_nav(code)` / `crawl_announcements()`。内部以「数据源链」模式工作——按 akshare→腾讯→新浪→样例 依次尝试，首个成功者返回，并记录命中源。
- **清洗器 cleaning**：`normalize_symbol` / `clean_stock_daily(df)` / `clean_fund_nav(df)` / `guess_industry(code, standard)` / `cross_source_validate`。输入原始 DataFrame，输出标准化、校验后的记录列表。
- **数据源注册表 datasource_registry**：维护数据源元信息（名称、类型、状态、命中次数），供前端「数据源」页可视化。
- **监控服务 monitor_service**：`check_completeness` / `detect_anomalies` / `dispatch_alert` / `api_stats`，输出健康报告与告警。
- **数据质量服务 data_quality_service**：登记/查询/解决 `DataQualityIssue`，支撑人工校对闭环。
- **导出服务 export_service**：`run_export(dataset, fmt, codes, encrypt)`，格式转换 + 脱敏 + 加密压缩 + 落记录。
- **权限依赖（deps.py）**：`get_current_user`（解析 JWT）、`require_admin`、行级/时间级/字段级权限注入，以 FastAPI 依赖的形式作用于各路由。

> （图 3-3，待补）核心类图（服务层 + 模型层关系）

## 3.4 数据库设计

### 3.4.1 设计概览

数据库共 **13 张表**，覆盖「主数据—行情数据—采集—导出—监控—权限审计」六个域。默认 SQLite，生产可切 MySQL（`sql/init.sql` 提供建表脚本）。关键表含创建/更新时间戳，行情表对 `(code, 日期)` 建唯一约束以支持 upsert 幂等采集。权限采用经典 RBAC：权限属性集中在 `roles` 表，`users` 通过 `role_id` 关联，便于「改角色即改一类用户权限」。

**表 3-2　数据表清单**

| 域 | 表名 | 说明 |
| --- | --- | --- |
| 主数据 | `instruments` | 证券标的（股票/基金）主表，含租户/部门作用域 |
| 权限 | `tenants` | 租户（机构/部门隔离） |
| 权限 | `roles` | 角色与权限属性（行级/时间级/字段级/功能权限载体） |
| 权限 | `users` | 用户（关联角色、租户、部门，存密码哈希） |
| 行情 | `stock_daily` | 股票日线（OHLC、成交量额、涨跌幅） |
| 行情 | `fund_nav` | 基金净值（单位净值、累计净值、复权净值、日增长率） |
| 文档 | `announcements` | 公告/舆情（文档型数据等价实现） |
| 采集 | `crawl_jobs` | 采集任务定义（频率、cron、模式、启停） |
| 采集 | `crawl_runs` | 采集运行记录（状态、行数、来源、耗时、错误） |
| 导出 | `export_records` | 导出历史（数据集、格式、行数、文件、加密） |
| 监控 | `alert_records` | 告警记录（类型、级别、消息、时间） |
| 质量 | `data_quality_issues` | 数据质量问题（类型、详情、状态、处理人） |
| 审计 | `audit_logs` | 操作审计（用户、动作、对象、详情、IP、时间） |

> 说明：数据源注册表（多源状态与命中统计）由 `datasource_registry` 服务在运行期维护，元数据「数据字典/血缘」由 `metadata_service` 基于模型自省动态生成，二者均不单独建物理表。

### 3.4.2 关键表字段（节选）

**roles（权限属性载体，RBAC 核心）**

| 字段 | 类型 | 约束/默认 | 说明 |
| --- | --- | --- | --- |
| id | INT | PK | 主键 |
| name | VARCHAR(32) | UNIQUE, NOT NULL | 角色名 admin/viewer/analyst |
| description | VARCHAR(128) | default '' | 角色说明 |
| data_scope | VARCHAR(16) | default 'all' | 行级范围 all/stock/fund |
| max_history_days | INT | default 0 | 历史时限（0=不限） |
| can_export | BOOL | default true | 功能权限：导出 |
| can_view_sensitive | BOOL | default false | 字段级：敏感字段可见 |

**users（用户）**：`id, username(UNIQUE), hashed_password(pbkdf2_sha256), full_name, is_active, role_id(FK→roles), tenant_id(FK→tenants,NULL), department, created_at`。

**instruments（标的主数据）**：`id, code(UNIQUE), name, asset_type(stock/fund), market(SH/SZ/OF), category, tenant_id(FK,NULL), department, is_active, created_at, updated_at`。`tenant_id` 为空表示全局公共标的，非空则仅对应机构/部门可见（支撑多租户隔离）。

**stock_daily（股票日线）**：`id, code, trade_date, open, high, low, close, volume, amount, pct_change, source, created_at`，唯一约束 `(code, trade_date)` + 联合索引。

**fund_nav（基金净值）**：`id, code, nav_date, unit_nav, accum_nav, adj_nav, daily_return, source, created_at`，唯一约束 `(code, nav_date)` + 联合索引。

**crawl_runs（采集运行记录）**：`id, job_id(FK,NULL), target_code, status(success/partial/failed/running), rows_affected, source, trigger(manual/scheduled), message, duration_ms, started_at, finished_at`。

> 注：行情表以标准化 `code` 字符串关联标的（非外键 ID），便于采集端直接按代码 upsert；标的与行情的关联在查询层通过 `code` 完成。

> （图 3-4，待补）数据库 ER 图（由 AI 依据模型生成后人工校正）

## 3.5 后端 API 设计

API 遵循 RESTful 风格，统一前缀 `/api`，认证用 `Authorization: Bearer <JWT>`。共 **9 个路由模块、约 40 个端点**。完整契约见 `docs/backend_api.md` 及运行时自动生成的 OpenAPI 文档（`/docs`）。

**表 3-3　API 模块总览**

| 模块 | 前缀 | 代表端点 | 权限 |
| --- | --- | --- | --- |
| 认证 auth | `/api/auth` | POST `/login`、GET `/me` | 公开 / 登录 |
| 数据 data | `/api` | GET `/instruments`、`/stocks/{code}/daily`、`/funds/{code}/nav` | 登录 |
| 概览/公告/源 | `/api` | GET `/dashboard`、`/health`（公开）、`/announcements`、`/datasources`、`/realtime/quotes` | 登录 |
| 任务 tasks | `/api/tasks` | GET ``、POST ``、PATCH/DELETE `/{id}`、POST `/crawl`、`/crawl-all`、`/{id}/run`、GET `/runs` | 管理员 |
| 导出 exports | `/api/exports` | POST ``、GET ``、GET `/{id}/download` | 导出权限 |
| 受控 SQL | `/api/query` | POST `/sql`（只读受控） | 管理员 |
| 监控 monitor | `/api/monitor` | GET `/metrics`、`/integrity`、`/alerts`、`/api-stats`、`/data-quality`、POST `/data-quality/{id}/resolve` | 登录 / 管理员 |
| 元数据/审计 | `/api/metadata`、`/api/audit` | GET `/metadata/dictionary`、`/metadata/lineage`、`/audit` | 登录 / 管理员 |
| 管理 admin | `/api/admin` | `/users`、`/roles`、`/tenants` CRUD | 管理员 |
| 实时 ws | `/ws/quotes` | WebSocket 行情推送 | 登录（token 参数） |

**统一约定**：分页用 `page`/`page_size`，返回 `{items, total, page, page_size}`；错误用标准 HTTP 状态码 + `{detail}`；时间统一 ISO 8601。

> （图 3-5，待补）Swagger UI `/docs` 自动生成接口文档截图

## 3.6 前端 UI 设计

### 3.6.1 信息架构

前端为单页应用，登录后进入 `MainLayout`（顶栏 + 左侧六组菜单 + 内容区）。菜单按业务域分六组，并按角色动态过滤（非管理员隐藏采集/SQL/系统管理等项）。

**表 3-4　菜单分组与页面**

| 分组 | 页面 | 路由 | 权限 |
| --- | --- | --- | --- |
| 总览 | 数据驾驶舱 Dashboard | `/dashboard` | 登录 |
| 数据中心 | 股票行情 Stocks | `/stocks` | 登录 |
| 数据中心 | 基金净值 Funds | `/funds` | 登录 |
| 数据中心 | 公告舆情 Announcements | `/announcements` | 登录 |
| 采集管理 | 采集任务 Tasks | `/tasks` | 管理员 |
| 采集管理 | 数据源 DataSources | `/datasources` | 登录 |
| 数据治理 | 数据质量 DataQuality | `/data-quality` | 登录 |
| 数据治理 | 元数据 Metadata | `/metadata` | 登录 |
| 运维监控 | 监控运维 Monitor | `/monitor` | 登录 |
| 运维监控 | 审计日志 Audit | `/audit` | 管理员 |
| 数据服务 | SQL 查询 SqlQuery | `/sql` | 管理员 |
| 数据服务 | 数据导出 Exports | `/exports` | 导出权限 |
| 系统 | 系统管理 Admin | `/admin` | 管理员 |
| — | 登录 Login | `/login` | 公开 |

### 3.6.2 视觉风格

采用**深色金融科技风**，由 `styles/theme.css` 的 CSS 变量统一控制：深色背景、青绿主色、红绿语义色（涨红跌绿，符合 A 股习惯）、卡片化布局与微动效。统计数字用等宽字体强调专业感。

> （图 3-6，待补）登录页　（图 3-7，待补）数据驾驶舱
> （图 3-8，待补）股票行情 + K 线　（图 3-9，待补）UI 设计风格说明

## 3.7 企业级能力的轻量等价实现

题目部分需求面向工业级基础设施。为保证「克隆即跑、断网可演示」，本组采用架构等价实现，并在代码中预留可替换接口：

**表 3-5　等价实现对照**

| 题目要求 | 工业级方案 | 本项目等价实现 | 升级路径 |
| --- | --- | --- | --- |
| 实时数据内存缓存 | Redis | 进程内 TTL 缓存 `core/cache.py` | 替换为 redis-py，接口不变 |
| 历史数据列式存储 | ClickHouse | 关系库 + 受控 SQL 聚合 | 行情表迁移至 CH，查询层适配 |
| 文档/舆情存储 | MongoDB/ES | `announcements` 关系表 | 接入 ES，保留同字段 |
| 商业数据源 | Wind/同花顺 API | akshare + HTTP 多源兜底 | 注册表登记新 source 实现 |
| 分布式任务队列 | Celery/Airflow | APScheduler 进程内调度 | 替换调度后端，job 定义复用 |

这一策略使系统在**架构完整性**与**可演示性**之间取得平衡：六大模块能力齐备，又无需助教安装任何中间件。

<div style="page-break-after: always;"></div>

---

# 第 4 章　系统实现

> **合并来源说明**：本章整合模块 3 编码实现内容，依据当前 backend/app、frontend/src、sdk、sql 目录逐文件复核后重写实现说明。

> 对应课程模块 3。本章按「后端核心能力 → 前端实现」组织，重点说明三层数据权限、多源采集兜底、清洗标准化、监控告警等关键逻辑。代码节选见附录 A。

## 4.0 实现复核总览

本章说明均以当前最新代码为准。实现层面采用“API 路由层 → 服务层 → ORM 数据层”的单向依赖结构，前端通过统一 Axios 客户端访问 `/api`，WebSocket 用于实时行情推送。后端启动生命周期为“初始化数据库 → 自动迁移 → 种子用户/标的/样例行情 → 启动调度器 → 可选后台采集真实数据”。

**表 4-1　源码模块与课程需求对应关系**

| 课程题目能力 | 主要代码位置 | 实现说明 |
| --- | --- | --- |
| 多渠道数据源接入 | services/crawler.py、datasource_registry.py | 股票优先 akshare，失败后依次走腾讯、新浪，最后回退样例；基金优先 akshare，失败回退样例 |
| 数据采集调度 | api/tasks.py、services/task_service.py、tasks/scheduler.py | 支持任务 CRUD、手动触发、批量采集、cron 调度、运行日志与重试统计 |
| 数据清洗与标准化 | services/cleaning.py、calendar_service.py | 代码标准化、OHLC 修正、异常缺失剔除、基金收益率/复权净值、交易日历 |
| 数据存储与管理 | models.py、database.py、sql/init.sql | 13 张业务表，包含唯一约束、索引、种子数据和 SQLite/MySQL 双模式 |
| 查询与 API 服务 | api/data.py、api/query.py、schemas.py | RESTful 查询、分页、白名单只读 SQL、字段脱敏、时间权限钳制 |
| WebSocket 实时推送 | api/ws.py、services/realtime_service.py | 实时行情快照，交易时段优先尝试新浪接口，非交易/失败时回退库内最新行情 |
| 数据导出 | api/exports.py、services/export_service.py | CSV/Excel/Parquet 兼容设计，支持导出记录、用户隔离、配额校验、ZIP/AES 加密 |
| 监控与运维 | api/monitor.py、monitor_service.py、metrics_middleware.py | 健康检查、系统指标、完整性检查、异常检测、API 性能统计、告警闭环 |
| 元数据与血缘 | metadata_service.py、api/monitor.py | 数据字典、字段说明、数据来源、更新频率与血缘链路展示 |
| 权限与安全 | api/deps.py、core/security.py、api/admin.py、user_service.py | JWT、密码哈希、RBAC、多租户、行级/时间级/字段级/功能级权限、审计日志 |
| 前端页面 | frontend/src/views、layouts、components | 14 个业务页面，深色金融科技风，K 线/折线/仪表盘等图表组件 |
| Python 封装 | sdk/stockfund_client.py | 对登录、标的查询、股票/基金查询、导出和文件下载进行客户端封装 |


## 4.1 后端工程结构

后端基于 FastAPI，按 4.1 节所述四层组织。应用入口 `main.py` 通过 ASGI `lifespan` 完成启动编排：

1. **建表**：调用 `init_db()` 创建全部 ORM 表，并执行 `_auto_migrate()` 为已有 SQLite 库补齐新增列（如 `data_quality_issues`、用户权限字段），保证旧库平滑升级。
2. **播种**：调用 `seed.py` 写入三个演示用户、若干股票/基金标的与样例行情，确保首次启动即有可演示数据。
3. **启动调度器**：加载所有启用且含 cron 的采集任务注册到 APScheduler。
4. **可选后台预采集**：当配置 `AUTO_CRAWL_ON_STARTUP=true` 时，以 best-effort 方式异步拉取一次真实数据（失败回退样例），不阻塞启动；默认关闭，避免离线演示时刷外网错误日志——此时完全依赖第 2 步播种的样例数据演示。
5. **关闭钩子**：安全停止调度器。

CORS、`APIMetricsMiddleware`（性能监控）在创建应用时注册；所有路由通过 `app.include_router` 挂载到 `/api` 与 `/ws`。

## 4.2 认证与三层数据权限

这是本项目权限体系的核心，对应题目「用户权限与安全管理」模块，实现了**功能权限 + 行级 + 时间级 + 字段级**四类控制。

### 4.2.1 认证流程

- **登录**：`POST /api/auth/login` 校验用户名/密码（`passlib` 的 `pbkdf2_sha256` 哈希比对），通过后用 `python-jose` 签发 JWT，载荷含 `sub`（用户名）、`role`、`exp`（过期时间，默认配置项 `access_token_expire_minutes`）。
- **校验**：受保护接口依赖 `get_current_user`——从 `Authorization: Bearer` 头取出 token，解码校验签名与过期，查库取用户对象；失败抛 401。
- **功能权限**：`require_admin` 依赖校验 `role == 'admin'`，作用于采集、任务管理、SQL 查询、系统管理等路由；导出路由额外校验 `can_export`。

### 4.2.2 三层数据权限

**表 4-1　三层数据权限实现**

| 层级 | 载体字段 | 实现位置 | 效果（以 analyst 为例） |
| --- | --- | --- | --- |
| 行级 | `data_scope` (all/stock/fund) | 查询标的/行情时按 type 过滤 | analyst=stock，看不到基金 |
| 时间级 | `max_history_days` | 钳制查询 `start_date` 下界 | analyst=365，只能查近一年 |
| 字段级 | `can_view_sensitive` | 响应序列化前对 `amount` 等脱敏 | analyst 看到成交额为掩码 |

三层控制以 FastAPI 依赖 + 服务层过滤组合实现：行级在查询条件中加 `instruments.asset_type` 过滤；时间级把用户请求的起始日期与 `today - max_history_days` 取较晚者；字段级在构造响应时将敏感字段替换为掩码（如 `***`）。这些权限属性都挂在用户所属的 `roles` 角色上，三个演示账号正是为了在答辩中**一眼看出**三层差异而设计。

> （图 4-1，待补）analyst 账号登录后只见股票、近一年、成交额脱敏的对比截图

## 4.3 数据采集与多源兜底

采集器 `crawler.py` 实现「数据源链」模式，保证**断网可演示**：

```
crawl_stock_daily(code):
   尝试 akshare      → 成功则 source=akshare
   失败→尝试 腾讯财经 → 成功则 source=tencent
   失败→尝试 新浪财经 → 成功则 source=sina
   全失败→内置样例生成器 → source=sample（带确定性随机游走，形态逼真）
```

每个代码独立 try/except，单代码失败不影响其它代码，错误记入运行记录 `errors`，整体状态置 `partial`。采集支持 **full / incremental** 两种模式：增量模式先查库中该标的最新日期，只拉取其后的数据。采集全程包指数退避重试，重试次数与最终命中源写入 `crawl_runs`。

基金净值 `crawl_fund_nav` 与公告 `crawl_announcements` 同理。所有采集均经清洗后再 upsert 入库（按唯一约束幂等）。

## 4.4 数据清洗与标准化

清洗器 `cleaning.py` 在入库前对原始数据做四件事：

1. **代码标准化** `normalize_symbol`：`sh600519` / `600519` / `600519.SH` 等多种写法统一为 `600519.SH`（按交易所规则补市场后缀）。
2. **异常/缺失值处理**：剔除价格非正、NaN、缺失的行。
3. **一致性校验**：OHLC 关系校验（`high ≥ max(open,close)`、`low ≤ min(open,close)`），不合法行登记数据质量问题。
4. **衍生字段计算**：股票算涨跌幅 `pct_change`；基金算复权净值 `adj_nav`（分红再投资）与日增长率 `daily_return`。

**行业分类标准化** `guess_industry(code, standard)` 支持申万/中信/GICS 三套标准的代码段映射。**跨源交叉验证** `cross_source_validate` 在采集时用副源比对主源价格，偏差超阈值时登记 `DataQualityIssue` 供人工校对。

## 4.5 存储、缓存与限流

- **存储**：SQLAlchemy 2.0 声明式模型，默认 SQLite（`stock_fund_platform.db`），`DATABASE_URL` 改一行即切 MySQL。行情表唯一约束保证 upsert 幂等。
- **缓存** `core/cache.py`：进程内 TTL 缓存（字典 + 过期时间戳），用于仪表盘聚合、实时快照等热点只读查询，等价替换 Redis，接口预留便于平滑升级。
- **限流** `core/rate_limit.py`：令牌桶算法，按用户 + 接口维度限制查询频率，普通用户超额返回 429。

## 4.6 查询、SQL 接口与 WebSocket

- **行情查询**：`/stocks/{code}/daily`、`/funds/{code}/nav` 支持分页与日期筛选，叠加三层权限与缓存。
- **受控 SQL** `/api/query/sql`：仅管理员可用，**只允许 SELECT**——服务端解析校验语句类型、拒绝 DML/DDL、强制 `LIMIT` 上限，防注入与误操作。对应题目「通用 SQL 查询接口」。
- **WebSocket** `/ws/quotes`：客户端带 token 建连后订阅标的，服务端周期推送实时行情快照（`realtime_service` 生成）；前端断线时**自动降级为 HTTP 轮询**，保证行情条始终滚动。

## 4.7 数据导出与加密压缩

导出服务 `export_service.run_export` 流程：按数据权限查询 → pandas 组装 DataFrame → 按格式写文件（CSV / Excel / Parquet）→ 可选 AES 加密压缩（`pyzipper`）→ 落 `export_records`。要点：

- **格式兜底**：Parquet 引擎（pyarrow）缺失时自动回退 CSV 并在记录中标注。
- **字段级脱敏**：导出同样遵守 `can_view_sensitive`，无权用户导出的敏感列为掩码。
- **配额**：普通用户每日导出受配置项 `VIEWER_EXPORT_DAILY_QUOTA`（默认 20 次）限制，超额返回 429；管理员不受限。
- **下载**：`GET /exports/{id}/download` 以文件流返回，文件已清理则 404 提示重导。

## 4.8 监控运维与告警

监控服务 `monitor_service` 对应题目「数据监控与运维」模块：

- **完整性检查** `check_completeness`：基于内置 A 股交易日历（`calendar_service`，剔除周末与节假日）检测行情缺口，输出完整率。
- **异常监测** `detect_anomalies`：涨跌幅超阈值、成交量突变、净值断崖等，登记数据质量问题。
- **延迟告警**：最新数据距今 > 7 天触发告警。
- **API 性能监控** `APIMetricsMiddleware` + `/monitor/api-stats`：统计各接口请求数、平均耗时、错误率。
- **告警分发** `dispatch_alert`：落 `alert_records` 历史，并可配置 webhook 做 best-effort 推送。

## 4.9 数据质量与人工校对

`data_quality_service` 实现「自动登记 + 人工校对」闭环：清洗/交叉验证/异常监测发现的问题统一登记为 `DataQualityIssue`（类型、详情、状态）；管理员在前端「数据质量」页查看，`POST /data-quality/{id}/resolve` 标记为「已修正/已忽略」，对应题目「人工数据检查校对」。

## 4.10 任务调度

`tasks/scheduler.py` 基于 APScheduler：启动时把所有 `enabled=true` 且 cron 非空的 `CrawlJob` 注册为 cron 触发的 job，到点回调 `execute_job_by_id`（用独立 DB 会话执行采集，trigger=scheduled）。任务的 `frequency` 预设（实时/分钟/日/季度）映射到对应 cron 表达式。非法 cron 跳过并记日志；应用关闭时安全 shutdown。

## 4.11 前端实现要点

- **路由守卫** `router/index.js`：全局前置守卫校验登录态（无 token 跳登录），admin 专属路由校验角色，越权跳回仪表盘。
- **状态管理** `stores/auth.js`（Pinia）：持久化 token、用户名、角色，提供登录/登出与角色判断。
- **API 封装** `api/http.js`：Axios 实例设置 `baseURL=/api`，请求拦截器注入 `Authorization`，响应拦截器统一处理 401（清登录态跳登录）与错误提示；`api/index.js` 集中定义全部接口函数。
- **WebSocket 客户端**：封装连接/订阅/重连，断线自动降级 HTTP 轮询，驱动顶栏实时行情滚动条。
- **可视化组件**：`LineChart`（走势）、`KLineChart`（K 线）、`MiniChart`（迷你趋势）、`StatCard`（统计卡片），均基于 ECharts 封装。
- **主题** `styles/theme.css`：深色金融科技风的 CSS 变量集中定义，全局复用。
- **代理** `vite.config.js`：开发环境将 `/api`、`/ws` 代理到后端 `127.0.0.1:8000`，前端无需关心跨域。

> （图 4-2，待补）采集任务页　（图 4-3，待补）监控运维页　（图 4-4，待补）数据导出页　（图 4-5，待补）系统管理页

<div style="page-break-after: always;"></div>

---

# 第 5 章　测试与调试

> **合并来源说明**：本章整合 test.md、backend/tests 与缺陷修复记录，覆盖单元测试、接口测试、功能测试与 AI 辅助调试过程。

> 对应课程模块 4。本章说明测试策略、用例组织与执行结果，并记录关键缺陷的定位与修复过程（详见 test.md）。

## 5.1 测试策略

采用分层测试策略，以 **pytest** 为统一框架，配合 FastAPI 的 `TestClient` 做接口级测试。测试库使用独立的内存/临时 SQLite，每个测试用例隔离，`conftest.py` 提供 client、各角色已登录 token 等夹具（fixture）。测试覆盖三个层次：

- **单元测试**：纯函数逻辑（代码标准化、清洗、行业分类、缓存、限流、交易日历）。
- **接口测试**：HTTP 端点的鉴权、参数、响应、权限隔离。
- **功能/集成测试**：采集→清洗→入库→查询→导出的端到端链路，以及三层权限、SQL 安全、多租户隔离等增强能力。

**执行结果**：`python -m pytest -q` —— **65 个用例全部通过（65 passed），耗时约 4.2 秒**。

```text
tests\test_api.py ...........          [ 16%]
tests\test_cleaning.py ......          [ 26%]
tests\test_enhancements.py ...........  [ 43%]
tests\test_monitor_api.py ..........   [ 58%]
tests\test_upgrade.py ...........................  [100%]
============================= 65 passed in 4.22s ==============================
```

> （图 5-1，待补）pytest 全绿执行截图

## 5.2 单元测试

**test_cleaning.py（6 例）— 清洗与标准化**

| 用例 | 验证点 |
| --- | --- |
| test_normalize_code_stock_suffix_inference | 纯数字股票代码自动推断市场后缀 |
| test_normalize_code_prefix_form | sh/sz 前缀写法归一化 |
| test_normalize_code_fund | 基金代码标准化 |
| test_normalize_code_keeps_existing_suffix | 已带后缀的代码保持不变 |
| test_clean_stock_daily_drops_invalid_and_computes_pct | 剔除非法行并正确计算涨跌幅 |
| test_clean_fund_nav_computes_daily_return | 基金日增长率计算正确 |

**test_enhancements.py（11 例）— 增强逻辑单测**

| 用例 | 验证点 |
| --- | --- |
| test_guess_industry_known / _fallback | 行业分类已知映射与兜底 |
| test_clean_stock_fixes_inconsistent_high_low | OHLC 一致性修正 |
| test_cross_source_validate_detects_deviation | 跨源校验能检出偏差 |
| test_calendar_skips_weekend / _holiday / _normal_trading_day | 交易日历正确识别周末/节假日/交易日 |
| test_expected_trading_days_count | 区间预期交易日数量正确 |
| test_cache_hit_and_miss / _invalidate_prefix | TTL 缓存命中、失效、按前缀清除 |
| test_rate_limiter_blocks_over_limit | 限流器超额拦截 |

## 5.3 接口测试

**test_api.py（11 例）— 核心接口与基础权限**

覆盖：健康检查公开访问、登录成功/失败、`/me` 需令牌、标的已播种、股票日线分页查询、基金净值查询、**普通用户不可触发采集（403）**、管理员快速采集并查运行记录、任务生命周期与日志、CSV 导出与下载、仪表盘统计。

**test_monitor_api.py（10 例）— 监控与运维接口**

覆盖：性能指标端点、完整性端点、告警端点、数据字典、数据血缘、仪表盘含行业分布与成功率、**登录写审计日志**、审计需管理员、增量采集、普通用户带配额导出。

## 5.4 功能测试

**test_upgrade.py（27 例）— 增强能力端到端**，是覆盖最广的测试文件，重点验证四类权限与安全：

| 主题 | 代表用例 | 验证点 |
| --- | --- | --- |
| 字段级权限 | test_viewer_amount_masked_in_query / test_admin_amount_visible_in_query | 成交额对普通用户脱敏、对管理员可见 |
| 行级权限 | test_analyst_row_level_blocks_fund / test_analyst_can_access_stock / test_analyst_instruments_filtered_to_stock | analyst 只能访问股票、看不到基金 |
| 受控 SQL | test_sql_select_ok / _blocks_dml / _blocks_multi_statement / _blocks_non_whitelisted_table / _forbidden_for_viewer / _user_limit_is_overridden_by_api_limit | 仅 SELECT、拒 DML、拒多语句、表白名单、非管理员禁用、强制行数上限 |
| 导出与隔离 | test_encrypted_export / test_export_records_are_isolated_between_users | 加密导出、导出记录用户间隔离 |
| 实时与数据源 | test_datasources_listing / test_realtime_snapshot / test_realtime_sina_symbol | 数据源列表、实时快照、代码格式 |
| 公告与质量 | test_announcement_crawl_and_list / test_data_quality_endpoint / test_api_stats_endpoint | 公告采集查询、数据质量、API 统计 |
| 多租户与管理 | test_admin_user_crud / _endpoints_forbidden_for_viewer / test_roles_and_tenants_listing / test_tenant_department_scoped_instrument_visibility | 用户 CRUD、越权拦截、租户部门可见性隔离 |
| 清洗增强 | test_fund_adj_nav_computed / test_industry_multi_standard | 复权净值、多标准行业分类 |
| 告警与登录 | test_alert_records_deduplicate_and_resolve / test_login_returns_role_permissions | 告警去重与处理、登录返回权限 |

四类测试文件合计 65 个用例，覆盖了题目六大模块的关键路径与全部权限维度。

## 5.5 缺陷定位与修复记录

测试与联调过程中发现并修复的代表性缺陷如下（完整记录见 test.md）。每条遵循「现象 → 根因 → 修复」，体现「AI 协助定位 + 人工确认修复」的过程。

**表 5-1　缺陷修复记录（节选）**

| 编号 | 现象 | 根因 | 修复 |
| --- | --- | --- | --- |
| BUG-01 | akshare 调用报参数错误，采集全失败 | akshare 新版接口签名变更 | 适配新版函数签名，并加多源兜底链 |
| BUG-02 | 普通用户竟能导出敏感成交额 | 脱敏只在查询接口做了，导出漏改 | 导出服务统一接入 `can_view_sensitive` 脱敏 |
| BUG-03 | analyst 仍能查到一年前数据 | 时间钳制取了较早值 | 改为 `max(请求起始, today - max_history_days)` |
| BUG-04 | 多语句 SQL（`SELECT...;DROP...`）被执行 | 仅检查首词是否 SELECT | 增加多语句拆分检测 + 表白名单校验 |
| BUG-05 | 旧 SQLite 库新增权限字段后启动报缺列 | 模型加了字段但库未迁移 | `_auto_migrate()` 启动时按需 ALTER 补列 |
| BUG-06 | Parquet 导出在无 pyarrow 环境报错 | 硬依赖 pyarrow | 缺引擎时自动回退 CSV 并标注 |
| BUG-07 | 同一异常重复刷屏告警 | 告警未去重 | 告警按类型+对象去重，支持标记已处理 |
| BUG-08 | WebSocket 断线后行情条卡住 | 无重连/降级 | 断线自动降级 HTTP 轮询 |

> （图 5-2，待补）某缺陷修复前后的对比截图（如 analyst 时间权限）

<div style="page-break-after: always;"></div>

---

# 第 6 章　部署与使用

> **合并来源说明**：本章整合 install.md、user_guid.md，并将安装部署步骤、使用流程与答辩演示脚本合并呈现。

> 对应课程模块 5。本章整合安装部署文档（install.md）与使用说明书（user_guid.md），提供从零启动到演示的完整指引。设计目标：**`git clone` 后无需任何外部中间件即可一键启动**。

## 6.1 环境要求

| 项 | 要求 |
| --- | --- |
| 操作系统 | Windows 10/11、Linux、macOS 均可 |
| Python | 3.10 及以上（开发使用 3.13） |
| Node.js | 18 及以上（前端构建/开发） |
| 数据库 | 默认 SQLite（零安装）；可选 MySQL 8 |
| 网络 | 非必需。断网时自动使用内置样例数据演示 |

## 6.2 后端部署

```bash
# 1. 进入后端目录
cd backend

# 2. 创建并激活虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. （可选）复制环境变量模板并按需修改
cp .env.example .env

# 5. 启动服务（默认 http://127.0.0.1:8000）
uvicorn app.main:app --reload --port 8000
```

首次启动会自动建表、播种演示数据（三个角色用户 + 标的 + 样例行情）、注册调度任务；默认不联网采集（`AUTO_CRAWL_ON_STARTUP=false`），因此**断网也能立即演示**。启动后访问 `http://127.0.0.1:8000/docs` 可查看自动生成的接口文档。

## 6.3 前端部署

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 开发模式启动（默认 http://127.0.0.1:5173，已代理 /api 与 /ws 到后端）
npm run dev

# 4. 生产构建（产物在 dist/，可由 Nginx 等静态托管）
npm run build
```

浏览器打开前端地址，用演示账号登录即可。开发模式下 Vite 已将 `/api`、`/ws` 代理到后端 8000 端口，无需额外配置跨域。

## 6.4 切换 MySQL 与启用真实数据源

- **切 MySQL**：在 `backend/.env` 设置 `DATABASE_URL=mysql+pymysql://user:pwd@host:3306/stockfund`，先用 `sql/init.sql` 建库建表，再启动后端即可。
- **启用真实采集**：保持联网，采集器会优先走 akshare/腾讯/新浪真实源；无网络或源异常时自动回退样例数据，不影响功能演示。

## 6.5 配置项说明

配置由 `core/config.py`（pydantic-settings）统一管理，可经环境变量或 `.env` 覆盖：

**表 6-1　主要配置项**

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | sqlite:///./stock_fund_platform.db | 数据库连接串，切 MySQL 改此项 |
| `SECRET_KEY` | （示例值，生产需改） | JWT 签名密钥 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 720（12 小时） | 令牌有效期（分钟） |
| `ALGORITHM` | HS256 | JWT 签名算法 |
| `CORS_ORIGINS` | localhost:5173,127.0.0.1:5173 | 允许跨域来源 |
| `RATE_LIMIT_PER_MINUTE` | 120 | 查询限流阈值（令牌桶） |
| `CACHE_TTL_SECONDS` | 30 | 查询结果缓存有效期（秒） |
| `VIEWER_EXPORT_DAILY_QUOTA` | 20 | 普通用户每日导出配额 |
| `SQL_QUERY_MAX_ROWS` | 1000 | 受控 SQL 单次最大返回行数 |
| `USE_SAMPLE_DATA_FALLBACK` | true | 外部源不可用时回退样例 |
| `CRAWL_MAX_RETRIES` | 2 | 单标的采集最大重试次数 |
| `ANOMALY_PCT_CHANGE_THRESHOLD` | 11.0 | 单日涨跌幅异常阈值(%) |
| `ALERT_WEBHOOK_URL` | 空 | 告警 webhook（留空则只落库不外发） |
| `AUTO_CRAWL_ON_STARTUP` | false | 启动时是否后台联网预采集 |
| `EXPORT_ZIP_PASSWORD` | （示例值） | 加密导出 zip 密码 |

> 安全提示：生产环境务必修改 `SECRET_KEY`，并通过环境变量注入而非提交到仓库。`.env` 已在 `.gitignore` 中忽略。

## 6.6 软件使用说明

**登录**：用三个演示账号之一登录（admin/admin123、viewer/viewer123、analyst/analyst123），体验不同权限。

**表 6-2　各页面操作指引**

| 页面 | 操作 |
| --- | --- |
| 数据驾驶舱 | 查看标的数、数据量、采集成功率、行业分布、最近运行/导出；顶栏实时行情滚动 |
| 股票行情 | 选标的与日期范围，查看日线表格 + K 线/收盘价走势图 |
| 基金净值 | 查看单位/累计/复权净值走势 |
| 公告舆情 | 浏览采集到的公告列表，按标的筛选 |
| 采集任务（管理员） | 新建/编辑任务（频率、模式、cron），手动执行，查看运行日志 |
| 数据源 | 查看多源状态与命中统计，管理员可启停 |
| 数据质量 | 查看自动登记的质量问题，管理员标记修正/忽略 |
| 元数据 | 浏览数据字典与字段血缘 |
| 监控运维 | 查看健康、完整性、异常、告警、API 性能 |
| SQL 查询（管理员） | 输入只读 SELECT 语句查询，结果表格展示 |
| 数据导出 | 选数据集/格式/加密，导出并下载，查看历史 |
| 系统管理（管理员） | 用户/角色/租户的增删改查 |
| 审计日志（管理员） | 查看登录/采集/导出/管理等操作记录 |

## 6.7 演示脚本

建议答辩按以下顺序演示，可在 5—8 分钟内覆盖六大模块与四类权限：

1. **断网启动**（体现兜底）：关网络，启动前后端，仪表盘仍有数据。
2. **admin 全景**：仪表盘 → 股票 K 线 → 触发一次采集 → 看运行日志（source 显示兜底源）。
3. **数据治理**：数据质量页处理一条问题 → 元数据看字典/血缘。
4. **监控运维**：完整性、异常、告警、API 性能各看一眼。
5. **权限对比**（重头戏）：退出换 **analyst** 登录——菜单变少、看不到基金、行情只到近一年、成交额脱敏、导出被拒。
6. **安全**：admin 在 SQL 页演示 `SELECT` 成功、`DROP`/多语句被拦截。
7. **导出**：加密导出一份 CSV 并下载。
8. **审计**：回到审计页，看到上述操作均被记录。

> （图 6-1，待补）一键启动后的浏览器首屏　（图 6-2，待补）演示流程关键截图集

<div style="page-break-after: always;"></div>

---

# 第 7 章　AI 使用报告

> **合并来源说明**：本章整合 ai.md，按评分点呈现 Prompt 示例、AI 输出摘要、问题识别、人工迭代和诚信说明。

> 贯穿课程模块 1—5。本章按评分要求呈现：Prompt 示例、AI 输出截图（待补）、人工迭代与修改过程说明，以及 AI 易错点与伦理声明。完整逐条记录见 ai.md。

## 7.1 使用原则

本组严格遵循课程「人在回路（Human-In-The-Loop）」要求，确立三条原则：

1. **AI 做初稿，人做决策**：用 AI 生成用户故事、ER 图、API 模板、代码骨架、测试与文档初稿，但需求范围、架构选型、权限模型等关键决策由人确定。
2. **不盲信、必验证**：所有 AI 生成的代码都经过阅读、运行、测试三道关，发现问题回退 AI 重改或人工修正，绝不直接提交无法解释的代码。
3. **全程留痕**：在 `ai.md` 中持续记录原始提示词、AI 输出摘要、发现的问题与优化，作为过程证据。

## 7.2 各模块 AI 交互记录

下表按课程五个模块给出代表性 Prompt 与 AI 角色（完整记录见 ai.md）。

**表 7-1　各模块代表性 Prompt 示例**

| 模块 | 角色设定 | 代表性 Prompt（节选） | AI 产出 | 人工动作 |
| --- | --- | --- | --- | --- |
| 模块1 需求 | 产品经理 | 「作为产品经理，为『股票基金数据平台』生成新功能的用户故事，遵循『作为一个…我想…以便…』格式」 | 16 条用户故事初稿 | 删除超范围社交功能，补验收标准 |
| 模块1 需求 | 测试架构师 | 「为用户故事『数据导出』编写交互场景，含主路径与异常分支」 | 6 个用例初稿 | 校正接口路径与权限分支 |
| 模块2 设计 | 架构师 | 「以需求为输入，推荐分层架构与技术栈并说明理由」 | 分层架构 + 技术栈建议 | 确定轻量等价方案（无 Redis/CH/Mongo） |
| 模块2 设计 | DBA | 「根据这些实体生成 ER 图与建表 SQL（含唯一约束/索引）」 | ER 图 + init.sql 初稿 | 增加权限字段、唯一约束、自动迁移 |
| 模块2 设计 | 后端架构师 | 「按前后端分离原则生成 RESTful API 列表（OpenAPI 风格）」 | API 接口清单 | 调整权限分级与统一分页约定 |
| 模块3 实现 | 后端工程师 | 「实现采集器：akshare 优先，失败回退腾讯/新浪/样例，每代码独立容错」 | crawler.py 初稿 | 适配 akshare 新签名、加重试与日志 |
| 模块3 实现 | 安全工程师 | 「实现受控只读 SQL 接口：仅 SELECT、拒多语句、表白名单、强制 LIMIT」 | query.py 初稿 | 加多语句拆分检测、补测试 |
| 模块4 测试 | 测试工程师 | 「为 cleaning 模块写 pytest，覆盖代码标准化、异常值剔除、复权计算」 | test_cleaning.py | 补边界用例、修夹具隔离 |
| 模块4 测试 | 调试助手 | 「给出这段异常栈，分析 analyst 仍能查到一年前数据的原因」 | 定位时间钳制取值错误 | 改为取较晚边界并加回归测试 |
| 模块5 文档 | 技术写作 | 「根据现有代码生成安装部署文档与使用说明书」 | install/user_guid 初稿 | 核对命令、补演示脚本 |

> （图 7-1 至 7-5，待补）各模块 AI 交互过程截图（提示词 + AI 输出）

## 7.3 AI 易错点与人工修正

诚实记录 AI 在本项目中暴露的典型问题，以及人工如何纠正——这正是「人在回路」价值所在：

**表 7-2　AI 易错点与人工修正**

| AI 易错点 | 具体表现 | 人工修正 |
| --- | --- | --- |
| 使用过时 API | 生成的 akshare 调用用了旧版函数签名，运行报错 | 查最新文档，适配新签名并加多源兜底 |
| 权限改动不彻底 | 给查询接口加了脱敏，却忘了导出接口同样要脱敏 | 统一抽取脱敏逻辑，查询与导出共用 |
| 安全检查不严 | SQL 白名单只查首词，漏了多语句注入 | 增加分号拆分与逐句校验 |
| 边界条件错误 | 时间权限钳制取了较早值，等于没限制 | 改为 `max(请求起始, 今天-时限)` |
| 过度设计 | 需求阶段生成了社交/论坛等超范围功能 | 按题目范围裁剪，聚焦数据平台 |
| 迁移意识缺失 | 给模型加字段但未处理旧库升级 | 加 `_auto_migrate()` 启动自动补列 |
| 依赖硬编码 | Parquet 导出硬依赖 pyarrow，缺库即崩 | 加引擎缺失回退 CSV |

**AI 贡献与人工占比（自评）**：代码初稿约 70% 由 AI 生成，但其中约 40% 经过人工修改、补充或重写；需求与架构决策、权限模型设计、缺陷根因判断、测试边界设计主要由人完成。每位成员均能逐行解释本人负责模块中 AI 生成代码的逻辑（答辩可抽查）。

## 7.4 AI 伦理与诚信说明

- 本项目 AI 仅用于辅助生成代码、文档与测试初稿，所有产出均经人工审阅、运行与测试验证，无「盲目复制无法解释的 AI 代码直接提交」的情形。
- 代码中由 AI 生成的关键部分已在注释或 ai.md 中标注来源与人工修改说明。
- 报告内容真实反映项目实际状态（如测试数为实测 65 例、采集断网回退样例等），未夸大或虚构功能。
- 团队每位成员都参与了 AI 协作并能解释自己负责的逻辑，符合课程对「理解 AI 边界、审查与重构 AI 代码」的要求。

<div style="page-break-after: always;"></div>

---

# 第 8 章　总结与展望

> **合并来源说明**：本章在完整工程实现与测试结果基础上，对课程目标达成情况、项目特色、不足与后续扩展方向进行总结。

## 8.1 工作总结

本组围绕课程设计题目二，完成了一个**前后端分离、克隆即跑、断网可演示**的股票基金数据获取与管理平台，覆盖题目六大模块的全部关键能力：

- **数据获取**：akshare→腾讯→新浪→样例 四级数据源兜底，支持手动/定时、全量/增量采集，失败重试与告警。
- **数据清洗**：证券代码标准化、异常值剔除、OHLC 一致性校验、基金复权净值、行业多标准分类、跨源交叉验证。
- **数据存储**：13 张表的关系模型，SQLite/MySQL 双栈，唯一约束保证幂等，启动自动迁移。
- **查询与 API**：约 40 个 RESTful 端点 + 受控只读 SQL + WebSocket 实时推送 + Python SDK，统一分页与缓存。
- **监控运维**：完整性检查、异常监测、延迟告警、API 性能监控、告警分发与去重。
- **权限安全**：RBAC + 功能/行级/时间级/字段级四类权限、多租户隔离、操作审计、密码哈希。

工程质量上，后端 65 个 pytest 用例全部通过，覆盖单元、接口、功能与全部权限维度。全过程遵循「人在回路」的 AI 协作方式，沉淀了需求、设计、实现、测试、部署的完整文档。

## 8.2 项目特色

1. **克隆即跑、断网可演示**：默认零外部中间件，样例数据兜底，答辩不受网络波动影响。
2. **四类权限一目了然**：三个演示账号专为直观展示功能/行级/时间级/字段级权限差异而设计。
3. **轻量等价、可平滑升级**：用进程内缓存/关系库/注册表等价 Redis/ClickHouse/商业源，并预留替换接口。
4. **安全意识贯穿**：受控 SQL 多重防护、字段脱敏、配额限流、审计留痕。

## 8.3 不足与展望

- **数据源**：受商业授权限制未接入 Wind/同花顺，未来可在数据源注册表中扩展真实供应商实现。
- **存储**：当前用关系库等价列式存储，海量历史数据场景下可迁移 ClickHouse 提升聚合性能。
- **实时性**：WebSocket 推送为秒级轮询快照，未来可接入真正的行情流。
- **可观测性**：可进一步引入 Prometheus/Grafana 做指标可视化，替换当前内置 API 统计。

## 8.4 课程收获

通过本次课程设计，团队完整实践了一遍「需求—设计—实现—测试—部署」的软件工程流程，更重要的是掌握了与 AI 协作的正确姿势：**把 AI 当作高效的初稿生成器与调试助手，而非可以盲信的代码来源**。我们学会了审查、测试、重构 AI 生成的代码，识别其在过时 API、边界条件、安全检查上的典型盲区，并对每一行提交的代码负责。

<div style="page-break-after: always;"></div>

---

# 附录 A　核心代码节选

> **合并来源说明**：本附录节选当前最新代码中的关键实现，便于教师快速核验功能与设计对应关系。

> 以下为体现关键设计的代码节选，完整源码见项目仓库。

## A.1 受控只读 SQL 查询（安全设计）

`backend/app/api/query.py`——仅管理员、只允许单条 SELECT、禁多语句与 DML/DDL、表白名单、强制 LIMIT：

```python
# 允许查询的表白名单
_ALLOWED_TABLES = {
    "stock_daily", "fund_nav", "instruments", "crawl_jobs", "crawl_runs",
    "export_records", "announcements", "data_quality_issues", "alert_records",
}
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|replace|grant|"
    r"revoke|attach|detach|pragma|vacuum|reindex)\b", re.IGNORECASE)

def _validate_sql(sql: str) -> str:
    s = sql.strip().rstrip(";").strip()
    if not s:
        raise HTTPException(400, "SQL 不能为空")
    if ";" in s:                                   # 禁止多语句
        raise HTTPException(400, "只允许执行单条 SQL 语句")
    if not re.match(r"^(select|with)\b", s, re.IGNORECASE):
        raise HTTPException(400, "只允许 SELECT 查询语句")
    if _FORBIDDEN.search(s):                       # 禁 DML/DDL
        raise HTTPException(400, "检测到非法关键字，仅允许只读查询")
    referenced = set(re.findall(            # 表白名单校验
        r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", s, re.IGNORECASE))
    illegal = referenced - _ALLOWED_TABLES
    if illegal:
        raise HTTPException(400, f"不允许访问的表：{', '.join(sorted(illegal))}")
    return s

# 外层统一强制 LIMIT，用户尾部 LIMIT 被接口参数替代
exec_sql = f"SELECT * FROM ({bounded_sql}) AS _q LIMIT {max_rows + 1}"
```

## A.2 角色权限种子（RBAC 三账号）

`backend/app/services/user_service.py`——三个角色的权限属性，直观对应四类权限：

```python
# admin：全权限
get_or_create_role(db, "admin", "管理员：可采集、导出、管理任务与用户",
    data_scope="all", max_history_days=0, can_export=True, can_view_sensitive=True)
# viewer：全范围、可导出（受配额）、敏感字段脱敏
get_or_create_role(db, "viewer", "普通用户：仅可查询与查看（敏感字段脱敏）",
    data_scope="all", max_history_days=0, can_export=True, can_view_sensitive=False)
# analyst：仅股票（行级）、近 365 天（时间级）、禁导出（功能）
get_or_create_role(db, "analyst", "研究员：仅股票数据、近 365 天、不可导出",
    data_scope="stock", max_history_days=365, can_export=False, can_view_sensitive=False)
```

## A.3 导出配额与功能权限检查

`backend/app/api/exports.py`：

```python
def _check_quota(db: Session, user: User) -> None:
    if not user.role.can_export:                    # 功能权限
        raise HTTPException(403, "当前角色无导出权限")
    if user.role.name == "admin":
        return
    today_start = datetime.combine(date.today(), datetime.min.time())
    used = db.query(func.count(ExportRecord.id)).filter(
        ExportRecord.user_id == user.id,
        ExportRecord.created_at >= today_start).scalar() or 0
    if used >= settings.VIEWER_EXPORT_DAILY_QUOTA:  # 每日配额
        raise HTTPException(429, f"已达今日导出配额（{settings.VIEWER_EXPORT_DAILY_QUOTA} 次）")
```

## A.4 Python SDK（题目「Python 封装」）

`sdk/stockfund_client.py`——对平台 API 的轻量封装，便于量化脚本复用：

```python
from stockfund_client import StockFundClient

cli = StockFundClient("http://127.0.0.1:8000")
cli.login("admin", "admin123")
df = cli.stock_daily("600519.SH")          # 有 pandas 则返回 DataFrame
nav = cli.fund_nav("510300.OF")
cli.crawl(job_type="stock_daily", target_codes="600519.SH")
rows = cli.sql("SELECT code, COUNT(*) c FROM stock_daily GROUP BY code")
```

## A.5 应用启动编排（lifespan）

`backend/app/main.py`——建表→种子→调度→可选采集→安全关闭：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()                          # 建表 + 自动迁移
    run_all()                          # 播种角色/用户/标的/样例行情
    if settings.SCHEDULER_ENABLED:
        scheduler.start()              # 注册 cron 采集任务
    if settings.AUTO_CRAWL_ON_STARTUP:
        _kickoff_auto_crawl()          # 可选：后台联网预采集
    yield
    if settings.SCHEDULER_ENABLED:
        scheduler.shutdown()           # 安全停止调度器
```

<div style="page-break-after: always;"></div>

---

# 附录 B　图表索引

**图索引（截图待补位置一览）**

| 编号 | 标题 | 所在章节 |
| --- | --- | --- |
| 图 1-1 | GitHub 仓库首页与目录结构 | 1.5 |
| 图 1-2 | 阶段性 commit 记录 | 1.5 |
| 图 2-1 | 用例关系图 / 业务流程泳道图 | 2.3 |
| 图 3-1 | 系统总体架构图 | 3.2 |
| 图 3-2 | 部署拓扑图 | 3.2 |
| 图 3-3 | 核心类图 | 3.3 |
| 图 3-4 | 数据库 ER 图 | 3.4 |
| 图 3-5 | Swagger UI 接口文档 | 3.5 |
| 图 3-6~3-9 | 登录/驾驶舱/K线/UI风格 | 3.6 |
| 图 4-1 | analyst 三层权限对比 | 4.2 |
| 图 4-2~4-5 | 采集/监控/导出/系统管理页 | 4.11 |
| 图 5-1 | pytest 全绿执行 | 5.1 |
| 图 5-2 | 缺陷修复前后对比 | 5.5 |
| 图 6-1~6-2 | 一键启动首屏/演示流程 | 6.7 |
| 图 7-1~7-5 | 各模块 AI 交互过程 | 7.2 |

**表索引**

| 编号 | 标题 |
| --- | --- |
| 表 1-1/1-2 | 团队角色分工 / 模块分工 |
| 表 2-1 | 角色与演示账号 |
| 表 3-1~3-5 | 技术栈 / 数据表 / API / 菜单 / 等价实现 |
| 表 4-1 | 三层数据权限实现 |
| 表 5-1 | 缺陷修复记录 |
| 表 6-1/6-2 | 配置项 / 页面操作指引 |
| 表 7-1/7-2 | AI Prompt 示例 / AI 易错点 |

<div style="page-break-after: always;"></div>

---

# 附录 C　答辩问答准备

> 预演常见提问，确保每位成员都能解释本人模块。

**Q1：为什么不用 Redis/ClickHouse/MongoDB？**
A：题目要求的是这些组件提供的「能力」，不是组件本身。我们用进程内 TTL 缓存、关系库受控聚合、announcements 文档表做了**架构等价实现**，并在代码中预留可替换接口（见表 3-5），既覆盖需求又保证助教克隆即跑、无需装任何中间件。

**Q2：断网了怎么演示采集？**
A：采集器是四级数据源链 akshare→腾讯→新浪→样例。前三个是真实联网源，全失败时自动回退内置样例生成器（确定性随机游走，形态逼真），source 标记为 sample。所以断网也能完整演示采集→入库→查询全链路。

**Q3：四类权限具体怎么实现的？**
A：权限属性挂在 `roles` 表上。功能权限用 `require_admin` 依赖和 `can_export` 拦截；行级用 `data_scope` 过滤 `instruments.asset_type`；时间级用 `max_history_days` 钳制查询起始日期；字段级用 `can_view_sensitive` 对成交额等脱敏。analyst 账号一登录就能看到这四类差异。

**Q4：受控 SQL 怎么防注入？**
A：四重防护——只允许 SELECT/WITH 开头、禁止分号多语句、正则拦截 DML/DDL 关键字、表名白名单校验，最后外层强制包一层 LIMIT。对应测试 `test_sql_*` 共 6 个用例验证。

**Q5：AI 生成的代码你们都理解吗？**
A：是。我们遵循「人在回路」，所有 AI 代码都经过阅读、运行、测试三关，并在 ai.md 记录了 AI 的典型错误（过时 akshare API、脱敏漏改导出、时间钳制取错边界等）和我们的修正。每位成员能逐行解释本人负责模块的逻辑。

**Q6：测试覆盖了哪些？多少用例？**
A：65 个 pytest 用例全部通过，分布在 5 个测试文件：清洗单元（6）、增强逻辑单元（11）、核心接口（11）、监控接口（10）、增强能力端到端（27）。覆盖单元、接口、功能与全部四类权限维度。

**Q7：数据清洗做了哪些标准化？**
A：证券代码归一化（多种写法→标准格式）、异常/缺失值剔除、OHLC 一致性校验、基金复权净值计算、行业多标准（申万/中信/GICS）分类、跨源交叉验证登记质量问题。

**Q8：如何切换到 MySQL 与真实数据？**
A：MySQL 改一行 `DATABASE_URL`，先跑 `sql/init.sql` 建表即可；真实数据保持联网并把 `AUTO_CRAWL_ON_STARTUP` 设为 true，采集器会优先走真实源，源异常自动回退样例，不影响演示。

---

*（报告正文完。提交前请：① 填写封面与团队信息；② 在各「待补」处插入实测截图；③ 按需将本 Markdown 导出为 docx/PDF 并命名为「题目二-数据平台-成员1-成员2.docx」。）*
