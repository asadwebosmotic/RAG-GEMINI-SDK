from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from services.gemini_service import gemini_service
from services.chat_history_service import chat_history_service

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    user_id: Optional[str] = "anonymous"


class ChatResponse(BaseModel):
    text: str
    tool_calls: List[Dict[str, Any]]
    session_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with Gemini function calling"""
    try:
        # Get chat history
        history = await chat_history_service.get_history(request.session_id)
        formatted_history = chat_history_service.format_for_gemini(history)
        
        # Get response from Gemini
        response = await gemini_service.chat(
            message=request.message,
            history=formatted_history,
            user_id=request.user_id or "anonymous"
        )
        
        # Add messages to history
        await chat_history_service.add_message(
            request.session_id,
            "user",
            request.message
        )
        await chat_history_service.add_message(
            request.session_id,
            "model",
            response["text"]
        )
        
        return ChatResponse(
            text=response["text"],
            tool_calls=response.get("tool_calls", []),
            session_id=request.session_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.delete("/chat/{session_id}")
async def clear_chat(session_id: str):
    """Clear chat history for a session"""
    try:
        await chat_history_service.clear_history(session_id)
        return {"message": "Chat history cleared", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")

