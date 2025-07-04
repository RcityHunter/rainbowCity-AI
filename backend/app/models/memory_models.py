"""
记忆系统数据模型 - 定义分层记忆系统的数据结构
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
import numpy as np


class MemoryType(str, Enum):
    """记忆类型枚举"""
    CHAT_HISTORY = "chat_history"  # 第一层：聊天历史
    USER_MEMORY = "user_memory"    # 第二层：用户记忆
    SESSION_SUMMARY = "session_summary"  # 第三层：会话摘要


class MemoryImportance(int, Enum):
    """记忆重要性枚举"""
    LOW = 1    # 低重要性
    MEDIUM = 2  # 中等重要性
    HIGH = 3    # 高重要性
    CRITICAL = 4  # 关键重要性


class ChatHistoryMemory(BaseModel):
    """聊天历史记忆模型（第一层）"""
    id: str  # 记忆ID
    session_id: str  # 会话ID
    user_id: str  # 用户ID
    messages: List[Dict[str, Any]]  # 消息列表
    created_at: str  # 创建时间
    updated_at: str  # 更新时间
    embedding: Optional[List[float]] = None  # 向量嵌入
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)  # 元数据


class UserMemory(BaseModel):
    """用户记忆模型（第二层）"""
    id: str  # 记忆ID
    user_id: str  # 用户ID
    content: str  # 记忆内容
    memory_type: str  # 记忆类型（如：偏好、事实、关系等）
    importance: MemoryImportance = MemoryImportance.MEDIUM  # 重要性
    source_session_id: Optional[str] = None  # 来源会话ID
    created_at: str  # 创建时间
    updated_at: str  # 更新时间
    last_accessed: Optional[str] = None  # 最后访问时间
    access_count: int = 0  # 访问次数
    embedding: Optional[List[float]] = None  # 向量嵌入
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)  # 元数据


class SessionSummary(BaseModel):
    """会话摘要模型（第三层）"""
    id: str  # 摘要ID
    session_id: str  # 会话ID
    user_id: str  # 用户ID
    summary: str  # 摘要内容
    start_time: str  # 会话开始时间
    end_time: str  # 会话结束时间
    topics: List[str] = Field(default_factory=list)  # 讨论的主题
    key_points: List[str] = Field(default_factory=list)  # 关键点
    created_at: str  # 创建时间
    embedding: Optional[List[float]] = None  # 向量嵌入
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)  # 元数据


class MemoryQuery(BaseModel):
    """记忆查询模型"""
    user_id: str  # 用户ID
    query: str  # 查询内容
    memory_type: Optional[MemoryType] = None  # 记忆类型
    limit: int = 10  # 限制返回的记忆数量
    offset: int = 0  # 记忆偏移量
    sort_by: str = "relevance"  # 排序方式：relevance（相关性）, recency（最近）, importance（重要性）, vector（向量相似度）
    use_vector_search: bool = True  # 是否使用向量搜索
    metadata_filter: Optional[Dict[str, Any]] = None  # 元数据过滤条件
    embedding: Optional[List[float]] = None  # 查询的向量嵌入（如果已经生成）
    session_id: Optional[str] = None  # 会话ID（可选）
    tags: Optional[List[str]] = None  # 标签列表（可选）
