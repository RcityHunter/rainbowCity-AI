import logging
from fastapi import FastAPI, Request, Response, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from .db import init_db_connection, close_db

# 设置日志级别
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("app.py 模块加载中 - 这应该在启动时显示")

# 加载环境变量
load_dotenv()

# 创建 FastAPI 应用
app = FastAPI(
    title="彩虹城 AI API",
    description="彩虹城 AI 共生社区后端 API",
    version="1.0.0"
)

# 使用FastAPI的生命周期事件来初始化和关闭数据库连接
@app.on_event("startup")
async def startup_db_client():
    await init_db_connection()
    print("Database connection initialized on startup")

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_db()
    print("Database connection closed on shutdown")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境中应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由
from .routes.chat_routes import router as chat_router
from .routes.ai_routes import router as ai_router
from .routes.relationship_routes import router as relationship_router
from .routes.auth_routes import router as auth_router
from .routes.vip_routes import router as vip_router
from .routes.agent_routes import router as agent_router
from .routes.image_routes import router as image_router
from .routes.file_routes import router as file_router
from .routes.conversation_routes import router as conversation_router
from .routes.chat_history_routes import router as chat_history_router
from .routes.chat_sessions_routes import router as chat_sessions_router

# 所有路由模块已经迁移到 FastAPI
# 所有路由文件已经重命名，移除了 _fastapi 后缀

# 创建一个带有前缀 /api 的主路由器
api_router = APIRouter(prefix="/api")

# 将所有路由器包含在主路由器中
api_router.include_router(chat_router)
api_router.include_router(ai_router)
api_router.include_router(relationship_router)
api_router.include_router(auth_router)
api_router.include_router(vip_router)
api_router.include_router(agent_router)
api_router.include_router(image_router)
api_router.include_router(file_router)
api_router.include_router(conversation_router)
api_router.include_router(chat_history_router)
api_router.include_router(chat_sessions_router)

# 将主路由器注册到应用
app.include_router(api_router)
# app.include_router(file_router)

@app.get("/")
async def root():
    """健康检查端点"""
    logger.info("根路由被访问 - 健康检查")
    return {"status": "ok", "message": "彩虹城 AI API 服务正常运行"}

@app.get("/api/test")
async def test_api():
    """测试API端点"""
    logger.info("测试API端点被访问")
    return {"status": "ok", "message": "API测试端点正常工作"}

# 打印所有注册的路由
@app.on_event("startup")
async def print_routes():
    logger.info("打印所有注册的路由:")
    for route in app.routes:
        logger.info(f"路由: {route.path} [{', '.join(route.methods)}]")
    
    # 打印api_router中的路由
    logger.info("打印api_router中的路由:")
    for route in api_router.routes:
        logger.info(f"API路由: {route.path} [{', '.join(route.methods)}]")
        
    # 打印agent_router中的路由
    logger.info("打印agent_router中的路由:")
    for route in agent_router.routes:
        logger.info(f"Agent路由: {route.path} [{', '.join(route.methods)}]")


# 注意：所有路由器已经在上面通过api_router注册到应用中
# 不需要重复注册
# app.include_router(ai_router)
# app.include_router(relationship_router)
# app.include_router(chat_router)
# app.include_router(conversation_router)
# app.include_router(chat_history_router)
# app.include_router(auth_router)
# app.include_router(vip_router)
# app.include_router(image_router)
# app.include_router(file_router)
