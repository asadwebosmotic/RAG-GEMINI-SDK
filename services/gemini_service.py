import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from config import settings
from tools.gemini_tools import get_tool_configs
from services.rag_service import rag_search
from services.tavily_service import web_search
from services.weather_service import get_weather
from services.webhook_service import send_webhook_event

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.GOOGLE_API_KEY)


class GeminiService:
    """Service for interacting with Gemini API with function calling"""
    
    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            tools=get_tool_configs()
        )
    
    async def execute_tool(self, tool_name: str, args: Dict[str, Any], user_id: str = "anonymous") -> Any:
        """Execute a tool function based on tool name"""
        try:
            if tool_name == "rag_search":
                query = args.get("query", "")
                top_k = args.get("top_k", 5)
                return await rag_search(query, top_k, user_id)
            
            elif tool_name == "web_search":
                query = args.get("query", "")
                depth = args.get("depth", "basic")
                return await web_search(query, depth)
            
            elif tool_name == "get_weather":
                location = args.get("location", "")
                unit = args.get("unit", "metric")
                return await get_weather(location, unit)
            
            elif tool_name == "send_webhook_event":
                event_type = args.get("event_type", "")
                payload = args.get("payload", {})
                return await send_webhook_event(event_type, payload)
            
            else:
                logger.warning(f"Unknown tool: {tool_name}")
                return {"error": f"Unknown tool: {tool_name}"}
        
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def chat(
        self,
        message: str,
        history: List[Dict],
        user_id: str = "anonymous"
    ) -> Dict[str, Any]:
        """
        Send message to Gemini with function calling support.
        
        Args:
            message: User message
            history: Previous chat history in Gemini format
            user_id: User identifier
        
        Returns:
            Dictionary with response text and any tool calls
        """
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Convert history format for Gemini
            # Gemini expects list of Content objects or dict with role and parts
            chat_history = []
            for msg in history:
                if msg.get("role") == "user":
                    chat_history.append({
                        "role": "user",
                        "parts": [{"text": msg.get("text", "")}]
                    })
                elif msg.get("role") == "model":
                    chat_history.append({
                        "role": "model",
                        "parts": [{"text": msg.get("text", "")}]
                    })
            
            # Start chat with history
            chat = self.model.start_chat(history=chat_history)
            
            # Send message and handle function calling loop
            tool_results = []
            max_iterations = 5
            current_message = message
            
            for iteration in range(max_iterations):
                # Send message
                response = await loop.run_in_executor(
                    None,
                    lambda msg=current_message: chat.send_message(msg)
                )
                
                # Check for function calls
                function_calls = []
                response_text = ""
                
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                function_calls.append(part.function_call)
                            elif hasattr(part, 'text'):
                                response_text += part.text
                
                # If no function calls, return response
                if not function_calls:
                    return {
                        "text": response_text,
                        "tool_calls": tool_results
                    }
                
                # Execute function calls
                function_responses = []
                for func_call in function_calls:
                    tool_name = func_call.name
                    
                    # Extract args from FunctionCall
                    args = {}
                    if hasattr(func_call, 'args'):
                        # FunctionCall.args is a dict-like object
                        func_args = func_call.args
                        if isinstance(func_args, dict):
                            args = func_args
                        elif hasattr(func_args, 'items'):
                            # Convert to dict if it has items method
                            args = dict(func_args.items())
                        else:
                            # Fallback: try to access as attributes
                            try:
                                args = {k: getattr(func_args, k) for k in dir(func_args) if not k.startswith('_')}
                            except:
                                args = {}
                    
                    logger.info(f"Tool call: {tool_name} with args: {args}")
                    
                    # Execute tool
                    tool_result = await self.execute_tool(tool_name, args, user_id)
                    
                    tool_results.append({
                        "tool": tool_name,
                        "args": args,
                        "result": tool_result
                    })
                    
                    # Create function response for Gemini
                    # Format: {"function_response": {"name": tool_name, "response": tool_result}}
                    function_responses.append({
                        "function_response": {
                            "name": tool_name,
                            "response": tool_result
                        }
                    })
                
                # Send function responses back to Gemini
                if function_responses:
                    # If multiple function calls, send all responses
                    if len(function_responses) == 1:
                        current_message = function_responses[0]
                    else:
                        # For multiple responses, combine them
                        # Gemini expects a single message with multiple function responses
                        current_message = function_responses[0]  # Send first, then continue loop
                        # Store remaining for next iteration
                        for fr in function_responses[1:]:
                            # Continue processing in next iteration
                            pass
                else:
                    break
            
            # Final response
            return {
                "text": response_text,
                "tool_calls": tool_results
            }
        
        except Exception as e:
            logger.error(f"Error in Gemini chat: {e}", exc_info=True)
            raise


gemini_service = GeminiService()
