#!/usr/bin/env python3
"""
简单的 SurrealDB 测试脚本
"""

import surrealdb
import asyncio

async def main():
    try:
        # 创建连接
        db = surrealdb.Surreal("ws://localhost:8080")
        print("连接创建成功")
        
        # 登录
        token = db.signin({"username": "root", "password": "123"})
        print(f"登录成功: {token[:20]}...")
        
        # 选择命名空间和数据库
        result = db.use("rainbow", "test")
        print(f"选择成功: {result}")
        
        # 测试查询
        query_result = db.query("INFO FOR DB")
        print(f"查询结果: {query_result}")
        
    except Exception as e:
        print(f"错误: {e}")
        print(f"错误类型: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(main())
