-- 股票基金数据平台数据库初始化脚本
-- 创建时间: 2026-05-22

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(100) COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    role_id INT COMMENT '角色ID',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否激活',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 角色表
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '角色ID',
    role_name VARCHAR(50) NOT NULL UNIQUE COMMENT '角色名称',
    description VARCHAR(255) COMMENT '角色描述',
    permissions TEXT COMMENT '权限列表(JSON格式)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_role_name (role_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- 金融工具表(股票/基金基本信息)
CREATE TABLE IF NOT EXISTS instruments (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '工具ID',
    code VARCHAR(20) NOT NULL COMMENT '证券代码',
    name VARCHAR(100) NOT NULL COMMENT '证券名称',
    type ENUM('stock', 'fund') NOT NULL COMMENT '类型: stock-股票, fund-基金',
    market VARCHAR(20) COMMENT '市场: SH-上海, SZ-深圳, BJ-北京',
    industry VARCHAR(50) COMMENT '行业分类',
    list_date DATE COMMENT '上市日期',
    status ENUM('active', 'delisted') DEFAULT 'active' COMMENT '状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_code_type (code, type),
    INDEX idx_code (code),
    INDEX idx_type (type),
    INDEX idx_market (market),
    INDEX idx_industry (industry)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='金融工具表';

-- 股票日线数据表
CREATE TABLE IF NOT EXISTS stock_daily (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    code VARCHAR(20) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open DECIMAL(10, 2) COMMENT '开盘价',
    high DECIMAL(10, 2) COMMENT '最高价',
    low DECIMAL(10, 2) COMMENT '最低价',
    close DECIMAL(10, 2) COMMENT '收盘价',
    volume BIGINT COMMENT '成交量(股)',
    amount DECIMAL(15, 2) COMMENT '成交额(元)',
    change_pct DECIMAL(6, 2) COMMENT '涨跌幅(%)',
    turnover_rate DECIMAL(6, 2) COMMENT '换手率(%)',
    data_source VARCHAR(50) COMMENT '数据来源',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_code_date (code, trade_date),
    INDEX idx_code (code),
    INDEX idx_trade_date (trade_date),
    INDEX idx_code_date (code, trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票日线数据表';

-- 基金净值数据表
CREATE TABLE IF NOT EXISTS fund_nav (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    code VARCHAR(20) NOT NULL COMMENT '基金代码',
    nav_date DATE NOT NULL COMMENT '净值日期',
    unit_nav DECIMAL(10, 4) COMMENT '单位净值',
    accumulated_nav DECIMAL(10, 4) COMMENT '累计净值',
    daily_growth DECIMAL(6, 4) COMMENT '日增长率(%)',
    data_source VARCHAR(50) COMMENT '数据来源',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_code_date (code, nav_date),
    INDEX idx_code (code),
    INDEX idx_nav_date (nav_date),
    INDEX idx_code_date (code, nav_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='基金净值数据表';

-- 采集任务配置表
CREATE TABLE IF NOT EXISTS crawl_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '任务ID',
    job_name VARCHAR(100) NOT NULL COMMENT '任务名称',
    job_type ENUM('stock_daily', 'fund_nav', 'instrument_info') NOT NULL COMMENT '任务类型',
    target_codes TEXT COMMENT '目标代码列表(JSON格式,NULL表示全部)',
    schedule_cron VARCHAR(100) COMMENT '定时表达式(CRON)',
    is_enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    retry_times INT DEFAULT 3 COMMENT '重试次数',
    timeout_seconds INT DEFAULT 300 COMMENT '超时时间(秒)',
    extra_config TEXT COMMENT '额外配置(JSON格式)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_job_type (job_type),
    INDEX idx_is_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采集任务配置表';

-- 采集任务执行记录表
CREATE TABLE IF NOT EXISTS crawl_runs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '执行记录ID',
    job_id INT NOT NULL COMMENT '任务ID',
    start_time DATETIME NOT NULL COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    status ENUM('running', 'success', 'failed', 'timeout') NOT NULL COMMENT '执行状态',
    records_count INT DEFAULT 0 COMMENT '采集记录数',
    error_message TEXT COMMENT '错误信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_job_id (job_id),
    INDEX idx_start_time (start_time),
    INDEX idx_status (status),
    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采集任务执行记录表';

-- 数据导出记录表
CREATE TABLE IF NOT EXISTS export_records (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '导出记录ID',
    user_id INT NOT NULL COMMENT '用户ID',
    export_type ENUM('stock_daily', 'fund_nav', 'instrument') NOT NULL COMMENT '导出类型',
    query_params TEXT COMMENT '查询参数(JSON格式)',
    file_path VARCHAR(500) COMMENT '文件路径',
    file_format ENUM('csv', 'excel', 'parquet') DEFAULT 'csv' COMMENT '文件格式',
    record_count INT DEFAULT 0 COMMENT '记录数量',
    file_size BIGINT COMMENT '文件大小(字节)',
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending' COMMENT '导出状态',
    error_message TEXT COMMENT '错误信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    completed_at DATETIME COMMENT '完成时间',
    INDEX idx_user_id (user_id),
    INDEX idx_export_type (export_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据导出记录表';

-- 插入默认角色
INSERT INTO roles (role_name, description, permissions) VALUES
('admin', '管理员', '{"query": true, "export": true, "manage": true, "admin": true}'),
('user', '普通用户', '{"query": true, "export": true, "manage": false, "admin": false}');

-- 插入默认管理员用户 (密码: admin123, 实际使用时应使用bcrypt加密)
INSERT INTO users (username, email, password_hash, role_id) VALUES
('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILp92S.0i', 1);
