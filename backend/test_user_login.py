import asyncio
import os
import sys
import logging
import json
import requests
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 获取API地址
API_URL = os.getenv("API_URL", "http://localhost:5001")

async def test_user_login():
    """测试用户登录流程"""
    try:
        # 测试用户信息
        test_email = "testuser@example.com"
        test_password = "password"  # 对应哈希值 $2b$12$gxanQDLXhBS/t9PKMj4lROlu03GP.cItlllu28UqsCe202sFfj/ii
        
        logger.info(f"测试登录用户: {test_email}")
        
        # 构建登录请求
        login_url = f"{API_URL}/api/auth/login"
        login_data = {
            "username": test_email,
            "password": test_password
        }
        
        logger.info(f"发送登录请求到: {login_url}")
        logger.info(f"登录数据: {login_data}")
        
        # 发送登录请求 - 使用表单格式
        response = requests.post(login_url, data=login_data)
        
        # 检查响应
        logger.info(f"登录响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"登录成功! 响应数据: {json.dumps(response_data, indent=2)}")
            
            # 验证返回的token和用户信息
            if "access_token" in response_data:
                logger.info(f"获取到访问令牌: {response_data['access_token'][:20]}...")
                
                # 使用token获取用户信息
                me_url = f"{API_URL}/api/auth/profile"
                headers = {"Authorization": f"Bearer {response_data['access_token']}"}
                
                logger.info(f"使用令牌获取用户信息: {me_url}")
                me_response = requests.get(me_url, headers=headers)
                
                logger.info(f"用户信息响应状态码: {me_response.status_code}")
                if me_response.status_code == 200:
                    user_data = me_response.json()
                    logger.info(f"成功获取用户信息: {json.dumps(user_data, indent=2)}")
                else:
                    logger.error(f"获取用户信息失败: {me_response.text}")
            else:
                logger.error("响应中没有访问令牌")
        else:
            logger.error(f"登录失败: {response.text}")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_user_login())
