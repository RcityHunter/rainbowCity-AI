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

async def test_user_registration():
    """测试用户注册流程"""
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
        
        # 清理测试用户
        test_email = "testuser@example.com"
        logger.info(f"清理测试用户: {test_email}")
        db.query(f"DELETE FROM users WHERE email = '{test_email}'")
        
        # 创建测试用户
        logger.info("创建测试用户")
        user_data = {
            'email': test_email,
            'username': 'testuser',
            'display_name': 'Test User',
            'password_hash': '$2b$12$gxanQDLXhBS/t9PKMj4lROlu03GP.cItlllu28UqsCe202sFfj/ii',  # 密码: password
            'created_at': '2025-07-04T07:00:00.000000',
            'is_activated': True,
            'activation_status': 'active',
            'roles': ['normal'],
            'vip_level': 'free',
            'personal_invite_code': 'TEST-CODE',
            'daily_chat_limit': 10,
            'weekly_invite_limit': 10,
            'ai_companions_limit': 1
        }
        
        # 使用原始SQL插入用户
        fields = ", ".join(user_data.keys())
        values_list = []
        for v in user_data.values():
            if v is None:
                values_list.append("NULL")
            elif isinstance(v, str):
                values_list.append(f"'{v}'")
            elif isinstance(v, (list, dict)):
                json_str = json.dumps(v)
                values_list.append(f"'{json_str}'")
            else:
                values_list.append(str(v))
                
        values = ", ".join(values_list)
        query_str = f"INSERT INTO users ({fields}) VALUES ({values}) RETURN AFTER"
        logger.info(f"执行插入查询: {query_str}")
        result = db.query(query_str)
        
        if result and isinstance(result, list) and len(result) > 0 and 'result' in result[0]:
            if len(result[0]['result']) > 0:
                user = result[0]['result'][0]
                user_id = user.get('id')
                if hasattr(user_id, '__str__'):
                    user_id = str(user_id)
                logger.info(f"成功创建用户: ID={user_id}, 邮箱={user.get('email')}")
            else:
                logger.warning("插入查询返回空结果")
        else:
            logger.error(f"插入查询失败: {result}")
        
        # 查询用户
        logger.info(f"查询用户: {test_email}")
        result = db.query(f"SELECT * FROM users WHERE email = '{test_email}'")
        logger.info(f"查询结果类型: {type(result)}, 内容: {result}")
        
        # 直接处理结果，不期望'result'键
        if result and isinstance(result, list):
            users = result
            if users and len(users) > 0:
                user = users[0]
                user_id = user.get('id')
                if hasattr(user_id, '__str__'):
                    user_id = str(user_id)
                logger.info(f"找到用户: ID={user_id}, 用户名={user.get('username')}, 邮箱={user.get('email')}")
            else:
                logger.warning(f"未找到邮箱为 {test_email} 的用户")
        else:
            logger.warning(f"查询用户 {test_email} 失败")
        
        # 查询所有用户
        logger.info("查询所有用户")
        result = db.query("SELECT * FROM users")
        logger.info(f"查询所有用户结果类型: {type(result)}, 内容: {result}")
        
        # 直接处理结果，不期望'result'键
        if result and isinstance(result, list):
            # 检查是否有结果列表
            if len(result) > 0:
                # 如果第一个元素是字典并有'result'键
                if isinstance(result[0], dict) and 'result' in result[0]:
                    users = result[0]['result']
                else:
                    # 否则直接使用结果列表
                    users = result
                    
                logger.info(f"找到 {len(users)} 个用户:")
                for user in users:
                    user_id = user.get('id')
                    if hasattr(user_id, '__str__'):
                        user_id = str(user_id)
                    logger.info(f"用户ID: {user_id}, 用户名: {user.get('username')}, 邮箱: {user.get('email')}")
            else:
                logger.warning("结果列表为空")
        else:
            logger.warning("未找到任何用户")
        
        # 关闭连接
        db.close()
        logger.info("测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_user_registration())
