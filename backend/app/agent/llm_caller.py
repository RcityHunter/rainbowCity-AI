"""
LLM调用器
负责调用大语言模型，处理请求和响应
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import json
from openai import OpenAI

class LLMCaller(ABC):
    """LLM调用抽象基类"""
    
    @abstractmethod
    def invoke(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """调用LLM"""
        pass

class OpenAILLMCaller(LLMCaller):
    """基于OpenAI的LLM调用实现"""
    
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def invoke(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, max_tokens: int = 1000) -> Dict[str, Any]:
        """调用OpenAI模型"""
        try:
            # 准备请求参数
            request_params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": max_tokens,
            }
            
            # 检查是否有图片输入，如果有，设置特定参数
            has_image = False
            for message in messages:
                if isinstance(message.get('content'), list):
                    for content_item in message['content']:
                        if content_item.get('type') == 'image_url':
                            has_image = True
                            break
                if has_image:
                    break
                    
            # 如果有图片，添加特定参数
            if has_image:
                # 确保模型支持图片
                if self.model_name not in ["gpt-4o", "gpt-4-turbo"]:
                    self.model_name = "gpt-4o"  # 自动切换到支持图片的模型
                    request_params["model"] = self.model_name
            
            # 如果提供了工具定义，添加到请求中
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = "auto"
            
            # 调用API
            response = self.client.chat.completions.create(**request_params)
            
            # 解析响应
            message = response.choices[0].message
            content = message.content or ""
            
            # 处理工具调用
            tool_calls = []
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_calls.append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    })
            
            # 构建结果
            result = {
                "content": content,
                "tool_calls": tool_calls,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            return result
            
        except Exception as e:
            # 错误处理
            return {
                "content": f"LLM调用出错: {str(e)}",
                "tool_calls": [],
                "usage": {}
            }
