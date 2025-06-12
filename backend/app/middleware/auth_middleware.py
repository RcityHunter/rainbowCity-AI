import logging
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from app.utils.auth_utils import get_user_by_token
from starlette.middleware.base import BaseHTTPMiddleware

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    认证中间件，用于验证请求中的JWT令牌并获取当前用户
    """
    
    async def dispatch(self, request: Request, call_next):
        # 不需要认证的路径列表
        public_paths = [
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/refresh",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        
        # 如果是公开路径，直接放行
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
            
        # 检查认证头
        auth_header = request.headers.get("Authorization")
        
        # 开发环境下，如果没有认证头，使用默认用户ID
        if not auth_header:
            # 对于开发环境，我们可以设置一个默认用户
            import os
            if os.environ.get("APP_ENV") == "development":
                # 在开发环境中，如果没有提供令牌，使用默认用户ID
                request.state.user_id = "users:a21l8uegjvzds1108e2n"
                logger.info(f"Development mode: Using default user ID: {request.state.user_id}")
                return await call_next(request)
            else:
                # 在生产环境中，如果没有提供令牌，返回401错误
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Not authenticated"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
        
        # 提取令牌
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"}
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        # 验证令牌并获取用户
        user = await get_user_by_token(token)
        
        if not user:
            # 令牌无效或用户不存在
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token or user not found"},
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        # 将用户ID存储在请求状态中，以便后续处理程序使用
        request.state.user_id = f"users:{user.id}"
        logger.info(f"Authenticated user: {request.state.user_id}")
        
        # 继续处理请求
        return await call_next(request)