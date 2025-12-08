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
    async def execute_tool(self, tool_name: str, args: Dict[str, Any], user_id: str):
        try:
            if tool_name == "rag_search":
                return await rag_search(args.get("query", ""), args.get("top_k", 5), user_id)

            elif tool_name == "web_search":
                return await web_search(args.get("query", ""), args.get("depth", "basic"))

            elif tool_name == "get_weather":
                return await get_weather(args.get("location", ""), args.get("unit", "metric"))

            elif tool_name == "send_webhook_event":
                return await send_webhook_event(args.get("event_type", ""), args.get("payload", {}))

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
        # Build conversation with just the user message
        # -----------------------------------------------
        contents: List[Content] = [
            Content(
                role="user",
                parts=[types.Part(text=user_message)]
            )
        ]

        tool_results = []
        max_iterations = 6
        iteration = 0

        # -----------------------------------------------
        # Tool-calling loop
        # -----------------------------------------------
        while iteration < max_iterations:
            iteration += 1

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    tools=self.tools
                )
            )

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
                return {"text": response_text, "tool_calls": tool_results}

            # -----------------------------------------------
            # Execute tool calls
            # -----------------------------------------------
            function_response_parts: List[Part] = []

            for fc in tool_calls:
                tool_name = fc.name
                args = dict(fc.args.items()) if hasattr(fc.args, "items") else fc.args

                logger.info(f"Gemini requesting tool '{tool_name}' with args={args}")

                tool_result = await self.execute_tool(tool_name, args, user_id)

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
            "tool_calls": tool_results
        }


# Singleton instance
gemini_service = GeminiService()
