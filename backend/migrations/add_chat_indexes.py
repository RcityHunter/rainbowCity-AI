"""
为聊天相关表添加必要的索引，提高查询性能
"""

import logging
from app.db import execute_raw_query

async def run_migration():
    """执行迁移脚本，添加必要的索引"""
    try:
        logging.info("开始添加聊天表索引...")
        
        # 为chat_sessions表添加索引
        await execute_raw_query("""
        DEFINE INDEX IF NOT EXISTS idx_chat_sessions_id ON chat_sessions FIELDS id;
        """)
        logging.info("已添加chat_sessions.id索引")
        
        await execute_raw_query("""
        DEFINE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions FIELDS session_id;
        """)
        logging.info("已添加chat_sessions.session_id索引")
        
        await execute_raw_query("""
        DEFINE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions FIELDS user_id;
        """)
        logging.info("已添加chat_sessions.user_id索引")
        
        # 为chat_messages表添加索引
        await execute_raw_query("""
        DEFINE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages FIELDS session_id;
        """)
        logging.info("已添加chat_messages.session_id索引")
        
        await execute_raw_query("""
        DEFINE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages FIELDS user_id;
        """)
        logging.info("已添加chat_messages.user_id索引")
        
        logging.info("聊天表索引添加完成")
        return True
    except Exception as e:
        logging.error(f"添加聊天表索引失败: {str(e)}")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_migration())
