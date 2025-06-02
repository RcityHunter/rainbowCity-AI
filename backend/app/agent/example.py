"""
彩虹城AI-Agent对话管理系统使用示例
"""

import os
import sys
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.agent.ai_assistant import AIAssistant

def main():
    """主函数"""
    print("彩虹城AI-Agent对话管理系统示例")
    print("-" * 50)
    
    # 初始化AI助手
    assistant = AIAssistant(model_name="gpt-3.5-turbo")
    
    # 示例1：天气查询
    print("\n示例1：天气查询")
    user_query = "我明天要去新加坡旅行，需要带伞吗？"
    print(f"用户问题: {user_query}")
    
    response = assistant.process_query(user_query, session_id="session_001")
    print(f"AI回答: {response['response']}")
    
    if response['has_tool_calls']:
        print("\n工具调用结果:")
        for tool_result in response['tool_results']:
            print(f"- {tool_result['tool_name']}: {tool_result['result']}")
    
    # 示例2：AI-ID生成
    print("\n示例2：AI-ID生成")
    user_query = "我需要一个新的AI-ID，可以帮我生成一个吗？"
    print(f"用户问题: {user_query}")
    
    response = assistant.process_query(user_query, session_id="session_002")
    print(f"AI回答: {response['response']}")
    
    if response['has_tool_calls']:
        print("\n工具调用结果:")
        for tool_result in response['tool_results']:
            print(f"- {tool_result['tool_name']}: {tool_result['result']}")
    
    # 示例3：频率编号生成
    print("\n示例3：频率编号生成")
    user_query = "我有一个AI-ID: AI-20250526123456，请帮我生成对应的频率编号。"
    print(f"用户问题: {user_query}")
    
    response = assistant.process_query(user_query, session_id="session_003")
    print(f"AI回答: {response['response']}")
    
    if response['has_tool_calls']:
        print("\n工具调用结果:")
        for tool_result in response['tool_results']:
            print(f"- {tool_result['tool_name']}: {tool_result['result']}")
    
    # 查看日志
    print("\n日志示例 (session_001):")
    logs = assistant.get_session_logs("session_001")
    for i, log in enumerate(logs[:2]):  # 只显示前两条日志
        print(f"日志 {i+1}:")
        print(f"  类型: {log['event_type']}")
        print(f"  时间: {log['timestamp']}")
        if log['event_type'] == 'user_input':
            print(f"  内容: {log['content']['input']}")
        elif log['event_type'] == 'final_response':
            print(f"  内容: {log['content']['response'][:100]}...")
    
    print("\n完整日志已保存到:", response['log_file'])

if __name__ == "__main__":
    main()
