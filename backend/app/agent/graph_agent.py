"""
基于LangGraph的代理系统
实现基于有向图的工作流，支持多步骤推理和复杂工具调用
"""

from typing import Dict, List, Any, Optional, TypedDict, Annotated, Sequence
import os
import logging
import json
from datetime import datetime

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

# 导入本地模块
from .tool_invoker import ToolInvoker
from app.services.chat_memory_integration import ChatMemoryIntegration


class AgentState(TypedDict):
    """代理状态定义"""
    messages: List[Dict[str, Any]]  # 消息历史
    session_id: str                 # 会话ID
    user_id: str                    # 用户ID
    ai_id: Optional[str]            # AI ID
    tool_results: List[Dict]        # 工具调用结果
    current_tool_calls: List[Dict]  # 当前待执行的工具调用
    final_response: Optional[str]   # 最终响应


class GraphAgent:
    """基于LangGraph的代理实现"""
    
    def __init__(self, model_name: str = "gpt-4o"):
        """初始化图代理"""
        self.model_name = model_name
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # 工具调用器
        self.tool_invoker = ToolInvoker()
        
        # 聊天记忆集成
        self.chat_memory_integration = ChatMemoryIntegration()
        
        # 注册默认工具
        self._register_default_tools()
        
        # 构建工作流图
        self.workflow = self._build_workflow()
        
        logging.info(f"GraphAgent初始化完成，使用模型: {model_name}")
    
    def _register_default_tools(self):
        """注册默认工具"""
        # 复用现有的工具注册逻辑
        from .tool_invoker import get_weather, generate_ai_id, generate_frequency
        
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
                }
            }
        )
        
        # 可以根据需要添加更多工具
        logging.info("GraphAgent已注册默认工具")
        
    
    def _build_workflow(self) -> StateGraph:
        """构建代理工作流图"""
        # 创建状态图
        workflow = StateGraph(AgentState)
        
        # 添加节点
        
        # 1. LLM思考节点 - 决定下一步操作
        workflow.add_node("think", self._think)
        
        # 2. 工具执行节点 - 执行工具调用
        workflow.add_node("execute_tool", self._execute_tool)
        
        # 3. 生成最终响应节点
        workflow.add_node("generate_response", self._generate_response)
        
        # 设置入口节点
        workflow.set_entry_point("think")
        
        # 添加边 (节点之间的转换)
        
        # 从思考节点出发，根据结果决定下一步
        workflow.add_conditional_edges(
            "think",
            self._route_from_thinking,
            {
                "execute_tool": "execute_tool",   # 需要执行工具
                "respond": "generate_response",   # 直接生成回复
            }
        )
        
        # 工具执行完后，回到思考节点
        workflow.add_edge("execute_tool", "think")
        
        # 生成响应后，结束工作流
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def _think(self, state: AgentState) -> AgentState:
        """LLM思考节点 - 分析上下文并决定下一步操作"""
        # 准备消息历史
        messages = state["messages"]
        
        # 调用LLM进行思考
        response = self.llm.invoke(
            messages,
            tools=self.tool_invoker.get_tool_definitions()
        )
        
        # 检查是否有工具调用
        tool_calls = getattr(response, "tool_calls", None)
        
        if tool_calls:
            # 有工具调用，记录到状态中
            state["current_tool_calls"] = []
            
            for tool_call in tool_calls:
                try:
                    tool_call_id = tool_call.id
                    tool_name = tool_call.name
                    tool_args = json.loads(tool_call.args)
                    
                    state["current_tool_calls"].append({
                        "tool_call_id": tool_call_id,
                        "name": tool_name,
                        "args": tool_args
                    })
                except Exception as e:
                    logging.error(f"解析工具调用参数失败: {str(e)}")
            
            # 添加助手消息到历史
            state["messages"].append({
                "role": "assistant",
                "content": None,
                "tool_calls": tool_calls
            })
        else:
            # 没有工具调用，直接生成回复
            state["final_response"] = response.content
            
            # 添加助手消息到历史
            state["messages"].append({
                "role": "assistant",
                "content": response.content
            })
        
        return state
    
    def _route_from_thinking(self, state: AgentState) -> str:
        """路由决策 - 决定从思考后去向哪个节点"""
        if state["current_tool_calls"]:
            return "execute_tool"
        else:
            return "respond"
    
    def _execute_tool(self, state: AgentState) -> AgentState:
        """执行工具调用"""
        for tool_call in state["current_tool_calls"]:
            tool_id = tool_call["tool_call_id"]
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            try:
                # 执行工具调用
                result = self.tool_invoker.invoke_tool(tool_name, **tool_args)
                
                # 记录工具调用结果
                state["tool_results"].append({
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "args": tool_args,
                    "result": result
                })
                
                # 添加工具消息到历史
                state["messages"].append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": str(result)
                })
            except Exception as e:
                error_msg = f"工具调用失败: {str(e)}"
                logging.error(error_msg)
                
                # 添加错误消息到历史
                state["messages"].append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": error_msg
                })
        
        # 清除当前工具调用
        state["current_tool_calls"] = []
        
        return state
    
    def _generate_response(self, state: AgentState) -> AgentState:
        """生成最终回复"""
        if not state.get("final_response"):
            # 如果没有预设的最终回复，再次调用LLM生成
            messages = state["messages"]
            response = self.llm.invoke(messages)
            state["final_response"] = response.content
            
            # 添加最终助手消息到历史
            state["messages"].append({
                "role": "assistant",
                "content": response.content
            })
        
        return state
    
    async def process_query(self, 
                           user_input: str, 
                           session_id: str = None, 
                           user_id: str = None,
                           ai_id: str = None,
                           image_data: str = None,
                           file_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理用户查询
        
        Args:
            user_input: 用户输入文本
            session_id: 会话ID
            user_id: 用户ID
            ai_id: AI ID
            image_data: 图片数据
            file_data: 文件数据
            
        Returns:
            包含响应和会话信息的字典
        """
        # 生成会话ID (如果未提供)
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        # 设置用户ID (如果未提供)
        if not user_id:
            user_id = "anonymous"
            
        # 构建初始状态
        initial_state = AgentState(
            messages=[
                {
                    "role": "system",
                    "content": "你是彩虹城系统的AI助手，专门解答关于彩虹城系统、一体七翼、频率编号和关系管理的问题。如果需要外部数据，请明确说明需要调用什么工具。"
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            session_id=session_id,
            user_id=user_id,
            ai_id=ai_id,
            tool_results=[],
            current_tool_calls=[],
            final_response=None
        )
        
        # 执行工作流
        result = self.workflow.invoke(initial_state)
        final_state = result[0]  # 获取最终状态
        
        # 保存到聊天记忆 (可选)
        try:
            if user_id != "anonymous" and not user_id.startswith("anonymous"):
                # 保存用户消息
                await self.chat_memory_integration.save_message(
                    session_id=session_id,
                    user_id=user_id,
                    content=user_input,
                    role=f"{user_id}_user",
                    content_type="text"
                )
                
                # 保存AI回复
                await self.chat_memory_integration.save_message(
                    session_id=session_id,
                    user_id=user_id,
                    content=final_state["final_response"],
                    role=f"{user_id}_aiR",
                    content_type="text"
                )
        except Exception as e:
            logging.error(f"保存聊天记忆失败: {str(e)}")
        
        # 返回结果
        return {
            "response": final_state["final_response"],
            "session_id": session_id,
            "has_tool_calls": len(final_state["tool_results"]) > 0,
            "tool_results": final_state["tool_results"]
        }
