"""
聊天会话API路由
实现用户与AI聊天的会话管理和历史记录检索功能
"""

from fastapi import APIRouter, HTTPException, Depends, Path, Query, Body
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.models.chat_models import ChatHistoryResponse, ChatSessionsResponse
from app.services.chat_service import ChatService
from app.routes.auth_routes import get_current_user

# 创建路由器
router = APIRouter(prefix="/chats", tags=["聊天会话"])

@router.get("", response_model=ChatSessionsResponse)
async def get_user_sessions(
    limit: int = Query(20, description="每页会话数量"),
    offset: int = Query(0, description="分页偏移量"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取当前用户的所有聊天会话
    
    返回用户的聊天会话列表，按最后消息时间倒序排序
    """
    try:
        user_id = current_user.get('id')
        
        # 获取用户会话
        sessions = await ChatService.get_user_sessions(user_id, limit, offset)
        
        # 处理会话数据格式，确保与前端期望的格式匹配
        formatted_sessions = []
        for session in sessions:
            formatted_sessions.append({
                "id": session.get("id") or session.get("session_id"),
                "title": session.get("title") or "新对话",
                "preview": session.get("last_message") or "无预览内容",
                "lastUpdated": session.get("last_message_time") or session.get("updated_at"),
                "message_count": session.get("message_count") or 0
            })
        
        return {
            "chats": formatted_sessions
        }
    except Exception as e:
        logging.error(f"获取用户会话失败: {str(e)}")
        return {
            "success": False,
            "sessions": [],
            "error": str(e)
        }

@router.post("", response_model=Dict[str, Any])
async def create_chat_session(
    chat_data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    创建新的聊天会话
    
    接收前端发送的会话数据，创建新的会话记录
    """
    try:
        user_id = current_user.get('id')
        logging.info(f"创建新聊天会话: user_id={user_id}")
        logging.info(f"接收到的数据: {chat_data}")
        
        # 提取必要的字段
        session_id = chat_data.get('id')
        title = chat_data.get('title', '新对话')
        preview = chat_data.get('preview', '')
        last_updated = chat_data.get('lastUpdated', datetime.now().isoformat())
        messages = chat_data.get('messages', [])
        
        # 更新或创建会话
        session_result = await ChatService.update_session(
            session_id=session_id,
            user_id=user_id,
            title=title,
            last_message=preview,
            last_message_time=last_updated
        )
        
        # 保存消息
        if messages and len(messages) > 0:
            for message in messages:
                await ChatService.save_message(
                    session_id=session_id,
                    user_id=user_id,
                    role=message.get('role'),
                    content=message.get('content'),
                    content_type=message.get('type', 'text')
                )
        
        return {
            "id": session_id,
            "title": title,
            "preview": preview,
            "lastUpdated": last_updated,
            "success": True
        }
    except Exception as e:
        logging.error(f"创建聊天会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建聊天会话失败: {str(e)}")

@router.put("/{session_id}", response_model=Dict[str, Any])
async def update_chat_session(
    session_id: str = Path(..., description="会话ID"),
    chat_data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    更新现有的聊天会话
    
    接收前端发送的会话数据，更新现有的会话记录
    """
    try:
        user_id = current_user.get('id')
        logging.info(f"更新聊天会话: session_id={session_id}, user_id={user_id}")
        logging.info(f"接收到的数据: {chat_data}")
        
        # 提取必要的字段
        title = chat_data.get('title', '新对话')
        preview = chat_data.get('preview', '')
        last_updated = chat_data.get('lastUpdated', datetime.now().isoformat())
        messages = chat_data.get('messages', [])
        
        # 更新会话
        session_result = await ChatService.update_session(
            session_id=session_id,
            user_id=user_id,
            title=title,
            last_message=preview,
            last_message_time=last_updated
        )
        
        # 如果有新消息，保存消息
        if messages and len(messages) > 0:
            # 获取已有的消息 ID
            existing_messages = await ChatService.get_messages(session_id)
            existing_message_ids = [msg.get('id') for msg in existing_messages]
            
            # 只保存新消息
            for message in messages:
                if message.get('id') not in existing_message_ids:
                    await ChatService.save_message(
                        session_id=session_id,
                        user_id=user_id,
                        role=message.get('role'),
                        content=message.get('content'),
                        content_type=message.get('type', 'text')
                    )
        
        return {
            "id": session_id,
            "title": title,
            "preview": preview,
            "lastUpdated": last_updated,
            "success": True
        }
    except Exception as e:
        logging.error(f"更新聊天会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新聊天会话失败: {str(e)}")

@router.get("/{session_id}", response_model=ChatHistoryResponse)
async def get_session_messages(
    session_id: str = Path(..., description="会话ID"),
    limit: int = Query(100, description="每页消息数量"),
    offset: int = Query(0, description="分页偏移量"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取指定会话的聊天记录
    
    返回会话中的消息列表，按时间顺序排序
    """
    try:
        user_id = current_user.get('id')
        
        # 获取会话消息
        messages = await ChatService.get_messages(session_id, limit, offset)
        
        # 验证用户是否有权限访问该会话
        if messages and len(messages) > 0:
            first_message = messages[0]
            message_user_id = first_message.get('user_id')
            
            if message_user_id != user_id:
                return {
                    "success": False,
                    "session_id": session_id,
                    "messages": [],
                    "error": "无权访问此会话"
                }
        
        return {
            "success": True,
            "chat": {
                "id": session_id,
                "messages": messages
            }
        }
    except Exception as e:
        logging.error(f"获取会话消息失败: {str(e)}")
        return {
            "success": False,
            "session_id": session_id,
            "messages": [],
            "error": str(e)
        }

@router.delete("/{session_id}")
async def delete_session(
    session_id: str = Path(..., description="会话ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    删除指定的聊天会话
    
    删除会话及其所有消息
    """
    try:
        # 删除会话
        success = await ChatService.delete_session(session_id)
        
        return {
            "success": success,
            "session_id": session_id,
            "message": "会话已删除" if success else "删除会话失败"
        }
    except Exception as e:
        logging.error(f"删除会话失败: {str(e)}")
        return {
            "success": False,
            "session_id": session_id,
            "message": f"删除会话失败: {str(e)}"
        }
