import asyncio
import os
import sys
import logging
import json
from dotenv import load_dotenv
from surrealdb import Surreal

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 获取SurrealDB连接信息
SURREAL_URL = os.getenv("SURREAL_URL", "ws://localhost:8080")
SURREAL_USER = os.getenv("SURREAL_USER", "root")
SURREAL_PASS = os.getenv("SURREAL_PASS", "root")
SURREAL_NS = os.getenv("SURREAL_NS", "rainbow")
SURREAL_DB = os.getenv("SURREAL_DB", "test")

async def update_test_user_password():
    """更新测试用户的密码哈希"""
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
        
        # 查找测试用户
        test_email = "testuser@example.com"
        logger.info(f"查找测试用户: {test_email}")
        query_result = db.query(f"SELECT * FROM users WHERE email = '{test_email}'")
        logger.info(f"查询结果类型: {type(query_result)}, 内容: {query_result}")
        
        # 处理查询结果
        users = []
        if isinstance(query_result, list):
            if len(query_result) > 0 and 'result' in query_result[0]:
                users = query_result[0]['result']
            else:
                users = query_result
        
        if users and len(users) > 0:
            user = users[0]
            user_id = user.get('id')
            logger.info(f"找到用户: ID={user_id}, 用户名={user.get('username')}")
            
            # 新的密码哈希 - 对应密码 "password"
            new_password_hash = "$2b$12$Vhml/yntYi.HgnFM/bp8weGPd03D9hkaLUMxD5jgV.RgQn9mB8zP."
            
            # 更新密码哈希
            logger.info(f"更新用户密码哈希: {user_id}")
            update_query = f"UPDATE {user_id} SET password_hash = '{new_password_hash}'"
            update_result = db.query(update_query)
            logger.info(f"更新结果: {update_result}")
            
            # 验证更新
            verify_query = f"SELECT * FROM {user_id}"
            verify_result = db.query(verify_query)
            logger.info(f"验证结果: {verify_result}")
            
            logger.info("密码哈希更新成功")
        else:
            logger.warning(f"未找到用户: {test_email}")
            
    except Exception as e:
        logger.error(f"更新密码哈希过程中出错: {str(e)}")

if __name__ == "__main__":
    asyncio.run(update_test_user_password())
