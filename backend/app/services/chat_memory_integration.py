"""
聊天记忆集成 - 将聊天服务与记忆系统集成
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from app.services.memory_manager import MemoryManager
from app.services.memory_service import MemoryService
from app.services.embedding_service import embedding_service
from app.services.chat_service import ChatService


class ChatMemoryIntegration:
    """聊天记忆集成类 - 将聊天服务与记忆系统集成"""
    
    def __init__(self):
        """初始化聊天记忆集成"""
        self.memory_manager = MemoryManager()
        
    async def process_chat_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        content_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理聊天消息，保存到聊天历史并更新记忆系统
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            role: 消息角色
            content: 消息内容
            content_type: 消息类型
            metadata: 元数据
            
        Returns:
            处理结果
        """
        result = {
            "message_saved": False,
            "memory_updated": False
        }
        
        try:
            # 1. 保存消息到聊天服务
            saved_message = await ChatService.save_message(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                content_type=content_type,
                metadata=metadata
            )
            
            result["message_saved"] = bool(saved_message)
            result["message"] = saved_message
            
            # 2. 获取会话的所有消息
            messages = await ChatService.get_messages(session_id)
            
            # 3. 只有当消息数量达到一定阈值，或者是会话结束时，才更新记忆系统
            should_update_memory = len(messages) % 5 == 0  # 每5条消息更新一次
            should_generate_summary = len(messages) >= 20  # 当消息达到20条时生成摘要
            
            if should_update_memory or metadata and metadata.get("end_of_session"):
                # 4. 更新记忆系统
                memory_result = await self.memory_manager.process_conversation(
                    session_id=session_id,
                    user_id=user_id,
                    messages=messages,
                    extract_memories=True,
                    generate_summary=should_generate_summary
                )
                
                result["memory_updated"] = memory_result["chat_history_saved"]
                result["memories_extracted"] = memory_result.get("memories_extracted", False)
                result["summary_generated"] = memory_result.get("summary_generated", False)
            
            return result
        except Exception as e:
            logging.error(f"处理聊天消息失败: {str(e)}")
            return result
    
    async def save_chat_history(self, session_id: str, user_id: str, messages: List[Dict[str, Any]]) -> bool:
        """
        保存聊天历史
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            messages: 消息列表
            
        Returns:
            是否保存成功
        """
        try:
            # 保存聊天历史（自动生成向量嵌入）
            result = await MemoryService.save_chat_history(
                session_id=session_id,
                user_id=user_id,
                messages=messages,
                generate_embedding=True
            )
            
            return bool(result)
        except Exception as e:
            logging.error(f"保存聊天历史失败: {str(e)}")
            return False
    
    async def get_relevant_memories(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取与查询相关的记忆
        
        Args:
            user_id: 用户ID
            query: 查询文本
            limit: 返回结果数量限制
            
        Returns:
            相关记忆列表
        """
        try:
            # 使用记忆管理器获取相关记忆（默认使用向量搜索）
            memories = await self.memory_manager.get_relevant_memories(
                query=query,
                user_id=user_id,
                limit=limit,
                use_vector_search=True
            )
            
            return memories
        except Exception as e:
            logging.error(f"获取相关记忆失败: {str(e)}")
            return []
    
    async def enhance_response_with_memories(
        self,
        user_id: str,
        user_message: str,
        current_session_id: str
    ) -> Dict[str, Any]:
        """
        使用用户记忆增强响应
        
        Args:
            user_id: 用户ID
            user_message: 用户消息
            current_session_id: 当前会话ID
            
        Returns:
            相关记忆和上下文增强信息
        """
        result = {
            "relevant_memories": [],
            "session_summary": None,
            "context_enhancement": ""
        }
        
        # 导入超时处理模块
        import asyncio
        from asyncio import TimeoutError
        
        # 1. 检索相关的用户记忆（带超时处理）
        try:
            # 添加超时处理，最多等待3秒
            relevant_memories = await asyncio.wait_for(
                self.get_relevant_memories(user_id, user_message, limit=5),
                timeout=3.0  # 3秒超时
            )
            # 确保返回的是列表类型
            if not isinstance(relevant_memories, list):
                logging.warning(f"检索返回了非列表类型的结果: {type(relevant_memories)}")
                relevant_memories = []
            result["relevant_memories"] = relevant_memories
            logging.info(f"成功检索到{len(relevant_memories)}条相关记忆")
        except TimeoutError:
            logging.warning(f"检索相关记忆超时，继续处理但不使用记忆增强")
            relevant_memories = []
        except Exception as e:
            logging.error(f"检索相关记忆失败: {str(e)}")
            relevant_memories = []
        
        # 2. 获取当前会话的摘要（带超时处理）
        try:
            # 添加超时处理，最多等待2秒
            session_summary = await asyncio.wait_for(
                MemoryService.get_session_summary(current_session_id),
                timeout=2.0  # 2秒超时
            )
            result["session_summary"] = session_summary
            logging.info(f"成功获取会话摘要: {session_summary is not None}")
        except TimeoutError:
            logging.warning(f"获取会话摘要超时，继续处理但不使用会话摘要")
            session_summary = None
        except Exception as e:
            logging.error(f"获取会话摘要失败: {str(e)}")
            session_summary = None
        
        # 3. 构建上下文增强信息
        try:
            context_enhancement = ""
            
            # 添加会话摘要（如果存在）
            if session_summary:
                context_enhancement += f"当前对话摘要: {session_summary.get('summary', '')}\n\n"
                
            # 添加相关记忆
            if relevant_memories:
                context_enhancement += "用户相关信息:\n"
                for i, memory in enumerate(relevant_memories, 1):
                    memory_content = memory.get("content", "")
                    memory_type = memory.get("memory_type", "")
                    context_enhancement += f"{i}. {memory_content} ({memory_type})\n"
            
            result["context_enhancement"] = context_enhancement.strip()
            logging.info(f"成功构建上下文增强信息: {len(context_enhancement)} 字符")
        except Exception as e:
            logging.error(f"构建上下文增强信息失败: {str(e)}")
            result["context_enhancement"] = ""
        
        return result
