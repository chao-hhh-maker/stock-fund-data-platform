# 第四步快速参考指南

## 🚀 快速启动

### 启动后端服务
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8001
```

### 访问 API 文档
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### 运行测试
```bash
cd tests
python verify_step4.py
```

---

## 🔑 默认账户

### 管理员
- **用户名**: admin
- **密码**: admin123
- **角色**: admin
- **权限**: 查询、导出、管理、系统管理

---

## 📡 核心接口

### 1. 健康检查
```bash
GET /api/health
```

**响应**:
```json
{
  "status": "ok",
  "message": "服务运行正常"
}
```

---

### 2. 用户登录
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

---

### 3. 获取用户信息
```bash
GET /api/auth/me
Authorization: Bearer <token>
```

**响应**:
```json
{
  "code": 200,
  "message": "获取用户信息成功",
  "data": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role_name": "admin",
    "is_active": true
  }
}
```

---

## 🔧 配置说明

### 环境变量 (.env)

```bash
# 数据库配置
DATABASE_URL=mysql+pymysql://root:400113@localhost:3306/stock_fund_platform

# JWT配置
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24小时

# 应用配置
APP_NAME=股票基金数据平台
APP_VERSION=0.1.0
DEBUG=True
```

### 修改配置

**修改端口**:
```bash
python -m uvicorn app.main:app --reload --port 8002
```

**修改 Token 有效期**:
编辑 `.env` 文件：
```
ACCESS_TOKEN_EXPIRE_MINUTES=4320  # 3天
```

**修改密钥**:
编辑 `.env` 文件：
```
SECRET_KEY=new-secret-key-here
```

---

## 📁 目录结构

```
backend/app/
├── api/              # API 路由
│   └── auth.py       # 认证接口
├── models/           # 数据模型
│   ├── user.py       # 用户模型
│   └── role.py       # 角色模型
├── schemas/          # Pydantic schemas
│   └── auth.py       # 认证 schemas
├── core/             # 核心模块
│   ├── config.py     # 配置管理
│   ├── database.py   # 数据库连接
│   ├── security.py   # 安全认证
│   └── response.py   # 统一响应
├── services/         # 业务逻辑（预留）
├── tasks/            # 任务管理（预留）
└── main.py           # 应用入口
```

---

## 🔐 认证流程

### 1. 登录获取 Token
```python
import requests

response = requests.post(
    "http://localhost:8001/api/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = response.json()["data"]["access_token"]
```

### 2. 使用 Token 访问受保护接口
```python
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8001/api/auth/me",
    headers=headers
)
```

### 3. Token 验证（服务端）
```python
from app.api.auth import get_current_user
from fastapi import Depends

@app.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    return {"user": current_user.username}
```

---

## ⚠️ 错误码说明

| 错误码 | 含义 | 说明 |
|--------|------|------|
| 200 | SUCCESS | 成功 |
| 400 | BAD_REQUEST | 请求参数错误 |
| 401 | UNAUTHORIZED | 未认证或token无效 |
| 403 | FORBIDDEN | 权限不足 |
| 404 | NOT_FOUND | 资源不存在 |
| 422 | VALIDATION_ERROR | 数据验证失败 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |
| 503 | DATABASE_ERROR | 数据库错误 |

---

## 🧪 测试命令

### 测试健康检查
```bash
curl http://localhost:8001/api/health
```

### 测试登录
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 测试获取用户信息
```bash
curl http://localhost:8001/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 运行完整测试
```bash
python tests/verify_step4.py
```

---

## 🛠️ 常见问题

### Q1: 端口被占用
**解决**: 更换端口
```bash
python -m uvicorn app.main:app --reload --port 8002
```

### Q2: 数据库连接失败
**检查**:
1. MySQL 服务是否启动
2. 数据库是否存在
3. .env 中的 DATABASE_URL 是否正确

### Q3: 登录失败
**检查**:
1. 数据库中是否有 admin 用户
2. 密码是否正确（admin123）
3. 运行 `python tests/verify_db_users.py` 验证

### Q4: Token 验证失败
**检查**:
1. Token 是否过期（默认24小时）
2. Authorization 头格式是否正确（Bearer + 空格 + token）
3. SECRET_KEY 是否与生成 token 时一致

### Q5: Swagger 无法访问
**检查**:
1. 后端服务是否运行
2. 端口是否正确
3. 防火墙是否阻止

---

## 📚 相关文档

- **完整报告**: docs/STEP4_COMPLETE.md
- **最终总结**: docs/STEP4_FINAL_SUMMARY.md
- **检查清单**: docs/step4_checklist.md
- **项目进度**: docs/progress.md
- **数据库设计**: docs/db.md

---

## 🔗 有用链接

- FastAPI 文档: https://fastapi.tiangolo.com/
- SQLAlchemy 文档: https://docs.sqlalchemy.org/
- Pydantic 文档: https://docs.pydantic.dev/
- JWT 介绍: https://jwt.io/

---

## 💡 开发提示

### 添加新接口
1. 在 `app/api/` 下创建新的路由文件
2. 定义 Pydantic schemas（请求/响应）
3. 实现业务逻辑
4. 在 `main.py` 中注册路由

### 添加新模型
1. 在 `app/models/` 下创建模型文件
2. 继承 Base 类
3. 定义表结构和字段
4. 在 `models/__init__.py` 中导入

### 添加新配置
1. 在 `app/core/config.py` 的 Settings 类中添加
2. 在 `.env` 文件中设置值
3. 通过 `settings.XXX` 访问

---

**最后更新**: 2026-05-22  
**版本**: v1.0
