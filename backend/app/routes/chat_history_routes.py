"""
聊天历史记录API路由 - FastAPI版本
实现单用户与AI聊天的历史记录存储和检索功能
"""

from fastapi import APIRouter, HTTPException, Depends, Path, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union, Set
import time
from datetime import datetime
import logging

from app.db import create, query, update, run_async, get_db
from app.routes.auth_routes import get_current_user

# 创建路由器
router = APIRouter(prefix="/chats", tags=["聊天历史"])

# 定义请求和响应模型
class ChatCreate(BaseModel):
    title: str = "新聊天"
    model_used: str = "gemini-pro"
    last_message_preview: Optional[str] = None

class ChatUpdate(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None
    model_used: Optional[str] = None
    last_message_preview: Optional[str] = None

class MessageCreate(BaseModel):
    role: str
    content: str
    token_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

class MessagesBatchCreate(BaseModel):
    messages: List[MessageCreate]

class Chat(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str
    last_message_at: str
    model_used: str
    is_archived: bool = False
    is_pinned: bool = False
    last_message_preview: Optional[str] = None

class Message(BaseModel):
    id: str
    chat_id: str
    role: str
    content: str
    timestamp: str
    token_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    message: str
    chat_id: Optional[str] = None
    chat: Optional[Chat] = None

class ChatsResponse(BaseModel):
    chats: List[Chat]

class MessageResponse(BaseModel):
    message: str
    message_id: Optional[str] = None
    message: Optional[Message] = None

class MessagesResponse(BaseModel):
    messages: List[Message]
    total: int
    page: int
    per_page: int
    has_more: bool

class MessagesBatchResponse(BaseModel):
    message: str
    messages: List[Message]

@router.get("", response_model=ChatsResponse)
async def get_user_chats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取当前用户的所有聊天会话"""
    user_id = current_user.get('id')
    
    try:
        async def _get_chats():
            db = await get_db()
            if db is None:
                return []
            
            # 查询用户的所有未归档聊天，按最后消息时间和置顶状态排序
            result = await db.query(f"""
                SELECT * FROM chat 
                WHERE user_id = '{user_id}' AND is_archived = false 
                ORDER BY is_pinned DESC, last_message_at DESC
            """)
            
            if result and isinstance(result, list) and len(result) > 0:
                return result
            return []
        
        chats = await run_async(_get_chats())
        
        # 处理查询结果
        return {"chats": chats if chats else []}
            
    except Exception as e:
        logging.error(f"获取聊天列表时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取聊天列表失败: {str(e)}")

@router.post("", response_model=ChatResponse, status_code=201)
async def create_chat(
    chat_data: ChatCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """创建新的聊天会话"""
    user_id = current_user.get('id')
    
    try:
        # 创建新的聊天会话
        new_chat = {
            'user_id': user_id,
            'title': chat_data.title,
            'created_at': datetime.now().isoformat(),
            'last_message_at': datetime.now().isoformat(),
            'model_used': chat_data.model_used,
            'is_archived': False,
            'is_pinned': False
        }
        
        # 如果提供了预览，则添加
        if chat_data.last_message_preview:
            new_chat['last_message_preview'] = chat_data.last_message_preview
        
        result = create('chat', new_chat)
        
        if result and len(result) > 0:
            chat_id = result[0].get('id')
            return {
                'message': 'Chat created successfully',
                'chat_id': chat_id,
                'chat': result[0]
            }
        else:
            raise HTTPException(status_code=500, detail="创建聊天会话失败")
            
    except Exception as e:
        logging.error(f"创建聊天会话时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建聊天会话失败: {str(e)}")

@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str = Path(..., description="聊天会话ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """获取特定聊天会话的详情"""
    user_id = current_user.get('id')
    
    try:
        # 查询聊天会话
        chats = query('chat', {'id': f'chat:{chat_id}'})
        
        if not chats or len(chats) == 0:
            raise HTTPException(status_code=404, detail="聊天会话不存在")
        
        chat = chats[0]
        
        # 验证所有权
        if chat.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="无权访问此聊天会话")
        
        return {
            'message': 'Chat retrieved successfully',
            'chat': chat
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取聊天会话时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取聊天会话失败: {str(e)}")

@router.put("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_data: ChatUpdate,
    chat_id: str = Path(..., description="聊天会话ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """更新聊天会话信息"""
    user_id = current_user.get('id')
    
    try:
        # 查询聊天会话
        chats = query('chat', {'id': f'chat:{chat_id}'})
        
        if not chats or len(chats) == 0:
            raise HTTPException(status_code=404, detail="聊天会话不存在")
        
        chat = chats[0]
        
        # 验证所有权
        if chat.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="无权修改此聊天会话")
        
        # 准备更新数据
        update_data = {}
        
        if chat_data.title is not None:
            update_data['title'] = chat_data.title
        
        if chat_data.is_archived is not None:
            update_data['is_archived'] = chat_data.is_archived
        
        if chat_data.is_pinned is not None:
            update_data['is_pinned'] = chat_data.is_pinned
        
        if chat_data.model_used is not None:
            update_data['model_used'] = chat_data.model_used
        
        if chat_data.last_message_preview is not None:
            update_data['last_message_preview'] = chat_data.last_message_preview
        
        # 更新聊天会话
        updated_chat = update('chat', chat_id, update_data)
        
        return {
            'message': 'Chat updated successfully',
            'chat': updated_chat
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"更新聊天会话时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新聊天会话失败: {str(e)}")

@router.delete("/{chat_id}", response_model=Dict[str, str])
async def delete_chat(
    chat_id: str = Path(..., description="聊天会话ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """删除聊天会话"""
    user_id = current_user.get('id')
    
    try:
        # 查询聊天会话
        chats = query('chat', {'id': f'chat:{chat_id}'})
        
        if not chats or len(chats) == 0:
            raise HTTPException(status_code=404, detail="聊天会话不存在")
        
        chat = chats[0]
        
        # 验证所有权
        if chat.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="无权删除此聊天会话")
        
        # 删除聊天会话
        async def _delete_chat():
            db = await get_db()
            if db is None:
                return False
            
            # 删除聊天会话
            await db.delete(f"chat:{chat_id}")
            
            # 删除相关的消息
            # 注意：这里应该使用批量删除，但当前DB接口可能不支持
            # 实际应用中应该考虑使用事务或批量操作
            
            return True
        
        result = await run_async(_delete_chat())
        
        if result:
            return {"message": "Chat deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="删除聊天会话失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"删除聊天会话时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除聊天会话失败: {str(e)}")

@router.get("/{chat_id}/messages", response_model=MessagesResponse)
async def get_chat_messages(
    chat_id: str = Path(..., description="聊天会话ID"),
    page: int = Query(1, description="页码，从1开始"),
    per_page: int = Query(20, description="每页消息数"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """获取特定聊天会话的消息"""
    user_id = current_user.get('id')
    
    try:
        # 查询聊天会话
        chats = query('chat', {'id': f'chat:{chat_id}'})
        
        if not chats or len(chats) == 0:
            raise HTTPException(status_code=404, detail="聊天会话不存在")
        
        chat = chats[0]
        
        # 验证所有权
        if chat.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="无权访问此聊天会话")
        
        # 计算分页参数
        offset = (page - 1) * per_page
        
        # 获取消息
        async def _get_messages():
            db = await get_db()
            if db is None:
                return [], 0
            
            # 查询总消息数
            count_result = await db.query(f"""
                SELECT COUNT(*) as total FROM message 
                WHERE chat_id = 'chat:{chat_id}'
            """)
            
            total = 0
            if count_result and isinstance(count_result, list) and len(count_result) > 0:
                if isinstance(count_result[0], dict) and 'total' in count_result[0]:
                    total = count_result[0]['total']
                elif isinstance(count_result[0], list) and len(count_result[0]) > 0:
                    total = count_result[0][0].get('total', 0)
            
            # 查询消息，按时间戳升序排序
            result = await db.query(f"""
                SELECT * FROM message 
                WHERE chat_id = 'chat:{chat_id}' 
                ORDER BY timestamp ASC
                LIMIT {per_page} OFFSET {offset}
            """)
            
            messages = []
            if result and isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict) and 'result' in result[0]:
                    messages = result[0]['result']
                elif isinstance(result[0], list):
                    messages = result[0]
                else:
                    messages = result
            
            return messages, total
        
        messages, total = await run_async(_get_messages())
        
        # 计算是否有更多消息
        has_more = (offset + len(messages)) < total
        
        return {
            'messages': messages,
            'total': total,
            'page': page,
            'per_page': per_page,
            'has_more': has_more
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取聊天消息时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取聊天消息失败: {str(e)}")

@router.post("/{chat_id}/messages", response_model=MessageResponse, status_code=201)
async def add_chat_message(
    message_data: MessageCreate,
    chat_id: str = Path(..., description="聊天会话ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """添加消息到聊天会话"""
    user_id = current_user.get('id')
    
    try:
        # 验证角色
        if message_data.role not in ['user', 'assistant', 'system']:
            raise HTTPException(status_code=400, detail="无效的消息角色")
        
        # 查询聊天会话
        chats = query('chat', {'id': f'chat:{chat_id}'})
        
        if not chats or len(chats) == 0:
            raise HTTPException(status_code=404, detail="聊天会话不存在")
        
        chat = chats[0]
        
        # 验证所有权
        if chat.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="无权访问此聊天会话")
        
        # 准备消息数据
        new_message = {
            'chat_id': f'chat:{chat_id}',
            'role': message_data.role,
            'content': message_data.content,
            'timestamp': message_data.timestamp or datetime.now().isoformat()
        }
        
        # 添加可选字段
        if message_data.token_count is not None:
            new_message['token_count'] = message_data.token_count
        
        if message_data.metadata is not None:
            new_message['metadata'] = message_data.metadata
        
        # 创建消息
        result = create('message', new_message)
        
        if result and len(result) > 0:
            message_id = result[0].get('id')
            
            # 更新聊天会话的最后消息时间和预览
            preview = message_data.content
            if len(preview) > 100:
                preview = preview[:97] + '...'
            
            update_data = {
                'last_message_at': new_message['timestamp'],
                'last_message_preview': preview
            }
            
            update('chat', chat_id, update_data)
            
            return {
                'message': 'Message added successfully',
                'message_id': message_id,
                'message': result[0]
            }
        else:
            raise HTTPException(status_code=500, detail="添加消息失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"添加消息时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加消息失败: {str(e)}")

@router.post("/{chat_id}/messages/batch", response_model=MessagesBatchResponse, status_code=201)
async def add_chat_messages_batch(
    messages_data: MessagesBatchCreate,
    chat_id: str = Path(..., description="聊天会话ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """批量添加消息到聊天会话"""
    user_id = current_user.get('id')
    
    if not messages_data.messages:
        raise HTTPException(status_code=400, detail="未提供消息")
    
    try:
        # 先验证聊天会话存在且属于当前用户
        chats = query('chat', {'id': f'chat:{chat_id}'})
        
        if not chats or len(chats) == 0:
            raise HTTPException(status_code=404, detail="聊天会话不存在")
        
        chat = chats[0]
        
        if chat.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="无权访问此聊天会话")
        
        # 批量创建消息
        async def _create_messages_batch():
            db = await get_db()
            if db is None:
                return []
            
            created_messages = []
            last_message = None
            
            for msg in messages_data.messages:
                # 验证角色
                if msg.role not in ['user', 'assistant', 'system']:
                    continue
                
                # 准备消息数据
                message_data = {
                    'chat_id': f'chat:{chat_id}',
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp or datetime.now().isoformat()
                }
                
                # 添加可选字段
                if msg.token_count is not None:
                    message_data['token_count'] = msg.token_count
                
                if msg.metadata is not None:
                    message_data['metadata'] = msg.metadata
                
                # 创建消息
                result = await db.create('message', message_data)
                
                if result and len(result) > 0:
                    created_messages.append(result[0])
                    last_message = result[0]
            
            # 如果有消息被创建，更新聊天会话的最后消息时间和预览
            if last_message:
                preview = last_message.get('content', '')
                if len(preview) > 100:
                    preview = preview[:97] + '...'
                
                update_data = {
                    'last_message_at': last_message.get('timestamp', datetime.now().isoformat()),
                    'last_message_preview': preview
                }
                
                await db.update(f"chat:{chat_id}", update_data)
            
            return created_messages
        
        created_messages = await run_async(_create_messages_batch())
        
        if created_messages:
            return {
                'message': f'{len(created_messages)} messages added successfully',
                'messages': created_messages
            }
        else:
            raise HTTPException(status_code=500, detail="批量添加消息失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"批量添加消息时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量添加消息失败: {str(e)}")
