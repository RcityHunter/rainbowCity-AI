"""
记忆服务 - 处理分层记忆系统的创建、存储和检索
"""

import logging
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple

from app.db import query, create, update, delete
from app.models.memory_models import (
    MemoryType, MemoryImportance, ChatHistoryMemory,
    UserMemory, SessionSummary, MemoryQuery
)
from app.services.embedding_service import embedding_service


class MemoryService:
    """记忆服务类 - 管理三层记忆系统"""
    
    @staticmethod
    async def save_chat_history(
        session_id: str,
        user_id: str,
        messages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        generate_embedding: bool = True
    ) -> Dict[str, Any]:
        """
        保存聊天历史记忆（第一层）
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            messages: 消息列表
            metadata: 元数据
            
        Returns:
            保存的聊天历史记忆
        """
        try:
            # 准备记忆数据
            memory_id = str(uuid.uuid4())
            current_time = datetime.now().isoformat()
            
            memory_data = {
                "id": memory_id,
                "session_id": session_id,
                "user_id": user_id,
                "messages": messages,
                "created_at": current_time,
                "updated_at": current_time,
                "metadata": metadata or {},
                "memory_type": MemoryType.CHAT_HISTORY,
                "embedding": None  # 先设为None，稍后生成
            }
            
            # 查询是否已存在该会话的聊天历史
            existing_history = await query('memory', {
                'session_id': session_id,
                'memory_type': MemoryType.CHAT_HISTORY
            })
            
            if existing_history:
                # 更新现有记录
                memory_id = existing_history[0]['id']
                memory_data['id'] = memory_id
                memory_data['created_at'] = existing_history[0]['created_at']
                result = await update('memory', {'id': memory_id}, memory_data)
            else:
                # 创建新记录
                result = await create('memory', memory_data)
                
            return result or memory_data
        except Exception as e:
            logging.error(f"保存聊天历史记忆失败: {str(e)}")
            # 返回原始数据而不是抛出异常，确保流程继续
            return memory_data
    
    @staticmethod
    async def save_user_memory(
        user_id: str,
        content: str,
        memory_type: str,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        source_session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        generate_embedding: bool = True
    ) -> Dict[str, Any]:
        """
        保存用户记忆（第二层）
        
        Args:
            user_id: 用户ID
            content: 记忆内容
            memory_type: 记忆类型（如：偏好、事实、关系等）
            importance: 重要性
            source_session_id: 来源会话ID
            metadata: 元数据
            
        Returns:
            保存的用户记忆
        """
        try:
            # 准备记忆数据
            memory_id = str(uuid.uuid4())
            current_time = datetime.now().isoformat()
            
            memory_data = {
                "id": memory_id,
                "user_id": user_id,
                "content": content,
                "memory_type": memory_type,
                "importance": importance,
                "source_session_id": source_session_id,
                "created_at": current_time,
                "updated_at": current_time,
                "last_accessed": current_time,
                "access_count": 1,
                "metadata": metadata or {},
                "memory_type": MemoryType.USER_MEMORY,
                "embedding": None  # 先设为None，稍后生成
            }
            
            # 创建新记录
            result = await create('memory', memory_data)
            
            # 如果需要生成嵌入，异步处理
            if generate_embedding and content:
                # 创建异步任务生成嵌入，但不等待它完成
                asyncio.create_task(
                    embedding_service.update_memory_embedding(
                        memory_id=memory_data["id"],
                        memory_type=MemoryType.USER_MEMORY,
                        text=content
                    )
                )
                
            return result or memory_data
        except Exception as e:
            logging.error(f"保存用户记忆失败: {str(e)}")
            # 返回原始数据而不是抛出异常，确保流程继续
            return memory_data
    
    @staticmethod
    async def save_session_summary(
        session_id: str,
        user_id: str,
        summary: str,
        start_time: str,
        end_time: str,
        topics: List[str] = None,
        key_points: List[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        generate_embedding: bool = True
    ) -> Dict[str, Any]:
        """
        保存会话摘要（第三层）
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            summary: 摘要内容
            start_time: 会话开始时间
            end_time: 会话结束时间
            topics: 讨论的主题
            key_points: 关键点
            metadata: 元数据
            
        Returns:
            保存的会话摘要
        """
        try:
            # 准备记忆数据
            memory_id = str(uuid.uuid4())
            current_time = datetime.now().isoformat()
            
            memory_data = {
                "id": memory_id,
                "session_id": session_id,
                "user_id": user_id,
                "summary": summary,
                "start_time": start_time,
                "end_time": end_time,
                "topics": topics or [],
                "key_points": key_points or [],
                "created_at": current_time,
                "metadata": metadata or {},
                "memory_type": MemoryType.SESSION_SUMMARY,
                "embedding": None  # 先设为None，稍后生成
            }
            
            # 查询是否已存在该会话的摘要
            existing_summary = await query('memory', {
                'session_id': session_id,
                'memory_type': MemoryType.SESSION_SUMMARY
            })
            
            if existing_summary:
                # 更新现有记录
                memory_id = existing_summary[0]['id']
                memory_data['id'] = memory_id
                memory_data['created_at'] = existing_summary[0]['created_at']
                result = await update('memory', {'id': memory_id}, memory_data)
            else:
                # 创建新记录
                result = await create('memory', memory_data)
                
            return result or memory_data
        except Exception as e:
            logging.error(f"保存会话摘要失败: {str(e)}")
            # 返回原始数据而不是抛出异常，确保流程继续
            return memory_data
    
    @staticmethod
    async def get_chat_history(
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        获取聊天历史记忆
        
        Args:
            session_id: 会话ID
            limit: 限制返回的消息数量
            offset: 消息偏移量
            
        Returns:
            聊天历史记忆
        """
        try:
            # 查询聊天历史
            results = await query('memory', {
                'session_id': session_id,
                'memory_type': MemoryType.CHAT_HISTORY
            })
            
            if not results:
                return None
                
            # 更新访问时间和计数
            memory = results[0]
            memory['last_accessed'] = datetime.now().isoformat()
            memory['access_count'] = memory.get('access_count', 0) + 1
            
            await update('memory', {'id': memory['id']}, memory)
            
            return memory
        except Exception as e:
            logging.error(f"获取聊天历史记忆失败: {str(e)}")
            return None
    
    @staticmethod
    async def get_user_memories(
        user_id: str,
        memory_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "recency"
    ) -> List[Dict[str, Any]]:
        """
        获取用户记忆
        
        Args:
            user_id: 用户ID
            memory_type: 记忆类型（如：偏好、事实、关系等）
            limit: 限制返回的记忆数量
            offset: 记忆偏移量
            sort_by: 排序方式（recency, importance, access_count）
            
        Returns:
            用户记忆列表
        """
        try:
            # 构建查询条件
            query_params = {
                'user_id': user_id,
                'memory_type': MemoryType.USER_MEMORY
            }
            
            if memory_type:
                query_params['memory_type'] = memory_type
                
            # 确定排序方式
            sort_field = 'updated_at'
            sort_order = -1  # 降序
            
            if sort_by == "importance":
                sort_field = 'importance'
                sort_order = -1
            elif sort_by == "access_count":
                sort_field = 'access_count'
                sort_order = -1
                
            # 查询用户记忆
            results = await query(
                'memory',
                query_params,
                sort=[(sort_field, sort_order)],
                limit=limit,
                offset=offset
            )
            
            # 更新访问时间和计数
            for memory in results:
                memory['last_accessed'] = datetime.now().isoformat()
                memory['access_count'] = memory.get('access_count', 0) + 1
                await update('memory', {'id': memory['id']}, memory)
            
            return results or []
        except Exception as e:
            logging.error(f"获取用户记忆失败: {str(e)}")
            return []
    
    @staticmethod
    async def get_session_summary(session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话摘要
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话摘要
        """
        try:
            # 查询会话摘要
            results = await query('memory', {
                'session_id': session_id,
                'memory_type': MemoryType.SESSION_SUMMARY
            })
            
            if not results:
                return None
                
            return results[0]
        except Exception as e:
            logging.error(f"获取会话摘要失败: {str(e)}")
            return None
    
    @classmethod
    async def search_memories(cls, query_params: MemoryQuery) -> List[Dict[str, Any]]:
        """
        搜索记忆
        
        Args:
            query_params: 搜索参数
            
        Returns:
            符合条件的记忆列表
        """
        try:
            # 构建查询条件
            query_conditions = {}
            
            # 添加用户ID过滤
            if query_params.user_id:
                query_conditions['user_id'] = query_params.user_id
                
            # 添加记忆类型过滤
            if query_params.memory_type:
                query_conditions['memory_type'] = query_params.memory_type
                
            # 添加会话ID过滤
            if query_params.session_id:
                query_conditions['session_id'] = query_params.session_id
                
            # 添加标签过滤
            if query_params.tags and len(query_params.tags) > 0:
                # 注意：这里需要根据数据库的实际支持情况调整
                # 这里使用简化的实现，只查询包含第一个标签的记忆
                query_conditions['tags'] = query_params.tags[0]
                
            # 构建排序参数
            sort_params = {}
            if query_params.sort_by == "recency":
                sort_params['updated_at'] = 'DESC'
            elif query_params.sort_by == "importance":
                sort_params['importance'] = 'DESC'
            elif query_params.sort_by == "access_count":
                sort_params['access_count'] = 'DESC'
            else:
                # 默认按时间排序
                sort_params['updated_at'] = 'DESC'
                
            # 执行数据库查询
            try:
                # 查询记忆
                results = await query('memory', query_conditions, sort=sort_params, limit=query_params.limit, offset=query_params.offset)
                
                # 确保结果是列表类型
                if results is None:
                    results = []
                elif not isinstance(results, list):
                    # 如果返回的不是列表，将其转换为列表
                    if isinstance(results, dict):
                        results = [results]
                    else:
                        logging.error(f"查询返回了意外的类型: {type(results)}，转换为空列表")
                        results = []
            except Exception as e:
                logging.error(f"查询记忆表失败: {str(e)}")
                return []
            
            # 如果使用向量搜索且有嵌入
            if query_params.use_vector_search and query_params.embedding:
                try:
                    # 确定要搜索的记忆类型
                    memory_type = query_params.memory_type.value if query_params.memory_type else None
                    
                    # 如果指定了记忆类型，只在该类型中搜索
                    if memory_type:
                        # 执行向量搜索
                        similar_memories = await embedding_service.search_similar(
                            memory_type=memory_type,
                            query_embedding=query_params.embedding,
                            k=query_params.limit
                        )
                        
                        # 获取搜索结果的完整记忆数据
                        if similar_memories:
                            memory_ids = [mem_id for mem_id, _ in similar_memories]
                            vector_results = []
                            
                            # 获取每个记忆的完整数据
                            for memory_id in memory_ids:
                                memory_data = await query('memory', {'id': memory_id})
                                if memory_data:
                                    vector_results.append(memory_data[0])
                            
                            # 替换结果集
                            if vector_results:
                                results = vector_results
                    else:
                        # 在所有记忆类型中搜索
                        all_similar_memories = []
                        for mem_type in [MemoryType.USER_MEMORY, MemoryType.CHAT_HISTORY, MemoryType.SESSION_SUMMARY]:
                            similar = await embedding_service.search_similar(
                                memory_type=mem_type.value,
                                query_embedding=query_params.embedding,
                                k=query_params.limit
                            )
                            all_similar_memories.extend(similar)
                        
                        # 获取搜索结果的完整记忆数据
                        if all_similar_memories:
                            memory_ids = [mem_id for mem_id, _ in all_similar_memories]
                            vector_results = []
                            
                            # 获取每个记忆的完整数据
                            for memory_id in memory_ids:
                                memory_data = await query('memory', {'id': memory_id})
                                if memory_data:
                                    vector_results.append(memory_data[0])
                            
                            # 替换结果集
                            if vector_results:
                                results = vector_results
                except Exception as e:
                    logging.error(f"向量搜索失败: {str(e)}")
            
            # 如果启用了向量搜索，并且有查询文本，则进行向量搜索
            if query_params.use_vector_search and query_params.query and results:
                try:
                    # 生成查询的向量嵌入
                    query_embedding = await embedding_service.get_embedding(query_params.query)
                    
                    if query_embedding:
                        # 计算每个记忆与查询的余弦相似度
                        for memory in results:
                            memory_embedding = memory.get('embedding')
                            if memory_embedding:
                                similarity = embedding_service.calculate_similarity(query_embedding, memory_embedding)
                                memory['similarity_score'] = similarity
                            else:
                                memory['similarity_score'] = 0
                        
                        # 按相似度排序
                        results = sorted(results, key=lambda x: x.get('similarity_score', 0), reverse=True)
                except Exception as e:
                    logging.error(f"向量搜索失败: {str(e)}")

            
            # 应用排序
            if results and (not query_params.use_vector_search or not query_params.query):
                try:
                    if query_params.sort_by == "recency":
                        # 按时间排序（最新的在前）
                        results = sorted(results, key=lambda x: x.get('updated_at', ''), reverse=True)
                    elif query_params.sort_by == "importance":
                        # 按重要性排序
                        results = sorted(results, key=lambda x: x.get('importance', MemoryImportance.LOW), reverse=True)
                    elif query_params.sort_by == "access_count":
                        # 按访问次数排序
                        results = sorted(results, key=lambda x: x.get('access_count', 0), reverse=True)
                    elif query_params.sort_by == "relevance":
                        # 按相关性排序（关键词匹配）
                        results = sorted(
                            results,
                            key=lambda x: _calculate_relevance(x, query_params.query),
                            reverse=True
                        )
                except Exception as sort_error:
                    logging.error(f"相关性排序错误: {str(sort_error)}")

            
            # 更新访问时间和计数 - 使用异步任务处理，不阻塞主流程
            async def update_memory_access(memory):
                try:
                    memory['last_accessed'] = datetime.now().isoformat()
                    memory['access_count'] = memory.get('access_count', 0) + 1
                    await asyncio.wait_for(
                        update('memory', {'id': memory['id']}, memory),
                        timeout=2.0  # 2秒超时
                    )
                except Exception as update_error:
                    logging.error(f"更新记忆访问信息失败: {str(update_error)}")
            
            # 创建更新任务但不等待它们完成
            for memory in results:
                asyncio.create_task(update_memory_access(memory))
            
            return results or []
        except Exception as e:
            logging.error(f"搜索记忆失败: {str(e)}")
            return []
    
    @staticmethod
    async def delete_memory(memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否删除成功
        """
        try:
            # 删除记忆
            result = await delete('memory', {'id': memory_id})
            return True
        except Exception as e:
            logging.error(f"删除记忆失败: {str(e)}")
            return False
    
    @staticmethod
    async def delete_session_memories(session_id: str) -> bool:
        """
        删除会话相关的所有记忆
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        try:
            # 删除会话相关的所有记忆
            await delete('memory', {'session_id': session_id})
            return True
        except Exception as e:
            logging.error(f"删除会话记忆失败: {str(e)}")
            return False


# 辅助函数

def _calculate_relevance(memory: Dict[str, Any], query: str) -> float:
    """
    计算记忆与查询的相关性分数
    
    Args:
        memory: 记忆数据
        query: 查询内容
        
    Returns:
        相关性分数（0-1之间）
    """
    # 简单实现：检查查询词在内容中出现的次数
    content = ""
    
    if memory.get('memory_type') == MemoryType.CHAT_HISTORY:
        # 对于聊天历史，检查所有消息内容
        for msg in memory.get('messages', []):
            if isinstance(msg.get('content'), str):
                content += " " + msg.get('content', '')
    elif memory.get('memory_type') == MemoryType.USER_MEMORY:
        # 对于用户记忆，检查记忆内容
        content = memory.get('content', '')
    elif memory.get('memory_type') == MemoryType.SESSION_SUMMARY:
        # 对于会话摘要，检查摘要内容和关键点
        content = memory.get('summary', '')
        for point in memory.get('key_points', []):
            content += " " + point
            
    # 计算查询词在内容中的出现频率
    query_words = query.lower().split()
    content_lower = content.lower()
    
    matches = 0
    for word in query_words:
        if word in content_lower:
            matches += content_lower.count(word)
            
    # 计算相关性分数（简单实现）
    if not query_words:
        return 0
        
    return min(1.0, matches / len(query_words))
