"""
初始化向量存储 - 在应用启动时初始化向量索引和处理现有数据
"""

import logging
import asyncio
from typing import List, Dict, Any

from app.db import query
from app.models.memory_models import MemoryType
from app.services.embedding_service import embedding_service


async def initialize_vector_storage():
    """初始化向量存储，为现有记忆生成向量嵌入"""
    try:
        logging.info("开始初始化向量存储...")
        
        # 确保嵌入服务已初始化
        await embedding_service.ensure_initialized()
        
        # 尝试在数据库中创建向量索引（如果数据库支持）
        await embedding_service.create_vector_index_in_db()
        
        # 处理现有记忆数据
        await process_existing_memories()
        
        logging.info("向量存储初始化完成")
    except Exception as e:
        logging.error(f"初始化向量存储失败: {str(e)}")


async def process_existing_memories():
    """处理现有记忆数据，为没有向量嵌入的记忆生成嵌入"""
    try:
        # 处理用户记忆
        await process_memory_type(MemoryType.USER_MEMORY)
        
        # 处理会话摘要
        await process_memory_type(MemoryType.SESSION_SUMMARY)
        
        # 处理聊天历史（可能数量较大，最后处理）
        await process_memory_type(MemoryType.CHAT_HISTORY)
        
    except Exception as e:
        logging.error(f"处理现有记忆数据失败: {str(e)}")


async def process_memory_type(memory_type: MemoryType):
    """处理特定类型的记忆数据"""
    try:
        logging.info(f"开始处理 {memory_type.value} 类型的记忆...")
        
        # 查询没有向量嵌入的记忆
        memories = await query('memory', {
            'memory_type': memory_type.value,
            'embedding': None
        })
        
        if not memories:
            logging.info(f"没有找到需要处理的 {memory_type.value} 记忆")
            return
        
        logging.info(f"找到 {len(memories)} 条需要处理的 {memory_type.value} 记忆")
        
        # 创建任务列表
        tasks = []
        
        # 根据记忆类型处理
        for memory in memories:
            if memory_type == MemoryType.USER_MEMORY:
                # 用户记忆
                if 'content' in memory and memory['content']:
                    tasks.append(
                        embedding_service.update_memory_embedding(
                            memory_id=memory['id'],
                            memory_type=memory_type.value,
                            text=memory['content']
                        )
                    )
            
            elif memory_type == MemoryType.SESSION_SUMMARY:
                # 会话摘要
                if 'summary' in memory and memory['summary']:
                    # 构建完整文本（摘要+主题+关键点）
                    text_content = memory['summary']
                    if 'topics' in memory and memory['topics']:
                        text_content += "\n主题: " + ", ".join(memory['topics'])
                    if 'key_points' in memory and memory['key_points']:
                        text_content += "\n关键点: " + ", ".join(memory['key_points'])
                    
                    tasks.append(
                        embedding_service.update_memory_embedding(
                            memory_id=memory['id'],
                            memory_type=memory_type.value,
                            text=text_content
                        )
                    )
            
            elif memory_type == MemoryType.CHAT_HISTORY:
                # 聊天历史
                if 'messages' in memory and memory['messages']:
                    # 提取所有消息内容作为文本
                    text_content = "\n".join([
                        msg.get("content", "") 
                        for msg in memory['messages'] 
                        if isinstance(msg.get("content"), str)
                    ])
                    
                    if text_content:
                        tasks.append(
                            embedding_service.update_memory_embedding(
                                memory_id=memory['id'],
                                memory_type=memory_type.value,
                                text=text_content
                            )
                        )
        
        # 批量处理任务，每批50个
        batch_size = 50
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            results = await asyncio.gather(*batch, return_exceptions=True)
            
            # 统计成功和失败的数量
            success_count = sum(1 for r in results if r is True)
            error_count = sum(1 for r in results if r is not True)
            
            logging.info(f"处理 {memory_type.value} 批次 {i//batch_size + 1}: 成功 {success_count}, 失败 {error_count}")
        
        logging.info(f"完成处理 {memory_type.value} 类型的记忆")
    
    except Exception as e:
        logging.error(f"处理 {memory_type.value} 类型的记忆失败: {str(e)}")
