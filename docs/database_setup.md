# 数据库设置指南

## 前置要求

- MySQL 8.0 或更高版本
- MySQL服务正在运行

## 快速开始

### 方法一: 使用命令行工具(推荐)

1. **启动MySQL服务**

   Windows:
   ```powershell
   # 以管理员身份运行PowerShell
   net start mysql80
   # 或者
   net start mysql
   ```

   Linux/Mac:
   ```bash
   sudo systemctl start mysql
   # 或者
   sudo service mysql start
   ```

2. **创建数据库**

   ```bash
   mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS stock_fund_platform DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;"
   ```

3. **执行初始化脚本**

   ```bash
   mysql -u root -p stock_fund_platform < sql/init.sql
   ```

4. **验证数据库**

   ```bash
   python scripts/verify_db.py
   ```

### 方法二: 使用MySQL客户端工具

1. 打开MySQL Workbench、Navicat或其他MySQL客户端
2. 连接到MySQL服务器
3. 执行以下SQL创建数据库:
   ```sql
   CREATE DATABASE IF NOT EXISTS stock_fund_platform DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
   USE stock_fund_platform;
   ```
4. 打开并执行 `sql/init.sql` 文件中的所有SQL语句

### 方法三: 逐条执行SQL

如果上述方法都不可用,可以手动在MySQL客户端中逐条执行 `sql/init.sql` 中的SQL语句。

## 默认账户

系统会自动创建以下默认账户:

**管理员账户**:
- 用户名: `admin`
- 密码: `admin123`
- 角色: 管理员(所有权限)

⚠️ **重要**: 首次登录后请立即修改默认密码!

## 数据库配置

编辑 `backend/.env` 文件配置数据库连接:

```env
DATABASE_URL=mysql+pymysql://root:@localhost:3306/stock_fund_platform
```

根据你的MySQL配置修改:
- `root`: MySQL用户名
- ``: MySQL密码(如果有的话)
- `localhost`: MySQL服务器地址
- `3306`: MySQL端口
- `stock_fund_platform`: 数据库名称

## 常见问题

### Q1: 无法连接MySQL服务器

**解决方案**:
1. 检查MySQL服务是否启动
2. 确认MySQL端口是否正确(默认3306)
3. 检查防火墙设置

### Q2: 访问被拒绝

**解决方案**:
1. 确认MySQL用户名和密码正确
2. 检查用户是否有创建数据库的权限
3. 尝试使用 `mysql -u root -p` 直接登录测试

### Q3: 字符集错误

**解决方案**:
确保数据库使用 `utf8mb4` 字符集:
```sql
ALTER DATABASE stock_fund_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Q4: 表已存在

如果需要重新初始化,先删除旧表:
```sql
USE stock_fund_platform;
DROP TABLE IF EXISTS export_records, crawl_runs, crawl_jobs, fund_nav, stock_daily, instruments, users, roles;
```

然后重新执行 `sql/init.sql`

## 数据库维护

### 备份数据库

```bash
mysqldump -u root -p stock_fund_platform > backup_$(date +%Y%m%d).sql
```

### 恢复数据库

```bash
mysql -u root -p stock_fund_platform < backup_20260522.sql
```

### 查看表大小

```sql
SELECT
    table_name AS '表名',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS '大小(MB)'
FROM information_schema.TABLES
WHERE table_schema = 'stock_fund_platform'
ORDER BY (data_length + index_length) DESC;
```

### 清理过期数据

定期清理旧的执行记录:
```sql
-- 删除30天前的采集执行记录
DELETE FROM crawl_runs WHERE start_time < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- 删除90天前的导出记录
DELETE FROM export_records WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
```

## 下一步

数据库设置完成后,继续执行开发计划的第四步:实现后端认证和基础接口。
