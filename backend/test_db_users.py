import asyncio
import os
import sys
import logging
import pytest
from dotenv import load_dotenv
from surrealdb import Surreal

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 获取SurrealDB连接信息
SURREAL_URL = os.getenv("SURREAL_URL", "ws://localhost:8000")
SURREAL_USER = os.getenv("SURREAL_USER", "root")
SURREAL_PASS = os.getenv("SURREAL_PASS", "root")
SURREAL_NS = os.getenv("SURREAL_NS", "test")
SURREAL_DB = os.getenv("SURREAL_DB", "test")

@pytest.mark.asyncio
async def test_connection():
    """测试SurrealDB连接"""
    try:
        logger.info(f"连接到 SurrealDB: {SURREAL_URL}")
        db = Surreal(SURREAL_URL)
        
        # 登录
        logger.info(f"登录 SurrealDB: {SURREAL_USER}")
        token = db.signin({"username": SURREAL_USER, "password": SURREAL_PASS})
        logger.info(f"登录成功: {token[:20]}...")
        
        # 选择命名空间和数据库
        logger.info(f"选择命名空间和数据库: {SURREAL_NS}, {SURREAL_DB}")
        result = db.use(SURREAL_NS, SURREAL_DB)
        logger.info(f"选择成功: {result}")
        
        # 查询所有用户
        logger.info("查询所有用户")
        result = db.query("SELECT * FROM users")
        
        if result and isinstance(result, list) and len(result) > 0 and 'result' in result[0]:
            users = result[0]['result']
            logger.info(f"找到 {len(users)} 个用户:")
            for user in users:
                user_id = user.get('id')
                if hasattr(user_id, '__str__'):
                    user_id = str(user_id)
                logger.info(f"用户ID: {user_id}, 用户名: {user.get('username')}, 邮箱: {user.get('email')}")
        else:
            logger.warning("未找到任何用户")
        
        # 测试特定用户查询
        test_email = "123456@test.com"
        logger.info(f"测试查询特定用户: {test_email}")
        result = db.query(f"SELECT * FROM users WHERE email = '{test_email}'")
        
        if result and isinstance(result, list) and len(result) > 0 and 'result' in result[0]:
            users = result[0]['result']
            if users and len(users) > 0:
                logger.info(f"找到用户: {users[0].get('username')}, 邮箱: {users[0].get('email')}")
            else:
                logger.warning(f"未找到邮箱为 {test_email} 的用户")
        else:
            logger.warning(f"查询用户 {test_email} 失败")
        
        # 关闭连接
        db.close()
        logger.info("测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection())
