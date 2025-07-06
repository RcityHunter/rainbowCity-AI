import os
import requests
import json
import logging
from typing import Dict, Any, Optional

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 从环境变量获取OAuth配置
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:3000/oauth/google/callback")

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.environ.get("GITHUB_REDIRECT_URI", "http://localhost:3000/oauth/github/callback")

# Google OAuth2 配置
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# GitHub OAuth 配置
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API_URL = "https://api.github.com/user"
GITHUB_USER_EMAILS_API_URL = "https://api.github.com/user/emails"

async def get_google_auth_url(state: str = None) -> str:
    """
    获取Google OAuth授权URL
    """
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    
    if state:
        params["state"] = state
        
    auth_url = f"{GOOGLE_AUTH_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    return auth_url

async def get_github_auth_url(state: str = None) -> str:
    """
    获取GitHub OAuth授权URL
    """
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "user:email"
    }
    
    if state:
        params["state"] = state
        
    auth_url = f"{GITHUB_AUTH_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    return auth_url

async def get_google_token(code: str) -> Optional[Dict[str, Any]]:
    """
    使用授权码获取Google访问令牌
    """
    try:
        # 记录OAuth配置信息（注意不要记录完整的client_secret）
        logger.info(f"Google OAuth config - Client ID: {GOOGLE_CLIENT_ID[:5]}...{GOOGLE_CLIENT_ID[-5:] if GOOGLE_CLIENT_ID else ''}")
        logger.info(f"Google OAuth config - Redirect URI: {GOOGLE_REDIRECT_URI}")
        logger.info(f"Processing authorization code: {code[:5]}...")
        
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        logger.info(f"Sending token request to: {GOOGLE_TOKEN_URL}")
        response = requests.post(GOOGLE_TOKEN_URL, data=token_data)
        
        # 记录响应状态和内容（不包含敏感信息）
        logger.info(f"Token response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Token request failed with status {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return None
            
        response.raise_for_status()
        token_response = response.json()
        
        # 记录成功获取令牌（不记录实际令牌）
        if "access_token" in token_response:
            logger.info("Successfully obtained access token")
        
        return token_response
    except Exception as e:
        logger.error(f"Error getting Google token: {str(e)}")
        return None

async def get_github_token(code: str) -> Optional[Dict[str, Any]]:
    """
    使用授权码获取GitHub访问令牌
    """
    try:
        # 记录OAuth配置信息（注意不要记录完整的client_secret）
        logger.info(f"GitHub OAuth config - Client ID: {GITHUB_CLIENT_ID[:5]}...{GITHUB_CLIENT_ID[-5:] if GITHUB_CLIENT_ID else ''}")
        logger.info(f"GitHub OAuth config - Redirect URI: {GITHUB_REDIRECT_URI}")
        logger.info(f"Processing authorization code: {code[:5]}...")
        
        token_data = {
            "code": code,
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "redirect_uri": GITHUB_REDIRECT_URI
        }
        
        headers = {
            "Accept": "application/json"
        }
        
        logger.info(f"Sending token request to: {GITHUB_TOKEN_URL}")
        response = requests.post(GITHUB_TOKEN_URL, data=token_data, headers=headers)
        
        # 记录响应状态和内容（不包含敏感信息）
        logger.info(f"Token response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Token request failed with status {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return None
            
        response.raise_for_status()
        token_response = response.json()
        
        # 记录成功获取令牌（不记录实际令牌）
        if "access_token" in token_response:
            logger.info("Successfully obtained GitHub access token")
        
        return token_response
    except Exception as e:
        logger.error(f"Error getting GitHub token: {str(e)}")
        return None

async def get_google_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """
    使用访问令牌获取Google用户信息
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(GOOGLE_USER_INFO_URL, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        logger.error(f"Error getting Google user info: {str(e)}")
        return None

async def get_github_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """
    使用访问令牌获取GitHub用户信息
    """
    try:
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/json"
        }
        
        # 获取用户基本信息
        user_response = requests.get(GITHUB_USER_API_URL, headers=headers)
        user_response.raise_for_status()
        user_data = user_response.json()
        
        # 如果用户没有公开邮箱，则获取用户邮箱列表
        if not user_data.get("email"):
            email_response = requests.get(GITHUB_USER_EMAILS_API_URL, headers=headers)
            email_response.raise_for_status()
            emails = email_response.json()
            
            # 获取主要邮箱
            primary_email = next((email for email in emails if email.get("primary")), None)
            if primary_email:
                user_data["email"] = primary_email.get("email")
        
        return user_data
    except Exception as e:
        logger.error(f"Error getting GitHub user info: {str(e)}")
        return None
