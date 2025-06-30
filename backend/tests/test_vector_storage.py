"""
向量存储测试脚本 - 测试向量嵌入和向量搜索功能
"""

import asyncio
import logging
import sys
import os
import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目依赖
from app.services.embedding_service import embedding_service
from app.services.memory_service import MemoryService
from app.models.memory_models import MemoryType, MemoryImportance, MemoryQuery
from app.db import init_db_connection, close_db
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_embedding_generation():
    """测试向量嵌入生成"""
    logger.info("测试向量嵌入生成...")
    
    # 确保嵌入服务已初始化
    await embedding_service.ensure_initialized()
    
    # 测试文本
    test_texts = [
        "我喜欢在周末去公园散步",
        "人工智能技术正在快速发展",
        "今天天气真好，阳光明媚",
        "这本书非常有趣，我一口气读完了",
        "我正在学习如何烹饪意大利面"
    ]
    
    # 生成嵌入
    embeddings = []
    for text in test_texts:
        embedding = await embedding_service.generate_embedding(text)
        embeddings.append(embedding)
        logger.info(f"文本: '{text}' 生成的嵌入维度: {len(embedding)}")
    
    # 验证嵌入维度
    for i, embedding in enumerate(embeddings):
        assert len(embedding) == embedding_service.vector_dim, f"嵌入 {i} 维度不正确"
    
    logger.info("向量嵌入生成测试通过!")
    return embeddings, test_texts


async def test_vector_index():
    """测试向量索引功能"""
    logger.info("测试向量索引功能...")
    
    # 生成测试嵌入
    embeddings, test_texts = await test_embedding_generation()
    
    # 创建测试内存类型
    test_memory_type = "test_memory"
    
    # 创建测试索引
    index = embedding_service._vector_index.get(test_memory_type)
    if not index:
        # 初始化新索引
        import hnswlib
        index = hnswlib.Index(space='cosine', dim=embedding_service.vector_dim)
        index.init_index(max_elements=100, ef_construction=200, M=16)
        embedding_service._vector_index[test_memory_type] = index
    
    # 添加向量到索引
    id_mapping = {}
    for i, embedding in enumerate(embeddings):
        # 将embedding转换为numpy数组并重塑为二维数组
        embedding_array = np.array([embedding])  # 转换为2D数组
        index.add_items(embedding_array, np.array([i]))
        id_mapping[i] = f"test_memory_{i}"
    
    # 保存ID映射
    embedding_service._id_mapping[test_memory_type] = id_mapping
    
    # 测试搜索
    query_text = "我喜欢户外活动和散步"
    query_embedding = await embedding_service.generate_embedding(query_text)
    
    # 搜索相似向量
    results = await embedding_service.search_similar(
        memory_type=test_memory_type,
        query_embedding=query_embedding,
        k=3
    )
    
    logger.info(f"查询: '{query_text}'")
    logger.info(f"搜索结果:")
    for i, (memory_id, similarity) in enumerate(results):
        original_index = int(memory_id.split('_')[-1])
        logger.info(f"  {i+1}. 相似度: {similarity:.4f}, 文本: '{test_texts[original_index]}'")
    
    logger.info("向量索引测试通过!")


async def test_memory_service_with_vectors():
    """测试内存服务的向量功能"""
    logger.info("测试内存服务的向量功能...")
    
    # 连接数据库
    await init_db_connection()
    
    # 生成测试用户ID
    user_id = f"test_user_{int(datetime.now().timestamp())}"
    
    # 1. 保存用户记忆并生成嵌入
    memories = []
    memory_contents = [
        "用户喜欢旅行，特别是去海边",
        "用户是一名软件工程师，擅长Python编程",
        "用户有一只名叫小花的猫",
        "用户喜欢听古典音乐，尤其是贝多芬",
        "用户计划明年去日本旅行"
    ]
    
    logger.info("保存测试用户记忆...")
    for content in memory_contents:
        memory = await MemoryService.save_user_memory(
            user_id=user_id,
            content=content,
            memory_type="preference",
            importance=MemoryImportance.MEDIUM,
            generate_embedding=True
        )
        memories.append(memory)
        # 等待一下，确保嵌入生成完成
        await asyncio.sleep(0.5)
    
    logger.info(f"已保存 {len(memories)} 条测试记忆")
    
    # 2. 使用向量搜索查询记忆
    logger.info("测试向量搜索...")
    
    # 等待一下，确保所有嵌入都已生成
    await asyncio.sleep(2)
    
    # 测试查询
    test_queries = [
        "用户有什么宠物?",
        "用户的职业是什么?",
        "用户有什么旅行计划?"
    ]
    
    for query in test_queries:
        # 生成查询嵌入
        query_embedding = await embedding_service.generate_embedding(query)
        
        # 创建记忆查询
        memory_query = MemoryQuery(
            user_id=user_id,
            query=query,
            limit=3,
            sort_by="vector",
            use_vector_search=True,
            embedding=query_embedding
        )
        
        # 执行搜索
        results = await MemoryService.search_memories(memory_query)
        
        logger.info(f"\n查询: '{query}'")
        logger.info(f"搜索结果:")
        for i, memory in enumerate(results):
            logger.info(f"  {i+1}. {memory.get('content', '')}")
    
    logger.info("内存服务向量功能测试完成!")
    
    # 清理测试数据
    # 注意：在实际测试中可能需要保留数据进行验证，这里为了不影响生产数据选择清理
    # await clean_test_data(user_id)


async def clean_test_data(user_id: str):
    """清理测试数据"""
    from app.db import delete
    
    logger.info(f"清理用户 {user_id} 的测试数据...")
    await delete('memory', {'user_id': user_id})
    logger.info("测试数据清理完成")


async def main():
    """主测试函数"""
    try:
        logger.info("开始向量存储功能测试...")
        
        # 测试向量嵌入生成
        await test_embedding_generation()
        
        # 测试向量索引
        await test_vector_index()
        
        # 测试内存服务的向量功能
        await test_memory_service_with_vectors()
        
        logger.info("所有测试完成!")
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭数据库连接
        await close_db()


if __name__ == "__main__":
    # 设置日志级别，方便调试
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        # 运行测试
        asyncio.run(main())
    except Exception as e:
        logging.error(f"测试运行失败: {str(e)}")
        import traceback
        traceback.print_exc()
