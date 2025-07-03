from fastapi import APIRouter, HTTPException, Request
import logging
from app.db import USE_MOCK_MODE

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/test", tags=["测试路由"])

@router.get("/status")
async def test_status():
    """
    测试服务器状态
    """
    return {
        "status": "ok",
        "mock_mode": USE_MOCK_MODE,
        "message": "服务器正常运行"
    }

@router.get("/mock-auth")
async def test_mock_auth():
    """
    测试模拟认证
    """
    # 创建一个模拟用户
    user = {
        "id": "mock-user-123",
        "email": "mock@example.com",
        "username": "mock_user",
        "display_name": "Mock User",
        "roles": ["user"],
        "is_activated": True
    }
    
    # 返回模拟认证信息
    return {
        "status": "success",
        "message": "模拟认证成功",
        "user": user,
        "token": "mock-token-123456",
        "mock_mode": USE_MOCK_MODE
    }
