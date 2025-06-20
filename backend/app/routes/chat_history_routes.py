"""
聊天历史记录API路由 - FastAPI版本
实现单用户与AI聊天的历史记录存储和检索功能
"""

from fastapi import APIRouter, HTTPException, Depends, Path, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union, Set
import time
import json
from datetime import datetime
import logging

from app.db import create, query, update, run_async, get_db
from app.routes.auth_routes import get_current_user
from app.utils.chat_utils import ensure_chat_id_format

# 创建路由器
router = APIRouter(prefix="/chats", tags=["聊天历史"])

# 定义请求和响应模型
class MessageCreate(BaseModel):
    role: str = Field(..., description="消息角色，如 'user', 'assistant', 'system'")
    content: str = Field(..., description="消息内容")
    type: Optional[str] = Field(None, description="消息类型，如 'text'")
    token_count: Optional[int] = Field(None, description="消息的token数量")
    metadata: Optional[Dict[str, Any]] = Field(None, description="消息的元数据")
    timestamp: Optional[str] = Field(None, description="消息的时间戳")

class ChatCreate(BaseModel):
    title: str = Field("新聊天", description="聊天会话标题")
    model_used: str = Field("gpt-4-turbo", description="使用的模型")
    last_message_preview: Optional[str] = Field(None, description="最后一条消息的预览")
    messages: Optional[List[Dict[str, Any]]] = Field(None, description="消息列表")  # 使用Dict而不是MessageCreate以增加灵活性

class ChatUpdate(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None
    model_used: Optional[str] = None
    last_message_preview: Optional[str] = None

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
    timestamp: Optional[str] = None  # 修改为可选字段
    token_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    message: str
    id: Optional[str] = None
    title: Optional[str] = None
    preview: Optional[str] = None
    lastUpdated: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None

class Conversation(BaseModel):
    id: str
    title: str
    preview: str
    lastUpdated: str
    is_pinned: Optional[bool] = False
    is_archived: Optional[bool] = False
    messages: Optional[List[Dict[str, Any]]] = None

class ChatsResponse(BaseModel):
    conversations: List[Conversation]

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

@router.get("")
async def get_user_chats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取当前用户的所有聊天会话"""
    user_id = current_user.get('id')
    
    try:
        # 使用query函数查询用户的所有未归档聊天
        chats = await query('chat', {'user_id': user_id, 'is_archived': False})
        
        # 按最后消息时间和置顶状态排序
        if chats:
            # 先按置顶状态排序
            pinned = [chat for chat in chats if chat.get('is_pinned')]
            not_pinned = [chat for chat in chats if not chat.get('is_pinned')]
            
            # 然后按最后消息时间排序
            pinned.sort(key=lambda x: x.get('last_message_at', ''), reverse=True)
            not_pinned.sort(key=lambda x: x.get('last_message_at', ''), reverse=True)
            
            # 合并结果
            chats = pinned + not_pinned
        
        # 处理查询结果并转换为前端期望的格式
        conversations = []
        if chats:
            for chat in chats:
                conversation = {
                    "id": chat.get("id"),
                    "title": chat.get("title", "新对话"),
                    "preview": chat.get("last_message_preview", ""),
                    "lastUpdated": chat.get("last_message_at", ""),
                    # 可选字段
                    "is_pinned": chat.get("is_pinned", False),
                    "is_archived": chat.get("is_archived", False)
                }
                conversations.append(conversation)
        
        return {"conversations": conversations}
            
    except Exception as e:
        logging.error(f"获取聊天列表时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取聊天列表失败: {str(e)}")

@router.post("", status_code=201)
async def create_chat(
    chat_data: ChatCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # 打印请求数据以便调试
    logging.info(f"Received chat_data: {chat_data}")
    
    # 确保messages是列表类型
    if not isinstance(chat_data.messages, list):
        logging.warning(f"chat_data.messages is not a list, it's {type(chat_data.messages)}")
        chat_data.messages = []
        
    if chat_data.messages:
        logging.info(f"Number of messages: {len(chat_data.messages)}")
        for i, msg in enumerate(chat_data.messages):
            if not isinstance(msg, dict):
                logging.warning(f"Message {i} is not a dict, it's {type(msg)}")
                continue
            content = msg.get('content', '')
            content_preview = str(content)[:30] if not isinstance(content, dict) else str(content)[:30]
            logging.info(f"Message {i}: role={msg.get('role')}, type={msg.get('type')}, content={content_preview}...")
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
        
        result = await create('chat', new_chat)
        
        # 增强对result的检查
        if not result:
            logging.error("Create chat returned empty result")
            raise HTTPException(status_code=500, detail="创建聊天会话失败，服务器返回空结果")
            
        # 记录结果类型以便调试
        logging.info(f"DB Create - Result type: {type(result)}")
        logging.info(f"DB Create - Result: {result}")
        
        # 处理字典结果
        if isinstance(result, dict):
            chat_result = result
            chat_id = result.get('id')
            if not chat_id:
                logging.error("Create chat result missing 'id' field")
                raise HTTPException(status_code=500, detail="创建聊天会话失败，缺少ID字段")
        # 处理列表结果(兼容旧版本)
        elif isinstance(result, list) and len(result) > 0:
            first_result = result[0]
            if not isinstance(first_result, dict):
                logging.error(f"Create chat result[0] is not a dict: {type(first_result)}")
                raise HTTPException(status_code=500, detail="创建聊天会话失败，返回结果不是字典类型")
                
            chat_id = first_result.get('id')
            if not chat_id:
                logging.error("Create chat result missing 'id' field")
                raise HTTPException(status_code=500, detail="创建聊天会话失败，缺少ID字段")
                
            chat_result = first_result
        else:
            logging.error(f"Create chat returned unexpected result type: {type(result)}")
            raise HTTPException(status_code=500, detail="创建聊天会话失败，返回结果格式错误")
        
        # 如果有消息，批量创建
        if isinstance(chat_data.messages, list) and len(chat_data.messages) > 0:
            try:
                # 初始化默认值
                last_message_content = ""
                last_timestamp = datetime.now().isoformat()
                
                # 过滤出有效的消息（字典类型）
                valid_messages = [msg for msg in chat_data.messages if isinstance(msg, dict)]
                
                if valid_messages:
                    # 记录最后一条有效消息的内容和时间戳，用于更新聊天会话
                    last_message = valid_messages[-1]
                    # 安全地获取内容和时间戳
                    content_value = last_message.get('content')
                    if isinstance(content_value, (dict, list)):
                        try:
                            last_message_content = json.dumps(content_value)
                        except:
                            last_message_content = str(content_value)
                    else:
                        last_message_content = str(content_value) if content_value is not None else ""
                    
                    last_timestamp = last_message.get('timestamp', datetime.now().isoformat())
                
                # 批量创建消息
                for msg in valid_messages:
                    try:
                        # 创建消息数据
                        content = msg.get('content')
                        # 如果内容是字典或其他复杂对象，转换为JSON字符串
                        if isinstance(content, (dict, list)):
                            try:
                                content_str = json.dumps(content)
                            except Exception as json_err:
                                logging.error(f"Failed to convert content to JSON: {str(json_err)}")
                                content_str = str(content)
                        else:
                            content_str = str(content) if content is not None else ''
                            
                        message_data = {
                            'chat_id': chat_id,
                            'session_id': chat_id,  # 使用chat_id作为session_id
                            'role': msg.get('role', 'user'),
                            'content': content_str
                        }
                    except Exception as msg_prep_err:
                        logging.error(f"Error preparing message data: {str(msg_prep_err)}")
                        continue
                    
                    # 添加可选字段
                    if 'type' in msg:
                        message_data['content_type'] = msg.get('type')
                    
                    if 'token_count' in msg:
                        message_data['token_count'] = msg.get('token_count')
                    
                    if 'metadata' in msg:
                        message_data['metadata'] = msg.get('metadata', {})
                        
                    # 创建消息 - 使用message表而不chat_messages表
                    try:
                        await create('message', message_data)
                        logging.info(f"Message created successfully for chat: {chat_id}")
                    except Exception as msg_err:
                        logging.error(f"Failed to create message: {str(msg_err)}")
                        # 继续处理下一条消息，不中断整个批处理
                    
                # 更新聊天会话的最后一条消息预览和时间戳
                update_data = {
                    'last_message_preview': str(last_message_content)[:50] if last_message_content else "",  # 只取前50个字符
                    'last_message_at': last_timestamp
                }
                
                # 安全地更新数据库
                try:
                    await update('chat', chat_id, update_data)
                except Exception as db_err:
                    logging.error(f"Failed to update chat in database: {str(db_err)}")
                
                # 更新返回结果中的chat对象
                try:
                    if isinstance(chat_result, dict):
                        chat_result.update(update_data)
                    else:
                        logging.warning(f"chat_result is not a dict, it's {type(chat_result)}")
                        # 创建一个新的字典作为chat_result
                        chat_result = {
                            'id': chat_id,
                            'title': chat_data.title,
                            'last_message_preview': str(last_message_content)[:50] if last_message_content else "",
                            'last_message_at': last_timestamp
                        }
                except Exception as update_err:
                    logging.error(f"Failed to update chat_result: {str(update_err)}")
                    # 不中断流程，继续返回结果
            except Exception as e:
                logging.error(f"添加消息时出错: {str(e)}")
                # 即使添加消息失败，我们仍然返回创建的聊天会话
            
            # 确保chat_result是字典类型
            if not isinstance(chat_result, dict):
                chat_result = {
                    'id': chat_id,
                    'title': chat_data.title,
                    'last_message_preview': '',
                    'last_message_at': datetime.now().isoformat()
                }
                
            # 返回格式与前端期望的一致
            try:
                # 确保返回的消息是可序列化的
                messages_to_return = []
                if isinstance(chat_data.messages, list):
                    for msg in chat_data.messages:
                        if isinstance(msg, dict):
                            # 创建一个新字典，只包含必要的字段
                            safe_msg = {
                                'role': msg.get('role', 'user'),
                                'content': msg.get('content', ''),
                            }
                            # 添加可选字段
                            if 'type' in msg:
                                safe_msg['type'] = msg.get('type')
                            if 'timestamp' in msg:
                                safe_msg['timestamp'] = msg.get('timestamp')
                            messages_to_return.append(safe_msg)
                
                return {
                    'message': 'Chat created successfully',
                    'id': chat_id,  # 使用id而不是chat_id
                    'title': chat_data.title,
                    'preview': chat_result.get('last_message_preview', ''),
                    'lastUpdated': chat_result.get('last_message_at', datetime.now().isoformat()),
                    'messages': messages_to_return
                }
            except Exception as return_err:
                logging.error(f"Error preparing return data: {str(return_err)}")
                # 返回最小化的响应
                return {
                    'message': 'Chat created successfully',
                    'id': chat_id,
                    'title': chat_data.title,
                    'preview': '',
                    'lastUpdated': datetime.now().isoformat(),
                    'messages': []
                }
            else:
                raise HTTPException(status_code=500, detail="创建聊天会话失败")
            
    except Exception as e:
        # 更详细的错误日志
        logging.error(f"创建聊天会话时出错: {str(e)}")
        logging.error(f"Error type: {type(e).__name__}")
        logging.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details'}")
        
        # 如果错误是数字或空值，返回更有用的错误信息
        if str(e) == '0' or not str(e):
            raise HTTPException(status_code=500, detail="创建聊天会话失败，请检查服务器日志")
        else:
            raise HTTPException(status_code=500, detail=f"创建聊天会话失败: {str(e)}")

@router.get("/{chat_id}")
async def get_chat(
    chat_id: str = Path(..., description="聊天会话ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """获取特定聊天会话的详情"""
    user_id = current_user.get('id')
    
    try:
        # 查询聊天会话 - 检查ID格式
        chat_id_for_query = chat_id
        # 如果ID已经包含chat:前缀，则直接使用，否则添加前缀
        if chat_id.startswith("chat:"):
            # 从URL中获取的ID可能已经包含前缀，需要去除
            chat_id_for_query = chat_id
        else:
            chat_id_for_query = f"chat:{chat_id}"
        logging.info(f"查询聊天会话，ID: {chat_id_for_query}")
        chats = await query("chat", {"id": chat_id_for_query})
        
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
        # 查询聊天会话 - 检查ID格式
        chat_id_for_query = chat_id
        # 如果ID已经包含chat:前缀，则直接使用，否则添加前缀
        if chat_id.startswith("chat:"):
            # 从URL中获取的ID可能已经包含前缀，需要去除
            chat_id_for_query = chat_id
        else:
            chat_id_for_query = f"chat:{chat_id}"
        logging.info(f"查询聊天会话，ID: {chat_id_for_query}")
        chats = await query("chat", {"id": chat_id_for_query})
        
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
        # 查询聊天会话 - 检查ID格式
        chat_id_for_query = chat_id
        # 如果ID已经包含chat:前缀，则直接使用，否则添加前缀
        if chat_id.startswith("chat:"):
            # 从URL中获取的ID可能已经包含前缀，需要去除
            chat_id_for_query = chat_id
        else:
            chat_id_for_query = f"chat:{chat_id}"
        logging.info(f"查询聊天会话，ID: {chat_id_for_query}")
        chats = await query("chat", {"id": chat_id_for_query})
        
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
        # 查询聊天会话 - 检查ID格式
        chat_id_for_query = chat_id
        # 如果ID已经包含chat:前缀，则直接使用，否则添加前缀
        if chat_id.startswith("chat:"):
            # 从URL中获取的ID可能已经包含前缀，需要去除
            chat_id_for_query = chat_id
        else:
            chat_id_for_query = f"chat:{chat_id}"
        logging.info(f"查询聊天会话，ID: {chat_id_for_query}")
        chats = await query("chat", {"id": chat_id_for_query})
        
        if not chats or len(chats) == 0:
            raise HTTPException(status_code=404, detail="聊天会话不存在")
        
        chat = chats[0]
        
        # 验证所有权
        if chat.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="无权访问此聊天会话")
        
        # 查询消息 - 使用辅助函数确保正确的ID格式
        chat_id_with_prefix = ensure_chat_id_format(chat_id)
        logging.info(f"查询消息，chat_id: {chat_id_with_prefix}")
        
        # 先从 message 表查询
        all_messages = await query('message', {'chat_id': chat_id_with_prefix})
        logging.info(f"message表查询结果: {all_messages}")
        logging.info(f"message表查询结果类型: {type(all_messages)}")
        
        # 如果在message表中没有找到，尝试从 chat_messages 表查询
        if not all_messages or len(all_messages) == 0:
            logging.info(f"在message表中没有找到消息，尝试从 chat_messages 表查询")
            try:
                chat_messages = await query('chat_messages', {'session_id': chat_id_with_prefix})
                logging.info(f"chat_messages表查询结果: {chat_messages}")
                
                # 如果在chat_messages表中找到了消息，将其转换为message表的格式
                if chat_messages and len(chat_messages) > 0:
                    all_messages = []
                    for msg in chat_messages:
                        # 转换格式
                        converted_msg = {
                            'id': msg.get('id', f"msg_{int(time.time())}_{id(msg)}"),
                            'chat_id': chat_id_with_prefix,
                            'role': msg.get('role', 'unknown'),
                            'content': msg.get('content', ''),
                            'timestamp': msg.get('created_at', datetime.now().isoformat())
                        }
                        # 添加可选字段
                        if 'metadata' in msg:
                            converted_msg['metadata'] = msg['metadata']
                        if 'token_count' in msg:
                            converted_msg['token_count'] = msg['token_count']
                        
                        all_messages.append(converted_msg)
                    
                    logging.info(f"从 chat_messages 表转换了 {len(all_messages)} 条消息")
            except Exception as e:
                logging.error(f"查询 chat_messages 表出错: {str(e)}")
        
        # 如果仍然没有找到消息，尝试使用原始 SQL 查询
        if not all_messages or len(all_messages) == 0:
            try:
                from app.db import execute_raw_query
                logging.info(f"尝试使用原始 SQL 查询消息")
                # 先查询 message 表
                message_query_result = await execute_raw_query(f"SELECT * FROM message WHERE chat_id = '{chat_id_with_prefix}'")
                logging.info(f"message表原始查询结果: {message_query_result}")
                
                # 如果没有结果，查询 chat_messages 表
                if not message_query_result or len(message_query_result) == 0:
                    chat_messages_query_result = await execute_raw_query(f"SELECT * FROM chat_messages WHERE session_id = '{chat_id_with_prefix}'")
                    logging.info(f"chat_messages表原始查询结果: {chat_messages_query_result}")
                    
                    # 如果在chat_messages表中找到了消息，将其转换为message表的格式
                    if chat_messages_query_result and len(chat_messages_query_result) > 0:
                        all_messages = []
                        for msg in chat_messages_query_result:
                            # 转换格式
                            converted_msg = {
                                'id': msg.get('id', f"msg_{int(time.time())}_{id(msg)}"),
                                'chat_id': chat_id_with_prefix,
                                'role': msg.get('role', 'unknown'),
                                'content': msg.get('content', ''),
                                'timestamp': msg.get('created_at', datetime.now().isoformat())
                            }
                            # 添加可选字段
                            if 'metadata' in msg:
                                converted_msg['metadata'] = msg['metadata']
                            if 'token_count' in msg:
                                converted_msg['token_count'] = msg['token_count']
                            
                            all_messages.append(converted_msg)
                else:
                    all_messages = message_query_result
            except Exception as e:
                logging.error(f"原始 SQL 查询出错: {str(e)}")
        
        total = len(all_messages) if all_messages else 0
        logging.info(f"消息总数: {total}")
        
        # 如果仍然没有消息，记录详细日志
        if total == 0:
            logging.warning(f"没有找到任何消息，尝试查询数据库中的所有消息表")
            try:
                from app.db import execute_raw_query
                message_sample = await execute_raw_query("SELECT * FROM message LIMIT 10")
                chat_messages_sample = await execute_raw_query("SELECT * FROM chat_messages LIMIT 10")
                logging.info(f"message表样本数据: {message_sample}")
                logging.info(f"chat_messages表样本数据: {chat_messages_sample}")
            except Exception as e:
                logging.error(f"查询样本数据出错: {str(e)}")

        
        
        # 计算分页
        offset = (page - 1) * per_page
        
        # 按时间戳排序
        if all_messages:
            # 确保所有消息都有timestamp字段，如果没有则使用当前时间
            for msg in all_messages:
                if 'timestamp' not in msg or not msg['timestamp']:
                    msg['timestamp'] = datetime.now().isoformat()
                    logging.info(f"添加缺失的timestamp字段: {msg['id'] if 'id' in msg else 'unknown'}")
            
            all_messages.sort(key=lambda x: x.get('timestamp', ''))
            
            # 分页获取消息
            messages = all_messages[offset:offset + per_page] if offset < total else []
            
            # 确保所有返回的消息都有必需的字段
            for msg in messages:
                # 确保所有必需字段都存在
                if 'id' not in msg:
                    msg['id'] = f"msg_{int(time.time())}_{id(msg)}"
                if 'role' not in msg:
                    msg['role'] = 'unknown'
                if 'content' not in msg:
                    msg['content'] = ''
        else:
            messages = []
        
        # 计算是否有更多消息
        has_more = (offset + len(messages)) < total
        
        logging.info(f"返回消息数量: {len(messages)}")
        if messages:
            logging.info(f"第一条消息示例: {messages[0]}")
        else:
            logging.info("没有消息返回")
        
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
        
        # 查询聊天会话 - 检查ID格式
        chat_id_for_query = chat_id
        # 如果ID已经包含chat:前缀，则直接使用，否则添加前缀
        if chat_id.startswith("chat:"):
            # 从URL中获取的ID可能已经包含前缀，需要去除
            chat_id_for_query = chat_id
        else:
            chat_id_for_query = f"chat:{chat_id}"
        logging.info(f"查询聊天会话，ID: {chat_id_for_query}")
        chats = await query("chat", {"id": chat_id_for_query})
        
        if not chats or len(chats) == 0:
            raise HTTPException(status_code=404, detail="聊天会话不存在")
        
        chat = chats[0]
        
        # 验证所有权
        if chat.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="无权访问此聊天会话")
        
        # 准备消息数据
        new_message = {
            'chat_id': chat_id_for_query,  # 使用已经格式化的chat_id
            'role': message_data.role,
            'content': message_data.content,
            'timestamp': message_data.timestamp or datetime.now().isoformat()
        }
        
        # 添加可选字段
        if message_data.token_count is not None:
            new_message['token_count'] = message_data.token_count
        
        if message_data.metadata is not None:
            new_message['metadata'] = message_data.metadata
        
        # 创建消息 - 使用异步版本的create函数
        try:
            logging.info(f"尝试创建消息: {new_message}")
            result = await create('message', new_message)  # 使用await关键字
            logging.info(f"消息创建结果: {result}")
            
            if result and (isinstance(result, dict) or (isinstance(result, list) and len(result) > 0)):
                # 处理字典结果
                if isinstance(result, dict):
                    message_id = result.get('id')
                # 处理列表结果
                else:
                    message_id = result[0].get('id')
                
                logging.info(f"消息创建成功，ID: {message_id}")
                
                # 更新聊天会话的最后消息时间和预览
                preview = message_data.content
                if len(preview) > 100:
                    preview = preview[:97] + '...'
                
                update_data = {
                    'last_message_at': new_message['timestamp'],
                    'last_message_preview': preview
                }
                
                # 使用异步版本的update函数
                await update('chat', chat_id_for_query, update_data)  # 使用正确格式的chat_id
                
                # 成功后返回结果
                return {
                    'status': 'Message added successfully',
                    'message_id': message_id,
                    'message': result[0] if isinstance(result, list) else result
                }
            else:
                logging.error(f"消息创建结果为空或无效: {result}")
                raise HTTPException(status_code=500, detail="添加消息失败，服务器返回空结果")
        except Exception as e:
            logging.error(f"创建消息时出错: {str(e)}")
            raise HTTPException(status_code=500, detail=f"添加消息失败: {str(e)}")
            
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
        chats = await query('chat', {'id': f'chat:{chat_id}'})
        
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
