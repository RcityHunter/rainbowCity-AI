from fastapi import APIRouter, HTTPException, Depends, Request, Header, status, Security
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import jwt
import uuid
import re
import logging
import os
import asyncio
from functools import wraps

from app.db import db_session, query
from app.models.user import User
from app.models.invite import InviteCode
from app.models.enums import VIPLevel, UserRole

# 创建路由器
router = APIRouter(prefix="/auth", tags=["用户认证"])

# 配置 OAuth2 密码流
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# 从环境变量获取 SECRET_KEY
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-for-jwt")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 天

# 定义请求和响应模型
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    display_name: Optional[str] = None
    invite_code: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    email: str
    username: str
    display_name: Optional[str] = None
    created_at: str
    is_activated: bool
    activation_status: str
    roles: List[str]
    vip_level: str
    personal_invite_code: str
    daily_chat_limit: int
    weekly_invite_limit: int
    ai_companions_limit: int

class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    display_name: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class InviteCodeVerify(BaseModel):
    code: str

class InviteCodeResponse(BaseModel):
    valid: bool
    type: Optional[str] = None
    benefits: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class SystemInviteCodeCreate(BaseModel):
    max_uses: Optional[int] = None
    expires_days: Optional[int] = None
    benefits: Optional[Dict[str, Any]] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

# 验证邮箱格式
def is_valid_email(email: str) -> bool:
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

# 验证密码强度
def is_strong_password(password: str) -> bool:
    """
    验证密码强度:
    - 至少8个字符
    - 至少包含一个数字
    - 至少包含一个大写字母
    - 至少包含一个小写字母
    """
    if len(password) < 8:
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    return True

# 生成个人邀请码
def generate_personal_invite_code() -> str:
    return f"INV-{uuid.uuid4().hex[:8].upper()}"

# 创建 JWT token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 用户认证依赖
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 解码 token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
            
        # 使用正确的ID字段查询用户
        logging.info(f"Searching for user with ID: {user_id}")
        
        # 尝试直接使用ID查询
        users_result = query('users', {'id': user_id})
        
        # Check if the result is a coroutine and await it if needed
        if asyncio.iscoroutine(users_result):
            users = await users_result
        else:
            users = users_result
        
        # 如果没有找到用户，尝试使用邮箱查询
        if not users or len(users) == 0:
            logging.info("User not found by ID, trying to find by email...")
            # 尝试使用最近登录的用户邮箱查询
            email_from_token = payload.get("email")
            logging.info(f"Trying email lookup for user: {payload.get('email')}")
            users_result = query('users', {'email': payload.get('email')})
            
            # Check if the result is a coroutine and await it if needed
            if asyncio.iscoroutine(users_result):
                users = await users_result
            else:
                users = users_result
        
        # 如果仍然没有找到用户，尝试直接使用ID查询
        if not users or len(users) == 0:
            logging.info("User not found by email, trying direct ID lookup...")
            try:
                # 尝试直接使用ID查询
                direct_id = user_id.split(':')[1] if ':' in user_id else user_id
                logging.info(f"Attempting direct database query for ID: {direct_id}")
                
                # 尝试使用直接查询
                direct_result_or_coroutine = query(user_id, {})
                
                # Check if the result is a coroutine and await it if needed
                if asyncio.iscoroutine(direct_result_or_coroutine):
                    direct_result = await direct_result_or_coroutine
                else:
                    direct_result = direct_result_or_coroutine
                
                if direct_result and len(direct_result) > 0:
                    users = [direct_result[0]]
            except Exception as e:
                logging.error(f"Error in direct ID lookup: {e}")
        
        if not users or len(users) == 0:
            raise credentials_exception
            
        user_data = users[0]
        return user_data
    except jwt.PyJWTError:
        raise credentials_exception

# 注册路由
@router.post("/register", response_model=TokenResponse)
async def register(user: UserRegister):
    """
    用户注册
    """
    try:
        # 验证邮箱格式
        if not is_valid_email(user.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
            
        # 验证密码强度
        if not is_strong_password(user.password):
            raise HTTPException(
                status_code=400, 
                detail="Password must be at least 8 characters and contain uppercase, lowercase, and numbers"
            )
            
        # 检查邮箱是否已存在
        existing_users = query('users', {'email': user.email})
        if existing_users and len(existing_users) > 0:
            raise HTTPException(status_code=400, detail="Email already registered")
            
        # 检查用户名是否已存在
        existing_usernames = query('users', {'username': user.username})
        if existing_usernames and len(existing_usernames) > 0:
            raise HTTPException(status_code=400, detail="Username already taken")
            
        # 验证邀请码（如果提供）
        invite_benefits = {}
        if user.invite_code:
            # 查找邀请码
            invites = query('invite_code', {'code': user.invite_code})
            
            if not invites or len(invites) == 0:
                raise HTTPException(status_code=400, detail="Invalid invite code")
                
            invite = invites[0]
            
            # 检查邀请码是否有效
            if invite.get('max_uses', 0) > 0 and invite.get('used_count', 0) >= invite.get('max_uses'):
                raise HTTPException(status_code=400, detail="Invite code has reached maximum uses")
                
            if invite.get('expires_at') and datetime.fromisoformat(invite.get('expires_at')) < datetime.utcnow():
                raise HTTPException(status_code=400, detail="Invite code has expired")
                
            # 获取邀请码提供的权益
            invite_benefits = invite.get('benefits', {})
            
            # 更新邀请码使用次数
            from app.db import update as db_update
            db_update('invite_code', invite.get('id'), {'used_count': invite.get('used_count', 0) + 1})
            
        # 生成密码哈希
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash(user.password, method='pbkdf2:sha256', salt_length=8)
        
        # 准备用户数据
        user_data = {
            'email': user.email,
            'username': user.username,
            'display_name': user.display_name or user.username,
            'password_hash': password_hash,
            'created_at': datetime.utcnow().isoformat(),
            'is_activated': True,
            'activation_status': 'active',
            'roles': ['normal'],
            'vip_level': invite_benefits.get('vip_level', 'free'),
            'personal_invite_code': generate_personal_invite_code(),
            'daily_chat_limit': invite_benefits.get('daily_chat_limit', 10),
            'weekly_invite_limit': invite_benefits.get('weekly_invite_limit', 10),
            'ai_companions_limit': invite_benefits.get('ai_companions_limit', 1)
        }
        
        # 创建用户
        from app.db import create
        result = create('users', user_data)
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create user")
            
        # 生成 JWT token
        token_data = {
            "user_id": result.get('id'),
            "email": user.email
        }
        access_token = create_access_token(token_data)
        
        # 返回用户信息和认证令牌
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error during registration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

# 登录路由
@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    用户登录
    """
    try:
        # 查询用户
        users_result = query('users', {'email': form_data.username})
        
        # Check if the result is a coroutine and await it if needed
        if asyncio.iscoroutine(users_result):
            users = await users_result
        else:
            users = users_result
        
        if not users or len(users) == 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        user = users[0]
        
        # 验证密码
        from werkzeug.security import check_password_hash
        if not check_password_hash(user.get('password_hash', ''), form_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # 生成 JWT token
        token_data = {
            "user_id": user.get('id'),
            "email": user.get('email')
        }
        access_token = create_access_token(token_data)
        
        # 返回用户信息和认证令牌
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error during login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

# 获取用户资料
@router.get("/profile", response_model=Dict[str, Any])
async def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    获取当前登录用户的资料
    """
    return current_user

# 更新用户资料
@router.put("/profile", response_model=Dict[str, Any])
async def update_profile(profile: ProfileUpdate, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    更新当前登录用户的资料
    """
    try:
        update_data = {}
        
        # 检查用户名是否已存在
        if profile.username and profile.username != current_user.get('username'):
            existing_usernames = query('users', {'username': profile.username})
            if existing_usernames and len(existing_usernames) > 0:
                raise HTTPException(status_code=400, detail="Username already taken")
            update_data['username'] = profile.username
            
        # 更新显示名
        if profile.display_name:
            update_data['display_name'] = profile.display_name
            
        if not update_data:
            return current_user
            
        # 更新用户资料
        from app.db import update as db_update
        result = db_update('users', current_user.get('id'), update_data)
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to update profile")
            
        # 返回更新后的用户信息
        users = query('users', {'id': current_user.get('id')})
        if not users or len(users) == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return users[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

# 修改密码
@router.put("/change-password", response_model=Dict[str, str])
async def change_password(password_data: PasswordChange, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    修改当前登录用户的密码
    """
    try:
        # 验证当前密码
        from werkzeug.security import check_password_hash, generate_password_hash
        if not check_password_hash(current_user.get('password_hash', ''), password_data.current_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
            
        # 验证新密码强度
        if not is_strong_password(password_data.new_password):
            raise HTTPException(
                status_code=400, 
                detail="Password must be at least 8 characters and contain uppercase, lowercase, and numbers"
            )
            
        # 生成新密码哈希
        new_password_hash = generate_password_hash(password_data.new_password, method='pbkdf2:sha256', salt_length=8)
        
        # 更新密码
        from app.db import update as db_update
        result = db_update('users', current_user.get('id'), {'password_hash': new_password_hash})
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to update password")
            
        return {"message": "Password updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error changing password: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to change password: {str(e)}")

# 获取邀请码
@router.get("/invite-codes", response_model=Dict[str, Any])
async def get_invite_codes(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    获取当前用户的邀请码
    """
    # 查询用户创建的邀请码
    invite_codes = query('invite_code', {'creator_id': current_user.get('id')})
    
    return {
        'personal_invite_code': current_user.get('personal_invite_code'),
        'invite_codes': invite_codes or []
    }

# 验证邀请码
@router.post("/verify-invite-code", response_model=InviteCodeResponse)
async def verify_invite_code(invite_data: InviteCodeVerify):
    """
    验证邀请码是否有效
    """
    try:
        # 查找邀请码
        invites = query('invite_code', {'code': invite_data.code})
        
        if not invites or len(invites) == 0:
            return {"valid": False, "error": "Invite code not found"}
            
        invite = invites[0]
        
        # 检查邀请码是否有效
        if invite.get('max_uses', 0) > 0 and invite.get('used_count', 0) >= invite.get('max_uses'):
            return {"valid": False, "error": "Invite code has reached maximum uses"}
            
        if invite.get('expires_at') and datetime.fromisoformat(invite.get('expires_at')) < datetime.utcnow():
            return {"valid": False, "error": "Invite code has expired"}
            
        # 返回邀请码信息
        return {
            "valid": True,
            "type": invite.get('type'),
            "benefits": invite.get('benefits')
        }
        
    except Exception as e:
        logging.error(f"Error verifying invite code: {str(e)}")
        return {"valid": False, "error": f"Failed to verify invite code: {str(e)}"}

# 创建系统邀请码
@router.post("/create-system-invite", response_model=Dict[str, Any])
async def create_system_invite(invite_data: SystemInviteCodeCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    管理员创建系统邀请码
    """
    try:
        # 检查用户是否为管理员
        if 'admin' not in current_user.get('roles', []):
            raise HTTPException(status_code=403, detail="Only administrators can create system invites")
            
        # 准备邀请码数据
        invite_code = f"SYS-{uuid.uuid4().hex[:8].upper()}"
        expires_at = None
        
        if invite_data.expires_days:
            expires_at = (datetime.utcnow() + timedelta(days=invite_data.expires_days)).isoformat()
            
        invite_data_dict = {
            'code': invite_code,
            'type': 'system',
            'creator_id': current_user.get('id'),
            'created_at': datetime.utcnow().isoformat(),
            'max_uses': invite_data.max_uses or 1,
            'used_count': 0,
            'expires_at': expires_at,
            'benefits': invite_data.benefits or {}
        }
        
        # 创建邀请码
        from app.db import create
        result = create('invite_code', invite_data_dict)
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create invite code")
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating system invite: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create system invite: {str(e)}")

# 管理员获取所有用户
@router.get("/admin/users", response_model=Dict[str, Any])
async def get_all_users(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    管理员获取所有用户列表
    """
    try:
        # 检查用户是否为管理员
        if 'admin' not in current_user.get('roles', []):
            raise HTTPException(status_code=403, detail="Only administrators can access this endpoint")
            
        # 查询所有用户
        users = query('users', {})
        
        return {
            'total': len(users),
            'users': users
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting all users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")

# 管理员更新用户角色
@router.put("/admin/users/{user_id}/roles", response_model=Dict[str, Any])
async def update_user_roles(
    user_id: str, 
    roles: List[str], 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    管理员更新用户角色
    """
    try:
        # 检查用户是否为管理员
        if 'admin' not in current_user.get('roles', []):
            raise HTTPException(status_code=403, detail="Only administrators can update user roles")
            
        # 查询用户
        users = query('users', {'id': user_id})
        
        if not users or len(users) == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        # 更新用户角色
        from app.db import update as db_update
        result = db_update('users', user_id, {'roles': roles})
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to update user roles")
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating user roles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update user roles: {str(e)}")

# 管理员更新用户VIP级别
@router.put("/admin/users/{user_id}/vip", response_model=Dict[str, Any])
async def update_user_vip(
    user_id: str, 
    vip_level: str, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    管理员更新用户VIP级别
    """
    try:
        # 检查用户是否为管理员
        if 'admin' not in current_user.get('roles', []):
            raise HTTPException(status_code=403, detail="Only administrators can update user VIP level")
            
        # 检查VIP级别是否有效
        if vip_level not in [level.value for level in VIPLevel]:
            raise HTTPException(status_code=400, detail=f"Invalid VIP level: {vip_level}")
            
        # 查询用户
        users = query('users', {'id': user_id})
        
        if not users or len(users) == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        # 更新用户VIP级别
        from app.db import update as db_update
        result = db_update('users', user_id, {'vip_level': vip_level})
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to update user VIP level")
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating user VIP level: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update user VIP level: {str(e)}")
