"""
AI助手主控制器
整合上下文构建、LLM调用、工具调度和事件日志等模块，实现完整的对话处理流程
"""

from typing import Dict, Any, List, Optional
import json
import uuid
import time

from .context_builder import ContextBuilder
from .llm_caller import OpenAILLMCaller
from .tool_invoker import ToolInvoker, get_weather, generate_ai_id, generate_frequency
from .event_logger import EventLogger

class AIAssistant:
    """主AI助手控制器，整合所有模块"""
    
    def __init__(self, model_name: str = "gpt-4o"):
        self.context_builder = ContextBuilder()
        self.llm_caller = OpenAILLMCaller(model_name)
        self.tool_invoker = ToolInvoker()
        self.event_logger = EventLogger()
        
        # 注册默认工具
        self._register_default_tools()
        
    def _register_default_tools(self):
        """注册默认工具"""
        # 天气工具
        self.tool_invoker.register_tool(
            name="get_weather",
            func=get_weather,
            description="获取指定城市和日期的天气信息",
            parameters={
                "city": {
                    "type": "string",
                    "description": "城市名称，如北京、上海、新加坡等"
                },
                "date": {
                    "type": "string",
                    "description": "日期，如今天、明天、后天等",
                    "optional": True
                }
            }
        )
        
        # AI-ID生成工具
        self.tool_invoker.register_tool(
            name="generate_ai_id",
            func=generate_ai_id,
            description="生成唯一的AI-ID标识符",
            parameters={
                "name": {
                    "type": "string",
                    "description": "AI的名称（可选）",
                    "optional": True
                }
            }
        )
        
        # 频率编号生成工具
        self.tool_invoker.register_tool(
            name="generate_frequency",
            func=generate_frequency,
            description="基于AI-ID生成频率编号",
            parameters={
                "ai_id": {
                    "type": "string",
                    "description": "AI-ID标识符"
                },
                "personality_type": {
                    "type": "string",
                    "description": "人格类型代码，默认为P",
                    "optional": True
                },
                "ai_type": {
                    "type": "string",
                    "description": "AI类型代码，默认为A",
                    "optional": True
                }
            }
        )
    
    def process_query(self, user_input: str, session_id: str = None, user_id: str = None, ai_id: str = None, image_data: str = None, file_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理用户查询的完整流程
        
        Args:
            user_input: 用户输入的文本
            session_id: 会话ID，如果不提供则自动生成
            user_id: 用户ID，如果不提供则自动生成
            ai_id: AI ID，如果不提供则自动生成
            image_data: 图片数据（Base64格式）
            file_data: 文件数据，包含类型、数据和元信息
        """
        
        # 生成会话ID和其他标识符（如果未提供）
        session_id = session_id or str(uuid.uuid4())
        user_id = user_id or "user_" + str(uuid.uuid4())[:8]
        ai_id = ai_id or "ai_" + str(uuid.uuid4())[:8]
        
        # 设置上下文构建器的会话信息
        self.context_builder.session_id = session_id
        self.context_builder.user_id = user_id
        self.context_builder.ai_id = ai_id
        
        # 1. 记录用户输入和文件信息
        file_type = file_data.get('type') if file_data else None
        file_info = file_data.get('info') if file_data else None
        
        self.event_logger.log_user_input(
            session_id, user_id, ai_id, user_input, 
            file_type=file_type, file_info=file_info
        )
        
        # 2. 构建初始上下文
        import logging
        logging.debug(f"Building initial context with user input and file data")
        
        # 如果有图片数据，优先使用image_data
        # 如果没有image_data但有文件数据且类型为图片，使用file_data
        if not image_data and file_data and file_type == 'image':
            logging.debug("Using image data from file_data")
            image_data = file_data.get('data')
            
        # 更新上下文，包含图片数据和文件数据（如果有）
        self.context_builder.update_context_with_user_message(
            user_input=user_input, 
            image_data=image_data,
            file_data=file_data
        )
        messages = self.context_builder.get_conversation_history()
        
        # 3. 第一次LLM调用（带工具定义）
        tool_definitions = self.tool_invoker.get_tool_definitions()
        first_response = self.llm_caller.invoke(messages, tools=tool_definitions)
        self.event_logger.log_llm_call(session_id, user_id, ai_id, messages, first_response, 1)
        
        # 4. 检查是否有工具调用
        if first_response.get("tool_calls"):
            # 处理所有工具调用
            for tool_call in first_response["tool_calls"]:
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]
                tool_call_id = tool_call.get("id", f"call_{int(time.time())}")
                
                # 5. 执行工具调用
                tool_result = self.tool_invoker.invoke_tool(tool_name, **tool_args)
                
                # 记录工具调用
                self.event_logger.log_tool_call(
                    session_id, user_id, ai_id,
                    tool_name, tool_args, tool_result
                )
                
                # 6. 更新上下文
                self.context_builder.update_context_with_tool_result(tool_name, tool_result, tool_call_id)
            
            # 7. 第二次LLM调用（不带工具定义）
            updated_messages = self.context_builder.get_conversation_history()
            final_response = self.llm_caller.invoke(updated_messages)
            self.event_logger.log_llm_call(session_id, user_id, ai_id, updated_messages, final_response, 2)
            
            # 8. 添加助手回复到上下文
            self.context_builder.add_assistant_message(final_response["content"])
            
            # 9. 记录最终响应
            self.event_logger.log_final_response(
                session_id, user_id, ai_id,
                final_response["content"], True
            )
            
            # 10. 保存日志
            log_file = self.event_logger.save_logs(session_id)
            
            # 返回结果
            return {
                "response": final_response["content"],
                "session_id": session_id,
                "has_tool_calls": True,
                "tool_results": self.context_builder.tool_results,
                "log_file": log_file
            }
        else:
            # 如果没有工具调用，直接使用第一次响应
            # 添加助手回复到上下文
            self.context_builder.add_assistant_message(first_response["content"])
            
            # 记录最终响应
            self.event_logger.log_final_response(
                session_id, user_id, ai_id,
                first_response["content"], False
            )
            
            # 保存日志
            log_file = self.event_logger.save_logs(session_id)
            
            # 返回结果
            return {
                "response": first_response["content"],
                "session_id": session_id,
                "has_tool_calls": False,
                "tool_results": [],
                "log_file": log_file
            }
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史"""
        return self.context_builder.get_conversation_history() if self.context_builder.session_id == session_id else []
    
    def get_session_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话日志"""
        logs = self.event_logger.get_session_logs(session_id)
        return [log.to_dict() for log in logs]
    
    def clear_session(self, session_id: str) -> bool:
        """清除会话数据"""
        if self.context_builder.session_id == session_id:
            self.context_builder.clear_context()
            return True
        return False
