from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from services.gemini_service import gemini_service

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"

class ChatResponse(BaseModel):
    text: str
    tool_calls: List[Dict[str, Any]]
    usage: Dict[str, int]

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with Gemini function calling"""
    try:
        # Get response from Gemini (no history for stateless operation)
        response = await gemini_service.chat(
            user_message=request.message,
            user_id=request.user_id or "anonymous"
        )
        
        return ChatResponse(
            text=response["text"],
            tool_calls=response.get("tool_calls", []),
            usage=response.get("usage", {"total_tokens": 0, "embedding_tokens": 0})
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

