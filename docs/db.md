# 数据库设计文档

## 数据库概述

本项目使用 MySQL 8.0 作为关系型数据库,采用 InnoDB 引擎,字符集为 utf8mb4。

数据库名称: `stock_fund_platform`

## 表结构说明

### 1. users (用户表)

存储系统用户信息,支持多角色权限管理。

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| id | INT | 用户ID,主键自增 | PRIMARY KEY |
| username | VARCHAR(50) | 用户名,唯一 | UNIQUE INDEX |
| email | VARCHAR(100) | 邮箱地址 | INDEX |
| password_hash | VARCHAR(255) | 密码哈希值(bcrypt) | - |
| role_id | INT | 角色ID,外键关联roles表 | - |
| is_active | TINYINT(1) | 是否激活,默认1 | - |
| created_at | DATETIME | 创建时间 | - |
| updated_at | DATETIME | 更新时间 | - |

**用途**: 管理系统用户账户,支持登录认证和权限控制。

---

### 2. roles (角色表)

定义系统角色及其权限配置。

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| id | INT | 角色ID,主键自增 | PRIMARY KEY |
| role_name | VARCHAR(50) | 角色名称,唯一 | UNIQUE INDEX |
| description | VARCHAR(255) | 角色描述 | - |
| permissions | TEXT | 权限列表(JSON格式) | - |
| created_at | DATETIME | 创建时间 | - |
| updated_at | DATETIME | 更新时间 | - |

**预设角色**:
- `admin`: 管理员,拥有所有权限
- `user`: 普通用户,仅查询和导出权限

**用途**: 实现基于角色的访问控制(RBAC)。

---

### 3. instruments (金融工具表)

存储股票和基金的基本信息。

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| id | INT | 工具ID,主键自增 | PRIMARY KEY |
| code | VARCHAR(20) | 证券代码 | UNIQUE(code, type), INDEX |
| name | VARCHAR(100) | 证券名称 | - |
| type | ENUM | 类型: stock/fund | INDEX |
| market | VARCHAR(20) | 市场: SH/SZ/BJ | INDEX |
| industry | VARCHAR(50) | 行业分类 | INDEX |
| list_date | DATE | 上市日期 | - |
| status | ENUM | 状态: active/delisted | - |
| created_at | DATETIME | 创建时间 | - |
| updated_at | DATETIME | 更新时间 | - |

**用途**: 统一管理所有金融工具的基础信息,支持代码标准化和行业分类。

---

### 4. stock_daily (股票日线数据表)

存储股票每日交易数据。

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| id | BIGINT | 记录ID,主键自增 | PRIMARY KEY |
| code | VARCHAR(20) | 股票代码 | INDEX, UNIQUE(code, trade_date) |
| trade_date | DATE | 交易日期 | INDEX, UNIQUE(code, trade_date) |
| open | DECIMAL(10,2) | 开盘价 | - |
| high | DECIMAL(10,2) | 最高价 | - |
| low | DECIMAL(10,2) | 最低价 | - |
| close | DECIMAL(10,2) | 收盘价 | - |
| volume | BIGINT | 成交量(股) | - |
| amount | DECIMAL(15,2) | 成交额(元) | - |
| change_pct | DECIMAL(6,2) | 涨跌幅(%) | - |
| turnover_rate | DECIMAL(6,2) | 换手率(%) | - |
| data_source | VARCHAR(50) | 数据来源 | - |
| created_at | DATETIME | 创建时间 | - |
| updated_at | DATETIME | 更新时间 | - |

**索引说明**:
- `uk_code_date`: 唯一索引,防止同一股票同一日期重复数据
- `idx_code`: 加速按股票代码查询
- `idx_trade_date`: 加速按日期范围查询
- `idx_code_date`: 复合索引,优化联合查询

**用途**: 存储股票历史行情数据,支持K线图展示和技术分析。

---

### 5. fund_nav (基金净值数据表)

存储基金每日净值数据。

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| id | BIGINT | 记录ID,主键自增 | PRIMARY KEY |
| code | VARCHAR(20) | 基金代码 | INDEX, UNIQUE(code, nav_date) |
| nav_date | DATE | 净值日期 | INDEX, UNIQUE(code, nav_date) |
| unit_nav | DECIMAL(10,4) | 单位净值 | - |
| accumulated_nav | DECIMAL(10,4) | 累计净值 | - |
| daily_growth | DECIMAL(6,4) | 日增长率(%) | - |
| data_source | VARCHAR(50) | 数据来源 | - |
| created_at | DATETIME | 创建时间 | - |
| updated_at | DATETIME | 更新时间 | - |

**索引说明**:
- `uk_code_date`: 唯一索引,防止同一基金同一日期重复数据
- `idx_code`: 加速按基金代码查询
- `idx_nav_date`: 加速按日期范围查询
- `idx_code_date`: 复合索引,优化联合查询

**用途**: 存储基金净值历史数据,支持净值走势分析和收益计算。

---

### 6. crawl_jobs (采集任务配置表)

配置数据采集任务的参数和调度规则。

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| id | INT | 任务ID,主键自增 | PRIMARY KEY |
| job_name | VARCHAR(100) | 任务名称 | - |
| job_type | ENUM | 任务类型: stock_daily/fund_nav/instrument_info | INDEX |
| target_codes | TEXT | 目标代码列表(JSON格式,NULL表示全部) | - |
| schedule_cron | VARCHAR(100) | 定时表达式(CRON) | - |
| is_enabled | TINYINT(1) | 是否启用,默认1 | INDEX |
| retry_times | INT | 重试次数,默认3 | - |
| timeout_seconds | INT | 超时时间(秒),默认300 | - |
| extra_config | TEXT | 额外配置(JSON格式) | - |
| created_at | DATETIME | 创建时间 | - |
| updated_at | DATETIME | 更新时间 | - |

**用途**: 管理数据采集任务,支持手动触发和定时自动执行。

---

### 7. crawl_runs (采集任务执行记录表)

记录每次采集任务的执行情况和结果。

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| id | BIGINT | 执行记录ID,主键自增 | PRIMARY KEY |
| job_id | INT | 任务ID,外键关联crawl_jobs | INDEX, FOREIGN KEY |
| start_time | DATETIME | 开始时间 | INDEX |
| end_time | DATETIME | 结束时间 | - |
| status | ENUM | 执行状态: running/success/failed/timeout | INDEX |
| records_count | INT | 采集记录数,默认0 | - |
| error_message | TEXT | 错误信息 | - |
| created_at | DATETIME | 创建时间 | - |

**外键约束**: `job_id` 关联 `crawl_jobs(id)`,删除任务时级联删除执行记录

**用途**: 追踪采集任务执行情况,便于故障排查和性能监控。

---

### 8. export_records (数据导出记录表)

记录用户的数据导出操作历史和结果。

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| id | BIGINT | 导出记录ID,主键自增 | PRIMARY KEY |
| user_id | INT | 用户ID,外键关联users | INDEX, FOREIGN KEY |
| export_type | ENUM | 导出类型: stock_daily/fund_nav/instrument | INDEX |
| query_params | TEXT | 查询参数(JSON格式) | - |
| file_path | VARCHAR(500) | 文件路径 | - |
| file_format | ENUM | 文件格式: csv/excel/parquet,默认csv | - |
| record_count | INT | 记录数量,默认0 | - |
| file_size | BIGINT | 文件大小(字节) | - |
| status | ENUM | 导出状态: pending/processing/completed/failed | INDEX |
| error_message | TEXT | 错误信息 | - |
| created_at | DATETIME | 创建时间 | INDEX |
| completed_at | DATETIME | 完成时间 | - |

**外键约束**: `user_id` 关联 `users(id)`,删除用户时级联删除导出记录

**用途**: 追踪数据导出历史,支持审计和文件管理。

---

## 索引设计说明

### 为什么创建这些索引?

1. **唯一索引 (UNIQUE)**
   - `users.username`: 保证用户名唯一性
   - `instruments(code, type)`: 保证同一类型的证券代码唯一
   - `stock_daily(code, trade_date)`: 防止重复采集同一股票同一天的数据
   - `fund_nav(code, nav_date)`: 防止重复采集同一基金同一天的数据

2. **普通索引 (INDEX)**
   - 外键字段: 加速关联查询
   - 查询频繁字段: code, date, status等
   - 复合索引: 优化多条件联合查询

3. **未创建索引的字段**
   - TEXT类型大字段: 不适合建索引
   - 低区分度字段: 如is_active只有两个值
   - 很少用于查询条件的字段

---

## 数据初始化

脚本会自动插入以下初始数据:

1. **默认角色**:
   - admin (管理员): 所有权限
   - user (普通用户): 查询和导出权限

2. **默认管理员账户**:
   - 用户名: admin
   - 密码: admin123 (首次登录后应立即修改)

---

## 数据库维护建议

1. **定期备份**: 建议每日全量备份,每小时增量备份
2. **数据清理**: 定期清理过期的crawl_runs和export_records记录
3. **性能监控**: 监控慢查询日志,优化查询语句
4. **空间管理**: 监控表空间使用情况,及时扩容

---

## 扩展考虑

未来可能需要增加的表:
- `user_permissions`: 细粒度权限控制表
- `data_quality_logs`: 数据质量检查日志表
- `system_configs`: 系统配置表
- `api_access_logs`: API访问日志表
