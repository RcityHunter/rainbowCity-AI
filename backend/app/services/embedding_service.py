"""
向量嵌入服务 - 负责生成和管理文本的向量嵌入
"""

import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
import asyncio
from datetime import datetime
import json

# 导入向量嵌入模型
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# 导入向量索引库
import hnswlib

# 导入项目依赖
from app.db import query, create, update, execute_raw_query, run_async
from app.models.memory_models import MemoryType


class EmbeddingService:
    """向量嵌入服务类 - 负责生成和管理文本的向量嵌入"""
    
    _instance = None
    _model = None
    _vector_index = {}  # 内存中的向量索引 {memory_type: hnswlib.Index}
    _id_mapping = {}    # ID映射 {memory_type: {index_id: memory_id}}
    _lock = asyncio.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化嵌入服务"""
        # 只在第一次初始化
        if not hasattr(self, 'initialized') or not self.initialized:
            self.model_name = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
            self.vector_dim = 384  # MiniLM-L6-v2的维度
            self.initialized = False
            # 不在初始化时创建异步任务，而是在首次使用时确保初始化
            self.initialize_async = None
    
    async def initialize(self):
        """异步初始化模型和向量索引"""
        try:
            # 使用异步锁确保只初始化一次
            async with self._lock:
                if self.initialized:
                    return
                
                logging.info(f"正在初始化嵌入模型: {self.model_name}")
                
                # 在单独的线程中加载模型，避免阻塞事件循环
                loop = asyncio.get_event_loop()
                self._model = await loop.run_in_executor(
                    None, 
                    lambda: SentenceTransformer(self.model_name)
                )
                
                # 初始化向量索引
                await self._initialize_vector_indices()
                
                self.initialized = True
                logging.info("嵌入服务初始化完成")
        except Exception as e:
            logging.error(f"初始化嵌入服务失败: {str(e)}")
            self.initialized = False
    
    async def _initialize_vector_indices(self):
        """初始化向量索引"""
        try:
            # 为每种记忆类型创建向量索引
            for memory_type in [MemoryType.CHAT_HISTORY, MemoryType.USER_MEMORY, MemoryType.SESSION_SUMMARY]:
                # 创建新的索引
                index = hnswlib.Index(space='cosine', dim=self.vector_dim)
                
                # 从数据库加载已有的向量嵌入
                memories_result = query('memory', {'memory_type': memory_type})
                memories = await run_async(memories_result)
                
                if memories and len(memories) > 0:
                    # 过滤出有嵌入的记忆
                    memories_with_embeddings = [m for m in memories if m.get('embedding') is not None]
                    
                    if memories_with_embeddings:
                        # 准备向量和ID
                        vectors = np.array([m['embedding'] for m in memories_with_embeddings])
                        ids = np.arange(len(memories_with_embeddings))
                        
                        # 初始化索引
                        index.init_index(
                            max_elements=max(1000, len(memories_with_embeddings) * 2),
                            ef_construction=200,
                            M=16
                        )
                        
                        # 添加向量到索引
                        index.add_items(vectors, ids)
                        
                        # 创建ID映射
                        self._id_mapping[memory_type.value] = {
                            i: memories_with_embeddings[i]['id'] 
                            for i in range(len(memories_with_embeddings))
                        }
                        
                        logging.info(f"为{memory_type.value}加载了{len(memories_with_embeddings)}个向量")
                    else:
                        # 初始化空索引
                        index.init_index(
                            max_elements=1000,
                            ef_construction=200,
                            M=16
                        )
                        self._id_mapping[memory_type.value] = {}
                else:
                    # 初始化空索引
                    index.init_index(
                        max_elements=1000,
                        ef_construction=200,
                        M=16
                    )
                    self._id_mapping[memory_type.value] = {}
                
                # 保存索引
                self._vector_index[memory_type.value] = index
                
            logging.info("向量索引初始化完成")
        except Exception as e:
            logging.error(f"初始化向量索引失败: {str(e)}")
    
    async def ensure_initialized(self):
        """确保服务已初始化"""
        if not self.initialized:
            try:
                # 如果异步任务已经创建，等待它完成
                if self.initialize_async is not None:
                    await self.initialize_async
                else:
                    # 如果还没有创建异步任务，直接初始化
                    try:
                        # 尝试获取当前事件循环
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        # 如果没有运行的事件循环，直接调用初始化方法
                        await self.initialize()
                    else:
                        # 如果有运行的事件循环，创建异步任务
                        self.initialize_async = asyncio.create_task(self.initialize())
                        await self.initialize_async
            except Exception as e:
                logging.error(f"等待初始化失败: {str(e)}")
                raise RuntimeError(f"初始化嵌入服务失败: {str(e)}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        生成文本的向量嵌入
        
        Args:
            text: 要嵌入的文本
            
        Returns:
            向量嵌入
        """
        await self.ensure_initialized()
        
        try:
            # 在单独的线程中生成嵌入，避免阻塞事件循环
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self._model.encode(text).tolist()
            )
            return embedding
        except Exception as e:
            logging.error(f"生成嵌入失败: {str(e)}")
            return []
    
    async def add_to_index(self, memory_type: str, memory_id: str, embedding: List[float]) -> bool:
        """
        将向量添加到索引
        
        Args:
            memory_type: 记忆类型
            memory_id: 记忆ID
            embedding: 向量嵌入
            
        Returns:
            是否添加成功
        """
        await self.ensure_initialized()
        
        try:
            async with self._lock:
                # 获取索引
                index = self._vector_index.get(memory_type)
                if index is None:
                    logging.error(f"找不到记忆类型的索引: {memory_type}")
                    return False
                
                # 获取ID映射
                id_mapping = self._id_mapping.get(memory_type, {})
                
                # 检查是否已存在
                existing_index = None
                for idx, mem_id in id_mapping.items():
                    if mem_id == memory_id:
                        existing_index = idx
                        break
                
                if existing_index is not None:
                    # 更新现有向量
                    index.mark_deleted(existing_index)
                    
                # 添加新向量
                new_index = len(id_mapping)
                
                # 如果索引已满，扩展它
                if new_index >= index.get_max_elements():
                    index.resize_index(max(1000, index.get_max_elements() * 2))
                
                # 添加向量
                index.add_items(np.array([embedding]), np.array([new_index]))
                
                # 更新ID映射
                id_mapping[new_index] = memory_id
                self._id_mapping[memory_type] = id_mapping
                
                return True
        except Exception as e:
            logging.error(f"添加向量到索引失败: {str(e)}")
            return False
    
    async def search_similar(
        self, 
        memory_type: str, 
        query_embedding: List[float], 
        k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        搜索相似向量
        
        Args:
            memory_type: 记忆类型
            query_embedding: 查询向量
            k: 返回的结果数量
            
        Returns:
            相似记忆ID和相似度分数的列表
        """
        await self.ensure_initialized()
        
        try:
            # 获取索引
            index = self._vector_index.get(memory_type)
            if index is None:
                logging.error(f"找不到记忆类型的索引: {memory_type}")
                return []
            
            # 获取ID映射
            id_mapping = self._id_mapping.get(memory_type, {})
            if not id_mapping:
                return []
            
            # 搜索相似向量
            k = min(k, len(id_mapping))
            if k == 0:
                return []
            
            # 执行搜索
            indices, distances = index.knn_query(np.array([query_embedding]), k=k)
            
            # 转换为记忆ID和相似度分数
            results = []
            for i, distance in zip(indices[0], distances[0]):
                memory_id = id_mapping.get(int(i))
                if memory_id:
                    # 将距离转换为相似度分数（1 - 距离）
                    similarity = 1.0 - distance
                    results.append((memory_id, similarity))
            
            return results
        except Exception as e:
            logging.error(f"搜索相似向量失败: {str(e)}")
            return []
    
    async def update_memory_embedding(self, memory_id: str, memory_type: str, text: str) -> bool:
        """
        更新记忆的向量嵌入
        
        Args:
            memory_id: 记忆ID
            memory_type: 记忆类型
            text: 要嵌入的文本
            
        Returns:
            是否更新成功
        """
        try:
            # 生成嵌入
            embedding = await self.generate_embedding(text)
            if not embedding:
                return False
            
            # 更新数据库中的嵌入
            update_result = update('memory', {'id': memory_id}, {'embedding': embedding})
            
            # 使用run_async来正确处理异步更新
            await run_async(update_result)
            
            # 更新索引
            await self.add_to_index(memory_type, memory_id, embedding)
            
            return True
        except Exception as e:
            logging.error(f"更新记忆嵌入失败: {str(e)}")
            return False
    
    @staticmethod
    async def create_vector_index_in_db():
        """在SurrealDB中创建向量索引（如果支持）"""
        try:
            # 检查SurrealDB版本是否支持向量索引
            # 注意：这需要SurrealDB 1.0.0+才支持
            version_query = "INFO FOR DB"
            version_result_coro = execute_raw_query(version_query)
            
            # 使用run_async来正确处理异步查询
            version_result = await run_async(version_result_coro)
            
            logging.info(f"数据库信息: {version_result}")
            
            # 创建向量索引的SQL（使用SurrealDB最新语法）
            # 使用HNSW索引，这是高维向量的最佳选择
            index_query = """
            DEFINE INDEX memory_vector ON memory FIELDS embedding HNSW DIMENSION 384;
            """
            
            try:
                index_result_coro = execute_raw_query(index_query)
                
                # 使用run_async来正确处理异步查询
                index_result = await run_async(index_result_coro)
                logging.info(f"创建向量索引结果: {index_result}")
                return True
            except Exception as e:
                logging.warning(f"创建向量索引失败（可能不支持或已存在）: {str(e)}")
                return False
        except Exception as e:
            logging.error(f"检查数据库向量支持失败: {str(e)}")
            return False


# 创建单例实例
embedding_service = EmbeddingService()
