"""
彩虹城AI-Agent对话管理系统API路由 - FastAPI版本
"""

from fastapi import APIRouter, HTTPException, Depends, Request, File, UploadFile, Form, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
import json
import os
import uuid
import base64
import mimetypes
import logging
from datetime import datetime

from app.agent.ai_assistant import AIAssistant
from app.agent.image_processor import ImageData
from app.agent.file_processor import handle_file_upload
from app.routes.auth_routes import get_current_user

# 配置日志
logging.basicConfig(level=logging.DEBUG)

# 创建路由器
router = APIRouter(prefix="/chat/agent", tags=["AI-Agent对话"])

# 创建AI助手实例
assistant = AIAssistant(model_name="gpt-3.5-turbo")

# 定义请求和响应模型
class Message(BaseModel):
    role: str
    content: str
    type: Optional[str] = "text"

class ChatRequest(BaseModel):
    messages: List[Message] = Field(default_factory=list)
    session_id: Optional[str] = None
    turn_id: Optional[str] = None
    user_id: Optional[str] = "anonymous"
    ai_id: Optional[str] = "ai_rainbow_city"
    image_data: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    session_id: str
    message: Optional[str] = None
    response: Optional[str] = None
    error: Optional[str] = None
    logs: Optional[List[Dict[str, Any]]] = None
    history: Optional[List[Dict[str, Any]]] = None

class HistoryResponse(BaseModel):
    success: bool
    session_id: str
    history: List[Dict[str, Any]]
    error: Optional[str] = None

class LogsResponse(BaseModel):
    success: bool
    session_id: str
    logs: List[Dict[str, Any]]
    error: Optional[str] = None

class ClearSessionResponse(BaseModel):
    success: bool
    session_id: str
    message: str
    error: Optional[str] = None

@router.post("", response_model=ChatResponse)
async def chat_agent(chat_data: ChatRequest):
    """AI-Agent聊天接口"""
    try:
        # 获取请求数据
        messages = chat_data.messages
        session_id = chat_data.session_id or str(uuid.uuid4())
        turn_id = chat_data.turn_id or str(uuid.uuid4())
        user_id = chat_data.user_id
        ai_id = chat_data.ai_id
        image_data = chat_data.image_data
        
        # 提取用户最后一条消息作为输入
        user_message = ""
        if messages:
            user_messages = [msg for msg in messages if msg.role == "user"]
            if user_messages:
                user_message = user_messages[-1].content
        
        # 创建AI助手实例
        ai_assistant = AIAssistant()
        
        # 处理用户查询
        result = ai_assistant.process_query(
            user_input=user_message,
            session_id=session_id,
            user_id=user_id,
            ai_id=ai_id,
            image_data=image_data
        )
        
        # 添加会话ID和轮次ID到响应
        if isinstance(result, dict):
            # 添加 success 字段
            result["success"] = True
            result["session_id"] = session_id
            if "response" in result and isinstance(result["response"], dict):
                if "metadata" not in result["response"]:
                    result["response"]["metadata"] = {}
                result["response"]["metadata"]["session_id"] = session_id
                result["response"]["metadata"]["turn_id"] = turn_id
        
        return result
    except Exception as e:
        logging.error(f"AI-Agent聊天接口错误: {str(e)}")
        return {
            "success": False,
            "session_id": chat_data.session_id or str(uuid.uuid4()),
            "error": str(e)
        }

@router.post("/with_file", response_model=ChatResponse)
async def chat_with_file(
    request: Request,
    user_input: Optional[str] = Form(None),  # 改为可选
    session_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form("anonymous"),
    ai_id: Optional[str] = Form("ai_rainbow_city"),
    file: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    document: Optional[UploadFile] = File(None)
):
    """带文件的AI-Agent聊天接口，支持图片、音频、视频和文档"""
    try:
        logging.debug("Received chat_with_file request")
        
        # 记录请求头信息，帮助诊断问题
        content_type = request.headers.get('content-type', 'unknown')
        content_length = request.headers.get('content-length', 'unknown')
        logging.debug(f"Request Content-Type: {content_type}")
        logging.debug(f"Request Content-Length: {content_length}")
        
        # 如果没有提供session_id，则生成一个新的
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # 处理 user_input 可能为 None 的情况
        if user_input is None:
            user_input = ""
            logging.debug("No user_input provided, using empty string")
        else:
            logging.debug(f"User message: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")
            
        logging.debug(f"Session ID: {session_id}")
        
        # 处理文件
        file_data = None
        file_type = None
        file_info = None
        
        # 检查所有可能的文件字段
        for file_field, file_obj in [
            ('file', file), ('image', image), ('audio', audio), 
            ('video', video), ('document', document)
        ]:
            if file_obj and file_obj.filename:
                logging.debug(f"Processing {file_field} file: {file_obj.filename}, content-type: {file_obj.content_type}")
                try:
                    # 读取文件内容
                    file_content = await file_obj.read()
                    logging.debug(f"File size: {len(file_content)} bytes")
                    
                    # 处理文件上传
                    file_info = handle_file_upload(
                        file_content,
                        file_obj.filename,
                        file_obj.content_type
                    )
                    
                    if file_info:
                        logging.debug(f"File upload successful: {file_info}")
                        # 确定文件类型
                        file_type = file_info['file_type']
                        logging.debug(f"Detected file type: {file_type}")
                        
                        # Base64编码
                        file_base64 = base64.b64encode(file_content).decode('utf-8')
                        # 添加数据URL前缀
                        mime_type = file_obj.content_type or mimetypes.guess_type(file_obj.filename)[0] or 'application/octet-stream'
                        file_data = f"data:{mime_type};base64,{file_base64}"
                        logging.debug(f"Created data URL with mime-type: {mime_type}")
                        break
                    else:
                        logging.error(f"File upload returned no info for {file_obj.filename}")
                except Exception as e:
                    logging.exception(f"Error processing file {file_obj.filename}: {str(e)}")
                    return {
                        "success": False,
                        "session_id": session_id,
                        "error": f"文件处理失败: {str(e)}"
                    }
        
        logging.debug(f"File processing complete. File type: {file_type}, File data present: {file_data is not None}")
        
        # 创建AI助手实例
        ai_assistant = AIAssistant()
        logging.debug("Created AI Assistant instance")
        
        # 准备文件数据参数
        file_data_param = None
        if file_data:
            file_data_param = {
                'type': file_type,
                'data': file_data,
                'info': file_info
            }
            logging.debug(f"Prepared file data parameter with type: {file_type}")
        
        # 处理用户查询
        logging.debug("Calling AI Assistant process_query")
        result = ai_assistant.process_query(
            user_input=user_input,
            session_id=session_id,
            user_id=user_id,
            ai_id=ai_id,
            image_data=file_data if file_type == 'image' else None,
            file_data=file_data_param
        )
        logging.debug(f"AI Assistant process_query completed with result keys: {result.keys() if result else 'None'}")
        
        # 确保结果中包含 success 字段
        if isinstance(result, dict):
            if 'success' not in result:
                result['success'] = True
        else:
            # 如果结果不是字典，创建一个新的字典
            result = {
                'success': True,
                'session_id': session_id,
                'response': str(result)
            }
            
        return result
    except Exception as e:
        logging.error(f"带文件的AI-Agent聊天接口错误: {str(e)}")
        return {
            "success": False,
            "session_id": session_id,
            "error": str(e)
        }

@router.post("/with_image", response_model=ChatResponse)
async def chat_with_image(
    request: Request,
    user_input: Optional[str] = Form(None),  # 改为可选，与 chat_with_file 保持一致
    session_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form("anonymous"),
    ai_id: Optional[str] = Form("ai_rainbow_city"),
    image: Optional[UploadFile] = File(None)
):
    """带图片的AI-Agent聊天接口（兼容旧版本）"""
    result = await chat_with_file(
        request=request,
        user_input=user_input,
        session_id=session_id,
        user_id=user_id,
        ai_id=ai_id,
        file=None,
        image=image,
        audio=None,
        video=None,
        document=None
    )
    
    # 确保结果中包含 success 字段
    if isinstance(result, dict) and 'success' not in result:
        result['success'] = True
    
    return result

@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str):
    """获取会话历史"""
    try:
        history = assistant.get_conversation_history(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "history": history
        }
        
    except Exception as e:
        logging.error(f"获取会话历史时出错: {str(e)}")
        return {
            "success": False,
            "session_id": session_id,
            "history": [],
            "error": str(e)
        }

@router.get("/logs/{session_id}", response_model=LogsResponse)
async def get_logs(session_id: str):
    """获取会话日志"""
    try:
        logs = assistant.get_session_logs(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "logs": logs
        }
        
    except Exception as e:
        logging.error(f"获取会话日志时出错: {str(e)}")
        return {
            "success": False,
            "session_id": session_id,
            "logs": [],
            "error": str(e)
        }

@router.post("/clear/{session_id}", response_model=ClearSessionResponse)
async def clear_session(session_id: str):
    """清除会话数据"""
    try:
        success = assistant.clear_session(session_id)
        
        return {
            "success": success,
            "session_id": session_id,
            "message": "会话数据已清除" if success else "未找到指定会话"
        }
        
    except Exception as e:
        logging.error(f"清除会话数据时出错: {str(e)}")
        return {
            "success": False,
            "session_id": session_id,
            "message": "清除会话数据失败",
            "error": str(e)
        }
