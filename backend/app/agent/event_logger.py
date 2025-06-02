"""
事件日志器
负责记录对话过程中的各种事件，包括用户输入、LLM调用、工具调用等
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os

@dataclass
class LogEntry:
    """日志条目结构"""
    session_id: str
    user_id: str
    ai_id: str
    timestamp: str
    event_type: str  # "user_input", "llm_call", "tool_call", "final_response"
    content: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "ai_id": self.ai_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "content": self.content
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

class EventLogger:
    """事件日志记录器"""
    
    def __init__(self, log_dir: str = None):
        self.logs: List[LogEntry] = []
        self.log_dir = log_dir or os.path.join(os.getcwd(), "logs")
        
        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)
        
    def log_user_input(self, session_id: str, user_id: str, ai_id: str, input_text: str, 
                     file_type: Optional[str] = None, file_info: Optional[Dict[str, Any]] = None) -> LogEntry:
        """记录用户输入和文件信息
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            ai_id: AI ID
            input_text: 用户输入文本
            file_type: 文件类型（图片、音频、视频、文档）
            file_info: 文件元信息
        """
        content = {"input": input_text}
        
        # 添加文件信息（如果有）
        if file_type:
            content["file_type"] = file_type
            
            if file_info:
                # 移除可能的大型数据字段，避免日志过大
                safe_file_info = {k: v for k, v in file_info.items() if k not in ['data', 'content']}
                content["file_info"] = safe_file_info
        
        entry = LogEntry(
            session_id=session_id,
            user_id=user_id,
            ai_id=ai_id,
            timestamp=datetime.now().isoformat(),
            event_type="user_input",
            content=content
        )
        self.logs.append(entry)
        return entry
        
    def log_llm_call(self, session_id: str, user_id: str, ai_id: str, 
                     prompt: List[Dict], response: Dict, call_number: int) -> LogEntry:
        """记录LLM调用"""
        entry = LogEntry(
            session_id=session_id,
            user_id=user_id,
            ai_id=ai_id,
            timestamp=datetime.now().isoformat(),
            event_type="llm_call",
            content={
                "call_number": call_number,
                "prompt": prompt,
                "response": response
            }
        )
        self.logs.append(entry)
        return entry
        
    def log_tool_call(self, session_id: str, user_id: str, ai_id: str,
                      tool_name: str, tool_args: Dict, tool_result: str) -> LogEntry:
        """记录工具调用"""
        entry = LogEntry(
            session_id=session_id,
            user_id=user_id,
            ai_id=ai_id,
            timestamp=datetime.now().isoformat(),
            event_type="tool_call",
            content={
                "tool_name": tool_name,
                "tool_args": tool_args,
                "tool_result": tool_result
            }
        )
        self.logs.append(entry)
        return entry
    
    def log_final_response(self, session_id: str, user_id: str, ai_id: str,
                           response: str, has_tool_calls: bool) -> LogEntry:
        """记录最终响应"""
        entry = LogEntry(
            session_id=session_id,
            user_id=user_id,
            ai_id=ai_id,
            timestamp=datetime.now().isoformat(),
            event_type="final_response",
            content={
                "response": response,
                "has_tool_calls": has_tool_calls
            }
        )
        self.logs.append(entry)
        return entry
    
    def save_logs(self, session_id: str) -> str:
        """保存会话日志到文件"""
        session_logs = [log for log in self.logs if log.session_id == session_id]
        if not session_logs:
            return ""
        
        # 创建日志文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_{session_id}_{timestamp}.json"
        filepath = os.path.join(self.log_dir, filename)
        
        # 写入日志
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([log.to_dict() for log in session_logs], f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def get_session_logs(self, session_id: str) -> List[LogEntry]:
        """获取指定会话的所有日志"""
        return [log for log in self.logs if log.session_id == session_id]
    
    def clear_logs(self) -> None:
        """清除所有日志"""
        self.logs = []
