#!/usr/bin/env python3
"""
测试 SurrealDB 用户注册功能
"""

import os
import logging
import asyncio
import surrealdb
from datetime import datetime
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 加载环境变量
load_dotenv()

# SurrealDB 配置
SURREAL_URL = os.environ.get('SURREAL_URL') or "ws://localhost:8080"
SURREAL_USER = os.environ.get('SURREAL_USER') or "root"
SURREAL_PASS = os.environ.get('SURREAL_PASS') or "123"
SURREAL_NS = os.environ.get('SURREAL_NS') or "rainbow"
SURREAL_DB = os.environ.get('SURREAL_DB') or "test"

async def test_register():
    """测试用户注册功能"""
    try:
        logging.info(f"创建 SurrealDB 客户端: {SURREAL_URL}")
        db = surrealdb.Surreal(SURREAL_URL)
        logging.info("客户端创建成功")
        
        logging.info(f"登录 SurrealDB: {SURREAL_USER}")
        token = db.signin({"username": SURREAL_USER, "password": SURREAL_PASS})
        logging.info(f"登录成功: {token[:20]}...")
        
        logging.info(f"选择命名空间和数据库: {SURREAL_NS}, {SURREAL_DB}")
        result = db.use(SURREAL_NS, SURREAL_DB)
        logging.info(f"选择成功: {result}")
        
        # 测试用户注册
        email = "test@example.com"
        username = "testuser"
        password_hash = "hashed_password"  # 实际应用中应该使用哈希函数
        
        # 检查邮箱是否已存在
        logging.info(f"检查邮箱是否已存在: {email}")
        query_result = db.query(f"SELECT * FROM users WHERE email = '{email}'")
        logging.info(f"查询结果: {query_result}")
        
        if query_result and len(query_result) > 0 and len(query_result[0].get('result', [])) > 0:
            logging.info("邮箱已存在")
        else:
            logging.info("邮箱不存在，可以注册")
            
            # 检查用户名是否已存在
            logging.info(f"检查用户名是否已存在: {username}")
            query_result = db.query(f"SELECT * FROM users WHERE username = '{username}'")
            logging.info(f"查询结果: {query_result}")
            
            if query_result and len(query_result) > 0 and len(query_result[0].get('result', [])) > 0:
                logging.info("用户名已存在")
            else:
                logging.info("用户名不存在，可以注册")
                
                # 创建用户
                logging.info("创建用户")
                user_data = {
                    'email': email,
                    'username': username,
                    'display_name': "Test User",
                    'password_hash': password_hash,
                    'created_at': datetime.utcnow().isoformat(),
                    'is_activated': True,
                    'roles': ['normal']
                }
                
                create_result = db.create('users', user_data)
                logging.info(f"创建结果: {create_result}")
        
        # 关闭连接
        logging.info("关闭连接")
        db.close()
        logging.info("测试完成")
        
    except Exception as e:
        logging.error(f"错误: {e}")
        logging.error(f"错误类型: {type(e).__name__}")
        if hasattr(e, '__dict__'):
            logging.error(f"错误详情: {e.__dict__}")

if __name__ == "__main__":
    asyncio.run(test_register())
