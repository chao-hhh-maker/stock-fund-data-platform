# 安装与部署文档（install.md）

> 模块 5 交付物 · 本地部署步骤（Windows / macOS / Linux 通用）

## 1. 环境要求

| 组件 | 版本 | 必需 |
| --- | --- | --- |
| Python | 3.10+（已在 3.13 验证） | 是 |
| Node.js | 18+（已在 22 验证） | 是 |
| MySQL | 8.0+ | 否（默认用 SQLite） |

## 2. 后端部署

```bash
cd backend

# 1) 创建虚拟环境
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

# 2) 安装依赖
pip install -r requirements.txt

# 3) 配置（可选，默认 SQLite 无需改）
cp .env.example .env

# 4) 启动
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

启动后：
- API 根：http://127.0.0.1:8000/
- Swagger 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/health

> 首次启动自动建表、创建默认账号、登记预置标的并生成样例行情，**无需手工初始化**。

### 默认账号
| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | admin | admin123 |
| 普通用户 | viewer | viewer123 |

## 3. 前端部署

```bash
cd frontend
npm install
npm run dev      # 开发模式，访问 http://localhost:5173
# 或
npm run build    # 生产构建，产物在 dist/
```

开发模式下 `/api` 已配置代理到后端 8000 端口，无需额外配置跨域。

## 4. 切换到 MySQL（可选）

```sql
CREATE DATABASE stock_fund_platform DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE stock_fund_platform;
SOURCE sql/init.sql;
```

修改 `backend/.env`：
```
DATABASE_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/stock_fund_platform?charset=utf8mb4
```
确保已安装 `pymysql`（在 requirements.txt 中），重启后端即可。

## 5. 启用真实数据源（可选）

默认无网络时使用内置样例数据。若要接入真实行情：
```bash
pip install akshare
```
安装后系统优先使用 akshare 拉取真实数据，失败时仍自动回退样例数据，不影响演示。

## 6. 运行测试

```bash
cd backend
python -m pytest
```

## 7. 常见问题

| 问题 | 解决 |
| --- | --- |
| 端口被占用 | 改用 `--port 8001` 并同步前端代理 target |
| 前端 npm 缓存权限报错 | `npm install --cache ./.npm-cache` |
| 数据库连接失败 | 检查 `.env` 的 DATABASE_URL，或删除 `.db` 文件让其重建 |
| 采集很慢 | 未装 akshare 时走样例数据，速度很快；装了 akshare 受网络影响 |
