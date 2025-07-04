import os
import jwt
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from app.models.user import User
from app.extensions import db
from app.db import execute_raw_query
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
        # 注意：这里假讼user_id格式为'users:uuid'，需要提取uuid部分
        if ':' in user_id:
            _, uuid = user_id.split(':', 1)
        else:
            uuid = user_id
        
        # 使用query函数代替db.fetch_one
        from app.db import query
        users_result = query('users', {'id': uuid})
        
        # 检查是否为协程并等待结果
        if asyncio.iscoroutine(users_result):
            users = await users_result
        else:
            users = users_result
        
        if users and len(users) > 0:
            # 获取第一个匹配的用户
            user = users[0]
            # 更新缓存
            user_cache[user_id] = {
                "user": user,
                "expires_at": datetime.now() + timedelta(seconds=CACHE_TIMEOUT)
            }
            logger.info(f"User {user_id} found in database")
            return user
        else:
            # 如果用户不存在，创建一个临时用户（用于开发/测试环境）
            # 无论环境如何，都创建临时用户以方便开发和测试
            logger.warning(f"User {user_id} not found, creating temporary user")
            temp_user = {
                "id": uuid,
                "username": f"temp_{uuid[:8]}",
                "email": f"temp_{uuid[:8]}@example.com",
                "password_hash": get_password_hash("temppassword"),
                "created_at": datetime.utcnow(),
                "is_activated": True
            }
            user = temp_user
            user_cache[user_id] = {
                "user": user,
                "expires_at": datetime.now() + timedelta(seconds=CACHE_TIMEOUT)
            }
            return user
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        return None


async def authenticate_user(username_or_email: str, password: str) -> Optional[Dict]:
    """验证用户凭证并返回用户信息
    
    Args:
        username_or_email: 用户名或邮箱
        password: 密码
        
    Returns:
        如果验证成功，返回用户信息字典，否则返回None
    """
    try:
        # 使用原始SQL查询替代条件字典查询，确保正确查找用户
        logging.info(f"尝试使用用户名或邮箱登录: {username_or_email}")
        query_str = f"SELECT * FROM users WHERE email = '{username_or_email}' OR username = '{username_or_email}'"
        logging.info(f"执行查询: {query_str}")
        
        # 执行查询
        result = await execute_raw_query(query_str)
        logging.info(f"查询结果类型: {type(result)}, 内容: {result}")
        
        # 处理查询结果 - 兼容不同版本的SurrealDB SDK返回格式
        users = []
        if result:
            # 如果是列表
            if isinstance(result, list):
                # 如果是旧格式，包含'result'键
                if len(result) > 0 and isinstance(result[0], dict) and 'result' in result[0]:
                    users = result[0]['result']
                    logging.info(f"旧格式结果，找到 {len(users)} 个用户")
                # 如果是新格式，直接使用列表
                else:
                    users = result
                    logging.info(f"新格式结果，找到 {len(users)} 个用户")
            # 如果是其他类型，尝试直接使用
            elif isinstance(result, dict):
                users = [result]
                logging.info("结果是单个字典，将其包装为列表")
        
        # 如果找到用户
        if users and len(users) > 0:
            user = users[0]
            logging.info(f"找到用户: {user.get('username')}, 开始验证密码")
            
            # 验证密码
            stored_password_hash = user.get('password_hash')
            if stored_password_hash:
                try:
                    # 使用passlib的verify_password函数验证密码
                    if verify_password(password, stored_password_hash):
                        logging.info("密码验证成功")
                        
                        # 将RecordID对象转换为字符串
                        user_id = user.get('id')
                        if hasattr(user_id, '__str__'):
                            user['id'] = str(user_id)
                            
                        # 确保所有RecordID对象都被序列化为字符串
                        for key, value in user.items():
                            if hasattr(value, '__str__') and hasattr(value, 'record_id'):
                                user[key] = str(value)
                                
                        return user
                    else:
                        logging.warning("密码验证失败")
                except Exception as verify_error:
                    logging.error(f"密码验证过程中出错: {str(verify_error)}")
            else:
                logging.warning("用户没有密码哈希值")
        else:
            logging.warning(f"未找到用户: {username_or_email}")
    except Exception as e:
        logging.error(f"认证过程中出错: {str(e)}")
    
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