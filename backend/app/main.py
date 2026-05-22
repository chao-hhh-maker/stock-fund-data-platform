from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.auth import router as auth_router

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="股票基金数据获取和管理平台后端服务",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
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


@app.get("/api/health")
def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "服务运行正常"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
