"""
聊天相关工具函数
"""

import logging

def ensure_chat_id_format(chat_id: str) -> str:
    """
    确保聊天ID格式正确，如果没有chat:前缀，则添加前缀
    处理可能是JSON对象的ID字符串
    
    Args:
        chat_id: 聊天ID，可能有或没有chat:前缀，也可能是JSON对象字符串
        
    Returns:
        格式化后的聊天ID，始终包含chat:前缀
    """
    # 检查是否是JSON对象字符串
    try:
        if chat_id.startswith('{') and chat_id.endswith('}'): 
            import json
            # 尝试解析JSON
            chat_id_obj = json.loads(chat_id)
            logging.info(f"检测到JSON对象ID: {chat_id_obj}")
            
            # 如果是SurrealDB格式的ID对象 {table_name: "chat", id: "xxx"}
            if isinstance(chat_id_obj, dict) and 'table_name' in chat_id_obj and 'id' in chat_id_obj:
                # 提取实际ID
                actual_id = chat_id_obj['id']
                logging.info(f"从SurrealDB对象中提取ID: {actual_id}")
                chat_id = actual_id
    except Exception as e:
        logging.warning(f"解析JSON对象ID失败: {e}, 使用原始ID: {chat_id}")
    
    # 应用常规的前缀处理
    formatted_id = chat_id if chat_id.startswith('chat:') else f'chat:{chat_id}'
    logging.info(f"格式化聊天ID: {chat_id} -> {formatted_id}")
    return formatted_id
