"""应用配置。

通过 pydantic-settings 从环境变量 / .env 文件读取配置。
默认使用 SQLite，做到 clone 即跑；生产 / 答辩可切换到 MySQL。
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置项。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 基础信息
    APP_NAME: str = "股票基金数据获取和管理平台"
    APP_ENV: str = "dev"
    API_PREFIX: str = "/api"
    DEBUG: bool = True

    # 数据库：默认 SQLite，零配置启动。
    # MySQL 示例：mysql+pymysql://user:pass@127.0.0.1:3306/stock_fund_platform?charset=utf8mb4
    DATABASE_URL: str = "sqlite:///./stock_fund_platform.db"

    # 安全 / JWT
    SECRET_KEY: str = "change-me-in-production-please-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12  # 12 小时

    # 默认管理员（首次启动自动创建）
    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_PASSWORD: str = "admin123"
    FIRST_USER_USERNAME: str = "viewer"
    FIRST_USER_PASSWORD: str = "viewer123"

    # CORS：以逗号分隔的字符串存储，避免 pydantic-settings 对 List 字段强制 JSON 解析
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # 采集器：当外部数据源不可用时，回退到内置样例数据，保证演示稳定。
    USE_SAMPLE_DATA_FALLBACK: bool = True
    # 强制只用样例数据（测试 / 纯离线演示用，跳过 akshare 网络请求）
    CRAWL_FORCE_SAMPLE: bool = False
    CRAWL_REQUEST_TIMEOUT: int = 25
    # 智能重试：单标的抓取失败时的最大尝试次数与退避基准秒数
    CRAWL_MAX_RETRIES: int = 2
    CRAWL_RETRY_BASE_DELAY: float = 0.4
    # 采集回看天数：只采最近 N 个自然日的数据，避免拉取全部历史导致超时
    CRAWL_LOOKBACK_DAYS: int = 400

    # 查询限流：每用户每窗口最大请求数（令牌桶）
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 120
    # 缓存：查询结果缓存有效期（秒）
    CACHE_TTL_SECONDS: int = 30
    # 普通用户每日导出配额
    VIEWER_EXPORT_DAILY_QUOTA: int = 20
    # 普通用户每日查询次数配额（0 表示不限，仅令牌桶限流）
    VIEWER_QUERY_DAILY_QUOTA: int = 0

    # 导出文件目录
    EXPORT_DIR: str = "./data/exports"
    # 导出加密压缩：zip 密码（用于演示加密导出，可在 .env 覆盖）
    EXPORT_ZIP_PASSWORD: str = "stockfund-2026"

    # 受控 SQL 查询：单次最大返回行数（强制 LIMIT）
    SQL_QUERY_MAX_ROWS: int = 1000

    # WebSocket 实时推送间隔（秒），轻量等价"实时"
    WS_PUSH_INTERVAL: int = 3
    # 启动后台自动采集真实数据。默认关闭，避免离线演示时启动后刷外网错误日志；需要真实行情可在 .env 开启。
    AUTO_CRAWL_ON_STARTUP: bool = False
    # 实时行情：交易时段轮询新浪秒级快照；休市显示最新收盘
    REALTIME_ENABLED: bool = True

    # 告警分发 webhook（留空则只落库不外发；配置后 best-effort POST）
    ALERT_WEBHOOK_URL: str = ""
    # 异常监测阈值
    ANOMALY_PCT_CHANGE_THRESHOLD: float = 11.0   # 单日涨跌幅超过该值视为异常(%)
    ANOMALY_VOLUME_RATIO: float = 5.0            # 成交量超过近期均值倍数视为异常

    # 调度器开关（测试时可关闭）
    SCHEDULER_ENABLED: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _normalize_cors(cls, v: object) -> object:
        """允许以 list 或逗号分隔字符串配置，统一存为字符串。"""
        if isinstance(v, (list, tuple)):
            return ",".join(str(i) for i in v)
        return v

    @field_validator("DEBUG", mode="before")
    @classmethod
    def _normalize_debug(cls, v: object) -> object:
        """兼容常见部署环境把 DEBUG 写成 dev/release/prod 的情况。"""
        if isinstance(v, str):
            value = v.strip().lower()
            if value in {"release", "prod", "production", "false", "0", "off", "no"}:
                return False
            if value in {"dev", "debug", "development", "true", "1", "on", "yes"}:
                return True
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """解析为列表供 CORS 中间件使用。"""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """缓存配置单例。"""
    return Settings()


settings = get_settings()


