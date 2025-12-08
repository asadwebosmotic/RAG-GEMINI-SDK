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
                    description="Search through uploaded PDF documents using RAG (Retrieval Augmented Generation). Use this when the user asks questions about uploaded documents or needs information from uploaded PDFs.",
                    parameters=types.Schema(
                        type='OBJECT',
                        properties={
                            "query": types.Schema(
                                type='STRING',
                                description="The search query to find relevant information in the PDF documents"
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
                    description="Search the web for current information, news, or general knowledge. Use this for real-time information, recent events, or information not in uploaded documents.",
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
                    description="Send a webhook event to trigger external workflows (e.g., n8n automation). Use this when the user wants to trigger an external action or workflow.",
                    parameters=types.Schema(
                        type='OBJECT',
                        properties={
                            "event_type": types.Schema(
                                type='STRING',
                                description="Type of event to trigger (e.g., 'user_action', 'notification', 'task_complete')"
                            ),
                            "payload": types.Schema(
                                type='OBJECT',
                                description="Additional data to send with the webhook event"
                            )
                        },
                        required=["event_type", "payload"]
                    )
                )
            ]
        )
    ]
    
    return tools
