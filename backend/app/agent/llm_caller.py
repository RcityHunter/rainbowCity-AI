"""
LLM调用器
负责调用大语言模型，处理请求和响应
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import json
import asyncio
import logging
from openai import AsyncOpenAI  # Changed to AsyncOpenAI for async support
import httpx  # Import httpx for creating AsyncClient

class LLMCaller(ABC):
    """LLM调用抽象基类"""
    
    @abstractmethod
    async def invoke(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """调用LLM (异步)"""
        pass

class OpenAILLMCaller(LLMCaller):
    """基于OpenAI的LLM调用实现"""
    
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        # Create an async HTTP client without proxy settings
        self.async_http_client = httpx.AsyncClient()
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"), http_client=self.async_http_client)
        self.is_closed = False
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def close(self):
        """关闭HTTP客户端连接"""
        if hasattr(self, 'async_http_client') and not self.is_closed:
            try:
                await self.async_http_client.aclose()
                self.is_closed = True
                # 显式释放资源
                self.async_http_client = None
                if hasattr(self, 'client'):
                    self.client = None
                logging.info("OpenAILLMCaller资源已正确关闭")
            except Exception as e:
                logging.error(f"关闭OpenAILLMCaller资源时出错: {str(e)}")
                # 即使出错也标记为已关闭，避免重复尝试关闭
                self.is_closed = True
            
    def __del__(self):
        """析构函数，确保资源被释放"""
        # 注意：这不是关闭异步资源的理想方式，但可以作为后备
        if hasattr(self, 'async_http_client') and not self.is_closed:
            logging.warning("OpenAILLMCaller实例在没有正确关闭的情况下被销毁")
            # 我们不能在这里使用await，所以只能记录警告
        
    async def invoke(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, max_tokens: int = 1000) -> Dict[str, Any]:
        """调用OpenAI模型 (异步)"""
        try:
            # 添加超时处理
            return await asyncio.wait_for(
                self._invoke_with_retry(messages, tools, max_tokens),
                timeout=20.0  # 20秒超时
            )
        except asyncio.TimeoutError:
            logging.error("OpenAI API调用超时")
            return {
                "content": "抱歉，AI响应超时。请稍后再试或尝试简化您的问题。",
                "tool_calls": [],
                "usage": {}
            }
        except Exception as e:
            # 错误处理
            logging.error(f"LLM调用出错: {str(e)}")
            return {
                "content": f"LLM调用出错: {str(e)}",
                "tool_calls": [],
                "usage": {}
            }
            
    async def _invoke_with_retry(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, max_tokens: int = 1000) -> Dict[str, Any]:
        """带重试的OpenAI API调用"""
        import time
        start_time = time.time()
        logging.info(f"开始OpenAI API调用，消息数量: {len(messages)}")
        
        try:
            # 准备请求参数
            request_params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": max_tokens,
            }
            
            # 检查模型是否支持 tools 参数
            # 只有特定模型支持 tools 参数，如 gpt-4-turbo, gpt-4o 等
            tools_supported_models = ["gpt-4-turbo", "gpt-4o", "gpt-4-vision", "gpt-4-1106-preview", "gpt-4-0125-preview"]
            tools_supported = any(model in self.model_name for model in tools_supported_models)
            
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
                    logging.info(f"检测到图片输入，切换到模型: {self.model_name}")
            
            # 如果提供了工具定义，且模型支持工具，添加到请求中
            if tools and tools_supported:
                logging.info(f"添加工具定义到请求，工具数量: {len(tools)}")
                request_params["tools"] = tools
                request_params["tool_choice"] = "auto"
            elif tools and not tools_supported:
                logging.warning(f"模型 {self.model_name} 不支持 tools 参数，已自动忽略工具定义")
            
            # 异步调用API
            # 使用正确的OpenAI API v1.0.0格式
            # 在v1.0.0中，不存在AsyncCompletions，只有chat.completions
            logging.info(f"开始调用OpenAI API，模型: {self.model_name}")
            
            # 添加超时控制
            import asyncio
            try:
                # 设置15秒超时
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(**request_params),
                    timeout=15.0
                )
                logging.info(f"OpenAI API调用成功，耗时: {time.time() - start_time:.2f}秒")
                
            except asyncio.TimeoutError:
                logging.error(f"OpenAI API调用超时 (15秒)")
                return {
                    "content": "抱歉，AI响应超时。请稍后再试或尝试更简短的问题。",
                    "tool_calls": [],
                    "usage": {}
                }
                
            except Exception as api_error:
                logging.error(f"OpenAI API调用错误: {str(api_error)}")
                logging.error(f"错误类型: {type(api_error).__name__}")
                
                # 如果错误与'tools'参数有关，则移除该参数重试
                if 'tools' in request_params:
                    logging.info("移除tools参数并重试")
                    request_params_without_tools = request_params.copy()
                    request_params_without_tools.pop('tools', None)
                    request_params_without_tools.pop('tool_choice', None)
                    
                    try:
                        response = await asyncio.wait_for(
                            self.client.chat.completions.create(**request_params_without_tools),
                            timeout=15.0
                        )
                        logging.info(f"不带tools的OpenAI API调用成功，耗时: {time.time() - start_time:.2f}秒")
                    except asyncio.TimeoutError:
                        logging.error(f"不带tools的OpenAI API调用也超时 (15秒)")
                        return {
                            "content": "抱歉，AI响应超时。请稍后再试或尝试更简短的问题。",
                            "tool_calls": [],
                            "usage": {}
                        }
                    except Exception as retry_error:
                        logging.error(f"不带tools的API调用也失败: {str(retry_error)}")
                        raise retry_error
                else:
                    raise api_error
            
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
            logging.error(f"OpenAI API调用失败: {str(e)}")
            # 提供一个友好的错误响应，而不是让整个请求失败
            return {
                "content": f"抱歉，AI响应出现错误: {str(e)}。请稍后再试。",
                "tool_calls": [],
                "usage": {}
            }
