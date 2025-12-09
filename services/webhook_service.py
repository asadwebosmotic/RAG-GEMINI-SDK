import logging
from typing import Dict, Any, Optional
import httpx
from config import settings

logger = logging.getLogger(__name__)


async def send_webhook_event(event_type: str = "user_action", payload: Optional[Dict[str, Any]] = None) -> Dict:
    """
    Send webhook event to configured webhook URL (e.g., n8n).
    
    Args:
        event_type: Type of event (default: "user_action")
        payload: Event payload dictionary (default: empty dict)
    
    Returns:
        Dictionary with webhook response status
    """
    logger.info(f"send_webhook_event called with event_type='{event_type}', payload={payload}")
    
    # Handle empty strings and None values
    if not event_type or event_type.strip() == "":
        event_type = "user_action"
        logger.info(f"Using default event_type: {event_type}")
    
    if payload is None:
        payload = {}
        logger.info(f"Using default payload: {payload}")
    elif isinstance(payload, str) and payload.strip() == "":
        payload = {}
        logger.info(f"Empty string payload, using default: {payload}")
    
    logger.info(f"Final parameters - event_type: '{event_type}', payload: {payload}")
    
    if not settings.WEBHOOK_URL:
        logger.warning("WEBHOOK_URL not configured, skipping webhook")
        return {
            "success": False,
            "message": "Webhook URL not configured"
        }
    
    try:
        from datetime import datetime
        webhook_payload = {
            "event_type": event_type,
            "payload": payload or {"source": "RAG-GEMINI-SDK"},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Attempting to send webhook to: {settings.WEBHOOK_URL}")
        logger.info(f"Webhook payload: {webhook_payload}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.WEBHOOK_URL,
                json=webhook_payload,
                timeout=10.0
            )
            response.raise_for_status()
            
            logger.info(f"Webhook sent successfully: {event_type} - Status: {response.status_code}")
            return {
                "success": True,
                "event_type": event_type,
                "status_code": response.status_code,
                "message": "Webhook sent successfully"
            }
    
    except httpx.HTTPStatusError as e:
        error_msg = f"Webhook returned {e.response.status_code} error"
        if e.response.status_code == 404:
            error_msg = "Webhook URL not found (404). Please verify the webhook URL is correct and the n8n workflow is active."
        elif e.response.status_code == 401 or e.response.status_code == 403:
            error_msg = "Webhook authentication failed. Check if the webhook requires authentication."
        
        logger.error(f"Webhook HTTP error: {error_msg}")
        return {
            "success": False,
            "event_type": event_type,
            "error": error_msg,
            "status_code": e.response.status_code
        }
    
    except Exception as e:
        logger.error(f"Error sending webhook: {e}")
        return {
            "success": False,
            "event_type": event_type,
            "error": f"Failed to send webhook: {str(e)}"
        }

