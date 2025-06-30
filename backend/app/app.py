import logging
import time
import asyncio
from fastapi import FastAPI, Request, Response, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os
import gc
from dotenv import load_dotenv
from .db import init_db_connection, close_db

# 设置向量嵌入模型环境变量（如果未设置）
if not os.getenv('EMBEDDING_MODEL'):
    os.environ['EMBEDDING_MODEL'] = 'all-MiniLM-L6-v2'  # 默认使用轻量级模型

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

# 添加全局异常处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    error_details = []
    for error in exc.errors():
        error_details.append({
            'loc': error.get('loc', []),
            'msg': error.get('msg', ''),
            'type': error.get('type', '')
        })
    logging.error(f"Validation error: {error_details}")
    return JSONResponse(
        status_code=422,
        content={"detail": error_details}
    )

# 使用FastAPI的生命周期事件来初始化和关闭数据库连接
@app.on_event("startup")
async def startup_db_client():
    await init_db_connection()
    print("Database connection initialized on startup")
    
    # 初始化向量存储
    from .services.initialize_vector_storage import initialize_vector_storage
    try:
        print("开始初始化向量存储...")
        await initialize_vector_storage()
        print("向量存储初始化完成")
    except Exception as e:
        print(f"向量存储初始化失败: {str(e)}")
        logging.error(f"向量存储初始化失败: {str(e)}")

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_db()
    print("Database connection closed on shutdown")

# 自定义中间件类来处理资源清理和请求超时
class ResourceCleanupMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = f"{int(time.time())}-{id(request)}"
        logging.info(f"[资源中间件-{request_id}] 请求开始处理: {request.url.path}")
        start_time = time.time()
        
        try:
            # 调用下一个中间件或路由处理函数
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            logging.info(f"[资源中间件-{request_id}] 请求完成: {request.url.path}, 耗时: {process_time:.2f}秒")
            
            # 强制进行垃圾回收
            gc.collect()
            logging.info(f"[资源中间件-{request_id}] 强制垃圾回收完成")
            
            return response
        except Exception as e:
            logging.error(f"[资源中间件-{request_id}] 请求处理异常: {str(e)}")
            # 强制进行垃圾回收
            gc.collect()
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error", "error": str(e)}
            )

# 添加资源清理中间件
app.add_middleware(ResourceCleanupMiddleware)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "https://accounts.google.com",  # OAuth提供商仍然使用HTTPS
        "https://github.com",          # OAuth提供商仍然使用HTTPS
        "https://rainbow-city-ai.vercel.app",  # 实际部署的Vercel域名（HTTPS协议）
        "http://rainbow-city-ai.vercel.app",   # 实际部署的Vercel域名（HTTP协议）
        "http://rainbow-city-frontend.vercel.app",  # 原预计的Vercel域名（HTTP协议）
        "https://rainbow-city-frontend.vercel.app", # 原预计的Vercel域名（HTTPS协议）
        "http://rainbowcity.ai",       # 如果你有自定义域名（HTTP协议）
        "https://rainbowcity.ai",      # 如果你有自定义域名（HTTPS协议）
        "http://*.vercel.app",         # 允许所有Vercel子域名（HTTP协议）
        "https://*.vercel.app",        # 允许所有Vercel子域名（HTTPS协议）
        "http://47.236.10.92",         # 后端服务器IP
        "http://47.236.10.92:5001"     # 后端服务器IP带端口
    ],
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
from .routes.oauth_routes import router as oauth_router
from .routes.search_routes import router as search_router

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
api_router.include_router(oauth_router)
api_router.include_router(search_router)

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
