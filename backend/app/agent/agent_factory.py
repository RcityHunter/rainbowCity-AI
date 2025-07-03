"""
代理工厂模块
提供统一的接口来创建和使用不同类型的代理实现
"""

from typing import Dict, Any, Optional, Literal
import logging
import os

from .ai_assistant import AIAssistant
from .graph_agent import GraphAgent

class AgentFactory:
    """代理工厂类，负责创建和管理不同类型的代理实例"""
    
    def __init__(self):
        self._agents = {}
        self._default_agent_type = os.getenv("DEFAULT_AGENT_TYPE", "classic")  # 默认使用传统代理
        logging.info(f"代理工厂初始化，默认代理类型: {self._default_agent_type}")
    
    async def get_agent(self, 
                        agent_type: Optional[str] = None, 
                        model_name: str = "gpt-4o") -> Any:
        """
        获取指定类型的代理实例
        
        Args:
            agent_type: 代理类型，可选值: "classic"(传统实现) 或 "graph"(LangGraph实现)
            model_name: 模型名称
            
        Returns:
            代理实例
        """
        # 如果未指定类型，使用默认类型
        if agent_type is None:
            agent_type = self._default_agent_type
        
        # 规范化类型名称
        agent_type = agent_type.lower().strip()
        
        # 创建缓存键
        cache_key = f"{agent_type}_{model_name}"
        
        # 如果缓存中已有实例，直接返回
        if cache_key in self._agents:
            return self._agents[cache_key]
        
        # 根据类型创建新实例
        if agent_type == "classic":
            agent = AIAssistant(model_name=model_name)
            self._agents[cache_key] = agent
            logging.info(f"创建传统代理实例，模型: {model_name}")
            return agent
        elif agent_type == "graph":
            agent = GraphAgent(model_name=model_name)
            self._agents[cache_key] = agent
            logging.info(f"创建LangGraph代理实例，模型: {model_name}")
            return agent
        else:
            # 未知类型，使用默认类型
            logging.warning(f"未知代理类型: {agent_type}，使用默认类型: {self._default_agent_type}")
            return await self.get_agent(self._default_agent_type, model_name)
    
    async def close_all(self):
        """关闭所有代理实例"""
        for key, agent in list(self._agents.items()):
            try:
                if hasattr(agent, "close") and callable(agent.close):
                    await agent.close()
                self._agents.pop(key, None)
            except Exception as e:
                logging.error(f"关闭代理实例时出错: {str(e)}")
        
        logging.info("所有代理实例已关闭")

# 创建全局代理工厂实例
agent_factory = AgentFactory()
