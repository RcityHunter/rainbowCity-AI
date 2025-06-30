"""
记忆管理器 - 负责从对话内容中智能提取和更新用户记忆
"""

import logging
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime

from app.services.memory_service import MemoryService
from app.services.llm_service import LLMService
from app.services.embedding_service import embedding_service
from app.models.memory_models import MemoryType, MemoryQuery


class MemoryManager:
    """记忆管理器类 - 负责从对话内容中智能提取和更新用户记忆"""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        初始化记忆管理器
        
        Args:
            llm_service: LLM服务实例，用于AI辅助的记忆提取和摘要生成
        """
        self.llm_service = llm_service or LLMService()
        self.memory_service = MemoryService()
        
    async def process_conversation(
        self,
        session_id: str,
        user_id: str,
        messages: List[Dict[str, Any]],
        extract_memories: bool = True,
        generate_summary: bool = False
    ) -> Dict[str, Any]:
        """
        处理对话，保存聊天历史并可选择提取记忆和生成摘要
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            messages: 消息列表
            extract_memories: 是否提取用户记忆
            generate_summary: 是否生成会话摘要
            
        Returns:
            处理结果
        """
        result = {
            "chat_history_saved": False,
            "memories_extracted": False,
            "summary_generated": False
        }
        
        try:
            # 1. 保存聊天历史（第一层）
            chat_history = await MemoryService.save_chat_history(
                session_id=session_id,
                user_id=user_id,
                messages=messages
            )
            result["chat_history_saved"] = bool(chat_history)
            
            # 2. 提取用户记忆（第二层）
            if extract_memories and len(messages) >= 2:  # 至少需要一问一答
                extracted_memories = await self.extract_user_memories(
                    messages=messages,
                    user_id=user_id,
                    session_id=session_id
                )
                result["memories_extracted"] = bool(extracted_memories)
                result["extracted_memories_count"] = len(extracted_memories)
            
            # 3. 生成会话摘要（第三层）
            if generate_summary and len(messages) >= 5:  # 只有当对话足够长时才生成摘要
                summary = await self.generate_session_summary(
                    messages=messages,
                    user_id=user_id,
                    session_id=session_id
                )
                result["summary_generated"] = bool(summary)
                
            return result
        except Exception as e:
            logging.error(f"处理对话失败: {str(e)}")
            return result
            
    async def extract_user_memories(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        从对话中提取用户记忆
        
        Args:
            messages: 对话消息列表
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            提取的记忆列表
        """
        try:
            # 准备对话历史文本
            conversation_text = self._prepare_conversation_text(messages)
            
            # 如果对话太短，不提取记忆
            if len(conversation_text.split()) < 20:  # 简单判断是否有足够的内容
                return []
            
            # 构建提取记忆的提示
            prompt = self._build_memory_extraction_prompt(conversation_text)
            
            # 调用LLM提取记忆
            llm_response = await self.llm_service.generate_text(prompt)
            
            # 解析LLM响应
            memories = self._parse_memory_extraction_response(llm_response)
            
            # 保存提取的记忆
            saved_memories = []
            for memory in memories:
                try:
                    # 保存用户记忆（自动生成向量嵌入）
                    saved_memory = await MemoryService.save_user_memory(
                        user_id=user_id,
                        content=memory['content'],
                        memory_type=memory['type'],
                        importance=memory['importance'],
                        source_session_id=session_id,
                        metadata={"extracted": True, "confidence": memory.get('confidence', 0.5)},
                        generate_embedding=True
                    )
                    saved_memories.append(saved_memory)
                except Exception as save_error:
                    logging.error(f"保存提取的记忆失败: {str(save_error)}")
            
            return saved_memories
        except Exception as e:
            logging.error(f"提取用户记忆失败: {str(e)}")
            return []
            
    async def generate_session_summary(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        生成会话摘要
        
        Args:
            messages: 对话消息列表
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            会话摘要或None（如果生成失败）
        """
        try:
            # 准备对话历史文本
            conversation_text = self._prepare_conversation_text(messages)
            
            # 如果对话太短，不生成摘要
            if len(conversation_text.split()) < 30:  # 简单判断是否有足够的内容
                return None
            
            # 构建生成摘要的提示
            prompt = self._build_summary_generation_prompt(conversation_text)
            
            # 调用LLM生成摘要
            llm_response = await self.llm_service.generate_text(prompt)
            
            # 解析LLM响应
            summary_data = self._parse_summary_response(llm_response)
            
            if not summary_data or 'summary' not in summary_data:
                logging.error("生成的摘要数据无效")
                return None
            
            # 获取当前时间作为结束时间
            end_time = datetime.now().isoformat()
            
            # 获取第一条消息的时间作为开始时间
            start_time = None
            for msg in messages:
                if msg.get('timestamp'):
                    start_time = msg['timestamp']
                    break
            
            if not start_time:
                start_time = end_time  # 如果没有找到开始时间，使用结束时间
            
            # 保存会话摘要（自动生成向量嵌入）
            saved_summary = await MemoryService.save_session_summary(
                session_id=session_id,
                user_id=user_id,
                summary=summary_data['summary'],
                start_time=start_time,
                end_time=end_time,
                topics=summary_data.get('topics', []),
                key_points=summary_data.get('key_points', []),
                metadata={"generated": True},
                generate_embedding=True
            )
            
            return saved_summary
        except Exception as e:
            logging.error(f"生成会话摘要失败: {str(e)}")
            return None
            
    def _prepare_conversation_text(self, messages: List[Dict[str, Any]]) -> str:
        """
        准备对话历史文本
        
        Args:
            messages: 消息列表
            
        Returns:
            对话历史文本
        """
        conversation_text = ""
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            conversation_text += f"{role.capitalize()}: {content}\n\n"
        
        return conversation_text
        
    def _build_memory_extraction_prompt(self, conversation_text: str) -> str:
        """
        构建提取记忆的提示
        
        Args:
            conversation_text: 对话历史文本
            
        Returns:
            提取记忆的提示
        """
        prompt = f"""
        请分析以下对话，提取关于用户的重要信息，包括但不限于：
        1. 个人信息（姓名、职业、兴趣爱好等）
        2. 偏好（喜欢/不喜欢的事物）
        3. 观点和价值观
        4. 重要的事实或经历
        5. 计划或意图
        
        对话内容：
        {conversation_text}
        
        请以JSON格式返回提取的记忆，每条记忆包含以下字段：
        - content: 记忆内容
        - type: 记忆类型（personal_info, preference, opinion, fact, plan）
        - importance: 重要性（1-4，其中4最重要）
        - confidence: 置信度（0-1之间的小数）
        
        示例输出：
        ```json
        [
          {{
            "content": "用户名叫张三",
            "type": "personal_info",
            "importance": 3,
            "confidence": 0.95
          }},
          {{
            "content": "用户喜欢科幻电影",
            "type": "preference",
            "importance": 2,
            "confidence": 0.8
          }}
        ]
        ```
        
        只返回JSON数组，不要包含其他解释文字。如果没有提取到任何记忆，返回空数组 []。
        """
        
        return prompt
        
    def _parse_memory_extraction_response(self, response: str) -> List[Dict[str, Any]]:
        """
        解析记忆提取响应
        
        Args:
            response: LLM响应
            
        Returns:
            解析后的记忆列表
        """
        try:
            # 尝试从响应中提取JSON
            json_str = response
            
            # 如果响应包含```json和```标记，提取其中的内容
            if "```json" in response and "```" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
                
            # 解析JSON
            memories = json.loads(json_str)
            
            # 验证和清理数据
            validated_memories = []
            for memory in memories:
                # 确保必要字段存在
                if "content" not in memory or "type" not in memory:
                    continue
                    
                # 规范化重要性
                importance = memory.get("importance", 2)
                if importance < 1:
                    importance = 1
                elif importance > 4:
                    importance = 4
                    
                memory["importance"] = importance
                
                # 规范化置信度
                confidence = memory.get("confidence", 0.8)
                if confidence < 0:
                    confidence = 0
                elif confidence > 1:
                    confidence = 1
                    
                memory["confidence"] = confidence
                
                validated_memories.append(memory)
                
            return validated_memories
        except Exception as e:
            logging.error(f"解析记忆提取响应失败: {str(e)}")
            return []
            
    def _build_summary_generation_prompt(self, conversation_text: str) -> str:
        """
        构建生成摘要的提示
        
        Args:
            conversation_text: 对话历史文本
            
        Returns:
            生成摘要的提示
        """
        prompt = f"""
        请为以下对话生成一个简洁的摘要，并提取主要讨论的话题和关键点。
        
        对话内容：
        {conversation_text}
        
        请以JSON格式返回，包含以下字段：
        - summary: 对话的简洁摘要（100-200字）
        - topics: 讨论的主要话题列表（3-5个）
        - key_points: 对话中的关键点列表（3-7个）
        
        示例输出：
        ```json
        {{
          "summary": "这段对话主要讨论了人工智能的发展趋势和潜在影响。用户对AI在医疗领域的应用表示了浓厚的兴趣，而助手提供了相关的研究进展和应用案例。",
          "topics": ["人工智能", "医疗应用", "技术伦理", "未来发展"],
          "key_points": [
            "用户对AI在医疗诊断方面的应用特别感兴趣",
            "AI在医学影像分析中已经达到或超过人类专家水平",
            "讨论了AI应用中的伦理考量和隐私保护问题",
            "探讨了未来5年内AI在医疗领域可能的突破"
          ]
        }}
        ```
        
        只返回JSON对象，不要包含其他解释文字。
        """
        
        return prompt
        
    def _parse_summary_response(self, response: str) -> Dict[str, Any]:
        """
        解析摘要生成响应
        
        Args:
            response: LLM响应
            
        Returns:
            解析后的摘要数据
        """
        try:
            # 尝试从响应中提取JSON
            json_str = response
            
            # 如果响应包含```json和```标记，提取其中的内容
            if "```json" in response and "```" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
                
            # 解析JSON
            summary_data = json.loads(json_str)
            
            # 确保必要字段存在
            if "summary" not in summary_data:
                summary_data["summary"] = "无法生成摘要"
                
            if "topics" not in summary_data or not isinstance(summary_data["topics"], list):
                summary_data["topics"] = []
                
            if "key_points" not in summary_data or not isinstance(summary_data["key_points"], list):
                summary_data["key_points"] = []
                
            return summary_data
        except Exception as e:
            logging.error(f"解析摘要生成响应失败: {str(e)}")
            return {
                "summary": "解析摘要失败",
                "topics": [],
                "key_points": []
            }
            
    async def get_relevant_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        use_vector_search: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取与查询相关的记忆
        
        Args:
            query: 查询文本
            user_id: 用户ID
            limit: 返回结果数量限制
            use_vector_search: 是否使用向量搜索
            
        Returns:
            相关记忆列表
        """
        try:
            # 生成查询的向量嵌入
            query_embedding = None
            if use_vector_search:
                try:
                    query_embedding = await embedding_service.generate_embedding(query)
                except Exception as e:
                    logging.error(f"生成查询嵌入失败: {str(e)}")
                    use_vector_search = False
            
            # 构建记忆查询
            memory_query = MemoryQuery(
                user_id=user_id,
                query=query,
                limit=limit,
                sort_by="vector" if use_vector_search else "relevance",
                use_vector_search=use_vector_search,
                embedding=query_embedding
            )
            
            # 搜索记忆
            memories = await MemoryService.search_memories(memory_query)
            
            return memories
        except Exception as e:
            logging.error(f"获取相关记忆失败: {str(e)}")
            return []
