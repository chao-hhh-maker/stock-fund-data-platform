from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.tasks import router as tasks_router
from app.tasks.scheduler.scheduler_manager import scheduler_manager

logger = logging.getLogger(__name__)

# 生命周期事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("应用启动中...")
    
    # 加载定时任务
    try:
        scheduler_manager.load_jobs_from_database()
        scheduler_manager.start()
        logger.info("定时任务调度器已启动")
    except Exception as e:
        logger.error(f"启动定时任务调度器失败: {e}")
    
    yield
    
    # 关闭时
    logger.info("应用关闭中...")
    try:
        scheduler_manager.shutdown(wait=True)
        logger.info("定时任务调度器已关闭")
    except Exception as e:
        logger.error(f"关闭定时任务调度器失败: {e}")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="股票基金数据获取和管理平台后端服务",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS(跨域资源共享)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(tasks_router)


@app.get("/api/health")
def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "服务运行正常"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
