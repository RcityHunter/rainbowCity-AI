import os
import requests
import json
import logging
import httpx
from typing import Dict, Any, Optional

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 从环境变量获取OAuth配置
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
# 修改为支持前端和后端的回调地址
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:3000/oauth/google/callback")

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
# 修改为支持前端的回调地址
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
    # 记录环境变量配置情况
    logger.info(f"GitHub OAuth config - Client ID: {GITHUB_CLIENT_ID[:5]}...{GITHUB_CLIENT_ID[-5:] if GITHUB_CLIENT_ID else ''}")
    logger.info(f"GitHub OAuth config - Redirect URI: {GITHUB_REDIRECT_URI}")
    
    # 生成随机状态码，如果没有提供
    if not state:
        import uuid
        state = str(uuid.uuid4())
        logger.info(f"Generated random state: {state[:5]}...")
    
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "user:email",
        "state": state
    }
    
    # 构建授权URL
    auth_url = f"{GITHUB_AUTH_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    logger.info(f"Generated GitHub auth URL (partial): {auth_url[:60]}...")
    
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
        logger.info(f"Full code length: {len(code)}")
        
        # 记录环境变量配置情况
        logger.info(f"Environment variables check:")
        logger.info(f"GOOGLE_CLIENT_ID set: {'Yes' if os.environ.get('GOOGLE_CLIENT_ID') else 'No'}")
        logger.info(f"GOOGLE_CLIENT_SECRET set: {'Yes' if os.environ.get('GOOGLE_CLIENT_SECRET') else 'No'}")
        logger.info(f"GOOGLE_REDIRECT_URI set: {'Yes' if os.environ.get('GOOGLE_REDIRECT_URI') else 'No'}")
        
        # 检查必要的配置
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            logger.error("Missing Google OAuth credentials (client ID or client secret)")
            return None
            
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        # 记录完整的请求数据（除了client_secret）
        log_data = token_data.copy()
        if "client_secret" in log_data:
            log_data["client_secret"] = "*****"
        logger.info(f"Token request data: {log_data}")
        logger.info(f"Sending token request to: {GOOGLE_TOKEN_URL}")
        
        # 使用httpx库发送请求，支持更好的调试
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 添加正确的内容类型头
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = await client.post(GOOGLE_TOKEN_URL, data=token_data, headers=headers)
            
            # 记录完整的响应信息
            logger.info(f"Token response status: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            
            if response.status_code != 200:
                logger.error(f"Token request failed with status {response.status_code}")
                logger.error(f"Response content: {response.text}")
                # 尝试解析错误响应
                try:
                    error_data = response.json()
                    logger.error(f"Error details: {error_data}")
                    if "error" in error_data and error_data["error"] == "invalid_grant":
                        logger.error("Invalid grant error - possible causes: code already used, expired, or redirect URI mismatch")
                        logger.error(f"Check that the registered redirect URI matches: {GOOGLE_REDIRECT_URI}")
                except Exception:
                    pass
                return None
                
            try:
                token_response = response.json()
            except Exception as json_err:
                logger.error(f"Failed to parse response as JSON: {str(json_err)}")
                logger.error(f"Raw response: {response.text}")
                return None
        
        # 检查响应中的错误
        if "error" in token_response:
            logger.error(f"Error in token response: {token_response['error']}")
            if "error_description" in token_response:
                logger.error(f"Error description: {token_response['error_description']}")
            return None
        
        # 记录成功获取令牌（不记录实际令牌）
        if "access_token" in token_response:
            logger.info("Successfully obtained access token")
        else:
            logger.warning(f"No access_token in response. Response keys: {token_response.keys()}")
        
        return token_response
    except Exception as e:
        import traceback
        logger.error(f"Error getting Google token: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

async def get_github_token(code: str, state: str = None) -> Optional[Dict[str, Any]]:
    """
    使用授权码获取GitHub访问令牌
    """
    try:
        # 记录OAuth配置信息（注意不要记录完整的client_secret）
        logger.info(f"GitHub OAuth config - Client ID: {GITHUB_CLIENT_ID[:5]}...{GITHUB_CLIENT_ID[-5:] if GITHUB_CLIENT_ID else ''}")
        logger.info(f"GitHub OAuth config - Redirect URI: {GITHUB_REDIRECT_URI}")
        logger.info(f"Processing authorization code: {code[:5]}...")
        logger.info(f"Full code length: {len(code)}")
        
        # 记录环境变量配置情况
        logger.info(f"Environment variables check:")
        logger.info(f"GITHUB_CLIENT_ID set: {'Yes' if os.environ.get('GITHUB_CLIENT_ID') else 'No'}")
        logger.info(f"GITHUB_CLIENT_SECRET set: {'Yes' if os.environ.get('GITHUB_CLIENT_SECRET') else 'No'}")
        logger.info(f"GITHUB_REDIRECT_URI set: {'Yes' if os.environ.get('GITHUB_REDIRECT_URI') else 'No'}")
        
        # 检查必要的配置
        if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
            logger.error("Missing GitHub OAuth credentials (client ID or client secret)")
            return None
        
        # 准备令牌请求数据
        token_data = {
            "code": code,
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "redirect_uri": GITHUB_REDIRECT_URI
        }
        
        # 如果提供了state，添加到请求中
        if state:
            token_data["state"] = state
        
        # 记录完整的请求数据（除了client_secret）
        log_data = token_data.copy()
        if "client_secret" in log_data:
            log_data["client_secret"] = "*****"
        logger.info(f"Token request data: {log_data}")
        
        headers = {
            "Accept": "application/json",
            "User-Agent": "RainbowCity-AI-App" # GitHub API 要求提供 User-Agent
        }
        
        logger.info(f"Sending token request to: {GITHUB_TOKEN_URL}")
        
        # 使用httpx库发送请求，支持更好的调试
        import httpx
        try:
            with httpx.Client(timeout=30.0) as client:
                # 尝试使用 JSON 格式发送请求
                json_headers = headers.copy()
                json_headers["Content-Type"] = "application/json"
                
                logger.info("Trying JSON format request first")
                response = client.post(GITHUB_TOKEN_URL, json=token_data, headers=json_headers)
                
                # 如果 JSON 格式失败，尝试表单格式
                if response.status_code != 200:
                    logger.info("JSON format failed, trying form data format")
                    response = client.post(GITHUB_TOKEN_URL, data=token_data, headers=headers)
                
                # 记录响应状态和内容（不包含敏感信息）
                logger.info(f"Token response status: {response.status_code}")
                logger.info(f"Response headers: {dict(response.headers)}")
                
                if response.status_code != 200:
                    logger.error(f"Token request failed with status {response.status_code}")
                    logger.error(f"Response content: {response.text}")
                    try:
                        error_data = response.json()
                        logger.error(f"Error details: {error_data}")
                        # 返回错误数据，而不是 None，以便调用者可以获取错误详情
                        return error_data
                    except:
                        logger.error("Could not parse error response as JSON")
                    return None
                
                try:
                    token_response = response.json()
                except Exception as json_err:
                    logger.error(f"Failed to parse response as JSON: {str(json_err)}")
                    logger.error(f"Raw response: {response.text}")
                    return None
                
                # 记录成功获取令牌（不记录实际令牌）
                if "access_token" in token_response:
                    logger.info("Successfully obtained GitHub access token")
                else:
                    logger.warning(f"No access_token in response. Response keys: {token_response.keys()}")
                    logger.warning(f"Response content (sanitized): {token_response}")
                
                return token_response
        except httpx.RequestError as req_err:
            logger.error(f"Request error during GitHub token exchange: {str(req_err)}")
            return None
    except Exception as e:
        import traceback
        logger.error(f"Error getting GitHub token: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

async def get_google_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """
    使用访问令牌获取Google用户信息
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        # 使用异步HTTP客户端
        async with httpx.AsyncClient() as client:
            response = await client.get(GOOGLE_USER_INFO_URL, headers=headers)
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
