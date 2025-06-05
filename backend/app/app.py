from fastapi import FastAPI, Request, Response, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建 FastAPI 应用
app = FastAPI(
    title="彩虹城 AI API",
    description="彩虹城 AI 共生社区后端 API",
    version="1.0.0"
)

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
    return {"status": "ok", "message": "彩虹城 AI API 服务正常运行"}

# 以下是路由导入的占位符，将在迁移过程中逐步实现
# from .routes.ai_routes import router as ai_router
# from .routes.relationship_routes import router as relationship_router
# from .routes.chat_routes import router as chat_router
# from .routes.auth_routes import router as auth_router
# from .routes.vip_routes import router as vip_router
# from .routes.agent_routes import router as agent_router
# from .routes.image_routes import router as image_router
# from .routes.file_routes import router as file_router
# from .routes.conversation_routes import router as conversation_router
# from .routes.chat_history_routes import router as chat_history_router

# 注册路由
# app.include_router(ai_router)
# app.include_router(relationship_router)
# app.include_router(chat_router)
# app.include_router(conversation_router)
# app.include_router(chat_history_router)
# app.include_router(auth_router)
# app.include_router(vip_router)
# app.include_router(agent_router)
# app.include_router(image_router)
# app.include_router(file_router)
