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
                try:
                    # 添加超时处理 - 增加超时时间从3秒到15秒
                    saved_message = await asyncio.wait_for(result, timeout=15.0)
                except asyncio.TimeoutError:
                    logging.error(f"保存消息超时(15秒)，返回原始数据: session_id={session_id}, user_id={user_id}, role={role}")
                    # 超时时返回原始数据，不中断流程
                    return message_data
            else:
                saved_message = result
                
            # 临时禁用会话更新，避免数据库阻塞
            # 注释掉会话更新代码，以确保消息流程不会被阻塞
            # await ChatService.update_session(
            #     session_id, 
            #     user_id, 
            #     last_message=content[:50] + "..." if len(content) > 50 else content,
            #     last_message_time=created_at
            # )
            
            # 记录日志，表明我们跳过了会话更新
            logging.info(f"临时跳过会话更新以避免阻塞: session_id={session_id}")
            
            return saved_message or message_data
        except Exception as e:
            logging.error(f"保存聊天消息失败: {str(e)}")
            # 返回原始数据而不是抛出异常，确保流程继续
            return message_data
    
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
<<<<<<< HEAD
            # 查询会话是否存在
            logging.info(f"ChatService.update_session - 查询会话: session_id={session_id}") # 确保完整记录会话ID
=======
>>>>>>> 7c9145c0328059e47c7c4107aa7ea494ff0ef2cb
            import asyncio
            from concurrent.futures import TimeoutError as FuturesTimeoutError
            
            # 设置更短的超时时间
            TIMEOUT_SECONDS = 3.0
            
            # 直接创建新会话，不进行查询
            # 这样可以避免查询操作可能导致的阻塞
>>>>>>> 7c9145c0328059e47c7c4107aa7ea494ff0ef2cb
            now = datetime.now().isoformat()
            
            # 直接创建或更新会话，不进行查询
            # 这样可以避免查询操作可能导致的阻塞
            session_data = {
                "id": session_id,
                "session_id": session_id,  
                "user_id": user_id,
                "title": title or "新对话",
                "last_message": last_message or "",
                "last_message_time": last_message_time or now,
                "updated_at": now
            }
            
            # 尝试创建新会话
            try:
                logging.info(f"ChatService.update_session - 尝试创建/更新会话: {session_data}")
                
                # 使用upsert操作 - 如果记录存在则更新，不存在则创建
                # 这样可以避免先查询再更新的两步操作
                result = None
                try:
                    # 首先尝试更新现有记录
                    update_result = update('chat_sessions', session_id, session_data)
                    if asyncio.iscoroutine(update_result):
                        result = await asyncio.wait_for(update_result, timeout=TIMEOUT_SECONDS)
                    else:
                        result = update_result
                    
                    logging.info(f"ChatService.update_session - 更新结果: {result}")
                    
                    # 如果更新失败，尝试创建新记录
                    if not result:
                        session_data["created_at"] = now  # 添加创建时间
                        create_result = create('chat_sessions', session_data)
                        if asyncio.iscoroutine(create_result):
                            result = await asyncio.wait_for(create_result, timeout=TIMEOUT_SECONDS)
                        else:
                            result = create_result
                        logging.info(f"ChatService.update_session - 创建结果: {result}")
                except (asyncio.TimeoutError, FuturesTimeoutError) as e:
                    logging.error(f"ChatService.update_session - 操作超时(15秒): session_id={session_id}, user_id={user_id}, error={str(e)}")
                    # 返回原始数据而不抛出异常，让流程继续
                    return session_data
                except Exception as e:
                    logging.error(f"ChatService.update_session - 操作失败: {str(e)}")
                    # 返回原始数据而不抛出异常，让流程继续
                    return session_data
                
                return result or session_data
                
            except Exception as e:
                logging.error(f"ChatService.update_session - 创建/更新会话失败: {str(e)}")
                # 返回原始数据而不抛出异常，让流程继续
                return session_data
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
        import time
        start_time = time.time()
        
        try:
            if not user_id:
                logging.error("获取用户会话失败: user_id 为空")
                return []
                
            logging.info(f"正在获取用户会话: user_id={user_id}, limit={limit}, offset={offset}")
            
            # 查询用户会话
            query_result = query('chat_sessions', {'user_id': user_id}, sort=[('updated_at', 'DESC')], limit=limit, offset=offset)
            
            # 检查结果是否为协程并等待它
            import asyncio
            if asyncio.iscoroutine(query_result):
                try:
                    # 添加15秒超时
                    sessions = await asyncio.wait_for(query_result, timeout=15.0)
                except asyncio.TimeoutError:
                    logging.error(f"获取用户会话超时(15秒): user_id={user_id}")
                    return []
            else:
                sessions = query_result
            
            query_time = time.time() - start_time
            if query_time > 1.0:  # 记录执行时间超过1秒的查询
                logging.warning(f"慢查询警告: 获取用户会话耗时 {query_time:.2f} 秒: user_id={user_id}")
                
            if sessions:
                logging.info(f"成功获取用户会话: user_id={user_id}, 找到 {len(sessions)} 个会话, 耗时 {query_time:.2f} 秒")
            else:
                logging.warning(f"用户没有会话: user_id={user_id}, 耗时 {query_time:.2f} 秒")
                
            return sessions or []
        except Exception as e:
            import traceback
            logging.error(f"获取用户会话失败: user_id={user_id}, error={str(e)}")
            logging.error(f"错误详情: {traceback.format_exc()}")
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
