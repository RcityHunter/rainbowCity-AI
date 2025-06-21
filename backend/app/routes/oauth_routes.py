from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Dict, Any, Optional
import logging
import uuid
from datetime import datetime, timedelta

from app.utils.oauth_utils import (
    get_google_auth_url,
    get_github_auth_url,
    get_google_token,
    get_github_token,
    get_google_user_info,
    get_github_user_info
)
from app.utils.auth_utils import create_access_token, get_password_hash
from app.db import query, create, update as db_update

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/oauth", tags=["OAuth认证"])

@router.get("/google/auth")
async def google_auth(state: str = None):
    """
    获取Google OAuth授权URL
    """
    try:
        auth_url = await get_google_auth_url(state)
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Error generating Google auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate Google auth URL")

@router.get("/github/auth")
async def github_auth(state: str = None):
    """
    获取GitHub OAuth授权URL
    """
    try:
        auth_url = await get_github_auth_url(state)
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Error generating GitHub auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate GitHub auth URL")

@router.post("/google/callback")
async def google_callback(request: Request):
    """
    处理Google OAuth回调
    """
    # 尝试从请求体或查询参数获取 code
    try:
        body = await request.json()
        code = body.get("code")
    except:
        # 如果请求体解析失败，尝试从查询参数获取
        query_params = request.query_params
        code = query_params.get("code")
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is required")
    
    try:
        # 记录接收到的授权码（部分）
        logger.info(f"Received Google authorization code: {code[:5]}...")
        
        # 获取访问令牌
        token_data = await get_google_token(code)
        if not token_data or "access_token" not in token_data:
            logger.error("Failed to get Google access token")
            raise HTTPException(status_code=400, detail="Failed to get access token")
            
        access_token = token_data["access_token"]
        logger.info("Successfully obtained Google access token")
        
        # 获取用户信息
        user_info = await get_google_user_info(access_token)
        if not user_info:
            logger.error("Failed to get Google user info")
            raise HTTPException(status_code=400, detail="Failed to get user info")
            
        # 提取用户数据
        email = user_info.get("email")
        if not email:
            logger.error("Email not provided by Google")
            raise HTTPException(status_code=400, detail="Email not provided by Google")
            
        logger.info(f"Processing Google OAuth for email: {email}")
        
        # 检查用户是否已存在
        existing_users = await query('users', {'email': email})
        
        if existing_users and len(existing_users) > 0:
            # 用户已存在，更新OAuth信息
            user = existing_users[0]
            user_id = user.get('id')
            logger.info(f"User exists with ID: {user_id}")
            
            # 更新用户的Google OAuth信息
            oauth_info = user.get('oauth_info', {})
            oauth_info['google'] = {
                'id': user_info.get('sub'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture'),
                'last_login': datetime.utcnow().isoformat(),
                'access_token': access_token
            }
            
            await db_update('users', user_id, {'oauth_info': oauth_info})
            logger.info(f"Updated OAuth info for existing user: {user_id}")
        else:
            # 创建新用户
            user_id = str(uuid.uuid4())
            username = f"google_{user_info.get('sub')[-8:]}"
            display_name = user_info.get('name', username)
            
            logger.info(f"Creating new user with ID: {user_id}, username: {username}")
            
            # 生成随机密码（用户无需知道，因为他们将使用OAuth登录）
            random_password = str(uuid.uuid4())
            password_hash = get_password_hash(random_password)
            
            # 准备OAuth信息
            oauth_info = {
                'google': {
                    'id': user_info.get('sub'),
                    'name': user_info.get('name'),
                    'picture': user_info.get('picture'),
                    'last_login': datetime.utcnow().isoformat(),
                    'access_token': access_token
                }
            }
            
            # 创建用户
            user = {
                'id': user_id,
                'email': email,
                'username': username,
                'display_name': display_name,
                'password_hash': password_hash,
                'created_at': datetime.utcnow().isoformat(),
                'is_activated': True,
                'activation_status': 'active',
                'roles': ['user'],
                'vip_level': 'basic',
                'oauth_info': oauth_info,
                'oauth_provider': 'google'
            }
            
            await create('users', user)
            logger.info(f"Created new user with ID: {user_id}")
            
        # 创建访问令牌
        token_data = {"sub": f"users:{user_id}"}
        access_token = create_access_token(token_data)
        logger.info(f"Created access token for user: {user_id}")
        
        # 获取用户信息返回给前端 - 尝试多种可能的查询方式
        logger.info(f"Querying user with original ID: {user_id}")
        user_data = await query('users', {'id': user_id})
        
        # 如果查询失败，尝试使用email查询（更可靠）
        if not user_data or len(user_data) == 0:
            logger.info(f"Original ID query failed, trying with email: {email}")
            user_data = await query('users', {'email': email})
            
        # 如果仍然失败，尝试使用格式化的ID查询
        if not user_data or len(user_data) == 0:
            formatted_id = f"users:{user_id}"
            logger.info(f"Email query failed, trying with formatted ID: {formatted_id}")
            user_data = await query('users', {'id': formatted_id})
            
        # 如果所有尝试都失败，记录调试信息
        if not user_data or len(user_data) == 0:
            all_users = await query('users', {})
            logger.error(f"Failed to find user after creation. User ID: {user_id}, Email: {email}")
            logger.error(f"Total users in database: {len(all_users)}")
            for u in all_users:
                logger.error(f"Available user: ID={u.get('id')}, Email={u.get('email')}")
            raise HTTPException(status_code=404, detail="User not found after creation/update")
            
        user = user_data[0]
        logger.info(f"Successfully retrieved user data for ID: {user_id}")
        
        # 移除敏感信息
        if 'password_hash' in user:
            del user['password_hash']
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Google callback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process Google callback: {str(e)}")

@router.post("/github/callback")
async def github_callback(request: Request):
    """
    处理GitHub OAuth回调
    """
    # 尝试从请求体或查询参数获取 code
    try:
        body = await request.json()
        code = body.get("code")
    except:
        # 如果请求体解析失败，尝试从查询参数获取
        query_params = request.query_params
        code = query_params.get("code")
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is required")
    
    try:
        # 记录接收到的授权码（部分）
        logger.info(f"Received GitHub authorization code: {code[:5]}...")
        
        # 获取访问令牌
        token_data = await get_github_token(code)
        if not token_data or "access_token" not in token_data:
            logger.error("Failed to get GitHub access token")
            raise HTTPException(status_code=400, detail="Failed to get access token")
            
        access_token = token_data["access_token"]
        logger.info("Successfully obtained GitHub access token")
        
        # 获取用户信息
        user_info = await get_github_user_info(access_token)
        if not user_info:
            logger.error("Failed to get GitHub user info")
            raise HTTPException(status_code=400, detail="Failed to get user info")
            
        # 提取用户数据
        email = user_info.get("email")
        if not email:
            logger.error("Email not provided by GitHub")
            raise HTTPException(status_code=400, detail="Email not provided by GitHub")
            
        logger.info(f"Processing GitHub OAuth for email: {email}")
        
        # 检查用户是否已存在
        existing_users = await query('users', {'email': email})
        
        if existing_users and len(existing_users) > 0:
            # 用户已存在，更新OAuth信息
            user = existing_users[0]
            user_id = user.get('id')
            logger.info(f"User exists with ID: {user_id}")
            
            # 更新用户的GitHub OAuth信息
            oauth_info = user.get('oauth_info', {})
            oauth_info['github'] = {
                'id': user_info.get('id'),
                'login': user_info.get('login'),
                'name': user_info.get('name'),
                'avatar_url': user_info.get('avatar_url'),
                'last_login': datetime.utcnow().isoformat(),
                'access_token': access_token
            }
            
            await db_update('users', user_id, {'oauth_info': oauth_info})
            logger.info(f"Updated OAuth info for existing user: {user_id}")
        else:
            # 创建新用户
            user_id = str(uuid.uuid4())
            username = f"github_{user_info.get('login')}"
            display_name = user_info.get('name', username)
            
            logger.info(f"Creating new user with ID: {user_id}, username: {username}")
            
            # 生成随机密码（用户无需知道，因为他们将使用OAuth登录）
            random_password = str(uuid.uuid4())
            password_hash = get_password_hash(random_password)
            
            # 准备OAuth信息
            oauth_info = {
                'github': {
                    'id': user_info.get('id'),
                    'login': user_info.get('login'),
                    'name': user_info.get('name'),
                    'avatar_url': user_info.get('avatar_url'),
                    'last_login': datetime.utcnow().isoformat(),
                    'access_token': access_token
                }
            }
            
            # 创建用户
            user = {
                'id': user_id,
                'email': email,
                'username': username,
                'display_name': display_name,
                'password_hash': password_hash,
                'created_at': datetime.utcnow().isoformat(),
                'is_activated': True,
                'activation_status': 'active',
                'roles': ['user'],
                'vip_level': 'basic',
                'oauth_info': oauth_info,
                'oauth_provider': 'github'
            }
            
            await create('users', user)
            logger.info(f"Created new user with ID: {user_id}")
            
        # 创建访问令牌
        token_data = {"sub": f"users:{user_id}"}
        access_token = create_access_token(token_data)
        logger.info(f"Created access token for user: {user_id}")
        
        # 获取用户信息返回给前端 - 尝试多种可能的查询方式
        logger.info(f"Querying user with original ID: {user_id}")
        user_data = await query('users', {'id': user_id})
        
        # 如果查询失败，尝试使用email查询（更可靠）
        if not user_data or len(user_data) == 0:
            logger.info(f"Original ID query failed, trying with email: {email}")
            user_data = await query('users', {'email': email})
            
        # 如果仍然失败，尝试使用格式化的ID查询
        if not user_data or len(user_data) == 0:
            formatted_id = f"users:{user_id}"
            logger.info(f"Email query failed, trying with formatted ID: {formatted_id}")
            user_data = await query('users', {'id': formatted_id})
            
        # 如果所有尝试都失败，记录调试信息
        if not user_data or len(user_data) == 0:
            all_users = await query('users', {})
            logger.error(f"Failed to find user after creation. User ID: {user_id}, Email: {email}")
            logger.error(f"Total users in database: {len(all_users)}")
            for u in all_users:
                logger.error(f"Available user: ID={u.get('id')}, Email={u.get('email')}")
            raise HTTPException(status_code=404, detail="User not found after creation/update")
            
        user = user_data[0]
        logger.info(f"Successfully retrieved user data for ID: {user_id}")
        
        # 移除敏感信息
        if 'password_hash' in user:
            del user['password_hash']
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing GitHub callback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process GitHub callback: {str(e)}")
