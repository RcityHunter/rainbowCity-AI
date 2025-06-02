from flask import Blueprint, request, Response, current_app
import json
import os
import time
import uuid
import requests
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

# 创建API蓝图
chat_bp = Blueprint('chat', __name__, url_prefix='/api')

# 设置CORS，允许前端访问
@chat_bp.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

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

# 添加一个支持工具调用的聊天端点
@chat_bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        messages = data.get('messages', [])
        session_id = data.get('session_id', '')
        turn_id = data.get('turn_id', '')
        
        # 记录会话信息
        print(f"Session ID: {session_id}, Turn ID: {turn_id}")
        
        # 添加系统消息，定义AI助手的角色和行为
        system_message = {
            "role": "system",
            "content": "你是彩虹城系统的AI助手，专门解答关于彩虹城系统、频率编号和关系管理的问题。当用户询问关于频率编号、AI-ID或关系管理的问题时，你应该推荐相应的工具。"
        }
        
        # 准备发送给OpenAI的消息
        openai_messages = [system_message]
        for msg in messages:
            role = msg.get('role')
            if role in ['user', 'assistant', 'system']:
                message_content = {
                    "role": role,
                    "content": msg.get('content', '')
                }
                # 如果消息有类型信息，可以在这里处理
                # 例如，对于图片消息，可以使用OpenAI的multi-modal API
                openai_messages.append(message_content)
        
        # 输出调试信息
        print(f"Processing messages: {json.dumps(messages[:2])}...")
        
        # 检查是否需要推荐工具
        should_recommend_tools = False
        last_user_message = ""
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                last_user_message = msg.get('content', '').lower()
                break
        
        # 检查用户消息中是否包含触发工具推荐的关键词
        tool_keywords = {
            "frequency_generator": ["频率", "编号", "生成频率", "频率编号"],
            "ai_id_generator": ["ai-id", "ai id", "标识符", "生成id"],
            "relationship_manager": ["关系", "管理关系", "关系管理"]
        }
        
        # 确定要推荐的工具
        recommended_tools = []
        for tool_id, keywords in tool_keywords.items():
            if any(keyword in last_user_message for keyword in keywords):
                for tool in AVAILABLE_TOOLS:
                    if tool["id"] == tool_id:
                        recommended_tools.append(tool)
                        break
        
        # 如果找到了推荐工具，设置标志
        if recommended_tools:
            should_recommend_tools = True
        
        # 根据是否推荐工具决定API调用方式
        if should_recommend_tools:
            # 使用OpenAI客户端的API，带工具定义
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=openai_messages,
                tools=recommended_tools
            )
            
            # 提取回复内容和工具调用
            if response.choices and len(response.choices) > 0:
                assistant_message = response.choices[0].message
                content = assistant_message.content or ""
                tool_calls = assistant_message.tool_calls or []
                
                # 构造前端期望的响应格式
                response_data = {
                    "response": {
                        "content": content,
                        "type": "text",
                        "metadata": {
                            "model": response.model,
                            "created": int(response.created)
                        }
                    }
                }
                
                # 如果有工具调用，添加到响应中
                if tool_calls:
                    formatted_tool_calls = []
                    for tool_call in tool_calls:
                        formatted_tool_calls.append({
                            "id": tool_call.id,
                            "name": tool_call.function.name,
                            "parameters": json.loads(tool_call.function.arguments)
                        })
                    
                    response_data["tool_calls"] = formatted_tool_calls
                
                print(f"Sending response with tools: {content[:50]}...")
                return response_data
        else:
            # 使用OpenAI客户端的API（无工具）
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=openai_messages
            )
            
            # 提取回复内容
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                
                # 构造前端期望的响应格式
                response_data = {
                    "response": {
                        "content": content,
                        "type": "text",
                        "metadata": {
                            "model": response.model,
                            "created": int(response.created)
                        }
                    }
                }
                
                print(f"Sending response: {content[:50]}...")
                return response_data
        
        # 如果没有有效的响应
        error_message = "OpenAI API 响应中没有内容"
        print(error_message)
        return {"error": error_message}, 500
            
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return {"error": str(e)}, 500

@chat_bp.route('/chat/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return Response(
        json.dumps({"status": "ok", "service": "chat-service"}),
        status=200,
        mimetype='application/json'
    )

@chat_bp.route('/chat/test', methods=['POST'])
def chat_test():
    """测试端点，返回一个固定的响应"""
    def generate():
        # 返回一个固定的测试响应
        yield f"data: {json.dumps({'type': 'text-delta', 'textDelta': '你好！'})}\n\n"
        yield f"data: {json.dumps({'type': 'text-delta', 'textDelta': '我是彩虹城一体七翼系统的AI助手。'})}\n\n"
        yield f"data: {json.dumps({'type': 'text-delta', 'textDelta': '我可以帮助你了解一体七翼系统、频率编号和关系管理。'})}\n\n"
        yield f"data: {json.dumps({'type': 'finish'})}\n\n"
    
    return Response(generate(), mimetype="text/event-stream")

@chat_bp.route('/chat/agent', methods=['POST'])
def chat_agent():
    try:
        data = request.json
        user_message = ""
        session_id = data.get('session_id', str(uuid.uuid4()))
        user_id = data.get('user_id', 'user_' + str(uuid.uuid4())[:8])
        ai_id = data.get('ai_id', 'ai_rainbow_city')
        
        # 获取最后一条用户消息
        messages = data.get('messages', [])
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                user_message = msg.get('content', '')
                break
        
        if not user_message:
            return Response(
                json.dumps({
                    "error": "未提供用户消息"
                }),
                status=400,
                mimetype='application/json'
            )
        
        # 使用AI-Agent处理用户请求
        result = ai_assistant.process_query(
            user_input=user_message,
            session_id=session_id,
            user_id=user_id,
            ai_id=ai_id
        )
        
        # 构建响应
        response_data = {
            "response": {
                "content": result["response"],
                "type": "text",
                "metadata": {
                    "model": "agent-enhanced",
                    "created": int(time.time()),
                    "session_id": session_id,
                    "has_tool_calls": result["has_tool_calls"]
                }
            }
        }
        
        # 如果有工具调用，添加工具调用信息
        if result["has_tool_calls"] and result["tool_results"]:
            tool_calls = []
            for tool_result in result["tool_results"]:
                tool_call = {
                    "id": f"call_{int(time.time())}",
                    "name": tool_result["tool_name"],
                    "result": tool_result["result"]
                }
                tool_calls.append(tool_call)
            
            response_data["tool_calls"] = tool_calls
        
        return Response(
            json.dumps(response_data),
            status=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        current_app.logger.error(f"处理Agent聊天请求时出错: {str(e)}")
        return Response(
            json.dumps({
                "error": str(e)
            }),
            status=500,
            mimetype='application/json'
        )

@chat_bp.route('/chat/simple', methods=['POST'])
def chat_simple():
    """简单的聊天端点，直接返回JSON响应，支持工具调用和多模态消息"""
    # 获取请求数据
    data = request.json
    messages = data.get('messages', [])
    session_id = data.get('session_id', '')
    turn_id = data.get('turn_id', '')
    
    # 打印收到的消息，便于调试
    print(f"Simple chat - Session ID: {session_id}, Turn ID: {turn_id}")
    print("Received messages:", messages[:2] if len(messages) > 2 else messages)
    
    # 获取最后一条用户消息
    user_message = None
    user_message_type = None
    has_image = False
    has_audio = False
    
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            user_message = msg.get('content', '').lower()
            user_message_type = msg.get('type', 'text')
            
            # 检查是否有图片或音频
            if user_message_type == 'image':
                has_image = True
            elif user_message_type == 'audio':
                has_audio = True
                
            # 找到第一条用户消息就跳出，但继续检查是否有其他类型的消息
            if not has_image and not has_audio:
                break
    
    # 预定义的回复
    responses = {
        "你好": "你好！我是彩虹城AI助手。我可以帮助你了解彩虹城系统、频率编号和关系管理。",
        "彩虹城": "彩虹城系统是Rainbow City平台的核心功能，用于生成、管理和可视化AI标识符和频率编号。它由多个核心组件组成，每个组件都代表了AI的不同特性。",
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
    return Response(
        json.dumps(response_data),
        status=200,
        mimetype='application/json'
    )
