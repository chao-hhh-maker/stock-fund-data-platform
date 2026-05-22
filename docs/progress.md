# 项目开发进度

## 整体进度: 55% (6/11 步骤完成)

---

## ✅ 已完成步骤

### 第一步: 范围确定
**完成时间**: 2026-05-07
**工作量**: 约 4 小时

**完成内容**:
- [x] 确认项目边界和MVP功能
- [x] 创建 README.md 说明文档
- [x] 定义 MVP 和非 MVP 功能清单
- [x] 创建 construction-guide.md 建设指南

**产出物**:
- `README.md` - 项目说明文档
- `construction-guide.md` - 完整落地流程指南

---

### 第二步: 工程骨架搭建
**完成时间**: 2026-05-22
**工作量**: 约 6 小时

**完成内容**:
- [x] 创建基础目录结构 (backend, frontend, sql, scripts, tests)
- [x] 初始化后端 Python 环境
- [x] 安装后端依赖包 (FastAPI, SQLAlchemy, Pandas, Akshare等)
- [x] 创建后端分层目录 (app/api, models, schemas, services, core, tasks)
- [x] 实现最小后端应用 (/health 接口)
- [x] 初始化前端 Vue 项目
- [x] 安装前端依赖 (Element Plus, Axios, Pinia, Vue Router, ECharts)
- [x] 验证前后端服务正常启动

**产出物**:
- `backend/app/main.py` - 后端主应用
- `backend/requirements.txt` - 后端依赖清单
- `backend/.env` - 后端环境配置
- `frontend/` - 前端项目目录

**验证结果**:
- ✅ 后端服务启动成功 (http://localhost:8000)
- ✅ 健康检查接口响应正常
- ✅ 前端页面可访问 (http://localhost:5173)
- ✅ 目录结构稳定

---

### 第三步: 数据库设计
**完成时间**: 2026-05-22
**工作量**: 约 8 小时

**完成内容**:
- [x] 设计8张核心表结构
  - users (用户表)
  - roles (角色表)
  - instruments (金融工具表)
  - stock_daily (股票日线数据表)
  - fund_nav (基金净值数据表)
  - crawl_jobs (采集任务配置表)
  - crawl_runs (采集任务执行记录表)
  - export_records (数据导出记录表)
- [x] 编写 SQL 初始化脚本 (sql/init.sql)
- [x] 创建数据库和表结构
- [x] 插入默认角色和管理员账户
- [x] 创建 backend/.env 配置文件
- [x] 编写数据库设计文档 (docs/db.md)
- [x] 编写数据库设置指南 (docs/database_setup.md)
- [x] 创建数据库验证脚本 (scripts/verify_db.py)

**产出物**:
- `sql/init.sql` - 数据库初始化脚本
- `docs/db.md` - 数据库设计文档
- `docs/database_setup.md` - 数据库设置指南
- `scripts/verify_db.py` - 数据库验证脚本
- `backend/.env` - 环境配置文件

**设计要点**:
- 所有核心表使用 InnoDB 引擎, utf8mb4 字符集
- 关键字段建立唯一索引防止重复数据
- 外键约束保证数据一致性
- 预设管理员和普通用户两种角色
- 详细记录每个字段的用途和索引原因

**验证结果**:
- ✅ MySQL服务已启动
- ✅ 数据库和表结构已创建
- ✅ 默认角色和管理员账户已插入
- ✅ 密码哈希验证通过

---

## 🔄 进行中步骤

无

---

## ✅ 已完成步骤

### 第四步: 后端认证与基础接口
**完成时间**: 2026-05-22
**工作量**: 约 8 小时

**完成内容**:
- [x] 实现 JWT 认证机制
  - 创建 app/core/security.py 安全模块
  - 实现密码哈希和验证功能
  - 实现 JWT token 生成和解码功能
- [x] 创建 POST /api/auth/login 登录接口
  - 支持用户名密码登录
  - 返回 JWT access token
  - 统一响应格式
- [x] 创建 GET /api/auth/me 获取当前用户接口
  - 基于 JWT token 认证
  - 返回用户详细信息
  - 包含角色信息
- [x] 创建 GET /api/health 健康检查接口
  - 服务状态检查
  - 快速验证服务可用性
- [x] 统一错误码规范
  - 创建 ErrorCode 常量类
  - 定义常见错误码 (200, 400, 401, 403, 404, 422, 500, 503)
  - 统一响应格式 Response 和 ErrorResponse
- [x] Swagger 文档完善
  - FastAPI 自动生成 API 文档
  - 接口描述和参数说明完整
  - 可通过 /docs 和 /redoc 访问
- [x] 实现依赖注入 get_current_user
  - 从 token 中提取用户信息
  - 验证用户有效性
  - 检查用户激活状态
- [x] 创建 Pydantic schemas
  - LoginRequest - 登录请求
  - TokenResponse - Token 响应
  - UserInfo - 用户信息

**产出物**:
- `backend/app/api/auth.py` - 认证接口
- `backend/app/core/security.py` - 安全认证模块
- `backend/app/core/response.py` - 统一响应格式
- `backend/app/schemas/auth.py` - 认证相关 schemas
- `backend/app/models/user.py` - 用户模型
- `backend/app/models/role.py` - 角色模型
- `tests/test_step4.py` - 第四步测试脚本

**验证结果**:
- ✅ 后端服务启动成功 (http://localhost:8001)
- ✅ 健康检查接口响应正常
- ✅ 登录接口可以获取 token
- ✅ 通过 token 可以访问受保护接口
- ✅ 无效 token 被正确拒绝
- ✅ 错误密码被正确处理
- ✅ Swagger 文档可直接演示 (http://localhost:8001/docs)

**技术要点**:
- 使用 bcrypt 进行密码哈希
- 使用 python-jose 进行 JWT token 编解码
- 使用 OAuth2PasswordBearer 实现标准认证流程
- 使用 FastAPI 依赖注入实现权限控制
- 统一响应格式便于前端处理

---

## ✅ 已完成步骤

### 第五步: 数据采集器开发
**完成时间**: 2026-05-22
**工作量**: 约 10 小时

**完成内容**:
- [x] 创建采集器目录结构
  - app/tasks/crawlers - 采集器模块
  - app/tasks/cleaners - 数据清洗模块
  - app/services - 业务服务层
- [x] 实现股票日线采集器
  - 使用 Akshare 获取股票历史行情
  - 支持单只和批量采集
  - 自动前复权处理
- [x] 实现基金净值采集器
  - 使用 Akshare 获取基金净值数据
  - 支持单只和批量采集
  - 包含单位净值、累计净值、日增长率
- [x] 实现数据清洗和标准化
  - 缺失值处理（中位数填充）
  - 代码标准化（6位数字格式）
  - 字段类型统一转换
  - 重复记录去除
  - 无效记录过滤
- [x] 实现采集任务执行记录
  - 创建 CrawlJob 和 CrawlRun 模型
  - 记录开始时间、结束时间、状态
  - 记录采集记录数和错误信息
  - 失败时不中断整个流程
- [x] 创建采集服务层
  - CrawlService 协调采集器和数据库
  - 支持股票和基金两种采集类型
  - 自动处理数据入库（插入或更新）
  - 完整的异常处理和事务管理
- [x] 创建采集任务 API 接口
  - POST /api/tasks/crawl/stock - 股票采集
  - POST /api/tasks/crawl/fund - 基金采集
  - GET /api/tasks - 任务列表
  - GET /api/tasks/{task_id} - 任务详情
  - GET /api/tasks/{task_id}/logs - 执行日志

**产出物**:
- `backend/app/tasks/crawlers/stock_crawler.py` - 股票采集器
- `backend/app/tasks/crawlers/fund_crawler.py` - 基金采集器
- `backend/app/tasks/cleaners/data_cleaner.py` - 数据清洗工具
- `backend/app/services/crawl_service.py` - 采集服务
- `backend/app/api/tasks.py` - 采集任务 API
- `backend/app/models/crawl.py` - 采集任务模型
- `backend/app/models/stock_daily.py` - 股票数据模型
- `backend/app/models/fund_nav.py` - 基金数据模型
- `backend/app/models/instrument.py` - 金融工具模型
- `tests/test_crawlers.py` - 采集器测试脚本

**验证结果**:
- ✅ 股票采集器可成功获取数据并入库
- ✅ 基金采集器可成功获取数据并入库
- ✅ 数据清洗功能正常工作
- ✅ 采集任务执行记录完整
- ✅ 失败场景有明确日志
- ✅ API 接口可通过 Swagger 测试

**技术要点**:
- 使用 Akshare 作为数据源（免费、稳定）
- Pandas 进行数据处理和清洗
- SQLAlchemy ORM 进行数据库操作
- 批量采集时单个失败不影响其他
- 完整的事务管理和异常处理
- 详细的日志记录便于调试

---

## ✅ 已完成步骤

### 第六步: 任务管理系统
**完成时间**: 2026-05-22
**工作量**: 约 8 小时

**完成内容**:
- [x] 集成 APScheduler 定时任务调度器
  - 创建 TaskScheduler 管理器
  - 支持 CRON 表达式配置
  - 后台运行，不阻塞主线程
- [x] 实现任务相关接口完善
  - POST /api/tasks/crawl/stock - 手动触发股票采集
  - POST /api/tasks/crawl/fund - 手动触发基金采集
  - POST /api/tasks/create - 创建定时任务
  - POST /api/tasks/{task_id}/enable - 启用任务
  - POST /api/tasks/{task_id}/disable - 停用任务
  - GET /api/tasks - 任务列表
  - GET /api/tasks/{task_id} - 任务详情
  - GET /api/tasks/{task_id}/logs - 执行日志
- [x] 系统启动时加载已启用任务
  - lifespan 事件中自动加载
  - 从数据库查询 is_enabled=1 的任务
  - 自动注册到调度器
- [x] 系统关闭时安全退出调度器
  - lifespan 事件中优雅关闭
  - 等待当前任务完成
  - 释放资源
- [x] 任务执行前后写日志
  - 事件监听器记录执行结果
  - 成功/失败状态更新
  - 详细的错误信息记录
- [x] 任务启用/停用开关
  - 数据库 is_enabled 字段控制
  - API 接口动态启用/停用
  - 避免调试期误触发
- [x] 定时任务执行机制
  - 根据 CRON 表达式自动触发
  - 支持股票和基金两种类型
  - 执行结果自动记录到 crawl_runs

**产出物**:
- `backend/app/tasks/scheduler/scheduler_manager.py` - 调度器管理器
- `backend/app/api/tasks.py` - 完善的任务管理 API
- `backend/app/main.py` - 集成生命周期管理
- `tests/test_task_scheduler.py` - 任务管理测试脚本

**验证结果**:
- ✅ 可以从接口手动触发任务
- ✅ 到时间会自动触发任务（APScheduler）
- ✅ 能查看最近任务执行历史
- ✅ 任务可以启用/停用
- ✅ 系统启动/关闭时调度器正常工作
- ✅ 执行日志完整可追踪

**技术要点**:
- 使用 APScheduler 的 BackgroundScheduler
- FastAPI lifespan 事件管理生命周期
- 事件监听器跟踪任务执行状态
- CRON 表达式灵活配置调度时间
- 数据库和调度器状态同步

---

## ⏳ 待开始步骤

### 第四步: 后端认证与基础接口
**预计工作量**: 8-10 小时

**计划内容**:
- [ ] 实现 JWT 认证机制
- [ ] 创建 POST /api/auth/login 登录接口
- [ ] 创建 GET /api/auth/me 获取当前用户接口
- [ ] 统一错误码规范
- [ ] Swagger 文档完善

---

### 第五步: 数据采集器开发
**预计工作量**: 10-12 小时

**计划内容**:
- [ ] 实现股票日线采集器
- [ ] 实现基金净值采集器
- [ ] 数据清洗和标准化处理
- [ ] 采集结果写入数据库
- [ ] 异常处理和日志记录

---

### 第六步: 任务管理系统
**预计工作量**: 8-10 小时

**计划内容**:
- [ ] 任务 CRUD 接口
- [ ] APScheduler 定时任务集成
- [ ] 任务执行历史查询
- [ ] 任务启用/停用开关

---

### 第七步: 查询和导出接口
**预计工作量**: 8-10 小时

**计划内容**:
- [ ] 股票查询接口
- [ ] 基金查询接口
- [ ] 分页和筛选功能
- [ ] 数据导出接口
- [ ] 导出历史记录

---

### 第八步: 前端核心页面
**预计工作量**: 10-12 小时

**计划内容**:
- [ ] 登录页面
- [ ] 数据查询页面
- [ ] 任务管理页面
- [ ] 仪表盘页面

---

### 第九步: 联调测试
**预计工作量**: 6-8 小时

**计划内容**:
- [ ] 编写测试用例
- [ ] 接口测试
- [ ] 前端功能测试
- [ ] Bug修复

---

### 第十步: 文档补齐
**预计工作量**: 6-8 小时

**计划内容**:
- [ ] user_stories.md
- [ ] use_cases.md
- [ ] architect.md
- [ ] backend_api.md
- [ ] ui_design.md
- [ ] ai.md
- [ ] assign.md
- [ ] test.md
- [ ] install.md
- [ ] user_guid.md

---

### 第十一步: 演示演练
**预计工作量**: 3-4 小时

**计划内容**:
- [ ] 固定演示脚本
- [ ] 第一次完整演练
- [ ] 第二次计时演练
- [ ] 准备异常兜底方案

---

## 📝 备注

- 本进度表最后更新时间: 2026-05-22
- 实际工作量可能与预估有差异
- 每完成一个步骤后更新此文档
