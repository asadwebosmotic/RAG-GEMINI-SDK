"""
Gemini tool definitions for function calling.
Each tool maps to a service function.
"""
from typing import List
from google.genai import types

def get_tool_configs() -> List[types.Tool]:
    """Get tool configurations for Gemini API using proper SDK types"""
    
    # Define tools using Google GenAI SDK types
    tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="rag_search",
                    description="Search user's uploaded documents and personal knowledge base. Use for questions about personal information, documents, or content that might be in uploaded PDFs.",
                    parameters=types.Schema(
                        type='OBJECT',
                        properties={
                            "query": types.Schema(
                                type='STRING',
                                description="The search query to find relevant information in the user's documents"
                            ),
                            "top_k": types.Schema(
                                type='INTEGER',
                                description="Number of top results to return (default: 5, max: 10)"
                            )
                        },
                        required=["query"]
                    )
                ),
                types.FunctionDeclaration(
                    name="web_search",
                    description="Search the internet for current information, general knowledge, or topics not in personal documents. Use for famous people, current events, or general questions.",
                    parameters=types.Schema(
                        type='OBJECT',
                        properties={
                            "query": types.Schema(
                                type='STRING',
                                description="The search query to search the web"
                            ),
                            "depth": types.Schema(
                                type='STRING',
                                description="Search depth: 'basic' for quick results or 'advanced' for comprehensive results"
                            )
                        },
                        required=["query"]
                    )
                ),
                types.FunctionDeclaration(
                    name="get_weather",
                    description="Get current weather information for a specific location. Use this when users ask about weather conditions.",
                    parameters=types.Schema(
                        type='OBJECT',
                        properties={
                            "location": types.Schema(
                                type='STRING',
                                description="City name or location (e.g., 'New York', 'London, UK')"
                            ),
                            "unit": types.Schema(
                                type='STRING',
                                description="Temperature unit: 'metric' for Celsius or 'imperial' for Fahrenheit"
                            )
                        },
                        required=["location"]
                    )
                ),
                types.FunctionDeclaration(
                    name="send_webhook_event",
                    description=(
                        "Trigger the webhook immediately. "
                        "If the user does NOT specify event_type or payload, "
                        "use default values automatically. "
                        "Call this function whenever the user asks to 'trigger webhook', "
                        "'send webhook', 'fire webhook', or similar."),
                    parameters=types.Schema(
                        type='OBJECT',
                        properties={
                            "event_type": types.Schema(
                                type='STRING',
                                description="Type of event to trigger (default: 'user_action')"
                            ),
                            "payload": types.Schema(
                                type='OBJECT',
                                description="Additional data to send with the webhook event (default: empty dict)"
                            )
                        },
                        required=[]  # Nothing is required - both have defaults
                    )
                )
            ]
        )
    ]
    
    return tools
