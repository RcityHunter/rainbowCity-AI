"""
聊天服务 - 处理聊天记录的存储和检索
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.db import query, create, update, delete
from app.models.chat_models import ChatMessage, ChatSession

class ChatService:
    """聊天服务类"""
    
    @staticmethod
    async def save_message(
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        content_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        保存聊天消息到数据库
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            role: 消息角色 (用户账号 或 用户账号_aiR)
            content: 消息内容
            content_type: 消息类型 (text, image, audio, video, document)
            metadata: 元数据
            
        Returns:
            保存的消息记录
        """
        try:
            # 准备消息数据
            message_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            
            message_data = {
                "id": message_id,
                "session_id": session_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "content_type": content_type,
                "metadata": metadata or {},
                "created_at": created_at
            }
            
            # 保存消息到数据库
            result = create('chat_messages', message_data)
            
            # 检查结果是否为协程并等待它
            import asyncio
            if asyncio.iscoroutine(result):
                saved_message = await result
            else:
                saved_message = result
                
            # 更新会话信息
            await ChatService.update_session(
                session_id, 
                user_id, 
                last_message=content[:50] + "..." if len(content) > 50 else content,
                last_message_time=created_at
            )
            
            return saved_message
        except Exception as e:
            logging.error(f"保存聊天消息失败: {str(e)}")
            raise
    
    @staticmethod
    async def update_session(
        session_id: str,
        user_id: str,
        title: Optional[str] = None,
        last_message: Optional[str] = None,
        last_message_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新或创建会话信息
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            title: 会话标题
            last_message: 最后一条消息
            last_message_time: 最后一条消息时间
            
        Returns:
            更新后的会话信息
        """
        logging.info(f"ChatService.update_session - 开始更新会话: session_id={session_id}, user_id={user_id}")
        try:
            # 查询会话是否存在
            logging.info(f"ChatService.update_session - 查询会话: session_id={session_id}")
            import asyncio
            
            # 先使用id字段查询
            sessions_result = query('chat_sessions', {'id': session_id})
            
            # 检查结果是否为协程并等待它
            if asyncio.iscoroutine(sessions_result):
                sessions = await sessions_result
                logging.info(f"ChatService.update_session - 异步查询结果(id): {sessions}")
            else:
                sessions = sessions_result
                logging.info(f"ChatService.update_session - 同步查询结果(id): {sessions}")
            
            # 如果没有找到，尝试使用session_id字段查询
            if not sessions or len(sessions) == 0:
                logging.info(f"ChatService.update_session - 使用id字段未找到会话，尝试使用session_id字段")
                sessions_result = query('chat_sessions', {'session_id': session_id})
                
                # 检查结果是否为协程并等待它
                if asyncio.iscoroutine(sessions_result):
                    sessions = await sessions_result
                    logging.info(f"ChatService.update_session - 异步查询结果(session_id): {sessions}")
                else:
                    sessions = sessions_result
                    logging.info(f"ChatService.update_session - 同步查询结果(session_id): {sessions}")
                
            now = datetime.now().isoformat()
            
            if not sessions or len(sessions) == 0:
                # 创建新会话
                logging.info(f"ChatService.update_session - 创建新会话: session_id={session_id}")
                # 确保同时设置id和session_id字段，且值相同
                session_data = {
                    "id": session_id,  # 直接使用传入的session_id作为会话ID
                    "session_id": session_id,  # 也设置session_id字段为相同的值
                    "user_id": user_id,
                    "title": title or f"新对话 {now}",
                    "last_message": last_message or "",
                    "last_message_time": last_message_time or now,
                    "message_count": 1,
                    "created_at": now,
                    "updated_at": now
                }
                logging.info(f"ChatService.update_session - 新会话数据详情: id={session_data['id']}, session_id={session_data['session_id']}, title={session_data['title']}")
                logging.info(f"ChatService.update_session - 将使用create函数创建新会话到chat_sessions表")
                logging.info(f"ChatService.update_session - 新会话数据: {session_data}")
                
                result = create('chat_sessions', session_data)
                
                # 检查结果是否为协程并等待它
                if asyncio.iscoroutine(result):
                    final_result = await result
                    logging.info(f"ChatService.update_session - 异步创建结果: {final_result}")
                    return final_result
                else:
                    logging.info(f"ChatService.update_session - 同步创建结果: {result}")
                    return result
            else:
                # 更新现有会话
                session = sessions[0]
                session_id_db = session.get('id')
                
                # 准备更新数据
                update_data = {
                    "updated_at": now,
                    "message_count": session.get('message_count', 0) + 1
                }
                
                if title:
                    update_data["title"] = title
                    
                if last_message:
                    update_data["last_message"] = last_message
                    
                if last_message_time:
                    update_data["last_message_time"] = last_message_time
                
                # 更新会话
                logging.info(f"ChatService.update_session - 更新会话: session_id_db={session_id_db}, update_data={update_data}")
                result = update('chat_sessions', session_id_db, update_data)
                
                # 检查结果是否为协程并等待它
                if asyncio.iscoroutine(result):
                    final_result = await result
                    logging.info(f"ChatService.update_session - 异步更新结果: {final_result}")
                    return final_result
                else:
                    logging.info(f"ChatService.update_session - 同步更新结果: {result}")
                    return result
        except Exception as e:
            logging.error(f"ChatService.update_session - 更新会话信息失败: {str(e)}")
            import traceback
            logging.error(f"ChatService.update_session - 异常详情: {traceback.format_exc()}")
            raise
    
    @staticmethod
    async def get_messages(session_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取指定会话的消息记录
        
        Args:
            session_id: 会话ID
            limit: 限制返回的消息数量
            offset: 消息偏移量，用于分页
            
        Returns:
            消息记录列表
        """
        try:
            # 查询消息记录
            query_result = query('chat_messages', {'session_id': session_id}, sort=[('created_at', 1)], limit=limit, offset=offset)
            
            # 检查结果是否为协程并等待它
            import asyncio
            if asyncio.iscoroutine(query_result):
                messages = await query_result
            else:
                messages = query_result
                
            return messages or []
        except Exception as e:
            logging.error(f"获取聊天消息失败: {str(e)}")
            return []
    
    @staticmethod
    async def get_user_sessions(user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取用户的所有会话
        
        Args:
            user_id: 用户ID
            limit: 限制返回的会话数量
            offset: 会话偏移量，用于分页
            
        Returns:
            会话列表
        """
        try:
            # 查询用户会话
            query_result = query('chat_sessions', {'user_id': user_id}, sort=[('updated_at', -1)], limit=limit, offset=offset)
            
            # 检查结果是否为协程并等待它
            import asyncio
            if asyncio.iscoroutine(query_result):
                sessions = await query_result
            else:
                sessions = query_result
                
            return sessions or []
        except Exception as e:
            logging.error(f"获取用户会话失败: {str(e)}")
            return []
    
    @staticmethod
    async def delete_session(session_id: str) -> bool:
        """
        删除会话及其所有消息
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        try:
            # 删除会话
            session_result = delete('chat_sessions', {'session_id': session_id})
            
            # 检查结果是否为协程并等待它
            import asyncio
            if asyncio.iscoroutine(session_result):
                await session_result
            
            # 删除所有相关消息
            message_result = delete('chat_messages', {'session_id': session_id})
            
            # 检查结果是否为协程并等待它
            if asyncio.iscoroutine(message_result):
                await message_result
                
            return True
        except Exception as e:
            logging.error(f"删除会话失败: {str(e)}")
            return False
