# 安装与部署文档（install.md）

> **项目名称**：股票基金数据获取和管理平台  
> **课程模块**：模块 5：上线部署与报告撰写  
> **文档定位**：本地部署、可选 MySQL、测试运行、常见问题  
> **最终报告映射**：最终报告第 6 章 6.1-6.5 节  
> **代码依据**：README、backend/requirements.txt、frontend/package.json、backend/.env.example  
> **整理日期**：2026 年 6 月

## 0. 文档说明

本文档为课程设计过程文档的整理版，用于提交到 GitHub/Gitee 仓库。它与最终课程设计报告保持一致：仓库中保留本文件作为平时过程材料，最终报告中已将其核心内容合并到对应章节。

| 项目 | 内容 |
| --- | --- |
| 文档状态 | 最终整理版 |
| 是否合并进最终报告 | 是 |
| 后续需补充 | 团队真实姓名、学号、仓库地址、必要截图 |

---

## 1. 环境要求

| 组件 | 推荐版本 | 是否必需 | 用途 |
| --- | --- | --- | --- |
| Python | 3.10+（项目曾在 3.13 环境验证） | 是 | 后端 FastAPI 服务 |
| Node.js | 18+（项目曾在 22 环境验证） | 是 | 前端 Vite 开发与构建 |
| npm | 9+ | 是 | 前端依赖安装 |
| SQLite | Python 内置 | 是 | 默认数据库，克隆即跑 |
| MySQL | 8.0+ | 否 | 可选部署方案 |
| Git | 任意新版 | 建议 | 克隆仓库和版本管理 |

## 2. 获取代码

```bash
git clone https://github.com/XCT-byte/stock-fund-data-platform.git
cd stock-fund-data-platform
```

若使用压缩包提交，解压后直接进入项目根目录即可。

## 3. 后端启动（默认 SQLite）

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 首次可复制配置文件；默认 SQLite 不修改也能启动
copy .env.example .env     # Windows
# cp .env.example .env     # macOS / Linux

# 启动服务
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

启动后访问：

| 地址 | 说明 |
| --- | --- |
| `http://127.0.0.1:8000/` | API 根路径 |
| `http://127.0.0.1:8000/docs` | Swagger 在线接口文档 |
| `http://127.0.0.1:8000/api/health` | 健康检查 |

首次启动会自动完成：建表、创建默认账号、初始化标的、生成样例行情/净值、启动调度器。

## 4. 前端启动

打开新的终端：

```bash
cd frontend
npm install
npm run dev
```

访问：`http://localhost:5173`。开发模式下 Vite 已配置 `/api` 代理到后端 `http://127.0.0.1:8000`。

## 5. 默认演示账号

| 角色 | 用户名 | 密码 | 权限说明 |
| --- | --- | --- | --- |
| 管理员 | `admin` | `admin123` | 全权限：采集、导出、SQL、用户/角色/租户管理、审计 |
| 普通用户 | `viewer` | `viewer123` | 可查询和导出，但敏感字段脱敏 |
| 研究员 | `analyst` | `analyst123` | 仅股票、近 365 天、不可导出，演示行级/时间/功能权限 |

## 6. MySQL 部署（可选）

默认 SQLite 更适合课程演示；若老师要求关系型数据库脚本，可使用 MySQL：

```sql
CREATE DATABASE stock_fund_platform DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE stock_fund_platform;
SOURCE sql/init.sql;
```

修改 `backend/.env`：

```env
DATABASE_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/stock_fund_platform?charset=utf8mb4
```

重启后端即可。

## 7. 真实数据源（可选）

系统默认具备样例兜底数据。若安装 akshare 并且网络可用，采集器会优先使用真实数据源；若失败则自动回退样例数据，不影响演示。

```bash
pip install akshare
```

## 8. 运行测试

```bash
cd backend
python -m pytest -q
```

项目测试文件共定义 65 个 pytest 用例。提交前建议截图保存测试通过结果，并插入最终 Word 报告。

## 9. 生产构建

```bash
cd frontend
npm run build
```

构建产物位于 `frontend/dist/`。课程演示一般使用 `npm run dev` 即可。

## 10. 常见问题

| 问题 | 原因 | 解决方式 |
| --- | --- | --- |
| `ModuleNotFoundError: jose` | 后端依赖未安装完整 | 确认虚拟环境已激活，重新 `pip install -r requirements.txt` |
| 8000 端口被占用 | 本机已有服务占用端口 | 改为 `--port 8001`，并同步修改前端代理 |
| npm 安装失败或权限报错 | npm 缓存目录权限问题 | `npm install --cache ./.npm-cache` |
| 前端访问接口失败 | 后端未启动或代理端口不一致 | 检查后端端口和 `vite.config.js` |
| 真实采集失败 | 网络或数据源接口不可用 | 正常现象，系统会自动回退样例数据 |
| MySQL 建表失败 | 字符集、保留字或连接串问题 | 使用 `utf8mb4`，确认 SQL 中保留字已加反引号 |

## 11. 截图占位

- 【图：后端启动成功，待补】
- 【图：Swagger 文档页面，待补】
- 【图：前端启动成功，待补】
- 【图：pytest 通过结果，待补】
