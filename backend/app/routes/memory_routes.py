"""
记忆系统API路由 - 提供记忆系统的HTTP接口
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import time

from app.services.memory_service import MemoryService
from app.services.memory_manager import MemoryManager
from app.models.memory_models import MemoryType, MemoryImportance, MemoryQuery

# 创建API路由器
router = APIRouter(tags=["记忆系统"])

# 创建记忆管理器实例
memory_manager = MemoryManager()

# 定义请求和响应模型
class UserMemoryRequest(BaseModel):
    user_id: str
    content: str
    memory_type: str
    importance: Optional[int] = 2
    source_session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SessionSummaryRequest(BaseModel):
    session_id: str
    user_id: str
    summary: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    topics: Optional[List[str]] = None
    key_points: Optional[List[str]] = None

class MemoryQueryRequest(BaseModel):
    user_id: Optional[str] = None
    query: Optional[str] = None
    memory_type: Optional[str] = None
    limit: Optional[int] = 10
    offset: Optional[int] = 0
    sort_by: Optional[str] = "recency"
    metadata_filter: Optional[Dict[str, Any]] = None

# API端点
@router.post("/memories/user", response_model=Dict[str, Any])
async def create_user_memory(request: UserMemoryRequest):
    """创建或更新用户记忆"""
    try:
        memory = await MemoryService.save_user_memory(
            user_id=request.user_id,
            content=request.content,
            memory_type=request.memory_type,
            importance=request.importance,
            source_session_id=request.source_session_id,
            metadata=request.metadata
        )
        return {"success": True, "memory": memory}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建用户记忆失败: {str(e)}")

@router.post("/memories/summary", response_model=Dict[str, Any])
async def create_session_summary(request: SessionSummaryRequest):
    """创建或更新会话摘要"""
    try:
        summary = await MemoryService.save_session_summary(
            session_id=request.session_id,
            user_id=request.user_id,
            summary=request.summary,
            start_time=request.start_time,
            end_time=request.end_time,
            topics=request.topics,
            key_points=request.key_points
        )
        return {"success": True, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话摘要失败: {str(e)}")

@router.post("/memories/search", response_model=Dict[str, Any])
async def search_memories(request: MemoryQueryRequest):
    """搜索记忆"""
    try:
        query = MemoryQuery(
            user_id=request.user_id,
            query=request.query,
            memory_type=request.memory_type,
            limit=request.limit,
            offset=request.offset,
            sort_by=request.sort_by,
            metadata_filter=request.metadata_filter
        )
        memories = await MemoryService.search_memories(query)
        return {"success": True, "memories": memories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索记忆失败: {str(e)}")

@router.get("/memories/user/{user_id}", response_model=Dict[str, Any])
async def get_user_memories(
    user_id: str,
    memory_type: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
):
    """获取用户记忆"""
    try:
        query = MemoryQuery(
            user_id=user_id,
            memory_type=memory_type,
            limit=limit,
            offset=offset,
            sort_by="recency"
        )
        memories = await MemoryService.search_memories(query)
        return {"success": True, "memories": memories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户记忆失败: {str(e)}")

@router.get("/memories/session/{session_id}", response_model=Dict[str, Any])
async def get_session_memories(session_id: str):
    """获取会话相关的所有记忆"""
    try:
        # 获取聊天历史
        chat_history = await MemoryService.get_chat_history(session_id)
        
        # 获取会话摘要
        summary = await MemoryService.get_session_summary(session_id)
        
        # 获取从该会话提取的用户记忆
        query = MemoryQuery(
            metadata_filter={"source_session_id": session_id},
            sort_by="recency"
        )
        user_memories = await MemoryService.search_memories(query)
        
        return {
            "success": True,
            "chat_history": chat_history,
            "summary": summary,
            "user_memories": user_memories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话记忆失败: {str(e)}")

@router.delete("/memories/user/{memory_id}", response_model=Dict[str, Any])
async def delete_user_memory(memory_id: str):
    """删除用户记忆"""
    try:
        success = await MemoryService.delete_memory(memory_id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除用户记忆失败: {str(e)}")

@router.delete("/memories/session/{session_id}", response_model=Dict[str, Any])
async def delete_session_memories(session_id: str):
    """删除会话相关的所有记忆"""
    try:
        success = await MemoryService.delete_session_memories(session_id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除会话记忆失败: {str(e)}")

@router.post("/memories/process", response_model=Dict[str, Any])
async def process_conversation(
    session_id: str,
    user_id: str,
    extract_memories: bool = True,
    generate_summary: bool = False
):
    """处理对话，提取记忆和生成摘要"""
    try:
        # 获取会话消息
        chat_history = await MemoryService.get_chat_history(session_id)
        if not chat_history or "messages" not in chat_history:
            raise HTTPException(status_code=404, detail="未找到会话历史")
            
        messages = chat_history["messages"]
        
        # 处理对话
        result = await memory_manager.process_conversation(
            session_id=session_id,
            user_id=user_id,
            messages=messages,
            extract_memories=extract_memories,
            generate_summary=generate_summary
        )
        
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理对话失败: {str(e)}")

@router.get("/memories/enhance", response_model=Dict[str, Any])
async def enhance_with_memories(
    user_id: str,
    query: str,
    session_id: Optional[str] = None
):
    """使用记忆增强上下文"""
    try:
        result = await memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query=query,
            limit=5
        )
        
        # 如果提供了会话ID，也获取会话摘要
        session_summary = None
        if session_id:
            session_summary = await MemoryService.get_session_summary(session_id)
            
        # 构建增强上下文
        context = ""
        if session_summary:
            context += f"当前对话摘要: {session_summary.get('summary', '')}\n\n"
            
        if result:
            context += "用户相关信息:\n"
            for i, memory in enumerate(result, 1):
                memory_content = memory.get("content", "")
                memory_type = memory.get("memory_type", "")
                context += f"{i}. {memory_content} ({memory_type})\n"
                
        return {
            "success": True,
            "relevant_memories": result,
            "session_summary": session_summary,
            "enhanced_context": context.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"增强上下文失败: {str(e)}")

# 健康检查端点
@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "记忆系统正常运行"}
