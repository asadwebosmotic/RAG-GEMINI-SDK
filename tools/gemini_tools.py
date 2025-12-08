"""
Gemini tool definitions for function calling.
Each tool maps to a service function.
"""
from typing import List, Dict, Any

# Tool schemas in Gemini format
TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "name": "rag_search",
        "description": "Search through uploaded PDF documents using RAG (Retrieval Augmented Generation). Use this when the user asks questions about uploaded documents or needs information from PDFs.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant information in the PDF documents"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of top results to return (default: 5, max: 10)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "web_search",
        "description": "Search the web for current information, news, or general knowledge. Use this for real-time information, recent events, or information not in uploaded documents.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to search the web"
                },
                "depth": {
                    "type": "string",
                    "description": "Search depth: 'basic' for quick results or 'advanced' for comprehensive results",
                    "enum": ["basic", "advanced"],
                    "default": "basic"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_weather",
        "description": "Get current weather information for a specific location. Use this when users ask about weather conditions.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or location (e.g., 'New York', 'London, UK')"
                },
                "unit": {
                    "type": "string",
                    "description": "Temperature unit: 'metric' for Celsius or 'imperial' for Fahrenheit",
                    "enum": ["metric", "imperial"],
                    "default": "metric"
                }
            },
            "required": ["location"]
        }
    },
    {
        "name": "send_webhook_event",
        "description": "Send a webhook event to trigger external workflows (e.g., n8n automation). Use this when the user wants to trigger an external action or workflow.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Type of event to trigger (e.g., 'user_action', 'notification', 'task_complete')"
                },
                "payload": {
                    "type": "object",
                    "description": "Additional data to send with the webhook event",
                    "additionalProperties": True
                }
            },
            "required": ["event_type", "payload"]
        }
    }
]


def get_tool_configs() -> List[Dict[str, Any]]:
    """Get tool configurations for Gemini API"""
    return TOOLS_SCHEMA

