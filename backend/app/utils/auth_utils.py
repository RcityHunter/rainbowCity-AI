import os
import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from app.models.user import User
from app.extensions import db
import asyncio

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 设置OAuth2密码承载依赖
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 从环境变量获取密钥，如果不存在则使用默认值
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "rainbowcity_default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

# 用户缓存，减少数据库查询
user_cache = {}
CACHE_TIMEOUT = 300  # 缓存超时时间（秒）


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码的哈希值
    """
    return pwd_context.hash(password)


async def get_user(user_id: str) -> Optional[User]:
    """
    根据用户ID获取用户信息
    """
    # 记录用户查找请求
    logger.info(f"Searching for user with ID: {user_id}")
    
    # 检查缓存
    if user_id in user_cache and user_cache[user_id]["expires_at"] > datetime.now():
        logger.info(f"User {user_id} found in cache")
        return user_cache[user_id]["user"]
    
    try:
        # 尝试从数据库获取用户
        # 注意：这里假设user_id格式为'users:uuid'，需要提取uuid部分
        if ':' in user_id:
            _, uuid = user_id.split(':', 1)
        else:
            uuid = user_id
            
        query = f"SELECT * FROM users WHERE id = '{uuid}' LIMIT 1"
        result = await db.fetch_one(query)
        
        if result:
            # 创建用户对象
            user = User(**dict(result))
            # 更新缓存
            user_cache[user_id] = {
                "user": user,
                "expires_at": datetime.now() + timedelta(seconds=CACHE_TIMEOUT)
            }
            logger.info(f"User {user_id} found in database")
            return user
        else:
            # 如果用户不存在，创建一个临时用户（用于开发/测试环境）
            if os.environ.get("APP_ENV") == "development":
                logger.warning(f"User {user_id} not found, creating temporary user for development")
                temp_user = {
                    "id": uuid,
                    "username": f"temp_{uuid[:8]}",
                    "email": f"temp_{uuid[:8]}@example.com",
                    "password_hash": get_password_hash("temppassword"),
                    "created_at": datetime.utcnow(),
                    "is_activated": True
                }
                user = User(**temp_user)
                user_cache[user_id] = {
                    "user": user,
                    "expires_at": datetime.now() + timedelta(seconds=CACHE_TIMEOUT)
                }
                return user
            
            logger.warning(f"User {user_id} not found")
            return None
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        return None


async def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    验证用户名和密码
    """
    try:
        query = f"SELECT * FROM users WHERE username = '{username}' OR email = '{username}' LIMIT 1"
        result = await db.fetch_one(query)
        
        if not result:
            return None
            
        user = User(**dict(result))
        
        if not verify_password(password, user.password_hash):
            return None
            
        return user
    except Exception as e:
        logger.error(f"Error authenticating user {username}: {str(e)}")
        return None


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    获取当前用户
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
        token_data = {"user_id": user_id}
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = await get_user(token_data["user_id"])
    
    if user is None:
        raise credentials_exception
        
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前激活用户
    """
    if not current_user.is_activated:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_user_by_token(token: str) -> Optional[User]:
    """
    根据令牌获取用户
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
            
        user = await get_user(user_id)
        return user
    except Exception:
        return None