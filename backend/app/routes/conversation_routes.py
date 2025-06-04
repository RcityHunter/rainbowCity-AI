"""
对话管理路由 - FastAPI版本
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Body, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import logging

from app.db import create, query, update, run_async, get_db
from app.routes.auth_routes import get_current_user

# 创建路由器
router = APIRouter(prefix="/conversations", tags=["对话管理"])

# 定义请求和响应模型
class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ConversationCreate(BaseModel):
    title: str
    messages: List[Message] = []

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    messages: Optional[List[Message]] = None

class Conversation(BaseModel):
    id: str
    user_id: str
    title: str
    preview: Optional[str] = None
    messages: List[Message]
    created_at: str
    last_updated: str

class ConversationResponse(BaseModel):
    message: str
    conversation: Conversation

class ConversationsResponse(BaseModel):
    conversations: List[Conversation]

class MessageResponse(BaseModel):
    message: str

@router.get("", response_model=ConversationsResponse)
async def get_conversations(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取用户的所有对话"""
    user_id = current_user.get('id')
    
    try:
        async def _get_conversations():
            try:
                db = await get_db()
                if db is None:
                    logging.warning("数据库连接为空，返回空列表")
                    return []
                
                # 先尝试直接查询
                try:
                    query_str = f"SELECT * FROM conversations WHERE user_id = '{user_id}'"
                    logging.debug(f"Direct SQL query: {query_str}")
                    result = await db.query(query_str)
                    
                    logging.debug(f"查询结果: {result}")
                    
                    if result and isinstance(result, list) and len(result) > 0:
                        if 'result' in result[0]:
                            return result[0]['result']
                        elif isinstance(result[0], list):
                            return result[0]
                        else:
                            return result
                except Exception as e:
                    logging.error(f"第一种查询方式出错: {str(e)}")
                
                # 尝试第二种查询方式
                try:
                    logging.debug("尝试第二种查询方式...")
                    result = await db.query(f"SELECT * FROM conversations")
                    logging.debug(f"全表查询结果: {result}")
                    
                    if result and isinstance(result, list) and len(result) > 0:
                        if 'result' in result[0]:
                            all_conversations = result[0]['result']
                            # 手动过滤用户ID
                            return [conv for conv in all_conversations if conv.get('user_id') == user_id]
                except Exception as e:
                    logging.error(f"第二种查询方式出错: {str(e)}")
                
                # 如果前两种方式都失败，尝试直接获取所有记录然后在应用层过滤
                try:
                    logging.debug("尝试获取所有记录...")
                    all_records = await db.select("conversations")
                    logging.debug(f"所有记录: {all_records}")
                    
                    if all_records and isinstance(all_records, list):
                        # 手动过滤用户ID
                        return [conv for conv in all_records if conv.get('user_id') == user_id]
                except Exception as e:
                    logging.error(f"第三种查询方式出错: {str(e)}")
                
                return []
            except Exception as e:
                logging.error(f"获取对话时出错: {str(e)}")
                return []
        
        conversations = await run_async(_get_conversations())
        
        # 如果没有找到对话，返回空列表
        if not conversations:
            return {"conversations": []}
        
        # 处理返回结果
        for conv in conversations:
            # 确保每个对话都有ID
            if 'id' not in conv and 'key' in conv:
                conv['id'] = conv['key'].split(':')[1] if ':' in conv['key'] else conv['key']
            
            # 确保消息列表存在
            if 'messages' not in conv:
                conv['messages'] = []
        
        return {"conversations": conversations}
    except Exception as e:
        logging.error(f"获取对话列表时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取对话列表失败: {str(e)}")

@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """创建新对话"""
    try:
        user_id = current_user.get('id')
        
        # 准备对话数据
        title = conversation_data.title
        messages = [msg.dict() for msg in conversation_data.messages]
        
        # 生成预览文本
        preview = ''
        if messages and len(messages) > 0:
            for msg in messages:
                if msg.get('role') == 'assistant' and msg.get('content'):
                    preview = msg.get('content')[:50] + '...' if len(msg.get('content')) > 50 else msg.get('content')
                    break
            
            if not preview and messages[0].get('content'):
                preview = messages[0].get('content')[:50] + '...' if len(messages[0].get('content')) > 50 else messages[0].get('content')
        
        # 创建对话记录
        new_conversation = {
            'user_id': user_id,
            'title': title,
            'preview': preview,
            'messages': messages,
            'created_at': datetime.utcnow().isoformat(),
            'last_updated': datetime.utcnow().isoformat()
        }
        
        conversation = create('conversations', new_conversation)
        
        return {
            'message': 'Conversation created successfully',
            'conversation': conversation
        }
    except Exception as e:
        logging.error(f"创建对话时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建对话失败: {str(e)}")

@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str = Path(..., description="对话ID"),
    conversation_data: ConversationUpdate = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """更新对话"""
    try:
        user_id = current_user.get('id')
        
        # 检查对话是否属于当前用户
        conversations = query('conversations', {'id': f'conversations:{conversation_id}'})
        if not conversations or len(conversations) == 0:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        conversation = conversations[0]
        if conversation.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="无权操作此对话")
        
        # 准备更新数据
        update_data = {}
        
        if conversation_data.title is not None:
            update_data['title'] = conversation_data.title
        
        if conversation_data.messages is not None:
            messages = [msg.dict() for msg in conversation_data.messages]
            update_data['messages'] = messages
            
            # 更新预览文本
            preview = ''
            if messages and len(messages) > 0:
                for msg in messages:
                    if msg.get('role') == 'assistant' and msg.get('content'):
                        preview = msg.get('content')[:50] + '...' if len(msg.get('content')) > 50 else msg.get('content')
                        break
                
                if not preview and messages[0].get('content'):
                    preview = messages[0].get('content')[:50] + '...' if len(messages[0].get('content')) > 50 else messages[0].get('content')
            
            if preview:
                update_data['preview'] = preview
        
        # 更新最后修改时间
        update_data['last_updated'] = datetime.utcnow().isoformat()
        
        # 更新对话
        updated_conversation = update('conversations', conversation_id, update_data)
        
        return {
            'message': 'Conversation updated successfully',
            'conversation': updated_conversation
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"更新对话时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新对话失败: {str(e)}")

@router.delete("/{conversation_id}", response_model=MessageResponse)
async def delete_conversation(
    conversation_id: str = Path(..., description="对话ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """删除对话"""
    try:
        user_id = current_user.get('id')
        
        # 检查对话是否属于当前用户
        conversations = query('conversations', {'id': f'conversations:{conversation_id}'})
        if not conversations or len(conversations) == 0:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        conversation = conversations[0]
        if conversation.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="无权操作此对话")
        
        # 删除对话
        async def _delete():
            try:
                db = await get_db()
                if db is None:
                    return False
                
                await db.delete(f"conversations:{conversation_id}")
                return True
            except Exception as e:
                logging.error(f"删除对话时数据库操作出错: {str(e)}")
                return False
        
        result = await run_async(_delete())
        
        if result:
            return {"message": "Conversation deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="删除对话失败")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"删除对话时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除对话失败: {str(e)}")
