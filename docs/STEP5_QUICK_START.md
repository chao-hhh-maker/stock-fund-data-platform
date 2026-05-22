# 第五步快速使用指南

## 🚀 快速开始

### 1. 启动后端服务
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8001
```

### 2. 访问 API 文档
打开浏览器访问: http://localhost:8001/docs

---

## 📡 采集数据

### 方法一：使用 Swagger UI（推荐）

#### 采集股票数据
1. 找到 `POST /api/tasks/crawl/stock`
2. 点击 "Try it out"
3. 输入参数（可选）:
   ```json
   {
     "stock_codes": ["000001", "600000"],
     "start_date": "20240101",
     "end_date": "20241231"
   }
   ```
4. 点击 "Execute"
5. 查看响应结果

#### 采集基金数据
1. 找到 `POST /api/tasks/crawl/fund`
2. 点击 "Try it out"
3. 输入参数（可选）:
   ```json
   {
     "fund_codes": ["000001", "110022"],
     "start_date": "2024-01-01",
     "end_date": "2024-12-31"
   }
   ```
4. 点击 "Execute"
5. 查看响应结果

---

### 方法二：使用 cURL

#### 采集股票
```bash
curl -X POST "http://localhost:8001/api/tasks/crawl/stock" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_codes": ["000001"],
    "start_date": "20240101",
    "end_date": "20241231"
  }'
```

#### 采集基金
```bash
curl -X POST "http://localhost:8001/api/tasks/crawl/fund" \
  -H "Content-Type: application/json" \
  -d '{
    "fund_codes": ["000001"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }'
```

---

### 方法三：使用 Python

```python
import requests

base_url = "http://localhost:8001"

# 采集股票
response = requests.post(
    f"{base_url}/api/tasks/crawl/stock",
    json={
        "stock_codes": ["000001", "600000"],
        "start_date": "20240101",
        "end_date": "20241231"
    }
)
print(response.json())

# 采集基金
response = requests.post(
    f"{base_url}/api/tasks/crawl/fund",
    json={
        "fund_codes": ["000001"],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
)
print(response.json())
```

---

## 🔍 查询任务状态

### 获取任务列表
```bash
GET /api/tasks?page=1&page_size=20
```

### 获取任务详情
```bash
GET /api/tasks/{task_id}
```

### 获取执行日志
```bash
GET /api/tasks/{task_id}/logs?page=1&page_size=20
```

---

## 🧪 运行测试

```bash
cd tests
python test_crawlers.py
```

测试内容:
1. 股票采集器功能测试
2. 基金采集器功能测试
3. 数据库数据验证

---

## 📊 查看数据库

### 连接数据库
```bash
mysql -u root -p stock_fund_platform
```

### 查询股票数据
```sql
-- 查看股票数据总数
SELECT COUNT(*) FROM stock_daily;

-- 查看某只股票的数据
SELECT * FROM stock_daily WHERE code = '000001' ORDER BY trade_date DESC LIMIT 10;

-- 查看最新采集日期
SELECT MAX(trade_date) FROM stock_daily;
```

### 查询基金数据
```sql
-- 查看基金数据总数
SELECT COUNT(*) FROM fund_nav;

-- 查看某只基金的数据
SELECT * FROM fund_nav WHERE code = '000001' ORDER BY nav_date DESC LIMIT 10;

-- 查看最新净值日期
SELECT MAX(nav_date) FROM fund_nav;
```

### 查询采集记录
```sql
-- 查看所有采集任务
SELECT * FROM crawl_jobs;

-- 查看执行记录
SELECT * FROM crawl_runs ORDER BY start_time DESC LIMIT 10;

-- 查看失败的任务
SELECT * FROM crawl_runs WHERE status = 'failed';
```

---

## ⚙️ 配置说明

### 默认采集范围
如果不指定股票代码/基金代码，系统会：
1. 先从数据库查询所有活跃的股票/基金
2. 如果数据库没有，使用测试代码：
   - 股票: ['000001', '600000', '000002']
   - 基金: ['000001', '110022', '000002']

### 默认日期范围
- **股票**: 最近一年（从今天往前推365天）
- **基金**: 最近一年（从今天往前推365天）

### 修改默认值
编辑采集器代码中的默认参数：
- 股票: `backend/app/tasks/crawlers/stock_crawler.py`
- 基金: `backend/app/tasks/crawlers/fund_crawler.py`

---

## 🔧 常见问题

### Q1: 采集速度慢怎么办？
A: 
- 减少每次采集的股票/基金数量
- 缩小日期范围
- 后续可以添加并发采集（第六步后）

### Q2: 采集失败怎么办？
A:
1. 检查网络连接
2. 检查股票代码/基金代码是否正确
3. 查看日志了解具体错误
4. 查看 crawl_runs 表的 error_message 字段

### Q3: 如何查看日志？
A:
- 控制台会实时输出日志
- 日志级别: INFO, WARNING, ERROR
- 包含详细的采集进度和错误信息

### Q4: 数据重复了怎么办？
A:
- 系统会自动检测重复（基于 code + date）
- 重复的记录会被更新而不是插入
- 不用担心重复数据问题

### Q5: 如何批量采集大量股票？
A:
- 建议分批采集，每批 10-20 只
- 避免一次性采集太多导致超时
- 可以编写脚本循环调用 API

---

## 💡 使用技巧

### 1. 先测试单只股票/基金
```json
{
  "stock_codes": ["000001"]
}
```

### 2. 确认成功后再批量采集
```json
{
  "stock_codes": ["000001", "600000", "000002", "600036"]
}
```

### 3. 指定日期范围减少数据量
```json
{
  "stock_codes": ["000001"],
  "start_date": "20241201",
  "end_date": "20241231"
}
```

### 4. 定期查看任务状态
```bash
GET /api/tasks/{task_id}/logs
```

### 5. 监控采集成功率
```sql
SELECT 
  status,
  COUNT(*) as count,
  AVG(records_count) as avg_records
FROM crawl_runs
GROUP BY status;
```

---

## 📝 示例场景

### 场景 1: 采集某只股票的最新数据
```json
POST /api/tasks/crawl/stock
{
  "stock_codes": ["000001"],
  "start_date": "20241201",
  "end_date": "20241231"
}
```

### 场景 2: 采集多只基金的年度数据
```json
POST /api/tasks/crawl/fund
{
  "fund_codes": ["000001", "110022", "000002"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

### 场景 3: 采集所有股票（数据库中有记录）
```json
POST /api/tasks/crawl/stock
{}
```

### 场景 4: 查看最近的采集任务
```bash
GET /api/tasks?page=1&page_size=10
```

---

## 🎯 下一步

完成数据采集后，可以进入：
- **第六步**: 任务管理系统（定时自动采集）
- **第七步**: 查询和导出接口（数据查询和下载）

---

**最后更新**: 2026-05-22  
**版本**: v1.0
