from fastapi import APIRouter, Request, Response, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import os
import time
import uuid
from openai import OpenAI
from dotenv import load_dotenv

# 导入AI-Agent模块
from app.agent.ai_assistant import AIAssistant

# 加载环境变量
load_dotenv()

# 获取OpenAI API密钥
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 初始OpenAI客户端
client = OpenAI(api_key=OPENAI_API_KEY)

# 创建AI-Agent实例
ai_assistant = AIAssistant(model_name="gpt-3.5-turbo")

# 创建API路由器
router = APIRouter(tags=["聊天"])

# 定义可用工具列表
AVAILABLE_TOOLS = [
    {
        "id": "frequency_generator",
        "name": "频率生成器",
        "description": "生成频率编号",
        "parameters": {
            "type": "object",
            "properties": {
                "ai_type": {
                    "type": "string",
                    "description": "AI类型代码"
                },
                "personality": {
                    "type": "string",
                    "description": "人格代码"
                }
            }
        }
    },
    {
        "id": "ai_id_generator",
        "name": "AI-ID生成器",
        "description": "生成AI标识符",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "AI名称"
                }
            }
        }
    },
    {
        "id": "relationship_manager",
        "name": "关系管理器",
        "description": "管理AI关系",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "search", "update"],
                    "description": "关系操作类型"
                }
            }
        }
    }
]

# 定义请求和响应模型
class Message(BaseModel):
    role: str
    content: str
    type: Optional[str] = "text"

class ChatRequest(BaseModel):
    messages: List[Message] = Field(default_factory=list)
    session_id: str = ""
    turn_id: str = ""

class ToolCall(BaseModel):
    id: str
    name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class ResponseMetadata(BaseModel):
    model: str
    created: int
    session_id: str
    turn_id: str

class ResponseContent(BaseModel):
    content: str
    type: str = "text"
    metadata: ResponseMetadata

class ChatResponse(BaseModel):
    success: bool = True
    response: ResponseContent
    tool_calls: Optional[List[ToolCall]] = None

# 添加一个支持工具调用的聊天端点
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        messages = request.messages
        session_id = request.session_id
        turn_id = request.turn_id
        
        # 记录会话信息
        print(f"Session ID: {session_id}, Turn ID: {turn_id}")
        
        # 添加系统消息，定义AI助手的角色和行为
        system_message = Message(
            role="system",
            content="你是彩虹城系统的AI助手，专门解答关于彩虹城系统、频率编号和关系管理的问题。当用户询问关于频率编号、AI-ID或关系管理的问题时，你应该推荐相应的工具。"
        )
        
        # 准备发送给OpenAI的消息
        openai_messages = [{"role": system_message.role, "content": system_message.content}]
        for msg in messages:
            if msg.role in ['user', 'assistant', 'system']:
                message_content = {
                    "role": msg.role,
                    "content": msg.content
                }
                # 如果消息有类型信息，可以在这里处理
                # 例如，对于图片消息，可以使用OpenAI的multi-modal API
                openai_messages.append(message_content)
        
        # 输出调试信息
        print(f"Processing messages: {json.dumps([m.dict() for m in messages[:2]])}...")
        
        # 检查是否需要推荐工具
        should_recommend_tools = False
        last_user_message = ""
        for msg in reversed(messages):
            if msg.role == 'user':
                last_user_message = msg.content.lower()
                break
        
        # 检查用户消息中是否包含触发工具推荐的关键词
        if "频率" in last_user_message or "编号" in last_user_message:
            should_recommend_tools = True
            # 调用OpenAI API获取响应
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=openai_messages,
                tools=AVAILABLE_TOOLS,
                tool_choice="auto"
            )
            
            # 处理响应
            ai_message = response.choices[0].message
            
            # 检查是否有工具调用
            if ai_message.tool_calls:
                # 有工具调用，处理工具调用
                tool_calls = []
                for tool_call in ai_message.tool_calls:
                    tool_calls.append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "parameters": json.loads(tool_call.function.arguments)
                    })
                
                # 返回带有工具调用的响应
                return {
                    "success": True,
                    "response": {
                        "content": ai_message.content,
                        "type": "text",
                        "metadata": {
                            "model": response.model,
                            "created": int(time.time()),
                            "session_id": session_id,
                            "turn_id": turn_id
                        }
                    },
                    "tool_calls": tool_calls
                }
            else:
                # 没有工具调用，返回普通响应
                return {
                    "success": True,
                    "response": {
                        "content": ai_message.content,
                        "type": "text",
                        "metadata": {
                            "model": response.model,
                            "created": int(time.time()),
                            "session_id": session_id,
                            "turn_id": turn_id
                        }
                    }
                }
        else:
            # 不需要工具调用，直接调用OpenAI API获取响应
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=openai_messages
            )
            
            # 处理响应
            ai_message = response.choices[0].message
            
            # 返回普通响应
            return {
                "success": True,
                "response": {
                    "content": ai_message.content,
                    "type": "text",
                    "metadata": {
                        "model": response.model,
                        "created": int(time.time()),
                        "session_id": session_id,
                        "turn_id": turn_id
                    }
                }
            }
            
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"聊天处理失败: {str(e)}")

# 健康检查端点
@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "聊天服务正常运行"}

# 测试端点，返回一个固定的响应
@router.post("/chat-test")
async def chat_test(request: ChatRequest):
    # 生成一个简单的响应
    def generate():
        return {
            "success": True,
            "response": {
                "content": "这是一个测试响应。我是彩虹城AI助手，很高兴为您服务！",
                "type": "text",
                "metadata": {
                    "model": "test-model",
                    "created": int(time.time()),
                    "session_id": request.session_id,
                    "turn_id": request.turn_id
                }
            }
        }
    
    return generate()

# 使用AI-Agent的聊天端点
@router.post("/chat-agent")
async def chat_agent(request: ChatRequest):
    try:
        messages = request.messages
        session_id = request.session_id
        user_id = "user_" + session_id if session_id else "anonymous"
        
        # 获取用户输入
        user_message = next((msg.content for msg in reversed(messages) if msg.role == "user"), "")
        
        if not user_message:
            return JSONResponse(
                status_code=400,
                content={"error": "未找到用户消息"}
            )
        
        # 检查是否有图片消息
        has_image = any(msg.type == "image" for msg in messages if hasattr(msg, "type"))
        
        # 使用AI-Agent处理请求
        try:
            # 设置会话信息
            ai_assistant.context_builder.session_id = session_id
            ai_assistant.context_builder.user_id = user_id
            
            # 处理用户查询
            response = ai_assistant.process_query(user_message)
            
            # 返回响应
            return {
                "success": True,
                "response": {
                    "content": response,
                    "type": "text",
                    "metadata": {
                        "model": "agent-model",
                        "created": int(time.time()),
                        "session_id": session_id,
                        "turn_id": request.turn_id
                    }
                }
            }
        except Exception as e:
            print(f"AI-Agent处理失败: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"AI-Agent处理失败: {str(e)}"}
            )
            
    except Exception as e:
        print(f"聊天处理失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"聊天处理失败: {str(e)}"}
        )

# 简单的聊天端点，直接返回JSON响应，支持工具调用和多模态消息
@router.post("/chat-simple")
async def chat_simple(request: ChatRequest):
    messages = request.messages
    session_id = request.session_id
    turn_id = request.turn_id
    
    # 获取最后一条用户消息
    user_message = ""
    has_image = False
    has_audio = False
    
    for msg in reversed(messages):
        if msg.role == "user":
            user_message = msg.content.lower()
            # 检查是否包含图片或音频
            if hasattr(msg, "type") and msg.type == "image":
                has_image = True
            elif hasattr(msg, "type") and msg.type == "audio":
                has_audio = True
            break
    
    # 预定义的响应
    responses = {
        "你好": "你好！我是彩虹城AI助手，很高兴为您服务。我可以回答关于彩虹城系统、频率编号和关系管理的问题。",
        "彩虹城": "彩虹城是一个AI共生社区系统，旨在促进人类与AI之间的和谐共生关系。系统包括频率编号、关系管理、AI-ID等多个核心功能。",
        "频率编号": "频率编号是彩虹城系统中的重要组成部分，它用于表示AI的频率特性。每个频率编号包含了值代码、序列号、人格代码、AI类型代码和哈希签名等多个部分。你想要生成一个频率编号吗？",
        "关系管理": "关系管理是彩虹城系统的重要功能，用于管理AI与人类用户之间的关系。它包括了关系创建、关系搜索、关系状态更新和关系强度评分等功能。你想使用关系管理器吗？",
        "ai-id": "彩虹城系统中的AI-ID是每个AI的唯一标识符，包含了关于AI的多种属性和特征。你想生成一个AI-ID吗？",
        "标识符": "彩虹城系统中的AI标识符是每个AI的唯一识别码，包含了关于AI的多种属性和特征。你想生成一个AI标识符吗？"
    }
    
    # 多模态消息的特殊响应
    if has_image:
        response = "我看到你上传了一张图片。这是一张很有趣的图片！你想要我如何帮助你分析这张图片吗？"
    elif has_audio:
        response = "我收到了你的音频消息。我已经分析了其中的内容。你想要我如何帮助你处理这条音频信息吗？"
    else:
        # 根据用户消息选择回复
        response = "我不太理解你的问题。可以请你再详细说明一下吗？"
        
        if user_message:
            # 尝试匹配预定义的回复
            for key, value in responses.items():
                if key in user_message:
                    response = value
                    break
    
    # 检查是否应该推荐工具
    should_recommend_tools = False
    tool_to_recommend = None
    
    if user_message:
        if "频率" in user_message or "编号" in user_message or "生成频率" in user_message:
            should_recommend_tools = True
            tool_to_recommend = "frequency_generator"
        elif "ai-id" in user_message or "ai id" in user_message or "标识符" in user_message or "生成id" in user_message:
            should_recommend_tools = True
            tool_to_recommend = "ai_id_generator"
        elif "关系" in user_message or "管理关系" in user_message:
            should_recommend_tools = True
            tool_to_recommend = "relationship_manager"
    
    # 准备响应数据
    response_data = {
        "response": {
            "content": response,
            "type": "text",
            "metadata": {
                "model": "simple-model",
                "created": int(time.time()),
                "session_id": session_id,
                "turn_id": turn_id
            }
        }
    }
    
    # 如果需要推荐工具，添加工具调用
    if should_recommend_tools and tool_to_recommend:
        for tool in AVAILABLE_TOOLS:
            if tool["id"] == tool_to_recommend:
                # 模拟工具调用
                tool_call = {
                    "id": f"call_{int(time.time())}",
                    "name": tool["name"],
                    "parameters": {}
                }
                
                # 根据工具类型设置参数
                if tool_to_recommend == "frequency_generator":
                    tool_call["parameters"] = {
                        "ai_type": "A",
                        "personality": "P"
                    }
                elif tool_to_recommend == "ai_id_generator":
                    tool_call["parameters"] = {
                        "name": "新AI"
                    }
                elif tool_to_recommend == "relationship_manager":
                    tool_call["parameters"] = {
                        "action": "search"
                    }
                
                response_data["tool_calls"] = [tool_call]
                break
    
    # 返回JSON响应
    return response_data
