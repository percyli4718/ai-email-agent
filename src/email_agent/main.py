"""
AI Email Agent 主应用模块

模块作用:
    本模块是 FastAPI 应用的主入口，负责应用的启动、生命周期管理、
    中间件配置和路由注册。定义了应用的整体结构和运行时行为。

使用场景:
    - 通过 uvicorn 启动应用时作为入口点
    - 管理应用的生命周期 (启动/关闭时的资源初始化/清理)
    - 配置 CORS 中间件，允许前端跨域访问
    - 注册 API 路由

在项目中的位置:
    位于 src/email_agent/main.py，是应用的最高层级，
    依赖配置模块、日志模块、数据库模块和 API 路由模块。
"""
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from email_agent.config import settings, get_settings
from email_agent.logging_config import setup_logging, get_logger
from email_agent.storage.database import get_database
from email_agent.api.routes import router

# 获取当前模块的日志记录器
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器

    功能描述:
        管理 FastAPI 应用的启动和关闭流程。
        启动时：初始化日志系统，记录启动日志，初始化数据库连接
        关闭时：关闭数据库连接，记录关闭日志

    参数:
        app: FastAPI 应用实例

    返回值:
        无 (异步上下文管理器)

    异常:
        无

    使用场景:
        FastAPI 在应用启动时自动调用此函数，
        yield 之前的代码在启动时执行，yield 之后的代码在关闭时执行
    """
    # 启动阶段：初始化日志系统，记录应用启动事件
    setup_logging(settings.log_level)
    logger.info("application_starting", env=settings.env)

    # 初始化数据库连接
    db = get_database(settings)

    # 等待应用运行...
    yield

    # 关闭阶段：关闭数据库连接，记录应用关闭事件
    await db.close()
    logger.info("application_shutdown")


# 创建 FastAPI 应用实例
# 配置应用元数据，用于 Swagger UI 文档展示
app = FastAPI(
    title="AI Email Agent",
    description="AI-powered email processing for pharmaceutical distribution",
    version="0.1.0",
    lifespan=lifespan  # 注册生命周期管理器
)

# 配置 CORS 中间件
# 允许前端应用跨域访问 API
app.add_middleware(
    CORSMiddleware,
    # 允许的源地址 (前端开发服务器)
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    # 允许携带认证信息 (cookies, authorization headers)
    allow_credentials=True,
    # 允许所有 HTTP 方法
    allow_methods=["*"],
    # 允许所有 HTTP 头
    allow_headers=["*"],
)

# 注册 API 路由
# 所有 /api/* 路径的路由都来自 router
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """
    根路径端点

    功能描述:
        返回应用的基本信息，用于健康检查和状态确认。

    参数:
        无

    返回值:
        dict: 包含应用名称、版本和运行状态的字典

    异常:
        无

    使用场景:
        - 负载均衡器健康检查
        - 前端应用确认后端服务可用
    """
    return {
        "name": "AI Email Agent",
        "version": "0.1.0",
        "status": "running"
    }


if __name__ == "__main__":
    """
    主程序入口

    功能描述:
        当直接运行此文件时，使用 uvicorn 启动应用服务器。
        开发环境下启用热重载功能。

    使用场景:
        开发时通过 python -m email_agent.main 或 python main.py 启动服务
    """
    import uvicorn
    uvicorn.run(
        # 应用导入路径
        "email_agent.main:app",
        # 监听所有网络接口
        host="0.0.0.0",
        # 服务端口
        port=8000,
        # 开发环境下启用热重载，代码变更时自动重启
        reload=settings.env == "development"
    )
