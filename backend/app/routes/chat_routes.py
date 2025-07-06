from fastapi import APIRouter, Request, Response, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import os
import time
import uuid
import logging
from openai import OpenAI
import httpx
from dotenv import load_dotenv
from tavily import TavilyClient

# 设置日志级别为 DEBUG
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 导入AI-Agent模块
from app.agent.ai_assistant import AIAssistant

# 导入记忆系统模块
from app.services.chat_memory_integration import ChatMemoryIntegration

# 导入 Tavily 搜索客户端
from tavily import TavilyClient

# 加载环境变量
load_dotenv()

# 获取OpenAI API密钥
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 初始OpenAI客户端
# 在新版本的 OpenAI SDK 中，如果需要设置代理，应该使用 http_client 参数
# 显式创建 httpx 客户端，不使用任何代理设置
http_client = httpx.Client()
client = OpenAI(api_key=OPENAI_API_KEY, http_client=http_client)

# 创建AI-Agent实例
ai_assistant = AIAssistant(model_name="gpt-3.5-turbo")

# 创建聊天记忆集成实例
chat_memory = ChatMemoryIntegration()

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
    },
    {
        "id": "web_search",
        "name": "网络搜索",
        "description": "使用 Tavily 搜索引擎在网络上搜索信息",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询"
                },
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "description": "搜索深度，basic 为基础搜索，advanced 为高级搜索"
                }
            },
            "required": ["query"]
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
    logging.info("===== CHAT FUNCTION EXECUTED =====")
    try:
        messages = request.messages
        session_id = request.session_id
        turn_id = request.turn_id
        
        # 记录会话信息
        logging.debug(f"Session ID: {session_id}, Turn ID: {turn_id}")
        
        # 添加系统消息，定义AI助手的角色和行为
        system_message = Message(
            role="system",
            content="你是彩虹城系统的AI助手，专门解答关于彩虹城系统、频率编号和关系管理的问题。当用户询问关于频率编号、AI-ID或关系管理的问题时，你应该推荐相应的工具。当用户询问需要最新信息或网络搜索的问题时，你应该使用网络搜索工具。"
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
        logging.debug(f"Processing messages: {json.dumps([m.dict() for m in messages[:2]])}...")
        
        # 检查是否需要推荐工具
        should_recommend_tools = False
        tool_to_recommend = None
        last_user_message = ""
        for msg in reversed(messages):
            if msg.role == 'user':
                last_user_message = msg.content.lower()
                break
        
        logging.debug(f"最后的用户消息: {last_user_message}")
        logging.info(f"处理用户消息: '{last_user_message[:30]}...'")
        
        logging.debug(f"检测是否是天气查询: {last_user_message}")
        logging.debug(f"用户消息类型: {type(last_user_message)}")
        logging.debug(f"用户消息长度: {len(last_user_message)}")
        logging.debug(f"用户消息字符: {[ord(c) for c in last_user_message[:10]]}...")
        logging.info(f"检测天气查询: '{last_user_message}'")

        
        # 检测是否是新加坡天气查询
        has_singapore = "新加坡" in last_user_message
        has_weather_terms = any(weather_term in last_user_message for weather_term in ["天气", "气温", "温度", "今天", "现在", "如何", "怎么样", "怎样"])
        logging.debug(f"包含'新加坡': {has_singapore}")
        logging.debug(f"包含天气相关词: {has_weather_terms}")
        weather_terms_list = ["天气", "气温", "温度", "今天", "现在", "如何", "怎么样", "怎样"]
        matched_terms = [term for term in weather_terms_list if term in last_user_message]
        logging.debug(f"天气相关词匹配: {matched_terms}")
        logging.info(f"新加坡天气检测结果 - 包含新加坡: {has_singapore}, 包含天气词: {has_weather_terms}")

        
        is_singapore_weather_query = has_singapore and has_weather_terms
        
        # 检测是否是济南天气查询
        is_jinan_weather_query = "济南" in last_user_message and any(weather_term in last_user_message for weather_term in ["天气", "气温", "温度", "今天", "现在", "如何", "怎么样", "怎样"])
        
        logging.debug(f"是否是新加坡天气查询: {is_singapore_weather_query}")
        logging.debug(f"是否是济南天气查询: {is_jinan_weather_query}")
        logging.info(f"天气查询检测结果 - 新加坡: {is_singapore_weather_query}, 济南: {is_jinan_weather_query}")
        
        # 特殊处理天气查询
        if is_singapore_weather_query or is_jinan_weather_query:
            # 检测是哪个城市的天气查询
            location = None
            search_query = ""
            
            if is_jinan_weather_query:
                location = "济南"
                search_query = "济南天气实时预报"
                logging.info(f"检测到济南天气查询，直接触发搜索")
            elif is_singapore_weather_query:
                location = "新加坡"
                # 使用多个关键词来获取更准确的结果
                search_query = "Singapore weather forecast today real-time current"
                logging.info(f"检测到新加坡天气查询，直接触发搜索: {search_query}")
            
            should_recommend_tools = True
            tool_to_recommend = "web_search"
            
            # 直接执行天气搜索
            try:
                # 从环境变量获取 API 密钥
                api_key = os.getenv("TAVILY_API_KEY")
                logging.debug(f"TAVILY_API_KEY 是否存在: {bool(api_key)}")
                if api_key:
                    # 创建 Tavily 客户端
                    client_tavily = TavilyClient(api_key=api_key)
                    
                    logging.debug(f"执行天气搜索，关键词: {search_query}")
                    
                    # 执行搜索
                    logging.debug(f"开始执行 Tavily 搜索，参数: query={search_query}, search_depth=advanced, max_results=5")
                    try:
                        search_result = client_tavily.search(
                            query=search_query,
                            search_depth="advanced",
                            max_results=5,
                            include_answer=True
                        )
                        logging.debug("Tavily 搜索成功完成")
                    except Exception as search_error:
                        logging.error(f"Tavily 搜索执行错误: {str(search_error)}")
                        # 重新抛出异常，让外层的异常处理捕获
                        raise search_error
                    
                    logging.debug(f"搜索结果类型: {type(search_result)}")
                    if isinstance(search_result, dict):
                        logging.debug(f"搜索结果键: {search_result.keys()}")
                        if "answer" in search_result:
                            logging.debug(f"搜索结果 answer 前100字符: {search_result['answer'][:100]}...")
                        else:
                            logging.debug("搜索结果中没有 answer 键")
                        if "results" in search_result:
                            logging.debug(f"搜索结果包含 {len(search_result['results'])} 个结果项")
                        else:
                            logging.debug("搜索结果中没有 results 键")
                    else:
                        logging.debug(f"搜索结果不是字典类型: {search_result}")
                    
                    # 将搜索结果添加到消息中
                    if "answer" in search_result and search_result["answer"]:
                        logging.debug(f"搜索结果中包含 answer: {search_result['answer'][:100]}...")
                        
                        # 根据不同城市提供相应的天气信息
                        location_name = location if location else "该地区"
                        
                        # 添加搜索结果作为系统消息
                        search_message = {
                            "role": "system",
                            "content": f"这是{location_name}天气的最新实时搜索结果:\n\n{search_result['answer']}\n\n请直接提供这些具体的天气信息，而不是建议用户去查询其他源。一定要提供具体的温度、天气状况和预报信息。"
                        }
                        
                        logging.debug(f"添加系统消息: {search_message['content'][:100]}...")
                        openai_messages.append(search_message)
                        
                        # 添加搜索结果链接作为参考
                    else:
                        logging.debug("搜索结果中不包含 answer")
                        if "results" in search_result and search_result["results"]:
                            sources = "\n\n数据来源:\n"
                            for i, result in enumerate(search_result["results"][:3]):
                                sources += f"- {result.get('title', '无标题')}: {result.get('url', '')}\n"
                            sources_message = {
                                "role": "system",
                                "content": f"{sources}\n请在回答中包含这些来源信息。"
                            }
                            openai_messages.append(sources_message)
                            
                        logging.debug("济南天气搜索成功，添加搜索结果到消息中")
            except Exception as e:
                logging.error(f"济南天气搜索错误: {str(e)}")
        
        # 检查用户消息中是否包含触发工具推荐的关键词
        elif "频率" in last_user_message or "编号" in last_user_message:
            should_recommend_tools = True
            tool_to_recommend = "frequency_generator"
            logging.debug("检测到频率工具关键词")
        elif "ai" in last_user_message and ("生成" in last_user_message or "创建" in last_user_message or "id" in last_user_message):
            should_recommend_tools = True
            tool_to_recommend = "ai_id_generator"
            logging.debug("检测到AI-ID工具关键词")
        elif "关系" in last_user_message or "联系" in last_user_message or "relationship" in last_user_message:
            should_recommend_tools = True
            tool_to_recommend = "relationship_manager"
            logging.debug("检测到关系管理工具关键词")
        # 扩展搜索关键词列表，增加更多天气相关关键词
        elif any(keyword in last_user_message for keyword in [
            "搜索", "查询", "查找", "最新", "新闻", "信息", "了解", "search", 
            "天气", "气温", "温度", "降雨", "降雪", "阴晴", "晴雨", "天气预报", "气象",
            "实时", "当前", "今天", "明天", "后天", "近期", "本周", "下周"
        ]):
            should_recommend_tools = True
            tool_to_recommend = "web_search"
            logging.debug("检测到搜索工具关键词，触发搜索")
            
            # 强制处理天气相关查询，直接调用 Tavily 搜索
            # 扩展天气关键词列表，确保能捕捉各种天气相关查询
            weather_terms = ["天气", "气温", "温度", "降雨", "降雪", "阴晴", "晴雨", "阴天", "晴天", "多云", 
                          "阴雨", "阵雨", "小雨", "中雨", "大雨", "暴雨", "雷雨", "雷电", "雷阵雨", 
                          "雪", "小雪", "中雪", "大雪", "暴雪", "雨夹雪", "雪夹雨", "冰雹", "冰雨",
                          "气象", "气象预报", "天气预报", "湿度", "空气质量", "空气", "空气指数", "空气质量指数",
                          "气压", "气压变化", "气压表", "气象发布", "气象台", "天气预警", "天气预报员", "天气预报局",
                          "热", "冷", "凉", "温暖", "炎热", "寒冷", "冬天", "夏天", "春天", "秋天", "季节", "季节性",
                          "weather", "temperature", "forecast", "rain", "snow", "sunny", "cloudy", "storm", "thunder", "humidity", "climate"]
            
            # 检查是否包含天气关键词
            if any(weather_term in last_user_message for weather_term in weather_terms):
                logging.debug(f"开始处理天气查询: {last_user_message}")
                try:
                    # 提取可能的地名
                    location = None
                    common_cities = ["北京", "上海", "广州", "深圳", "成都", "杭州", "南京", "武汉", "西安", "重庆", 
                                   "苏州", "天津", "济南", "青岛", "大连", "厦门", "长沙", "福州", "郑州", "洛阳",
                                   "新加坡", "东京", "纽约", "伦敦", "巴黎", "柯州", "布黎斯班", "悉尼", "香港", "台北",
                                   # 添加更多中国城市
                                   "哈尔滨", "沈阳", "长春", "南昌", "合肥", "太原", "石家庄", "呼和浩特", "兰州", "银川",
                                   "乌鲁木齐", "昭通", "昆明", "贵阳", "南宁", "海口", "三亚", "拉萨", "西宁", "唐山"]
                    
                    # 尝试提取地名
                    for city in common_cities:
                        if city in last_user_message:
                            location = city
                            logging.debug(f"检测到地名: {city}")
                            break
                    
                    # 如果没有找到具体地名，就尝试使用默认地名或整个查询
                    if location:
                        search_query = f"{location} 天气 实时"
                    else:
                        # 如果没有找到地名，尝试从消息中提取可能的地名
                        # 首先尝试使用全部消息
                        if len(last_user_message) < 50:
                            search_query = f"{last_user_message} 天气 实时"
                        else:
                            # 如果消息太长，只取前50个字符
                            search_query = f"{last_user_message[:50]} 天气 实时"
                    
                    logging.debug(f"构造的天气搜索查询: {search_query}")
                    # 这里可以添加调用天气API的代码
                except Exception as e:
                    logging.error(f"处理天气查询时出错: {str(e)}")
                    # 失败时继续正常处理

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
        
        # 处理工具调用响应
        if hasattr(ai_message, "tool_calls") and ai_message.tool_calls:
            tool_calls_data = ai_message.tool_calls
            tool_responses = []
            
            # 处理每个工具调用
            for tool_call in tool_calls_data:
                tool_call_id = tool_call.id
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # 处理天气查询结果
                if "answer" in locals() and answer:
                    logging.info("天气查询返回有效答案")
                    
                    # 添加搜索结果作为系统消息，使用更强烈的提示
                    search_message = {
                        "role": "system",
                        "content": f"这是最新的实时搜索结果，关于 '{search_query}':\n\n{answer}\n\n你必须基于这些最新信息回答用户的问题。请提供具体的天气信息，而不是仅仅建议用户去查询其他源。"
                    }
                    openai_messages.append(search_message)
                    logging.debug(f"添加了搜索结果到消息中")
                    logging.info("天气搜索结果已添加到对话中")
                    
                    # 添加搜索结果链接作为参考
                    if "search_result" in locals() and "results" in search_result and search_result["results"]:
                        sources = "\n\n数据来源:\n"
                        for i, result in enumerate(search_result["results"][:3]):
                            sources += f"- {result.get('title', '无标题')}: {result.get('url', '')}\n"
                        sources_message = {
                            "role": "system",
                            "content": f"{sources}\n请在回答中包含这些来源信息。不要仅仅建议用户去查询这些来源，而是直接提供具体的天气信息。"
                        }
                        openai_messages.append(sources_message)
                        logging.debug(f"添加了来源信息到消息中")
                    
                    logging.debug(f"天气查询搜索成功，添加搜索结果到消息中")
                    logging.info("天气搜索完成，数据已添加到对话中")
            
            # 调用OpenAI API获取响应
            # 如果检测到搜索关键词，明确指定使用 web_search 工具
            if tool_to_recommend == "web_search":
                # 提取可能的搜索查询
                search_query = last_user_message
                # 如果消息太长，尝试提取关键部分
                if len(search_query) > 100:
                    search_query = search_query[:100]
                
                # 直接调用 Tavily API
                try:
                    # 从环境变量获取 API 密钥
                    api_key = os.getenv("TAVILY_API_KEY")
                    logging.debug(f"TAVILY_API_KEY 是否存在: {bool(api_key)}")
                    if api_key:
                        # 创建 Tavily 客户端
                        client_tavily = TavilyClient(api_key=api_key)
                        
                        # 执行搜索
                        logging.debug(f"执行搜索，查询: {search_query}")
                        search_result = client_tavily.search(
                            query=search_query,
                            search_depth="basic",
                            max_results=5,
                            include_answer=True
                        )
                        
                        # 将搜索结果添加到消息中
                        if "answer" in search_result and search_result["answer"]:
                            logging.debug(f"搜索结果中包含 answer: {search_result['answer'][:100]}...")
                            search_message = {
                                "role": "system",
                                "content": f"根据最新的网络搜索结果，这是关于 '{search_query}' 的信息\n\n{search_result['answer']}\n\n请基于这些信息回答用户的问题。"
                            }
                            openai_messages.append(search_message)
                except Exception as e:
                    logging.error(f"Tavily 搜索错误: {str(e)}")
            
            # 如果不是明确的搜索请求，先让 AI 尝试回答
            if tool_to_recommend != "web_search":
                logging.info("不是明确的搜索请求，先让 AI 尝试回答")
                # 首先让 AI 尝试回答问题
                logging.debug("开始调用 OpenAI API 获取初步回答")
                initial_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=openai_messages,
                    max_tokens=150  # 限制初始回答的长度，以加快速度
                )
                logging.debug("获取初步回答成功")
                
                initial_content = initial_response.choices[0].message.content.lower()
                logging.debug(f"AI 初始回答: {initial_content[:100]}...")
                
                # 检测 AI 是否表示不知道或无法回答
                uncertainty_phrases = [
                    "我不知道", "无法提供", "没有这个信息", "无法回答", "不确定", 
                    "没有足够的信息", "知识有限", "知识库中没有", "训练数据中没有",
                    "知识库截止于", "信息可能过时", "无法获取实时信息", "无法搜索",
                    "建议您查询", "建议您搜索", "建议您查找", "无法访问互联网",
                    "抱歉", "sorry", "无法获取", "无法为您提供", "无法实时", "作为ai", "作为 ai",
                    "实时信息", "最新信息", "实时数据", "实时查询", "实时获取",
                    "天气应用程序", "气象网站", "搜索引擎"
                ]
                
                logging.debug(f"检查AI回答是否包含不确定性短语: {initial_content[:100]}...")
                
                # 检测是否包含不确定性短语
                matched_phrases = [phrase for phrase in uncertainty_phrases if phrase in initial_content]
                
                logging.debug(f"检测到的不确定性短语: {matched_phrases if matched_phrases else '无'}")                
                
                # 如果 AI 表示不确定或无法回答，自动触发搜索
                if matched_phrases:
                    logging.debug(f"AI 表示不确定，检测到以下短语: {matched_phrases}")
                    logging.info("AI 表示不确定，自动触发搜索")
                    
                    # 提取搜索查询
                    search_query = last_user_message
                    # 如果消息太长，尝试提取关键部分
                    if len(search_query) > 100:
                        search_query = search_query[:100]
                        
                    logging.info(f"由于AI不确定，触发搜索: '{search_query}'")
                    
                    try:
                        # 从环境变量获取 API 密钥
                        api_key = os.getenv("TAVILY_API_KEY")
                        if api_key:
                            # 创建 Tavily 客户端
                            client_tavily = TavilyClient(api_key=api_key)
                            
                            # 执行搜索
                            logging.debug(f"开始执行 Tavily 搜索，参数: query={search_query}, search_depth=basic, max_results=5")
                            search_result = client_tavily.search(
                                query=search_query,
                                search_depth="basic",
                                max_results=5,
                                include_answer=True
                            )
                            logging.debug("Tavily 搜索成功完成")
                            
                            # 将搜索结果添加到消息中
                            if "answer" in search_result and search_result["answer"]:
                                logging.debug(f"搜索结果包含答案，长度: {len(search_result['answer'])}")
                                # 添加搜索结果作为系统消息
                                search_message = {
                                    "role": "system",
                                    "content": f"我注意到你对这个问题不确定。根据最新的网络搜索结果，这是关于 '{search_query}' 的信息\n\n{search_result['answer']}\n\n请基于这些信息重新回答用户的问题。"
                                }
                                openai_messages.append(search_message)
                                logging.info(f"已将搜索结果添加到对话中，准备重新生成回答")
                                
                                # 添加搜索结果链接作为参考
                                if "results" in search_result and search_result["results"]:
                                    sources = "\n\n数据来源:\n"
                                    for i, result in enumerate(search_result["results"][:3]):
                                        sources += f"- {result.get('title', '无标题')}: {result.get('url', '')}\n"
                                    sources_message = {
                                        "role": "system",
                                        "content": f"{sources}\n请在回答中包含这些来源信息。"
                                    }
                                    openai_messages.append(sources_message)
                                    
                                # 打印调试信息
                                logging.info("AI 不确定，自动触发 Tavily 搜索成功")
                    except Exception as e:
                        logging.error(f"AI 不确定时的 Tavily 搜索错误: {str(e)}")
                
                try:
                    # 调用 OpenAI API 获取最终响应
                    logging.debug(f"准备调用 OpenAI API 获取最终响应，消息数量: {len(openai_messages)}")
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=openai_messages,
                        tools=AVAILABLE_TOOLS,
                        tool_choice="auto"
                    )
                    logging.debug("OpenAI API 调用成功完成")
                except Exception as api_error:
                    # 如果出现错误，尝试不使用tools参数
                    logging.error(f"API调用出错，尝试不使用tools参数: {str(api_error)}")
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=openai_messages
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
                
                # 处理工具调用响应
                if "tool_calls" in ai_message:
                    tool_calls_data = ai_message.tool_calls
                    tool_responses = []
                    
                    # 处理每个工具调用
                    for tool_call in tool_calls_data:
                        tool_call_id = tool_call.id
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        # 根据工具类型执行不同的操作
                        tool_response = None
                        if function_name == "frequency_generator":
                            # 模拟频率生成器的响应
                            ai_type = function_args.get("ai_type", "A")
                            personality = function_args.get("personality", "P")
                            frequency_number = f"V1-{int(time.time())}-{personality}-{ai_type}-HASH"
                            tool_response = {"frequency": frequency_number}
                        elif function_name == "ai_id_generator":
                            # 模拟AI-ID生成器的响应
                            name = function_args.get("name", "未命名AI")
                            ai_id = f"AI-{name}-{uuid.uuid4().hex[:8]}"
                            tool_response = {"ai_id": ai_id}
                        elif function_name == "relationship_manager":
                            # 模拟关系管理器的响应
                            action = function_args.get("action", "search")
                            if action == "search":
                                tool_response = {"relationships": [{"id": "rel-001", "type": "友好", "strength": 0.8}]}
                            elif action == "create":
                                tool_response = {"status": "success", "message": "关系创建成功"}
                            else:
                                tool_response = {"status": "error", "message": "未知的关系操作"}
                        elif function_name == "web_search":
                            # 使用 Tavily 搜索引擎执行搜索
                            try:
                                # 从环境变量获取 API 密钥
                                api_key = os.getenv("TAVILY_API_KEY")
                                if not api_key:
                                    tool_response = {"error": "Tavily API key not configured"}
                                else:
                                    # 创建 Tavily 客户端
                                    client = TavilyClient(api_key=api_key)
                                    
                                    # 准备搜索参数
                                    query = function_args.get("query")
                                    search_depth = function_args.get("search_depth", "basic")
                                    
                                    # 执行搜索
                                    search_result = client.search(
                                        query=query,
                                        search_depth=search_depth,
                                        max_results=5,  # 限制结果数量
                                        include_answer=True
                                    )
                                    
                                    # 构建响应
                                    tool_response = {
                                        "answer": search_result.get("answer"),
                                        "results": search_result.get("results", [])
                                    }
                            except Exception as e:
                                tool_response = {"error": f"Search error: {str(e)}"}
                        
                        # 将工具响应添加到消息中
                        if tool_response:
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps(tool_response, ensure_ascii=False)
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
        logging.error(f"Error in chat endpoint: {str(e)}")
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

# 使用AI-Agent的聊天端点，集成记忆系统
@router.post("/chat-agent")
async def chat_agent(request: ChatRequest):
    # 导入超时处理模块
    import asyncio
    from asyncio import TimeoutError
    import logging
    
    # 定义一个内部处理函数，用于超时控制
    async def process_chat_request():
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
            
            # 使用记忆系统增强上下文
            memory_context = {}
            try:
                # 获取相关记忆和上下文增强
                memory_context = await chat_memory.enhance_response_with_memories(
                    user_id=user_id,
                    user_message=user_message,
                    current_session_id=session_id
                )
                
                # 如果有相关记忆，将其添加到上下文中
                enhanced_context = memory_context.get("context_enhancement", "")
                if enhanced_context:
                    logging.info(f"使用记忆增强上下文: {enhanced_context[:100]}...")
            except Exception as e:
                logging.error(f"获取记忆上下文失败: {str(e)}")
                # 即使记忆增强失败，也继续处理请求
                memory_context = {}
            
            # 使用AI-Agent处理请求
            try:
                # 设置会话信息
                ai_assistant.context_builder.session_id = session_id
                ai_assistant.context_builder.user_id = user_id
                
                # 如果有记忆上下文，添加到处理中
                context_prefix = ""
                if memory_context and "context_enhancement" in memory_context and memory_context["context_enhancement"]:
                    context_prefix = f"用户上下文信息:\n{memory_context['context_enhancement']}\n\n用户当前问题: "
                
                # 处理用户查询，添加记忆上下文
                enhanced_query = f"{context_prefix}{user_message}" if context_prefix else user_message
                
                # 添加超时处理，最多等待25秒
                try:
                    response = await asyncio.wait_for(
                        asyncio.create_task(ai_assistant.process_query(enhanced_query)),
                        timeout=25.0  # 25秒超时
                    )
                except TimeoutError:
                    logging.error("AI处理请求超时，返回默认响应")
                    return JSONResponse(
                        status_code=504,  # Gateway Timeout
                        content={
                            "error": "处理请求超时",
                            "message": "服务器处理请求时间过长，请稍后再试或简化您的问题。"
                        }
                    )
                
                # 异步保存消息到记忆系统，但不等待完成
                try:
                    # 创建任务但不等待
                    asyncio.create_task(
                        chat_memory.process_chat_message(
                            session_id=session_id,
                            user_id=user_id,
                            role="user",
                            content=user_message,
                            content_type="text"
                        )
                    )
                    
                    # 创建任务但不等待
                    asyncio.create_task(
                        chat_memory.process_chat_message(
                            session_id=session_id,
                            user_id=user_id,
                            role="assistant",
                            content=response,
                            content_type="text"
                        )
                    )
                    logging.info("已创建异步任务保存聊天消息")
                except Exception as e:
                    logging.error(f"创建保存消息任务失败: {str(e)}")
                
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
                            "turn_id": request.turn_id,
                            "memory_enhanced": bool(context_prefix)
                        }
                    },
                    "memory_context": memory_context if memory_context else None
                }
            except Exception as e:
                logging.error(f"AI-Agent处理失败: {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={"error": f"AI-Agent处理失败: {str(e)}"}
                )
                
        except Exception as e:
            logging.error(f"聊天处理失败: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"聊天处理失败: {str(e)}"}
            )
    
    # 设置整个请求的超时时间为30秒
    try:
        return await asyncio.wait_for(
            process_chat_request(),
            timeout=30.0  # 30秒全局超时
        )
    except TimeoutError:
        logging.error("整个请求处理超时")
        return JSONResponse(
            status_code=504,  # Gateway Timeout
            content={
                "error": "请求处理超时",
                "message": "服务器响应时间过长，请稍后再试。"
            }
        )
    except Exception as e:
        logging.error(f"处理请求时发生未预期的错误: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"处理请求时发生错误: {str(e)}"}
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
        elif any(keyword in user_message.lower() for keyword in ["搜索", "查询", "查找", "最新", "新闻", "信息", "了解", "search"]):
            should_recommend_tools = True
            tool_to_recommend = "web_search"
    
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
                elif tool_to_recommend == "web_search":
                    # 提取可能的搜索查询
                    search_query = user_message
                    # 如果消息太长，尝试提取关键部分
                    if len(search_query) > 100:
                        search_query = search_query[:100]
                    tool_call["parameters"] = {
                        "query": search_query,
                        "search_depth": "basic"
                    }
                    
                    # 实际执行搜索
                    try:
                        # 从环境变量获取 API 密钥
                        api_key = os.getenv("TAVILY_API_KEY")
                        if api_key:
                            # 创建 Tavily 客户端
                            client = TavilyClient(api_key=api_key)
                            
                            # 执行搜索
                            search_result = client.search(
                                query=search_query,
                                search_depth="basic",
                                max_results=5,  # 限制结果数量
                                include_answer=True
                            )
                            
                            # 如果搜索成功，替换原来的响应
                            if "answer" in search_result and search_result["answer"]:
                                response = search_result["answer"]
                                
                                # 添加搜索结果链接
                                if "results" in search_result and search_result["results"]:
                                    response += "\n\n相关链接:\n"
                                    for i, result in enumerate(search_result["results"][:3]):
                                        response += f"- {result.get('title', '无标题')}: {result.get('url', '')}\n"
                    except Exception as e:
                        logging.error(f"Tavily 搜索错误: {str(e)}")
                        # 搜索失败时不替换原来的响应
                
                response_data["tool_calls"] = [tool_call]
                break
    
    # 返回JSON响应
    return response_data
