"""
聊天相关工具函数
"""

import logging

def ensure_chat_id_format(chat_id: str) -> str:
    """
    确保聊天ID格式正确，如果没有chat:前缀，则添加前缀
    
    Args:
        chat_id: 聊天ID，可能有或没有chat:前缀
        
    Returns:
        格式化后的聊天ID，始终包含chat:前缀
    """
    formatted_id = chat_id if chat_id.startswith('chat:') else f'chat:{chat_id}'
    logging.info(f"格式化聊天ID: {chat_id} -> {formatted_id}")
    return formatted_id
