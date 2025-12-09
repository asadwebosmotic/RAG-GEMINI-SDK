import logging
from typing import Dict, Any, List, Optional

from google import genai
from google.genai import types
from google.genai.types import Content, Part, FunctionCall

from config import settings
from tools.gemini_tools import get_tool_configs
from services.rag_service import rag_search
from services.tavily_service import web_search
from services.weather_service import get_weather
from services.webhook_service import send_webhook_event

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Gemini function-calling service using the NEW official Gemini SDK.

    - Uses models.generate_content_async()
    - Supports multi-tool-call loop
    - Correctly formats FunctionCallPart + FunctionResponsePart
    - Stateless chat without history
    """

    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model = settings.GEMINI_MODEL or "gemini-2.0-flash"
        self.tools = get_tool_configs()

    # -------------------------------------------------------------------------
    # Executes backend Python tools when Gemini requests them
    # -------------------------------------------------------------------------
    async def execute_tool(self, tool_name: str, args: Dict[str, Any], user_id: str, token_tracker: Dict[str, int]):
        try:
            if tool_name == "rag_search":
                result = await rag_search(args.get("query", ""), args.get("top_k", 5), user_id)
                logger.info(f"rag_search returned {len(result.get('results', []))} results")
                
                # Track embedding tokens
                embedding_tokens_used = result.get("embedding_tokens", 0)
                token_tracker["embedding_tokens"] += embedding_tokens_used
                logger.info(f"Embedding tokens used: {embedding_tokens_used}")
                
                return result

            elif tool_name == "web_search":
                return await web_search(args.get("query", ""), args.get("depth", "basic"))

            elif tool_name == "get_weather":
                return await get_weather(args.get("location", ""), args.get("unit", "metric"))

            elif tool_name == "send_webhook_event":
                # Handle empty args properly
                event_type = args.get("event_type", "user_action")
                payload = args.get("payload", {})
                
                # Convert empty strings to defaults
                if not event_type or event_type.strip() == "":
                    event_type = "user_action"
                if payload is None or (isinstance(payload, str) and payload.strip() == ""):
                    payload = {}
                
                logger.info(f"Calling send_webhook_event with event_type='{event_type}', payload={payload}")
                return await send_webhook_event(event_type, payload)

            logger.error(f"Unknown tool requested: {tool_name}")
            return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.exception(f"Tool execution failed: {tool_name}")
            return {"error": str(e)}



    # -------------------------------------------------------------------------
    # Main chat method — function-calling loop
    # -------------------------------------------------------------------------
    async def chat(
        self,
        user_message: str,
        user_id: str = "anonymous"
    ) -> Dict[str, Any]:

        # -----------------------------------------------
        # Build conversation with system instruction + user message
        # -----------------------------------------------
        system_instruction = """You are an Intelligent AI assistant Who is an Orchaestrator. So you first
        analyses the user query and decide what to reply. The reply should be from your general knowledge or
        from the tools you have. You have five different tools as below:
        1. rag_Search: For personal documents/uploaded content in vector db.
        2. Web_Search: For general knowledge, current events, famous people or anything not avaialble in the rag search vector db.
        3. get_weather: Weather queries only.
        4. send_webhook_event: triggers webhook url if mentioned/asked in the query.
        
        Choose the right tool for each query.

        Be concise. No tool explanations."""

        contents: List[Content] = [
            Content(
                role="user",
                parts=[types.Part(text=f"{system_instruction}\n\nUser Query: {user_message}")]
            )
        ]

        tool_results = []
        max_iterations = 3
        iteration = 0
        
        # Initialize token tracker
        token_tracker = {"total_tokens": 0, "embedding_tokens": 0}

        # -----------------------------------------------
        # Tool-calling loop
        # -----------------------------------------------
        while iteration < max_iterations:
            iteration += 1

            # Retry logic for rate limits
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    response = await self.client.aio.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                            tools=self.tools
                        )
                    )
                    
                    # Track token usage
                    if hasattr(response, 'usage_metadata') and response.usage_metadata:
                        token_tracker["total_tokens"] += response.usage_metadata.total_token_count
                        logger.info(f"Gemini API tokens used: {response.usage_metadata.total_token_count}")
                    
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    error_str = str(e)
                    
                    # Check if it's a rate limit error
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        retry_count += 1
                        if retry_count < max_retries:
                            wait_time = 2 ** retry_count  # Exponential backoff: 2, 4, 8 seconds
                            logger.warning(f"Rate limit hit. Retrying in {wait_time}s... (attempt {retry_count}/{max_retries})")
                            import asyncio
                            await asyncio.sleep(wait_time)
                        else:
                            logger.error(f"Rate limit exceeded after {max_retries} retries")
                            raise  # Re-raise after all retries exhausted
                    else:
                        # Not a rate limit error, raise immediately
                        raise

            candidate = response.candidates[0] if response.candidates else None
            if not candidate:
                return {"text": "No response.", "tool_calls": tool_results}

            tool_calls: List[FunctionCall] = []
            response_text = ""

            # -----------------------------------------------
            # Parse response parts: function calls OR text
            # -----------------------------------------------
            for part in candidate.content.parts:
                if part.function_call:
                    tool_calls.append(part.function_call)

                elif part.text:
                    response_text += part.text

            # If no tool calls → final answer
            if not tool_calls:
                return {
                    "text": response_text, 
                    "tool_calls": tool_results,
                    "usage": {
                        "total_tokens": token_tracker["total_tokens"],
                        "embedding_tokens": token_tracker["embedding_tokens"]
                    }
                }

            # -----------------------------------------------
            # Execute tool calls
            # -----------------------------------------------
            function_response_parts: List[Part] = []

            for fc in tool_calls:
                tool_name = fc.name
                args = dict(fc.args.items()) if hasattr(fc.args, "items") else fc.args

                logger.info(f"Gemini requesting tool '{tool_name}' with args={args}")

                tool_result = await self.execute_tool(tool_name, args, user_id, token_tracker)

                tool_results.append({
                    "tool": tool_name,
                    "args": args,
                    "result": tool_result
                })

                function_response_parts.append(
                    types.Part(
                    function_response=types.FunctionResponse(
                        name=tool_name,
                        response=tool_result
                    )
                )
            )

            # -----------------------------------------------
            # Append function responses to conversation
            # -----------------------------------------------
            contents.append(
                types.Content(
                    role="user",  # MUST be user! (this is how docs specify)
                    parts=function_response_parts
                )
            )

        # Exceeded tool loop
        return {
            "text": "Tool call loop exceeded.",
            "tool_calls": tool_results,
            "usage": {
                "total_tokens": token_tracker["total_tokens"],
                "embedding_tokens": token_tracker["embedding_tokens"]
            }
        }


# Singleton instance
gemini_service = GeminiService()
