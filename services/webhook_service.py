import logging
from typing import Dict, Any, Optional
import httpx
from config import settings

logger = logging.getLogger(__name__)


async def send_webhook_event(event_type: str, payload: Dict[str, Any]) -> Dict:
    """
    Send webhook event to configured webhook URL (e.g., n8n).
    
    Args:
        event_type: Type of event
        payload: Event payload dictionary
    
    Returns:
        Dictionary with webhook response status
    """
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
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.WEBHOOK_URL,
                json=webhook_payload,
                timeout=10.0
            )
            response.raise_for_status()
            
            logger.info(f"Webhook sent successfully: {event_type}")
            return {
                "success": True,
                "event_type": event_type,
                "status_code": response.status_code,
                "message": "Webhook sent successfully"
            }
    
    except Exception as e:
        logger.error(f"Error sending webhook: {e}")
        return {
            "success": False,
            "event_type": event_type,
            "error": str(e)
        }

