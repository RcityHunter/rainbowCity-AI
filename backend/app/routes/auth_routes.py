from fastapi import APIRouter, HTTPException, Depends, Request, Header, status, Security
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, validator  # Removed EmailStr import temporarily
from typing import Dict, Any, Optional, List, Union
import asyncio
from datetime import datetime, timedelta
import uuid
import re
import logging
import os
import asyncio
from functools import wraps

from app.db import db_session, query, create, update as db_update
from app.models.user import User
from app.models.invite import InviteCode
from app.models.enums import VIPLevel, UserRole

# 导入认证工具类
from app.utils.auth_utils import (
    verify_password, 
    get_password_hash, 
    get_user, 
    authenticate_user, 
    create_access_token, 
    get_current_user, 
    get_current_active_user
)

# 创建路由器
router = APIRouter(prefix="/auth", tags=["用户认证"])

# 配置 OAuth2 密码流
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 从环境变量获取 SECRET_KEY
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "rainbowcity_default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 天

# 定义请求和响应模型
class UserRegister(BaseModel):
    email: str  # Temporarily using str instead of EmailStr
    username: str
    password: str
    display_name: Optional[str] = None
    invite_code: Optional[str] = None

class UserLogin(BaseModel):
    email: str  # Temporarily using str instead of EmailStr
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
    
class PasswordReset(BaseModel):
    email: str  # Temporarily using str instead of EmailStr
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

# 用户认证依赖 - 使用新的认证工具类
async def get_current_user_from_db(token: str = Depends(oauth2_scheme)):
    """
    从数据库获取当前用户，兼容旧的数据库查询方式
    """
    try:
        # 使用新的认证工具类获取用户
        user = await get_current_user(token)
        if user:
            return user
    except Exception as e:
        logging.error(f"Error getting user from token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
        existing_users_result = query('users', {'email': user.email})
        # 检查是否为协程并等待结果
        if asyncio.iscoroutine(existing_users_result):
            existing_users = await existing_users_result
        else:
            existing_users = existing_users_result
            
        if existing_users and len(existing_users) > 0:
            raise HTTPException(status_code=400, detail="Email already registered")
            
        # 检查用户名是否已存在
        existing_usernames_result = query('users', {'username': user.username})
        # 检查是否为协程并等待结果
        if asyncio.iscoroutine(existing_usernames_result):
            existing_usernames = await existing_usernames_result
        else:
            existing_usernames = existing_usernames_result
            
        if existing_usernames and len(existing_usernames) > 0:
            raise HTTPException(status_code=400, detail="Username already taken")
            
        # 验证邀请码（如果提供）
        invite_benefits = {}
        if user.invite_code:
            # 查找邀请码
            invites_result = query('invite_code', {'code': user.invite_code})
            
            # 检查是否为协程并等待结果
            if asyncio.iscoroutine(invites_result):
                invites = await invites_result
            else:
                invites = invites_result
            
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
            update_result = db_update('invite_code', invite.get('id'), {'used_count': invite.get('used_count', 0) + 1})
            
            # 检查是否为协程并等待结果
            if asyncio.iscoroutine(update_result):
                await update_result
            
        # 使用新的密码哈希函数
        password_hash = get_password_hash(user.password)
        
        # 打印密码哈希信息以进行调试
        logging.info(f"Generated password hash: {password_hash}")
        
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
        create_result = create('users', user_data)
        
        # 检查是否为协程并等待结果
        if asyncio.iscoroutine(create_result):
            result = await create_result
        else:
            result = create_result
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create user")
            
        # 生成 JWT token
        token_data = {
            "sub": f"users:{result.get('id')}",  # 使用标准JWT声明格式
            "email": user.email
        }
        access_token = create_access_token(token_data)
        
        # 返回用户信息和认证令牌
        # 确保用户ID被正确序列化为字符串
        user_id = result.get('id')
        if hasattr(user_id, '__str__'):
            user_id = str(user_id)
            
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": user.email,
                "username": user.username,
                "display_name": user.display_name or user.username,
                "roles": ['normal'],
                "vip_level": invite_benefits.get('vip_level', 'free')
            }
        }
    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

# 登录路由
@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    用户登录
    """
    try:
        # 使用新的认证工具类进行用户认证
        user = await authenticate_user(form_data.username, form_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查用户是否激活
        if not user.get('is_activated', False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is not activated",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # 生成 JWT token
        token_data = {
            "sub": f"users:{user.get('id')}",  # 使用标准JWT声明格式
            "email": user.get('email')
        }
        access_token = create_access_token(token_data)
        
        # 返回用户信息和认证令牌
        # 确保用户ID被正确序列化为字符串
        user_id = user.get('id')
        if hasattr(user_id, '__str__'):
            user_id = str(user_id)
            
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": user.get('email'),
                "username": user.get('username'),
                "display_name": user.get('display_name'),
                "roles": user.get('roles', ['normal']),
                "vip_level": user.get('vip_level', 'free')
            }
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

# 用户重置密码
@router.post("/reset-password", response_model=Dict[str, Any])
async def reset_password(reset_data: PasswordReset):
    """
    用户重置密码
    不需要原密码，但需要知道邮箱
    在实际生产环境中，应该添加邮箱验证或其他安全措施
    """
    try:
        # 验证密码强度
        if not is_strong_password(reset_data.new_password):
            raise HTTPException(
                status_code=400, 
                detail="Password must be at least 8 characters and contain uppercase, lowercase, and numbers"
            )
            
        # 查询用户
        users_result = query('users', {'email': reset_data.email})
        
        # 检查结果是否为协程并等待它
        if asyncio.iscoroutine(users_result):
            users = await users_result
        else:
            users = users_result
        
        if not users or len(users) == 0:
            # 为了安全考虑，不透露用户是否存在
            return {"message": "If the email exists, a password reset has been processed"}
            
        user = users[0]
        user_id = user.get('id')
        
        # 生成新的密码哈希
        from werkzeug.security import generate_password_hash
        new_hash = generate_password_hash(reset_data.new_password, method='pbkdf2:sha256', salt_length=8)
        
        # 记录新的密码哈希信息
        logging.info(f"New password hash for reset: {new_hash}")
        logging.info(f"New password hash type: {type(new_hash)}")
        logging.info(f"New password hash length: {len(new_hash)}")
        
        # 更新用户密码哈希
        from app.db import update as db_update
        update_result = db_update('users', user_id, {'password_hash': new_hash})
        
        if not update_result:
            raise HTTPException(status_code=500, detail="Failed to reset password")
            
        return {"message": "Password has been reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error resetting password: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")

# 修复用户密码哈希
@router.post("/admin/fix-password-hash", response_model=Dict[str, Any])
async def fix_password_hash(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    修复所有用户的密码哈希问题
    只有管理员可以执行此操作
    """
    try:
        # 检查用户是否为管理员
        if 'admin' not in current_user.get('roles', []):
            raise HTTPException(status_code=403, detail="Only administrators can perform this operation")
            
        # 查询所有用户
        users_result = query('users', {})
        
        # 检查结果是否为协程并等待它
        if asyncio.iscoroutine(users_result):
            users = await users_result
        else:
            users = users_result
            
        if not users:
            return {"message": "No users found to fix"}
            
        # 记录找到的用户数量
        logging.info(f"Found {len(users)} users to check for password hash fix")
        
        # 计数器
        fixed_count = 0
        skipped_count = 0
        failed_count = 0
        
        # 遍历所有用户
        for user in users:
            user_id = user.get('id')
            email = user.get('email')
            password_hash = user.get('password_hash')
            
            # 检查密码哈希是否需要修复
            if not password_hash or password_hash == 'pbkdf2:sha256':
                logging.info(f"Fixing password hash for user: {email}")
                
                # 为用户设置临时密码
                temp_password = f"Temp{uuid.uuid4().hex[:8]}123"
                
                # 生成新的密码哈希
                from werkzeug.security import generate_password_hash
                new_hash = generate_password_hash(temp_password, method='pbkdf2:sha256', salt_length=8)
                
                # 更新用户密码哈希
                from app.db import update as db_update
                update_result = db_update('users', user_id, {'password_hash': new_hash})
                
                if update_result:
                    fixed_count += 1
                    logging.info(f"Fixed password hash for user: {email}, new temp password: {temp_password}")
                else:
                    failed_count += 1
                    logging.error(f"Failed to fix password hash for user: {email}")
            else:
                skipped_count += 1
                logging.info(f"User {email} already has valid password hash, skipping")
                
        return {
            "message": "Password hash fix completed",
            "total_users": len(users),
            "fixed": fixed_count,
            "skipped": skipped_count,
            "failed": failed_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fixing password hashes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fix password hashes: {str(e)}")

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
