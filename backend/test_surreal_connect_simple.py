#!/usr/bin/env python3
"""
简单的 SurrealDB 连接测试脚本
按照官方文档的方式连接 SurrealDB
"""

import os
import logging
import asyncio
import surrealdb
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 加载环境变量
load_dotenv()

# SurrealDB 配置 - 使用确定的值而不是环境变量
SURREAL_URL = "ws://localhost:8080"
SURREAL_USER = "root"
SURREAL_PASS = "123"
SURREAL_NS = "rainbow"
SURREAL_DB = "test"

async def test_connection():
    """测试 SurrealDB 连接"""
    try:
        logging.info(f"创建并连接 SurrealDB 客户端: {SURREAL_URL}")
        # 正确方式：直接在创建时传入 URL
        db = surrealdb.Surreal(SURREAL_URL)
        logging.info("客户端创建成功，已连接")
        
        # 注意：不需要单独调用 connect 方法
        
        logging.info(f"登录 SurrealDB: {SURREAL_USER}")
        token = db.signin({"username": SURREAL_USER, "password": SURREAL_PASS})
        logging.info(f"登录成功: {token[:20]}...")
        
        logging.info(f"选择命名空间和数据库: {SURREAL_NS}, {SURREAL_DB}")
        result = db.use(SURREAL_NS, SURREAL_DB)
        logging.info(f"选择成功: {result}")
        
        # 测试创建和查询
        logging.info("创建测试记录")
        # 注意：create 方法不是异步的，不需要 await
        create_result = db.create("test", {
            "name": "Test Record",
            "value": "This is a test"
        })
        logging.info(f"创建结果: {create_result}")
        
        logging.info("查询测试记录")
        # 注意：query 方法不是异步的，不需要 await
        query_result = db.query("SELECT * FROM test")
        logging.info(f"查询结果: {query_result}")
        
        # 关闭连接
        logging.info("关闭连接")
        # 注意：close 方法不是异步的，不需要 await
        db.close()
        logging.info("测试完成")
        
    except Exception as e:
        logging.error(f"错误: {e}")
        logging.error(f"错误类型: {type(e).__name__}")
        if hasattr(e, '__dict__'):
            logging.error(f"错误详情: {e.__dict__}")

if __name__ == "__main__":
    asyncio.run(test_connection())
