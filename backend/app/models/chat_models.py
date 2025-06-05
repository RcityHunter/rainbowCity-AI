"""
聊天记录数据模型
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

class ChatMessage(BaseModel):
    """聊天消息模型"""
    id: Optional[str] = None
    session_id: str  # 会话ID，标识一个对话窗口
    user_id: str  # 用户ID，对应用户账号
    role: str  # 消息角色：用户账号 或 用户账号_aiR (AI回复)
    content: str  # 消息内容
    content_type: str = "text"  # 消息类型：text, image, audio, video, document
    metadata: Optional[Dict[str, Any]] = None  # 元数据，如图片URL、文件信息等
    created_at: Optional[str] = None  # 创建时间
    
class ChatSession(BaseModel):
    """聊天会话模型"""
    id: Optional[str] = None
    session_id: str  # 会话ID
    user_id: str  # 用户ID
    title: str  # 会话标题，通常是对话的摘要或首条消息的简短描述
    last_message: Optional[str] = None  # 最后一条消息内容
    last_message_time: Optional[str] = None  # 最后一条消息时间
    message_count: int = 0  # 消息数量
    created_at: Optional[str] = None  # 创建时间
    updated_at: Optional[str] = None  # 更新时间

class ChatHistoryResponse(BaseModel):
    """聊天历史响应模型"""
    success: bool
    session_id: str
    messages: List[ChatMessage]
    error: Optional[str] = None
    
class ChatSessionsResponse(BaseModel):
    """聊天会话列表响应模型"""
    success: bool
    sessions: List[ChatSession]
    error: Optional[str] = None
