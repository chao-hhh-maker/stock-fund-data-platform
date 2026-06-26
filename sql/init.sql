-- 股票基金数据获取和管理平台 - MySQL 初始化脚本
-- 适用于 MySQL 8.0+。SQLite 模式下由 SQLAlchemy 自动建表，无需执行本脚本。
--
-- 使用方式：
--   CREATE DATABASE stock_fund_platform DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
--   USE stock_fund_platform;
--   SOURCE sql/init.sql;

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS tenants (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(64)  NOT NULL UNIQUE,
    code        VARCHAR(32)  NOT NULL UNIQUE,
    description VARCHAR(128) NOT NULL DEFAULT '',
    is_active   TINYINT(1)   NOT NULL DEFAULT 1,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_tenants_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租户表';

CREATE TABLE IF NOT EXISTS roles (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    name               VARCHAR(32)  NOT NULL UNIQUE COMMENT '角色名：admin / viewer / analyst',
    description        VARCHAR(128) NOT NULL DEFAULT '',
    data_scope         VARCHAR(16)  NOT NULL DEFAULT 'all' COMMENT 'all / stock / fund',
    max_history_days   INT          NOT NULL DEFAULT 0 COMMENT '0=不限',
    can_export         TINYINT(1)   NOT NULL DEFAULT 1,
    can_view_sensitive TINYINT(1)   NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(64)  NOT NULL UNIQUE,
    hashed_password VARCHAR(256) NOT NULL,
    full_name       VARCHAR(64)  NOT NULL DEFAULT '',
    is_active       TINYINT(1)   NOT NULL DEFAULT 1,
    role_id         INT          NOT NULL,
    tenant_id       INT          NULL,
    department      VARCHAR(64)  NOT NULL DEFAULT '',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles(id),
    CONSTRAINT fk_users_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    INDEX ix_users_username (username),
    INDEX ix_users_tenant_id (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

CREATE TABLE IF NOT EXISTS instruments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    code        VARCHAR(16) NOT NULL UNIQUE COMMENT '标准化代码，如 600519.SH',
    name        VARCHAR(64) NOT NULL,
    asset_type  VARCHAR(16) NOT NULL COMMENT 'stock / fund',
    market      VARCHAR(8)  NOT NULL DEFAULT '',
    category    VARCHAR(32) NOT NULL DEFAULT '' COMMENT '行业或基金类型',
    tenant_id   INT         NULL COMMENT '为空表示公共标的',
    department  VARCHAR(64) NOT NULL DEFAULT '' COMMENT '为空表示部门公共',
    is_active   TINYINT(1)  NOT NULL DEFAULT 1,
    created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_instruments_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    INDEX ix_instruments_code (code),
    INDEX ix_instruments_asset_type (asset_type),
    INDEX ix_instruments_tenant_id (tenant_id),
    INDEX ix_instruments_department (department)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='证券标的主数据';

CREATE TABLE IF NOT EXISTS stock_daily (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    code       VARCHAR(16) NOT NULL,
    trade_date DATE        NOT NULL,
    open       DOUBLE,
    high       DOUBLE,
    low        DOUBLE,
    close      DOUBLE,
    volume     DOUBLE NOT NULL DEFAULT 0,
    amount     DOUBLE NOT NULL DEFAULT 0,
    pct_change DOUBLE NOT NULL DEFAULT 0 COMMENT '涨跌幅(%)',
    source     VARCHAR(32) NOT NULL DEFAULT '',
    created_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_stock_daily_code_date (code, trade_date),
    INDEX ix_stock_daily_code (code),
    INDEX ix_stock_daily_code_date (code, trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票日线行情';

CREATE TABLE IF NOT EXISTS fund_nav (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    code         VARCHAR(16) NOT NULL,
    nav_date     DATE        NOT NULL,
    unit_nav     DOUBLE,
    accum_nav    DOUBLE,
    adj_nav      DOUBLE NOT NULL DEFAULT 0 COMMENT '复权净值',
    daily_return DOUBLE NOT NULL DEFAULT 0 COMMENT '日增长率(%)',
    source       VARCHAR(32) NOT NULL DEFAULT '',
    created_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_fund_nav_code_date (code, nav_date),
    INDEX ix_fund_nav_code (code),
    INDEX ix_fund_nav_code_date (code, nav_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='基金净值';

CREATE TABLE IF NOT EXISTS crawl_jobs (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(64) NOT NULL,
    job_type     VARCHAR(32) NOT NULL COMMENT 'stock_daily / fund_nav / announcement',
    target_codes TEXT        COMMENT '逗号分隔的证券代码',
    mode         VARCHAR(16) NOT NULL DEFAULT 'full' COMMENT 'full / incremental',
    frequency    VARCHAR(16) NOT NULL DEFAULT 'daily' COMMENT 'realtime/minute/daily/weekly/quarterly/manual',
    cron         VARCHAR(64) NOT NULL DEFAULT '' COMMENT 'cron 表达式，空表示按频率或仅手动',
    enabled      TINYINT(1)  NOT NULL DEFAULT 1,
    created_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采集任务定义';

CREATE TABLE IF NOT EXISTS crawl_runs (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    job_id        INT NOT NULL,
    `trigger`     VARCHAR(16) NOT NULL DEFAULT 'manual' COMMENT 'manual / scheduled',
    status        VARCHAR(16) NOT NULL DEFAULT 'running' COMMENT 'running/success/partial/failed',
    started_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at   DATETIME    NULL,
    rows_affected INT         NOT NULL DEFAULT 0,
    retries       INT         NOT NULL DEFAULT 0,
    source        VARCHAR(32) NOT NULL DEFAULT '',
    message       TEXT,
    CONSTRAINT fk_crawl_runs_job FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    INDEX ix_crawl_runs_job_started (job_id, started_at),
    INDEX ix_crawl_runs_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采集运行记录';

CREATE TABLE IF NOT EXISTS export_records (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    dataset     VARCHAR(32) NOT NULL COMMENT 'stock_daily / fund_nav / instruments',
    file_format VARCHAR(16) NOT NULL DEFAULT 'csv',
    params      TEXT,
    file_name   VARCHAR(256) NOT NULL DEFAULT '',
    row_count   INT NOT NULL DEFAULT 0,
    status      VARCHAR(16) NOT NULL DEFAULT 'success',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_export_user FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX ix_export_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='导出记录';

CREATE TABLE IF NOT EXISTS audit_logs (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(64)  NOT NULL DEFAULT '',
    role       VARCHAR(32)  NOT NULL DEFAULT '',
    action     VARCHAR(32)  NOT NULL COMMENT 'login/crawl/export/sql/user 等',
    target     VARCHAR(128) NOT NULL DEFAULT '',
    detail     TEXT,
    ip         VARCHAR(64)  NOT NULL DEFAULT '',
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_audit_user_time (username, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作审计日志';

CREATE TABLE IF NOT EXISTS announcements (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    code         VARCHAR(16)  NOT NULL DEFAULT '',
    title        VARCHAR(256) NOT NULL,
    category     VARCHAR(32)  NOT NULL DEFAULT 'announcement',
    source       VARCHAR(32)  NOT NULL DEFAULT '',
    url          VARCHAR(512) NOT NULL DEFAULT '',
    summary      TEXT,
    sentiment    VARCHAR(16)  NOT NULL DEFAULT 'neutral',
    publish_date DATE         NOT NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_announcements_code (code),
    INDEX ix_announcement_code_time (code, publish_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公告/新闻/舆情';

CREATE TABLE IF NOT EXISTS data_quality_issues (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    issue_type    VARCHAR(32) NOT NULL,
    code          VARCHAR(16) NOT NULL DEFAULT '',
    dataset       VARCHAR(32) NOT NULL DEFAULT '',
    severity      VARCHAR(16) NOT NULL DEFAULT 'warning',
    message       TEXT,
    status        VARCHAR(16) NOT NULL DEFAULT 'open',
    resolved_by   VARCHAR(64) NOT NULL DEFAULT '',
    resolved_note TEXT,
    created_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at   DATETIME    NULL,
    INDEX ix_dq_status_time (status, created_at),
    INDEX ix_data_quality_issues_issue_type (issue_type),
    INDEX ix_data_quality_issues_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据质量问题';

CREATE TABLE IF NOT EXISTS alert_records (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    level           VARCHAR(16) NOT NULL DEFAULT 'warning',
    alert_type      VARCHAR(32) NOT NULL DEFAULT '',
    target          VARCHAR(128) NOT NULL DEFAULT '',
    message         TEXT,
    fingerprint     VARCHAR(64) NOT NULL DEFAULT '',
    status          VARCHAR(16) NOT NULL DEFAULT 'open',
    dispatch_status VARCHAR(16) NOT NULL DEFAULT 'pending',
    resolved_by     VARCHAR(64) NOT NULL DEFAULT '',
    resolved_note   TEXT,
    created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at     DATETIME    NULL,
    INDEX ix_alert_time (created_at),
    INDEX ix_alert_fingerprint_status (fingerprint, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警历史';

INSERT INTO tenants (code, name, description) VALUES
    ('HQ', '总部', '系统默认机构'),
    ('RESEARCH', '研究部', '演示部门级隔离')
ON DUPLICATE KEY UPDATE name = VALUES(name), description = VALUES(description);

INSERT INTO roles (name, description, data_scope, max_history_days, can_export, can_view_sensitive) VALUES
    ('admin', '管理员：可采集、导出、管理任务与用户', 'all', 0, 1, 1),
    ('viewer', '普通用户：可查询、可导出，敏感字段脱敏', 'all', 0, 1, 0),
    ('analyst', '研究员：仅股票数据、近 365 天、不可导出', 'stock', 365, 0, 0)
ON DUPLICATE KEY UPDATE
    description = VALUES(description),
    data_scope = VALUES(data_scope),
    max_history_days = VALUES(max_history_days),
    can_export = VALUES(can_export),
    can_view_sensitive = VALUES(can_view_sensitive);

