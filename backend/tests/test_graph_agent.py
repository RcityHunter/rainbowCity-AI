"""
LangGraph代理测试脚本
测试基于LangGraph的代理功能
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目依赖
from app.agent.graph_agent import GraphAgent
from app.agent.ai_assistant import AIAssistant

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

async def test_graph_agent():
    """测试GraphAgent基本功能"""
    logger.info("开始测试GraphAgent...")
    
    # 初始化GraphAgent
    agent = GraphAgent(model_name="gpt-4o")
    
    # 测试简单查询
    test_query = "你好，请介绍一下彩虹城系统"
    logger.info(f"测试查询: '{test_query}'")
    
    # 处理查询
    result = await agent.process_query(
        user_input=test_query,
        session_id="test_session_graph",
        user_id="test_user"
    )
    
    # 输出结果
    logger.info(f"GraphAgent响应: {result['response'][:100]}...")
    logger.info(f"是否有工具调用: {result['has_tool_calls']}")
    if result['has_tool_calls']:
        logger.info(f"工具调用结果数量: {len(result['tool_results'])}")
    
    logger.info("GraphAgent测试完成!")
    return result

async def test_traditional_assistant():
    """测试传统AIAssistant功能（用于比较）"""
    logger.info("开始测试传统AIAssistant...")
    
    # 初始化AIAssistant
    async with AIAssistant(model_name="gpt-4o") as assistant:
        # 测试相同查询
        test_query = "你好，请介绍一下彩虹城系统"
        logger.info(f"测试查询: '{test_query}'")
        
        # 处理查询
        result = await assistant._process_query_internal(
            user_input=test_query,
            session_id="test_session_traditional",
            user_id="test_user"
        )
        
        # 输出结果
        logger.info(f"传统Assistant响应: {result['response'][:100]}...")
        logger.info(f"是否有工具调用: {result['has_tool_calls']}")
        if result['has_tool_calls']:
            logger.info(f"工具调用结果数量: {len(result['tool_results'])}")
        
        logger.info("传统AIAssistant测试完成!")
        return result

async def test_tool_calling():
    """测试工具调用功能"""
    logger.info("开始测试GraphAgent工具调用...")
    
    # 初始化GraphAgent
    agent = GraphAgent(model_name="gpt-4o")
    
    # 测试需要工具调用的查询
    test_query = "今天北京的天气怎么样？"
    logger.info(f"测试工具调用查询: '{test_query}'")
    
    # 处理查询
    result = await agent.process_query(
        user_input=test_query,
        session_id="test_session_tool",
        user_id="test_user"
    )
    
    # 输出结果
    logger.info(f"GraphAgent响应: {result['response'][:100]}...")
    logger.info(f"是否有工具调用: {result['has_tool_calls']}")
    if result['has_tool_calls']:
        logger.info(f"工具调用结果数量: {len(result['tool_results'])}")
        for i, tool_result in enumerate(result['tool_results']):
            logger.info(f"工具 {i+1}: {tool_result['tool_name']}")
            logger.info(f"结果: {tool_result['result']}")
    
    logger.info("GraphAgent工具调用测试完成!")
    return result

async def main():
    """主测试函数"""
    try:
        logger.info("开始LangGraph代理测试...")
        
        # 测试基本功能
        await test_graph_agent()
        
        # 测试工具调用
        await test_tool_calling()
        
        # 可选：比较传统助手
        # await test_traditional_assistant()
        
        logger.info("所有测试完成!")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}", exc_info=True)
    finally:
        # 清理资源
        pass

if __name__ == "__main__":
    # 运行主测试函数
    asyncio.run(main())
