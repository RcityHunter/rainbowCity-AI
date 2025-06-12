"""
LLM Service for Rainbow City AI
This service handles interactions with language models for memory extraction, summarization,
and context enhancement.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMRequest(BaseModel):
    """Base model for LLM requests"""
    prompt: str
    max_tokens: int = 500
    temperature: float = 0.7
    
class LLMResponse(BaseModel):
    """Base model for LLM responses"""
    text: str
    usage: Dict[str, int] = {}
    
class LLMService:
    """Service for interacting with Language Models"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """Initialize the LLM service
        
        Args:
            api_key: API key for the LLM provider (defaults to env var)
            model: Model to use for LLM requests
        """
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.model = model
        self.api_base_url = os.environ.get("LLM_API_BASE_URL", "https://api.openai.com/v1")
        
        # For development/testing without actual API calls
        self.mock_mode = os.environ.get("LLM_MOCK_MODE", "false").lower() == "true"
        logger.info(f"LLM Service initialized with model: {model}, mock mode: {self.mock_mode}")
    
    async def extract_memories(self, conversation_text: str, user_id: str) -> List[Dict[str, Any]]:
        """Extract user memories from conversation text
        
        Args:
            conversation_text: Text of the conversation
            user_id: ID of the user
            
        Returns:
            List of extracted memories as dictionaries
        """
        if self.mock_mode:
            # Return mock memories for testing
            return self._mock_extract_memories(conversation_text)
        
        prompt = f"""
        Extract important information about the user from the following conversation.
        Focus on personal facts, preferences, and opinions that might be useful to remember.
        Format each memory as a JSON object with fields:
        - content: the actual memory
        - type: one of [FACT, PREFERENCE, OPINION]
        - importance: a number from 1-5 (5 being most important)
        
        Conversation:
        {conversation_text}
        
        Return ONLY a JSON array of memory objects, nothing else.
        """
        
        try:
            response = await self._call_llm(prompt)
            # Parse the response as JSON
            memories = json.loads(response.text)
            if not isinstance(memories, list):
                logger.warning("LLM didn't return a list of memories")
                return []
            return memories
        except Exception as e:
            logger.error(f"Error extracting memories: {e}")
            return []
    
    async def generate_summary(self, conversation_text: str, session_id: str) -> Dict[str, Any]:
        """Generate a summary of the conversation
        
        Args:
            conversation_text: Text of the conversation
            session_id: ID of the session
            
        Returns:
            Summary as a dictionary
        """
        if self.mock_mode:
            return self._mock_generate_summary(conversation_text)
        
        prompt = f"""
        Summarize the following conversation in a concise way.
        Focus on the main topics discussed and key points.
        
        Conversation:
        {conversation_text}
        
        Return ONLY a JSON object with fields:
        - content: the summary text
        - topics: array of main topics discussed
        - importance: a number from 1-5 (5 being most important)
        """
        
        try:
            response = await self._call_llm(prompt)
            # Parse the response as JSON
            summary = json.loads(response.text)
            return summary
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {"content": "", "topics": [], "importance": 1}
    
    async def enhance_context(self, query: str, memories: List[Dict[str, Any]], 
                             summary: Optional[Dict[str, Any]] = None) -> str:
        """Enhance a query with relevant memories and summary
        
        Args:
            query: User query to enhance
            memories: List of relevant memories
            summary: Optional session summary
            
        Returns:
            Enhanced context string
        """
        if self.mock_mode:
            return self._mock_enhance_context(query, memories, summary)
        
        memories_text = "\n".join([f"- {m['content']} (Type: {m['type']}, Importance: {m['importance']})" 
                                 for m in memories])
        
        summary_text = ""
        if summary and summary.get('content'):
            summary_text = f"\nSession Summary: {summary['content']}\nTopics: {', '.join(summary.get('topics', []))}"
        
        prompt = f"""
        Given the following user query and contextual information about the user,
        provide an enhanced context that can help answer the query more effectively.
        
        User Query: {query}
        
        User Memories:
        {memories_text}
        
        {summary_text}
        
        Return ONLY the enhanced context, written in a way that provides helpful background
        for answering the user's query. Do not answer the query directly.
        """
        
        try:
            response = await self._call_llm(prompt, max_tokens=300)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error enhancing context: {e}")
            return ""
    
    async def _call_llm(self, prompt: str, max_tokens: int = 500, 
                       temperature: float = 0.7) -> LLMResponse:
        """Make an API call to the LLM provider
        
        Args:
            prompt: Prompt to send to the LLM
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            LLMResponse object
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract the generated text from the response
                text = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                
                return LLMResponse(text=text, usage=usage)
        except Exception as e:
            logger.error(f"Error calling LLM API: {e}")
            # Return a fallback response
            return LLMResponse(text="I apologize, but I couldn't process that request.")
    
    # Mock methods for testing without API calls
    def _mock_extract_memories(self, conversation_text: str) -> List[Dict[str, Any]]:
        """Generate mock memories for testing"""
        # Simple keyword-based memory extraction for testing
        memories = []
        
        if "like" in conversation_text.lower():
            memories.append({
                "content": "User likes discussing AI technology",
                "type": "PREFERENCE",
                "importance": 3
            })
        
        if "name" in conversation_text.lower():
            memories.append({
                "content": "User's name might be mentioned in conversation",
                "type": "FACT",
                "importance": 4
            })
            
        # Always add at least one memory for testing
        memories.append({
            "content": "User is interested in Rainbow City system",
            "type": "OPINION",
            "importance": 2
        })
        
        return memories
    
    def _mock_generate_summary(self, conversation_text: str) -> Dict[str, Any]:
        """Generate a mock summary for testing"""
        # Simple length-based summary
        if len(conversation_text) > 500:
            return {
                "content": "This was a detailed conversation about Rainbow City systems and features",
                "topics": ["Rainbow City", "AI", "Features"],
                "importance": 3
            }
        else:
            return {
                "content": "Brief conversation about Rainbow City",
                "topics": ["Rainbow City"],
                "importance": 2
            }
    
    def _mock_enhance_context(self, query: str, memories: List[Dict[str, Any]], 
                             summary: Optional[Dict[str, Any]] = None) -> str:
        """Generate mock enhanced context for testing"""
        memory_texts = [m["content"] for m in memories]
        memory_context = " ".join(memory_texts)
        
        summary_text = ""
        if summary and summary.get("content"):
            summary_text = f" Based on previous conversation: {summary['content']}."
            
        return f"Context for query '{query}': {memory_context}.{summary_text}"
