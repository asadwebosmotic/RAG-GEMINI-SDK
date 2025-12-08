from fastapi import APIRouter
from typing import Dict
from core.dependencies import get_redis_client

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict:
    """Health check endpoint"""
    redis_status = "connected" if get_redis_client() else "disconnected"
    
    return {
        "status": "healthy",
        "services": {
            "redis": redis_status,
            "api": "operational"
        }
    }


@router.get("/")
async def root() -> Dict:
    """Root endpoint"""
    return {
        "message": "AI Agent Backend API",
        "version": "1.0.0"
    }

