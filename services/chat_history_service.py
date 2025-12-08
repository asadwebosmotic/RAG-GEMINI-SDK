import logging
from typing import List, Dict, Optional
import json
from config import settings
from core.dependencies import get_cache

logger = logging.getLogger(__name__)


class ChatHistoryService:
    """Manage chat history in Redis or in-memory fallback"""
    
    def __init__(self):
        self.cache = get_cache()
        self.max_history = settings.MAX_CHAT_HISTORY
    
    def _get_key(self, session_id: str) -> str:
        return f"chat_history:{session_id}"
    
    async def get_history(self, session_id: str) -> List[Dict]:
        """Retrieve chat history for a session"""
        try:
            key = self._get_key(session_id)
            
            if isinstance(self.cache, dict):
                history_json = self.cache.get(key)
            else:
                history_json = self.cache.get(key) if hasattr(self.cache, 'get') else None
            
            if history_json:
                if isinstance(history_json, str):
                    try:
                        history = json.loads(history_json)
                    except json.JSONDecodeError:
                        history = []
                else:
                    history = history_json
                if isinstance(history, list):
                    return history[-self.max_history:]  # Return last N messages
            return []
        
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return []
    
    async def add_message(self, session_id: str, role: str, text: str):
        """Add a message to chat history"""
        try:
            key = self._get_key(session_id)
            history = await self.get_history(session_id)
            
            message = {
                "role": role,
                "text": text
            }
            
            history.append(message)
            
            # Keep only last N messages
            history = history[-self.max_history:]
            
            # Store back
            if isinstance(self.cache, dict):
                self.cache[key] = history
            else:
                history_json = json.dumps(history)
                if hasattr(self.cache, 'setex'):
                    self.cache.setex(key, 86400 * 7, history_json)  # 7 days TTL
                else:
                    self.cache[key] = history
        
        except Exception as e:
            logger.error(f"Error adding message to history: {e}")
    
    async def clear_history(self, session_id: str):
        """Clear chat history for a session"""
        try:
            key = self._get_key(session_id)
            if isinstance(self.cache, dict):
                self.cache.pop(key, None)
            else:
                self.cache.delete(key)
        except Exception as e:
            logger.error(f"Error clearing chat history: {e}")
    
    def format_for_gemini(self, history: List[Dict]) -> List[Dict]:
        """
        Format chat history for Gemini API.
        Gemini expects: [{"role": "user", "text": "..."}, {"role": "model", "text": "..."}]
        """
        formatted = []
        for msg in history:
            formatted.append({
                "role": msg["role"],
                "text": msg["text"]
            })
        return formatted


chat_history_service = ChatHistoryService()

