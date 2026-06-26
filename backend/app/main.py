"""FastAPI 应用入口。

启动时：建表 → 初始化种子数据（用户 / 标的 / 样例行情）→ 启动调度器。
关闭时：安全停止调度器。
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, data, exports, monitor, query, tasks, ws
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.core.metrics_middleware import APIMetricsMiddleware
from app.seed import run_all
from app.tasks import scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    init_db()
    db = SessionLocal()
    try:
        run_all(db, with_market_data=True)
    finally:
        db.close()
    if settings.SCHEDULER_ENABLED:
        scheduler.start()
    # 后台自动采集真实数据：首屏先用样例秒开，后台拉真实数据，几秒后刷新即真实。
    if settings.AUTO_CRAWL_ON_STARTUP:
        _kickoff_auto_crawl()
    logger.info("应用启动完成：%s", settings.APP_NAME)
    yield
    # 关闭
    if settings.SCHEDULER_ENABLED:
        scheduler.shutdown()


def _kickoff_auto_crawl() -> None:
    """在后台线程对全部已登记标的拉真实数据（失败自动回退样例，不影响启动）。"""
    import threading

    def _run() -> None:
        from app.models import Instrument
        from app.services import crawler

        db = SessionLocal()
        try:
            stocks = [r[0] for r in db.query(Instrument.code).filter(Instrument.asset_type == "stock").all()]
            funds = [r[0] for r in db.query(Instrument.code).filter(Instrument.asset_type == "fund").all()]
            if stocks:
                crawler.crawl_stock_daily(db, stocks, incremental=False)
            if funds:
                crawler.crawl_fund_nav(db, funds, incremental=False)
            logger.info("启动后台采集完成：股票 %d / 基金 %d", len(stocks), len(funds))
        except Exception as exc:  # noqa: BLE001 - 后台采集失败不影响服务
            logger.warning("启动后台采集失败（已保留样例数据）：%s", exc)
        finally:
            db.close()

    threading.Thread(target=_run, name="startup-auto-crawl", daemon=True).start()


app = FastAPI(
    title=settings.APP_NAME,
    description="股票基金数据获取和管理平台 - 后端 API（课程设计题目二）",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 性能监控中间件（模块5）
app.add_middleware(APIMetricsMiddleware)

# 路由注册（统一前缀 /api）
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(monitor.router, prefix=settings.API_PREFIX)
app.include_router(data.router, prefix=settings.API_PREFIX)
app.include_router(tasks.router, prefix=settings.API_PREFIX)
app.include_router(exports.router, prefix=settings.API_PREFIX)
app.include_router(query.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)
app.include_router(ws.router, prefix=settings.API_PREFIX)


@app.get("/", tags=["根"], summary="服务根路径")
def root() -> dict:
    return {
        "app": settings.APP_NAME,
        "message": "后端 API 运行正常。前端页面请访问 http://localhost:5173",
        "api_docs": "/docs",
        "health": f"{settings.API_PREFIX}/health",
        "frontend": "http://localhost:5173",
    }
